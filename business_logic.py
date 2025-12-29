"""
Business Logic Module
Implements STRICT business rules for PL Number Material Request Management
ALL RULES ARE NON-NEGOTIABLE AND MUST BE ENFORCED
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_database


def get_ist_time():
    """Get current time in IST (UTC+5:30)"""
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)


def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt.tzinfo is None:
        # If naive, assume it's UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt + timedelta(hours=5, minutes=30)


def make_ist_datetime(date_obj, time_obj=None):
    """Create IST datetime from date and optional time"""
    if time_obj:
        naive_dt = datetime.combine(date_obj, time_obj)
    else:
        naive_dt = datetime.combine(date_obj, datetime.min.time())
    
    # Make it timezone-aware as IST
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return naive_dt.replace(tzinfo=ist_tz)


class ValidationError(Exception):
    """Custom exception for business rule violations"""
    pass


class PLNumberManager:
    """
    Manages PL Numbers (Products) with strict limit enforcement
    """
    
    VALID_SECTIONS = ['A', 'B', 'C', 'D']
    
    def __init__(self):
        self.db = get_database()
        self.products_collection = self.db.get_products_collection()
    
    def add_pl_number(
        self,
        pl_no: str,
        product_name: str,
        ear: int,
        global_limit: int,
        section_limits: Dict[str, int]
    ) -> Dict:
        """
        Add a new PL Number with validation
        
        Args:
            pl_no: Unique PL Number identifier
            product_name: Product name
            ear: Estimated Annual Requirement (yearly hard limit)
            global_limit: Global limit (must be <= EAR)
            section_limits: Dictionary with section limits for A, B, C, D
        
        Returns:
            Created product document
        
        Raises:
            ValidationError: If validation fails
        """
        # VALIDATION: Check all required fields
        if not pl_no or not pl_no.strip():
            raise ValidationError("PL No. cannot be empty")
        
        if not product_name or not product_name.strip():
            raise ValidationError("Product name cannot be empty")
        
        # VALIDATION: EAR must be positive
        if ear <= 0:
            raise ValidationError("EAR (Estimated Annual Requirement) must be greater than 0")
        
        # VALIDATION: Global limit must be positive and <= EAR
        if global_limit <= 0:
            raise ValidationError("Global limit must be greater than 0")
        
        if global_limit > ear:
            raise ValidationError(f"Global limit ({global_limit}) cannot exceed EAR ({ear})")
        
        # VALIDATION: All 4 sections must be present
        if not all(section in section_limits for section in self.VALID_SECTIONS):
            raise ValidationError(f"All sections {self.VALID_SECTIONS} must have defined limits")
        
        # VALIDATION: All section limits must be non-negative
        for section, limit in section_limits.items():
            if section not in self.VALID_SECTIONS:
                raise ValidationError(f"Invalid section '{section}'. Must be one of {self.VALID_SECTIONS}")
            
            if limit < 0:
                raise ValidationError(f"Section {section} limit cannot be negative")
        
        # VALIDATION: Sum of section limits should not exceed global limit
        total_section_limits = sum(section_limits.values())
        if total_section_limits > global_limit:
            raise ValidationError(
                f"Sum of section limits ({total_section_limits}) cannot exceed "
                f"global limit ({global_limit})"
            )
        
        # VALIDATION: Check if PL No. already exists
        if self.products_collection.find_one({'pl_no': pl_no.strip().upper()}):
            raise ValidationError(f"PL No. '{pl_no}' already exists")
        
        # Create product document
        product = {
            'pl_no': pl_no.strip().upper(),
            'product_name': product_name.strip(),
            'ear': ear,
            'global_limit': global_limit,
            'section_limits': {
                'A': section_limits['A'],
                'B': section_limits['B'],
                'C': section_limits['C'],
                'D': section_limits['D']
            },
            'created_at': get_ist_time()
        }
        
        # Insert into database
        result = self.products_collection.insert_one(product)
        product['_id'] = result.inserted_id
        
        return product
    
    def get_all_pl_numbers(self) -> List[Dict]:
        """
        Retrieve all PL Numbers
        """
        return list(self.products_collection.find().sort('pl_no', 1))
    
    def get_pl_number(self, pl_no: str) -> Optional[Dict]:
        """
        Retrieve a specific PL Number
        """
        return self.products_collection.find_one({'pl_no': pl_no.strip().upper()})
    
    def update_pl_number(
        self,
        pl_no: str,
        ear: int,
        global_limit: int,
        section_limits: Dict[str, int]
    ) -> bool:
        """
        Update PL Number limits (ADMIN ONLY)
        Validates that new limits don't violate existing requests
        """
        # Get existing product
        product = self.get_pl_number(pl_no)
        if not product:
            raise ValidationError(f"PL No. '{pl_no}' not found")
        
        # Validate new limits
        if ear <= 0:
            raise ValidationError("EAR must be greater than 0")
        
        if global_limit <= 0 or global_limit > ear:
            raise ValidationError(f"Global limit must be between 1 and {ear}")
        
        for section in self.VALID_SECTIONS:
            if section not in section_limits or section_limits[section] < 0:
                raise ValidationError(f"Invalid section limit for {section}")
        
        if sum(section_limits.values()) > global_limit:
            raise ValidationError("Sum of section limits exceeds global limit")
        
        # Update document
        result = self.products_collection.update_one(
            {'pl_no': pl_no.strip().upper()},
            {
                '$set': {
                    'ear': ear,
                    'global_limit': global_limit,
                    'section_limits': section_limits,
                    'updated_at': get_ist_time()
                }
            }
        )
        
        return result.modified_count > 0


class RequestManager:
    """
    Manages Material Requests with STRICT BUSINESS RULE ENFORCEMENT
    
    CRITICAL: All requests must pass validation before being saved
    NO WARNINGS, NO OVERRIDES, NO PARTIAL APPROVALS
    """
    
    VALID_SECTIONS = ['A', 'B', 'C', 'D']
    
    def __init__(self):
        self.db = get_database()
        self.requests_collection = self.db.get_requests_collection()
        self.pl_manager = PLNumberManager()
    
    def _get_section_total_requested(self, pl_no: str, section: str) -> int:
        """
        Calculate total requested quantity for a specific section
        
        Args:
            pl_no: PL Number
            section: Section (A/B/C/D)
        
        Returns:
            Total requested quantity for the section
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper(),
                    'requested_by': section
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$requested_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def _get_section_total_approved(self, pl_no: str, section: str) -> int:
        """
        Calculate total approved quantity for a specific section
        
        Args:
            pl_no: PL Number
            section: Section (A/B/C/D)
        
        Returns:
            Total approved quantity for the section
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper(),
                    'requested_by': section,
                    'status': {'$in': ['approved', 'delivered']}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$requested_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def _get_section_total_delivered(self, pl_no: str, section: str) -> int:
        """
        Calculate total delivered quantity for a specific section
        
        Args:
            pl_no: PL Number
            section: Section (A/B/C/D)
        
        Returns:
            Total delivered quantity for the section
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper(),
                    'requested_by': section,
                    'status': 'delivered'
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$delivered_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def _get_total_requested_all_sections(self, pl_no: str) -> int:
        """
        Calculate total requested quantity across ALL sections
        
        Args:
            pl_no: PL Number
        
        Returns:
            Total requested quantity across all sections
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper()
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$requested_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def _get_total_approved_all_sections(self, pl_no: str) -> int:
        """
        Calculate total approved quantity across ALL sections
        
        Args:
            pl_no: PL Number
        
        Returns:
            Total approved quantity across all sections
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper(),
                    'status': {'$in': ['approved', 'delivered']}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$requested_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def _get_total_delivered_all_sections(self, pl_no: str) -> int:
        """
        Calculate total delivered quantity across ALL sections
        
        Args:
            pl_no: PL Number
        
        Returns:
            Total delivered quantity across all sections
        """
        pipeline = [
            {
                '$match': {
                    'pl_no': pl_no.strip().upper(),
                    'status': 'delivered'
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$delivered_count'}
                }
            }
        ]
        
        result = list(self.requests_collection.aggregate(pipeline))
        return result[0]['total'] if result else 0
    
    def validate_request(
        self,
        pl_no: str,
        requested_by: str,
        requested_count: int
    ) -> Tuple[bool, str, Dict]:
        """
        CRITICAL VALIDATION METHOD
        Enforces ALL business rules before allowing a request
        
        Args:
            pl_no: PL Number
            requested_by: Requesting section (A/B/C/D)
            requested_count: Quantity requested
        
        Returns:
            Tuple of (is_valid, error_message, validation_details)
        
        Business Rules Enforced:
        1. PL Number must exist
        2. Section must be valid (A/B/C/D)
        3. Requested count must be positive
        4. SECTION LIMIT: existing section total + new request <= section limit
        5. YEARLY LIMIT: total all sections + new request <= EAR and global_limit
        """
        validation_details = {}
        
        # RULE 1: PL Number must exist
        product = self.pl_manager.get_pl_number(pl_no)
        if not product:
            return False, f"PL No. '{pl_no}' does not exist", validation_details
        
        validation_details['product'] = product
        
        # RULE 2: Section must be valid
        if requested_by not in self.VALID_SECTIONS:
            return False, f"Invalid section '{requested_by}'. Must be one of {self.VALID_SECTIONS}", validation_details
        
        # RULE 3: Requested count must be positive
        if requested_count <= 0:
            return False, "Requested count must be greater than 0", validation_details
        
        # Get current totals
        section_total = self._get_section_total_requested(pl_no, requested_by)
        all_sections_total = self._get_total_requested_all_sections(pl_no)
        
        validation_details['section_total'] = section_total
        validation_details['all_sections_total'] = all_sections_total
        validation_details['section_limit'] = product['section_limits'][requested_by]
        validation_details['ear'] = product['ear']
        validation_details['global_limit'] = product['global_limit']
        
        # RULE 4: SECTION LIMIT ENFORCEMENT (NON-NEGOTIABLE)
        section_limit = product['section_limits'][requested_by]
        new_section_total = section_total + requested_count
        
        if new_section_total > section_limit:
            error_msg = (
                f"❌ SECTION LIMIT EXCEEDED\n"
                f"Section {requested_by} limit: {section_limit}\n"
                f"Already requested: {section_total}\n"
                f"New request: {requested_count}\n"
                f"Would total: {new_section_total}\n"
                f"❌ REQUEST BLOCKED - Exceeds limit by {new_section_total - section_limit}"
            )
            return False, error_msg, validation_details
        
        # RULE 5: YEARLY LIMIT ENFORCEMENT (NON-NEGOTIABLE)
        # Check against both EAR and global_limit (use the more restrictive)
        yearly_limit = min(product['ear'], product['global_limit'])
        new_yearly_total = all_sections_total + requested_count
        
        if new_yearly_total > yearly_limit:
            error_msg = (
                f"❌ YEARLY LIMIT EXCEEDED\n"
                f"EAR (Yearly Limit): {product['ear']}\n"
                f"Global Limit: {product['global_limit']}\n"
                f"Effective Limit: {yearly_limit}\n"
                f"Already requested (all sections): {all_sections_total}\n"
                f"New request: {requested_count}\n"
                f"Would total: {new_yearly_total}\n"
                f"❌ REQUEST BLOCKED - Exceeds limit by {new_yearly_total - yearly_limit}"
            )
            return False, error_msg, validation_details
        
        # ALL VALIDATIONS PASSED
        success_msg = (
            f"✅ REQUEST VALIDATED\n"
            f"Section {requested_by}: {new_section_total}/{section_limit} "
            f"({section_limit - new_section_total} remaining)\n"
            f"Yearly Total: {new_yearly_total}/{yearly_limit} "
            f"({yearly_limit - new_yearly_total} remaining)"
        )
        
        return True, success_msg, validation_details
    
    def create_request(
        self,
        pl_no: str,
        requested_by: str,
        requested_count: int,
        request_date: Optional[datetime] = None,
        emp_id: str = None
    ) -> Dict:
        """
        Create a new material request
        
        CRITICAL: Request will ONLY be created if ALL validations pass
        
        Args:
            pl_no: PL Number
            requested_by: Requesting section (A/B/C/D)
            requested_count: Quantity requested
            request_date: Date of request (defaults to now)
            emp_id: Employee ID of the requester
        
        Returns:
            Created request document
        
        Raises:
            ValidationError: If ANY business rule is violated
        """
        # MANDATORY VALIDATION - THIS IS THE GATEKEEPER
        is_valid, message, details = self.validate_request(
            pl_no,
            requested_by,
            requested_count
        )
        
        if not is_valid:
            # REQUEST BLOCKED - DO NOT SAVE TO DATABASE
            raise ValidationError(message)
        
        # Validation passed - create request
        request = {
            'pl_no': pl_no.strip().upper(),
            'requested_by': requested_by,
            'requested_by_emp_id': emp_id,
            'requested_count': requested_count,
            'request_date': request_date or get_ist_time(),
            'delivered_count': None,
            'delivered_date': None,
            'status': 'pending',
            'created_at': get_ist_time()
        }
        
        # Insert into database
        result = self.requests_collection.insert_one(request)
        request['_id'] = result.inserted_id
        
        return request
    
    def get_all_requests(self, pl_no: Optional[str] = None) -> List[Dict]:
        """
        Retrieve all requests, optionally filtered by PL Number
        """
        query = {}
        if pl_no:
            query['pl_no'] = pl_no.strip().upper()
        
        return list(self.requests_collection.find(query).sort('request_date', -1))
    
    def update_delivery(
        self,
        request_id: str,
        delivered_count: int,
        delivered_date: Optional[datetime] = None
    ) -> bool:
        """
        Update delivery information for a request
        
        NOTE: Delivered quantity does NOT affect limit calculations
        Limits are based on REQUESTED quantities only
        """
        from bson.objectid import ObjectId
        
        if delivered_count <= 0:
            raise ValidationError("Delivered count must be greater than 0")
        
        # Get the request to validate
        request = self.requests_collection.find_one({'_id': ObjectId(request_id)})
        if not request:
            raise ValidationError("Request not found")
        
        if delivered_count > request['requested_count']:
            raise ValidationError(f"Delivered count ({delivered_count}) cannot exceed requested count ({request['requested_count']})")
        
        # Determine status: only allow full delivery
        if delivered_count != request['requested_count']:
            raise ValidationError(f"Partial delivery not allowed. Must deliver full requested quantity ({request['requested_count']})")
        
        # Full delivery - mark as delivered
        result = self.requests_collection.update_one(
            {'_id': ObjectId(request_id)},
            {
                '$set': {
                    'delivered_count': delivered_count,
                    'delivered_date': delivered_date or get_ist_time(),
                    'status': 'delivered',
                    'updated_at': get_ist_time()
                }
            }
        )
        
        return result.modified_count > 0
    
    def approve_request(
        self,
        request_id: str,
        approved_by_emp_id: str
    ) -> bool:
        """
        Approve a pending request
        
        Args:
            request_id: Request ID
            approved_by_emp_id: Employee ID of the approver
        
        Returns:
            True if approved successfully
        
        Raises:
            ValidationError: If request not found or not pending
        """
        from bson.objectid import ObjectId
        
        # Get request
        request = self.requests_collection.find_one({'_id': ObjectId(request_id)})
        if not request:
            raise ValidationError("Request not found")
        
        if request['status'] != 'pending':
            raise ValidationError("Request is not pending")
        
        # Approve
        result = self.requests_collection.update_one(
            {'_id': ObjectId(request_id)},
            {
                '$set': {
                    'status': 'approved',
                    'approved_by': approved_by_emp_id,
                    'approved_at': get_ist_time(),
                    'updated_at': get_ist_time()
                }
            }
        )
        
        return result.modified_count > 0
    
    def get_pl_summary(self, pl_no: str) -> Dict:
        """
        Get comprehensive summary for a PL Number
        Shows limits vs usage for each section (approved and delivered)
        """
        product = self.pl_manager.get_pl_number(pl_no)
        if not product:
            raise ValidationError(f"PL No. '{pl_no}' not found")
        
        summary = {
            'pl_no': product['pl_no'],
            'product_name': product['product_name'],
            'ear': product['ear'],
            'global_limit': product['global_limit'],
            'sections': {}
        }
        
        # Calculate usage for each section (approved and delivered)
        total_approved = 0
        total_delivered = 0
        for section in self.VALID_SECTIONS:
            approved_total = self._get_section_total_approved(pl_no, section)
            delivered_total = self._get_section_total_delivered(pl_no, section)
            section_limit = product['section_limits'][section]
            
            summary['sections'][section] = {
                'limit': section_limit,
                'approved': approved_total,
                'delivered': delivered_total,
                'remaining': section_limit - delivered_total,
                'percentage_used': round((delivered_total / section_limit * 100) if section_limit > 0 else 0, 2)
            }
            
            total_approved += approved_total
            total_delivered += delivered_total
        
        # Overall yearly summary
        yearly_limit = min(product['ear'], product['global_limit'])
        summary['yearly'] = {
            'limit': yearly_limit,
            'approved': total_approved,
            'delivered': total_delivered,
            'remaining': yearly_limit - total_delivered,
            'percentage_used': round((total_delivered / yearly_limit * 100) if yearly_limit > 0 else 0, 2)
        }
        
        return summary


