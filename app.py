"""
PL Number Material Request Management System
Streamlit Web Application with STRICT Business Rule Enforcement

CRITICAL PRINCIPLE:
"If any limit is exceeded, the system must block the request completely."
NO WARNINGS, NO OVERRIDES, NO PARTIAL APPROVALS
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from business_logic import (
    PLNumberManager,
    RequestManager,
    UserManager,
    ValidationError,
    make_ist_datetime,
    utc_to_ist
)
from database import get_database


# Page configuration
st.set_page_config(
    page_title="PL Request Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
        white-space: pre-line;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'pl_manager' not in st.session_state:
        st.session_state.pl_manager = PLNumberManager()
    
    if 'request_manager' not in st.session_state:
        st.session_state.request_manager = RequestManager()
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    if 'db_connected' not in st.session_state:
        try:
            db = get_database()
            st.session_state.db_connected = db.connected
        except Exception as e:
            st.session_state.db_connected = False
            st.session_state.db_error = str(e)
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    
    if 'emp_id' not in st.session_state:
        st.session_state.emp_id = None


def check_database_connection():
    """Check database connection and show error if not connected"""
    if not st.session_state.get('db_connected', False):
        st.error("❌ Database Connection Failed")
        st.error(st.session_state.get('db_error', 'Unknown error'))
        st.info("""
        **Setup Instructions:**
        1. Create a `.env` file in the project directory
        2. Add your MongoDB Atlas connection string:
           ```
           MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
           DATABASE_NAME=pl_request_system
           ```
        3. Restart the application
        """)
        st.stop()


def page_login():
    """Login page"""
    st.title("🔐 Login to PL Request System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Enter Your Credentials")
        
        with st.form("login_form"):
            emp_id = st.text_input("Employee ID", placeholder="e.g., EMP001")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            user_type = st.radio("Login Type", options=["Normal User", "Admin"], horizontal=True)
            
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                if not emp_id or not password:
                    st.error("Please enter both Employee ID and Password")
                else:
                    # Check if any users exist
                    all_users = st.session_state.user_manager.get_all_users()
                    
                    # Bootstrap: allow ADMIN/admin to create first user
                    if not all_users and emp_id.upper() == "ADMIN" and password == "admin":
                        st.session_state.logged_in = True
                        st.session_state.emp_id = "ADMIN"
                        st.session_state.user_type = "admin"
                        st.success("Welcome, ADMIN! Please create your first user account.")
                        st.rerun()
                    else:
                        # Authenticate against database
                        user = st.session_state.user_manager.authenticate_user(emp_id, password)
                        
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.emp_id = user['emp_id']
                            st.session_state.user_type = user['user_type']
                            st.success(f"Welcome, {user['emp_id']}!")
                            st.rerun()
                        else:
                            st.error("Invalid Employee ID or Password")


def page_add_pl_number():
    """Page: Add New PL Number"""
    st.title("📦 Add New PL Number")
    st.markdown("---")
    
    with st.form("add_pl_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            pl_no = st.text_input(
                "PL Number *",
                placeholder="e.g., PL-001",
                help="Unique identifier for the product"
            )
            product_name = st.text_input(
                "Product Name *",
                placeholder="e.g., Widget Type A"
            )
            ear = st.number_input(
                "EAR (Estimated Annual Requirement) *",
                min_value=1,
                value=1000,
                step=1,
                help="Yearly hard limit - cannot be exceeded"
            )
        
        with col2:
            global_limit = st.number_input(
                "Global Limit *",
                min_value=1,
                value=1000,
                step=1,
                help="Must be ≤ EAR"
            )
            
            st.markdown("### Section Limits")
            st.info("Sum of section limits should not exceed Global Limit")
        
        # Section limits
        st.markdown("### Section-wise Limits")
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            limit_a = st.number_input("Section A *", min_value=0, value=250, step=1)
        with col_b:
            limit_b = st.number_input("Section B *", min_value=0, value=250, step=1)
        with col_c:
            limit_c = st.number_input("Section C *", min_value=0, value=250, step=1)
        with col_d:
            limit_d = st.number_input("Section D *", min_value=0, value=250, step=1)
        
        # Show sum
        total_section_limits = limit_a + limit_b + limit_c + limit_d
        if total_section_limits > global_limit:
            st.warning(f"⚠️ Sum of section limits ({total_section_limits}) exceeds Global Limit ({global_limit})")
        else:
            st.success(f"✅ Sum of section limits: {total_section_limits} / {global_limit}")
        
        submitted = st.form_submit_button("➕ Add PL Number", type="primary", width='stretch')
        
        if submitted:
            try:
                section_limits = {
                    'A': limit_a,
                    'B': limit_b,
                    'C': limit_c,
                    'D': limit_d
                }
                
                product = st.session_state.pl_manager.add_pl_number(
                    pl_no=pl_no,
                    product_name=product_name,
                    ear=ear,
                    global_limit=global_limit,
                    section_limits=section_limits
                )
                
                st.success(f"✅ PL Number '{product['pl_no']}' added successfully!")
                st.balloons()
                
            except ValidationError as e:
                st.error(f"❌ Validation Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def page_add_request():
    """Page: Add New Request with STRICT Validation"""
    st.title("📝 Add New Material Request")
    st.markdown("---")
    
    st.warning("⚠️ **STRICT ENFORCEMENT**: Requests that violate section or yearly limits will be BLOCKED")
    
    # Get all PL numbers
    try:
        all_products = st.session_state.pl_manager.get_all_pl_numbers()
        
        if not all_products:
            st.info("ℹ️ No PL Numbers found. Please add a PL Number first.")
            if st.button("➕ Go to Add PL Number"):
                st.session_state.page = "add_pl"
                st.rerun()
            return
        
        pl_options = {f"{p['pl_no']} - {p['product_name']}": p['pl_no'] for p in all_products}
        
    except Exception as e:
        st.error(f"Error loading PL Numbers: {str(e)}")
        return
    
    # PL Number selection (outside form for reactivity)
    selected_pl = st.selectbox(
        "Select PL Number *",
        options=list(pl_options.keys()),
        help="Choose the product for which you're requesting materials"
    )
    
    # Show current status BEFORE the form
    if selected_pl:
        pl_no = pl_options[selected_pl]
        
        with st.expander("📊 View Current Status", expanded=False):
            try:
                summary = st.session_state.request_manager.get_pl_summary(pl_no)
                
                st.markdown(f"**Product:** {summary['product_name']}")
                st.markdown(f"**EAR:** {summary['ear']} | **Global Limit:** {summary['global_limit']}")
                
                # Section status
                cols = st.columns(4)
                for idx, section in enumerate(['A', 'B', 'C', 'D']):
                    with cols[idx]:
                        sect_data = summary['sections'][section]
                        st.metric(
                            f"Section {section}",
                            f"{sect_data['delivered']} / {sect_data['limit']}",
                            delta=f"{sect_data['remaining']} remaining"
                        )
                
                # Yearly status
                yearly = summary['yearly']
                st.progress(yearly['percentage_used'] / 100)
                st.markdown(f"**Yearly Total:** {yearly['delivered']} / {yearly['limit']} ({yearly['percentage_used']}% used)")
                
            except Exception as e:
                st.error(f"Error loading summary: {str(e)}")
    
    with st.form("add_request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Section selection inside form
            requested_by = st.selectbox(
                "Requesting Section *",
                options=['A', 'B', 'C', 'D'],
                help="Your section"
            )
        
        with col2:
            requested_count = st.number_input(
                "Requested Quantity *",
                min_value=1,
                value=1,
                step=1,
                help="Number of units requested"
            )
            
            request_date = st.date_input(
                "Request Date *",
                value=datetime.now(),
                help="Date of the request"
            )
        
        submitted = st.form_submit_button("🔍 Validate & Submit Request", type="primary", width='stretch')
        
        if submitted:
            try:
                pl_no = pl_options[selected_pl]
                
                # CRITICAL: Validate before saving
                st.info("🔍 Validating request against business rules...")
                
                is_valid, message, details = st.session_state.request_manager.validate_request(
                    pl_no=pl_no,
                    requested_by=requested_by,
                    requested_count=requested_count
                )
                
                if is_valid:
                    # Validation passed - create request
                    request = st.session_state.request_manager.create_request(
                        pl_no=pl_no,
                        requested_by=requested_by,
                        requested_count=requested_count,
                        request_date=make_ist_datetime(request_date),
                        emp_id=st.session_state.emp_id
                    )
                    
                    st.success("✅ REQUEST SAVED")
                    st.markdown(f"<div class='success-box'>{message}</div>", unsafe_allow_html=True)
                    st.balloons()
                    
                else:
                    # Validation failed - DO NOT SAVE
                    st.error("❌ REQUEST BLOCKED")
                    st.markdown(f"<div class='error-box'>{message}</div>", unsafe_allow_html=True)
                    
            except ValidationError as e:
                st.error("❌ REQUEST BLOCKED")
                st.markdown(f"<div class='error-box'>{str(e)}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ System Error: {str(e)}")


def page_view_pl_summary():
    """Page: View PL Number Summary"""
    st.title("📊 PL Number Summary")
    st.markdown("---")
    
    try:
        all_products = st.session_state.pl_manager.get_all_pl_numbers()
        
        if not all_products:
            st.info("ℹ️ No PL Numbers found.")
            return
        
        # Selection
        pl_options = {f"{p['pl_no']} - {p['product_name']}": p['pl_no'] for p in all_products}
        selected_pl = st.selectbox("Select PL Number", options=list(pl_options.keys()))
        
        if selected_pl:
            pl_no = pl_options[selected_pl]
            
            # Get summary
            summary = st.session_state.request_manager.get_pl_summary(pl_no)
            
            # Product info
            st.markdown(f"## {summary['pl_no']} - {summary['product_name']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("EAR (Yearly Limit)", summary['ear'])
            with col2:
                st.metric("Global Limit", summary['global_limit'])
            with col3:
                yearly = summary['yearly']
                st.metric(
                    "Yearly Delivered",
                    f"{yearly['delivered']} / {yearly['limit']}",
                    delta=f"{yearly['remaining']} remaining"
                )
            
            # Progress bar
            st.progress(yearly['percentage_used'] / 100)
            st.caption(f"Yearly consumption: {yearly['percentage_used']}%")
            
            st.markdown("---")
            
            # Section breakdown
            st.markdown("### Section-wise Breakdown")
            
            section_data = []
            for section in ['A', 'B', 'C', 'D']:
                sect = summary['sections'][section]
                section_data.append({
                    'Section': section,
                    'Limit': sect['limit'],
                    'Approved': sect['approved'],
                    'Delivered': sect['delivered'],
                    'Remaining': sect['remaining'],
                    'Used %': sect['percentage_used']
                })
            
            df = pd.DataFrame(section_data)
            
            # Display as table
            st.dataframe(
                df,
                width='stretch',
                hide_index=True
            )
            
            # Simple status display
            st.markdown("### Section Status")
            status_cols = st.columns(4)
            for i, section in enumerate(['A', 'B', 'C', 'D']):
                sect = summary['sections'][section]
                with status_cols[i]:
                    st.metric(
                        f"Section {section}", 
                        f"{sect['delivered']}/{sect['limit']}", 
                        f"{sect['percentage_used']:.1f}% used"
                    )
            
    except Exception as e:
        st.error(f"Error: {str(e)}")


def page_view_requests():
    """Page: View All Requests"""
    st.title("📋 View Requests")
    st.markdown("---")
    
    try:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            all_products = st.session_state.pl_manager.get_all_pl_numbers()
            pl_options = ["All"] + [f"{p['pl_no']} - {p['product_name']}" for p in all_products]
            selected_filter = st.selectbox("Filter by PL Number", options=pl_options)
        
        with col2:
            section_filter = st.selectbox("Filter by Section", options=["All", "A", "B", "C", "D"])
        
        with col3:
            status_filter = st.selectbox("Filter by Status", options=["All", "pending", "delivered"])
        
        # Get requests
        pl_no_filter = None
        if selected_filter != "All":
            pl_no_filter = selected_filter.split(" - ")[0]
        
        requests = st.session_state.request_manager.get_all_requests(pl_no=pl_no_filter)
        
        if not requests:
            st.info("ℹ️ No requests found.")
            return
        
        # Apply filters
        filtered_requests = requests
        
        if section_filter != "All":
            filtered_requests = [r for r in filtered_requests if r['requested_by'] == section_filter]
        
        if status_filter != "All":
            filtered_requests = [r for r in filtered_requests if r['status'] == status_filter]
        
        st.markdown(f"**Total Requests:** {len(filtered_requests)}")
        
        # Convert to DataFrame for display
        display_data = []
        for req in filtered_requests:
            display_data.append({
                'Request ID': str(req['_id'])[:8],
                'PL No.': req['pl_no'],
                'Section': req['requested_by'],
                'Emp ID': req.get('requested_by_emp_id', '-'),
                'Requested': req['requested_count'],
                'Request Date': utc_to_ist(req['request_date']).strftime('%Y-%m-%d'),
                'Approved By': req.get('approved_by', '-'),
                'Delivered': str(req.get('delivered_count', 0)) if req.get('delivered_count') else '-',
                'Delivery Date': utc_to_ist(req['delivered_date']).strftime('%Y-%m-%d') if req.get('delivered_date') else '-',
                'Status': req['status'].upper()
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")


def page_approve_requests():
    """Page: Approve Pending Requests & Update Deliveries (Admin Only)"""
    st.title("✅ Approve Requests & Update Deliveries")
    st.markdown("---")
    
    try:
        # Get all requests that need attention (pending or approved but not delivered)
        all_requests = st.session_state.request_manager.get_all_requests()
        pending_requests = [r for r in all_requests if r['status'] == 'pending']
        approved_requests = [r for r in all_requests if r['status'] == 'approved']
        
        # Show pending requests for approval
        if pending_requests:
            st.markdown("### 📋 Pending Requests (Need Approval)")
            st.markdown(f"**Pending Requests:** {len(pending_requests)}")
            
            for req in pending_requests:
                with st.container():
                    st.markdown(f"#### Request ID: {str(req['_id'])[:8]}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"**PL No:** {req['pl_no']}")
                        st.markdown(f"**Section:** {req['requested_by']}")
                    
                    with col2:
                        st.markdown(f"**Emp ID:** {req.get('requested_by_emp_id', '-')}")
                        st.markdown(f"**Requested:** {req['requested_count']}")
                    
                    with col3:
                        st.markdown(f"**Request Date:** {utc_to_ist(req['request_date']).strftime('%Y-%m-%d')}")
                        st.markdown("**Status:** PENDING")
                    
                    with col4:
                        # Approval options
                        action = st.radio(
                            "Action",
                            options=["Just Approve", "Approve & Deliver"],
                            key=f"action_{req['_id']}",
                            horizontal=True
                        )
                        
                        if action == "Just Approve":
                            if st.button(f"✅ Approve", key=f"approve_{req['_id']}"):
                                try:
                                    success = st.session_state.request_manager.approve_request(
                                        request_id=str(req['_id']),
                                        approved_by_emp_id=st.session_state.emp_id
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Request {str(req['_id'])[:8]} approved!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to approve request")
                                        
                                except ValidationError as e:
                                    st.error(f"Validation Error: {str(e)}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        elif action == "Approve & Deliver":
                            with st.form(f"approve_deliver_{req['_id']}"):
                                delivered_count = st.number_input(
                                    "Delivered Quantity", 
                                    min_value=1, 
                                    max_value=req['requested_count'], 
                                    value=req['requested_count']
                                )
                                delivered_date = st.date_input("Delivery Date", value=datetime.now())
                                
                                if st.form_submit_button("✅ Approve & Deliver"):
                                    try:
                                        # First approve
                                        approve_success = st.session_state.request_manager.approve_request(
                                            request_id=str(req['_id']),
                                            approved_by_emp_id=st.session_state.emp_id
                                        )
                                        
                                        if approve_success:
                                            # Then update delivery
                                            deliver_success = st.session_state.request_manager.update_delivery(
                                                request_id=str(req['_id']),
                                                delivered_count=delivered_count,
                                                delivered_date=make_ist_datetime(delivered_date)
                                            )
                                            
                                            if deliver_success:
                                                st.success(f"✅ Request {str(req['_id'])[:8]} approved and delivered!")
                                                st.rerun()
                                            else:
                                                st.error("Request approved but delivery update failed")
                                        else:
                                            st.error("Failed to approve request")
                                            
                                    except ValidationError as e:
                                        st.error(f"Validation Error: {str(e)}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    
                    st.markdown("---")
        else:
            st.info("ℹ️ No pending requests to approve.")
        
        # Show approved requests for delivery update
        if approved_requests:
            st.markdown("### 🚚 Approved Requests (Ready for Delivery Update)")
            st.markdown(f"**Approved Requests:** {len(approved_requests)}")
            
            for req in approved_requests:
                with st.container():
                    st.markdown(f"#### Request ID: {str(req['_id'])[:8]}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"**PL No:** {req['pl_no']}")
                        st.markdown(f"**Section:** {req['requested_by']}")
                    
                    with col2:
                        st.markdown(f"**Emp ID:** {req.get('requested_by_emp_id', '-')}")
                        st.markdown(f"**Requested:** {req['requested_count']}")
                    
                    with col3:
                        st.markdown(f"**Request Date:** {utc_to_ist(req['request_date']).strftime('%Y-%m-%d')}")
                        st.markdown(f"**Approved By:** {req.get('approved_by', '-')}")
                        if req.get('approved_at'):
                            st.markdown(f"**Approved Date:** {utc_to_ist(req['approved_at']).strftime('%Y-%m-%d')}")
                        st.markdown("**Status:** APPROVED")
                    
                    with col4:
                        # Delivery update - only full delivery allowed
                        with st.form(f"deliver_{req['_id']}"):
                            st.caption(f"Must deliver full requested quantity: {req['requested_count']}")
                            delivered_date = st.date_input("Delivery Date", value=datetime.now())
                            
                            if st.form_submit_button(f"📦 Deliver {req['requested_count']} units"):
                                try:
                                    success = st.session_state.request_manager.update_delivery(
                                        request_id=str(req['_id']),
                                        delivered_count=req['requested_count'],  # Full delivery only
                                        delivered_date=make_ist_datetime(delivered_date)
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Request {str(req['_id'])[:8]} fully delivered!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update delivery")
                                        
                                except ValidationError as e:
                                    st.error(f"Validation Error: {str(e)}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    
                    st.markdown("---")
        else:
            st.info("ℹ️ No approved requests waiting for delivery.")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")


def page_manage_users():
    """Page: Manage Users (Admin Only)"""
    st.title("👥 Manage Users")
    st.markdown("---")
    
    # Create new user
    st.markdown("### ➕ Create New User")
    with st.form("create_user_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_emp_id = st.text_input("Employee ID", placeholder="e.g., EMP001")
        
        with col2:
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
        
        with col3:
            new_user_type = st.selectbox("User Type", options=["normal", "admin"])
        
        submitted = st.form_submit_button("Create User", type="primary")
        
        if submitted:
            try:
                user = st.session_state.user_manager.create_user(
                    emp_id=new_emp_id,
                    password=new_password,
                    user_type=new_user_type,
                    created_by=st.session_state.emp_id
                )
                
                st.success(f"✅ User '{user['emp_id']}' created successfully!")
                st.rerun()
                
            except ValidationError as e:
                st.error(f"❌ Validation Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    
    # List all users
    st.markdown("### 📋 All Users")
    try:
        users = st.session_state.user_manager.get_all_users()
        
        if not users:
            st.info("No users found.")
        else:
            user_data = []
            for user in users:
                user_data.append({
                    'Emp ID': user['emp_id'],
                    'User Type': user['user_type'].upper(),
                    'Created By': user.get('created_by', '-'),
                    'Created At': utc_to_ist(user['created_at']).strftime('%Y-%m-%d %H:%M'),
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, width='stretch', hide_index=True)
            
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")


def main():
    """Main application"""
    # Initialize
    initialize_session_state()
    check_database_connection()
    
    # Check login
    if not st.session_state.logged_in:
        page_login()
        return
    
    # Sidebar navigation
    st.sidebar.title("🏭 PL Request System")
    st.sidebar.markdown("---")
    
    # User info
    st.sidebar.markdown(f"**User:** {st.session_state.emp_id}")
    st.sidebar.markdown(f"**Type:** {st.session_state.user_type.upper()}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.session_state.emp_id = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navigation options based on user type
    nav_options = [
        "📦 Add PL Number",
        "📝 Add Request",
        "📊 View PL Summary",
        "📋 View Requests"
    ]
    
    if st.session_state.user_type == "admin":
        nav_options.append("✅ Approve Requests")
        nav_options.append("👥 Manage Users")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        key="navigation"
    )
    
    st.sidebar.markdown("---")
    
    # Info box
    st.sidebar.markdown("### ℹ️ System Info")
    st.sidebar.success("✅ Database Connected")
    st.sidebar.caption(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚠️ Business Rules")
    st.sidebar.error("""
    **STRICT ENFORCEMENT:**
    - Section limits are HARD STOPS
    - Yearly limits (EAR) are HARD STOPS
    - No overrides allowed
    - No partial approvals
    """)
    
    # Route to pages
    if page == "📦 Add PL Number":
        page_add_pl_number()
    elif page == "📝 Add Request":
        page_add_request()
    elif page == "📊 View PL Summary":
        page_view_pl_summary()
    elif page == "📋 View Requests":
        page_view_requests()
    elif page == "✅ Approve Requests" and st.session_state.user_type == "admin":
        page_approve_requests()
    elif page == "👥 Manage Users" and st.session_state.user_type == "admin":
        page_manage_users()


if __name__ == "__main__":
    main()
