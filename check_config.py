"""
Configuration Checker Script
Validates environment setup before running the application
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Current version: {version_str}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is compatible (3.8+)")
        return True
    else:
        print("❌ Python 3.8 or higher is required")
        print(f"   You have: {version_str}")
        print(f"   Please upgrade Python")
        return False


def check_env_file():
    """Check if .env file exists and has required variables"""
    print_header("Checking Environment Configuration")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("\nTo fix:")
        print("1. Copy .env.example to .env")
        print("   cp .env.example .env")
        print("2. Edit .env with your MongoDB Atlas connection string")
        return False
    
    print("✅ .env file exists")
    
    # Check if file has content
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        if not content.strip():
            print("⚠️  .env file is empty")
            print("   Please add your MongoDB Atlas connection string")
            return False
        
        # Check for required variables
        has_mongodb_uri = 'MONGODB_URI' in content
        has_db_name = 'DATABASE_NAME' in content
        
        if has_mongodb_uri:
            print("✅ MONGODB_URI is defined")
            
            # Check if it's still the placeholder
            if '<username>' in content or '<password>' in content:
                print("⚠️  MONGODB_URI still has placeholders")
                print("   Please replace <username> and <password> with actual values")
                return False
        else:
            print("❌ MONGODB_URI is missing")
            return False
        
        if has_db_name:
            print("✅ DATABASE_NAME is defined")
        else:
            print("⚠️  DATABASE_NAME is missing (will use default: pl_request_system)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {str(e)}")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = {
        'streamlit': 'streamlit',
        'pymongo': 'pymongo',
        'dotenv': 'python-dotenv',
        'pandas': 'pandas'
    }
    
    all_installed = True
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {pip_name} is installed")
        except ImportError:
            print(f"❌ {pip_name} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
    
    return all_installed


def check_database_connection():
    """Test MongoDB Atlas connection"""
    print_header("Checking Database Connection")
    
    try:
        from database import get_database
        
        print("Attempting to connect to MongoDB Atlas...")
        db = get_database()
        
        if db.connected:
            print("✅ Successfully connected to MongoDB Atlas!")
            
            # Try to get collections
            products = db.get_products_collection()
            requests = db.get_requests_collection()
            
            # Get counts
            product_count = products.count_documents({})
            request_count = requests.count_documents({})
            
            print(f"   Database: {os.getenv('DATABASE_NAME', 'pl_request_system')}")
            print(f"   Products in database: {product_count}")
            print(f"   Requests in database: {request_count}")
            
            return True
        else:
            print("❌ Could not connect to MongoDB Atlas")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import database module: {str(e)}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nCommon issues:")
        print("  1. Incorrect connection string in .env")
        print("  2. Network access not configured in MongoDB Atlas")
        print("  3. Wrong username/password")
        print("  4. IP address not whitelisted")
        return False


def check_file_structure():
    """Check if all required files exist"""
    print_header("Checking File Structure")
    
    required_files = [
        ('app.py', 'Main application'),
        ('business_logic.py', 'Business logic'),
        ('database.py', 'Database configuration'),
        ('requirements.txt', 'Dependencies'),
        ('.env.example', 'Environment template')
    ]
    
    all_exist = True
    
    for filename, description in required_files:
        path = Path(filename)
        if path.exists():
            print(f"✅ {filename:20} ({description})")
        else:
            print(f"❌ {filename:20} MISSING ({description})")
            all_exist = False
    
    return all_exist


def run_all_checks():
    """Run all configuration checks"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*13 + "PL REQUEST SYSTEM - CONFIGURATION CHECK" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    
    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Database Connection", check_database_connection),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {check_name}: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print_header("CONFIGURATION CHECK SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {check_name}")
    
    print("\n" + "-"*70)
    print(f"Total Checks: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("-"*70)
    
    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED!")
        print("\nYour system is properly configured and ready to use.")
        print("\nTo start the application:")
        print("  streamlit run app.py")
        print("\nOptional: Run the test suite to verify functionality:")
        print("  python test_system.py")
        return 0
    else:
        print(f"\n⚠️  {failed} CHECK(S) FAILED")
        print("\nPlease fix the issues above before running the application.")
        print("\nFor help, see:")
        print("  - README.md for complete documentation")
        print("  - QUICKSTART.md for quick setup guide")
        return 1


if __name__ == "__main__":
    exit_code = run_all_checks()
    sys.exit(exit_code)