class UserManager:
    """
    Manages user authentication and user data
    """
    
    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db.get_users_collection()
    
    def create_user(self, emp_id: str, password: str, user_type: str, created_by: str = None) -> Dict:
        """
        Create a new user
        
        Args:
            emp_id: Employee ID (unique)
            password: Plain text password
            user_type: 'admin' or 'normal'
            created_by: Emp ID of the creator (for audit)
        
        Returns:
            Created user document
        
        Raises:
            ValidationError: If validation fails
        """
        if not emp_id or not emp_id.strip():
            raise ValidationError("Emp ID cannot be empty")
        
        if not password or not password.strip():
            raise ValidationError("Password cannot be empty")
        
        if user_type not in ['admin', 'normal']:
            raise ValidationError("User type must be 'admin' or 'normal'")
        
        # Check if emp_id already exists
        if self.users_collection.find_one({'emp_id': emp_id.strip().upper()}):
            raise ValidationError(f"Emp ID '{emp_id}' already exists")
        
        # Create user document
        user = {
            'emp_id': emp_id.strip().upper(),
            'password': password.strip(),
            'user_type': user_type,
            'created_by': created_by,
            'created_at': get_ist_time()
        }
        
        # Insert into database
        result = self.users_collection.insert_one(user)
        user['_id'] = result.inserted_id
        
        return user
    
    def authenticate_user(self, emp_id: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user
        
        Args:
            emp_id: Employee ID
            password: Password
        
        Returns:
            User document if authenticated, None otherwise
        """
        user = self.users_collection.find_one({
            'emp_id': emp_id.strip().upper(),
            'password': password.strip()
        })
        
        return user
    
    def get_user(self, emp_id: str) -> Optional[Dict]:
        """
        Get user by emp_id
        """
        return self.users_collection.find_one({'emp_id': emp_id.strip().upper()})
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all users
        """
        return list(self.users_collection.find().sort('emp_id', 1))
    
    def update_user_password(self, emp_id: str, new_password: str, updated_by: str) -> bool:
        """
        Update user password
        
        Args:
            emp_id: Employee ID
            new_password: New password
            updated_by: Who updated it
        
        Returns:
            True if updated
        """
        if not new_password or not new_password.strip():
            raise ValidationError("New password cannot be empty")
        
        result = self.users_collection.update_one(
            {'emp_id': emp_id.strip().upper()},
            {
                '$set': {
                    'password': new_password.strip(),
                    'updated_by': updated_by,
                    'updated_at': get_ist_time()
                }
            }
        )
        
        return result.modified_count > 0
