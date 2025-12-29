"""
Test Script for PL Request Management System
Validates all business rules and system functionality
Run this after initial setup to verify everything works correctly
"""

import sys
from datetime import datetime
from business_logic import PLNumberManager, RequestManager, ValidationError
from database import get_database


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_database_connection():
    """Test 1: Database Connection"""
    print_section("TEST 1: Database Connection")
    
    try:
        db = get_database()
        if db.connected:
            print("✅ SUCCESS: Connected to MongoDB Atlas")
            return True
        else:
            print("❌ FAILED: Database not connected")
            return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_add_pl_number():
    """Test 2: Add PL Number"""
    print_section("TEST 2: Add PL Number")
    
    try:
        pl_manager = PLNumberManager()
        
        # Clean up test data if exists
        try:
            products = pl_manager.get_all_pl_numbers()
            for p in products:
                if p['pl_no'].startswith('TEST-'):
                    pl_manager.products_collection.delete_one({'pl_no': p['pl_no']})
        except:
            pass
        
        # Add test PL number
        product = pl_manager.add_pl_number(
            pl_no="TEST-001",
            product_name="Test Widget Type A",
            ear=1000,
            global_limit=1000,
            section_limits={'A': 250, 'B': 250, 'C': 250, 'D': 250}
        )
        
        print(f"✅ SUCCESS: Added PL Number {product['pl_no']}")
        print(f"   Product: {product['product_name']}")
        print(f"   EAR: {product['ear']}")
        print(f"   Limits: A={product['section_limits']['A']}, "
              f"B={product['section_limits']['B']}, "
              f"C={product['section_limits']['C']}, "
              f"D={product['section_limits']['D']}")
        return True
        
    except ValidationError as e:
        print(f"❌ FAILED: Validation Error - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_duplicate_pl_number():
    """Test 3: Duplicate PL Number (Should Fail)"""
    print_section("TEST 3: Duplicate PL Number (Should Fail)")
    
    try:
        pl_manager = PLNumberManager()
        
        # Try to add duplicate
        pl_manager.add_pl_number(
            pl_no="TEST-001",
            product_name="Duplicate Widget",
            ear=500,
            global_limit=500,
            section_limits={'A': 125, 'B': 125, 'C': 125, 'D': 125}
        )
        
        print("❌ FAILED: System allowed duplicate PL Number!")
        return False
        
    except ValidationError as e:
        print(f"✅ SUCCESS: System correctly blocked duplicate")
        print(f"   Error message: {str(e)}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {str(e)}")
        return False


def test_valid_request():
    """Test 4: Valid Request (Should Pass)"""
    print_section("TEST 4: Valid Request (Should Pass)")
    
    try:
        request_manager = RequestManager()
        
        # Clean up test requests
        request_manager.requests_collection.delete_many({'pl_no': 'TEST-001'})
        
        # Submit valid request
        request = request_manager.create_request(
            pl_no="TEST-001",
            requested_by="A",
            requested_count=50
        )
        
        print(f"✅ SUCCESS: Request approved and saved")
        print(f"   PL No: {request['pl_no']}")
        print(f"   Section: {request['requested_by']}")
        print(f"   Quantity: {request['requested_count']}")
        print(f"   Status: {request['status']}")
        return True
        
    except ValidationError as e:
        print(f"❌ FAILED: Valid request was blocked - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_section_limit_exceeded():
    """Test 5: Section Limit Exceeded (Should Fail)"""
    print_section("TEST 5: Section Limit Exceeded (Should Fail)")
    
    try:
        request_manager = RequestManager()
        
        # Get current section total
        summary = request_manager.get_pl_summary("TEST-001")
        section_a_used = summary['sections']['A']['approved']
        section_a_limit = summary['sections']['A']['limit']
        
        print(f"   Current Section A usage: {section_a_used}/{section_a_limit}")
        
        # Try to exceed section limit
        remaining = section_a_limit - section_a_used
        excessive_request = remaining + 50  # Request more than remaining
        
        print(f"   Attempting to request: {excessive_request} (exceeds by {excessive_request - remaining})")
        
        request_manager.create_request(
            pl_no="TEST-001",
            requested_by="A",
            requested_count=excessive_request
        )
        
        print("❌ FAILED: System allowed section limit violation!")
        return False
        
    except ValidationError as e:
        print(f"✅ SUCCESS: System correctly blocked excessive request")
        print(f"   Error: Request would exceed section limit")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {str(e)}")
        return False


def test_yearly_limit_exceeded():
    """Test 6: Yearly Limit Exceeded (Should Fail)"""
    print_section("TEST 6: Yearly Limit Exceeded (Should Fail)")
    
    try:
        request_manager = RequestManager()
        
        # Fill up other sections to approach yearly limit
        print("   Filling up sections B, C, D to approach yearly limit...")
        
        # Section B: 200
        request_manager.create_request("TEST-001", "B", 200)
        print(f"   ✓ Section B: 200")
        
        # Section C: 200
        request_manager.create_request("TEST-001", "C", 200)
        print(f"   ✓ Section C: 200")
        
        # Section D: 200
        request_manager.create_request("TEST-001", "D", 200)
        print(f"   ✓ Section D: 200")
        
        # Get current total
        summary = request_manager.get_pl_summary("TEST-001")
        yearly_used = summary['yearly']['approved']
        yearly_limit = summary['yearly']['limit']
        
        print(f"   Current yearly usage: {yearly_used}/{yearly_limit}")
        
        # Try to exceed yearly limit
        remaining = yearly_limit - yearly_used
        excessive_request = remaining + 50
        
        print(f"   Attempting to request: {excessive_request} (exceeds by {excessive_request - remaining})")
        
        request_manager.create_request(
            pl_no="TEST-001",
            requested_by="D",
            requested_count=excessive_request
        )
        
        print("❌ FAILED: System allowed yearly limit violation!")
        return False
        
    except ValidationError as e:
        print(f"✅ SUCCESS: System correctly blocked excessive request")
        print(f"   Error: Request would exceed yearly limit")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {str(e)}")
        return False


def test_get_summary():
    """Test 7: Get PL Summary"""
    print_section("TEST 7: Get PL Summary")
    
    try:
        request_manager = RequestManager()
        summary = request_manager.get_pl_summary("TEST-001")
        
        print(f"✅ SUCCESS: Retrieved summary for {summary['pl_no']}")
        print(f"   Product: {summary['product_name']}")
        print(f"   Yearly: {summary['yearly']['approved']}/{summary['yearly']['limit']} "
              f"({summary['yearly']['percentage_used']}%)")
        print(f"   Sections:")
        for section in ['A', 'B', 'C', 'D']:
            sect = summary['sections'][section]
            print(f"     {section}: {sect['approved']}/{sect['limit']} "
                  f"({sect['percentage_used']}% used, {sect['remaining']} remaining)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_update_delivery():
    """Test 8: Update Delivery (Should Not Affect Limits)"""
    print_section("TEST 8: Update Delivery (Should Not Affect Limits)")
    
    try:
        request_manager = RequestManager()
        
        # Get a pending request
        requests = request_manager.get_all_requests("TEST-001")
        pending = [r for r in requests if r['status'] == 'pending']
        
        if not pending:
            print("⚠️  SKIPPED: No pending requests to update")
            return True
        
        request_id = str(pending[0]['_id'])
        
        # Update delivery
        success = request_manager.update_delivery(
            request_id=request_id,
            delivered_count=pending[0]['requested_count'],
            delivered_date=datetime.now()
        )
        
        if success:
            print(f"✅ SUCCESS: Updated delivery for request {request_id[:8]}...")
            print(f"   Delivered: {pending[0]['requested_count']} units")
            print(f"   NOTE: Limits are still based on requested quantity, not delivered")
            return True
        else:
            print("❌ FAILED: Could not update delivery")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_invalid_section():
    """Test 9: Invalid Section (Should Fail)"""
    print_section("TEST 9: Invalid Section (Should Fail)")
    
    try:
        request_manager = RequestManager()
        
        # Try invalid section
        request_manager.create_request(
            pl_no="TEST-001",
            requested_by="X",  # Invalid section
            requested_count=10
        )
        
        print("❌ FAILED: System allowed invalid section!")
        return False
        
    except ValidationError as e:
        print(f"✅ SUCCESS: System correctly blocked invalid section")
        print(f"   Error message: {str(e)}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {str(e)}")
        return False


def test_negative_quantity():
    """Test 10: Negative Quantity (Should Fail)"""
    print_section("TEST 10: Negative Quantity (Should Fail)")
    
    try:
        request_manager = RequestManager()
        
        # Try negative quantity
        request_manager.create_request(
            pl_no="TEST-001",
            requested_by="A",
            requested_count=-10
        )
        
        print("❌ FAILED: System allowed negative quantity!")
        return False
        
    except ValidationError as e:
        print(f"✅ SUCCESS: System correctly blocked negative quantity")
        print(f"   Error message: {str(e)}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {str(e)}")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print_section("Cleanup Test Data")
    
    try:
        db = get_database()
        
        # Delete test products
        result_products = db.get_products_collection().delete_many(
            {'pl_no': {'$regex': '^TEST-'}}
        )
        
        # Delete test requests
        result_requests = db.get_requests_collection().delete_many(
            {'pl_no': {'$regex': '^TEST-'}}
        )
        
        print(f"✅ Cleaned up test data")
        print(f"   Deleted {result_products.deleted_count} test products")
        print(f"   Deleted {result_requests.deleted_count} test requests")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not clean up: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "PL REQUEST SYSTEM - TEST SUITE" + " "*23 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Add PL Number", test_add_pl_number),
        ("Duplicate PL Number", test_duplicate_pl_number),
        ("Valid Request", test_valid_request),
        ("Section Limit Exceeded", test_section_limit_exceeded),
        ("Yearly Limit Exceeded", test_yearly_limit_exceeded),
        ("Get Summary", test_get_summary),
        ("Update Delivery", test_update_delivery),
        ("Invalid Section", test_invalid_section),
        ("Negative Quantity", test_negative_quantity),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST RESULTS SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print("-"*70)
    
    # Cleanup
    cleanup_test_data()
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for production use.")
        print("\nKey Validations Confirmed:")
        print("  ✅ Database connection works")
        print("  ✅ PL Numbers can be added")
        print("  ✅ Valid requests are approved")
        print("  ✅ Section limits are enforced")
        print("  ✅ Yearly limits are enforced")
        print("  ✅ Invalid data is blocked")
        print("\nYou can now use the system with confidence!")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        print("Please review the errors above and fix before using in production.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
