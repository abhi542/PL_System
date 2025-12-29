# PL Number Material Request Management System

A production-grade Streamlit web application for managing PL Number material requests with **STRICT, NON-NEGOTIABLE** business rule enforcement.

## 🎯 Core Principle

> **"If any limit is exceeded, the system must block the request completely."**

- ❌ NO warnings
- ❌ NO overrides
- ❌ NO partial approvals
- ✅ ONLY complete enforcement

---

## 📋 System Overview

This application manages material requests for products (PL Numbers) with fixed yearly and section-wise limits. The system enforces business rules at the database level, preventing any request that would violate constraints.

### Key Features

- **PL Number Management**: Define products with limits
- **Request Management**: Submit and track material requests
- **Strict Validation**: Automatic enforcement of all business rules
- **Real-time Monitoring**: Track usage vs. limits
- **Delivery Tracking**: Update delivery status (doesn't affect limits)

---

## 🏗️ Architecture

### Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Database**: MongoDB Atlas (Cloud)
- **Validation**: Business logic layer with strict enforcement

### Project Structure

```
pl_request_system/
├── app.py                  # Main Streamlit application
├── business_logic.py       # Business rules & validation
├── database.py             # MongoDB connection & config
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── .env                   # Your configuration (create this)
├── README.md              # This file
└── SCHEMA.md              # Database schema documentation
```

---

## 🚀 Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (free tier works)
- pip (Python package manager)

### 2. MongoDB Atlas Setup

1. **Create a MongoDB Atlas account** at https://www.mongodb.com/cloud/atlas
2. **Create a new cluster** (free M0 tier is sufficient)
3. **Configure network access**:
   - Go to Network Access
   - Add IP Address: `0.0.0.0/0` (allow access from anywhere)
   - Or add your specific IP address
4. **Create database user**:
   - Go to Database Access
   - Add New Database User
   - Choose password authentication
   - Set username and password (save these!)
   - Grant "Read and write to any database" role
5. **Get connection string**:
   - Go to Database → Connect
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your actual password
   - Replace `<username>` if needed

### 3. Install Dependencies

```bash
# Navigate to project directory
cd pl_request_system

# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your details
# Replace with your actual MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=pl_request_system
```

**Example .env file:**
```
MONGODB_URI=mongodb+srv://myuser:mypassword123@cluster0.abcdef.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=pl_request_system
```

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 📊 Database Schema

### Collections

#### 1. `products` Collection

Stores PL Number definitions with limits.

```javascript
{
  "_id": ObjectId,
  "pl_no": "PL-001",              // Unique identifier (uppercase)
  "product_name": "Widget Type A",
  "ear": 1000,                     // Estimated Annual Requirement
  "global_limit": 1000,            // Must be ≤ EAR
  "section_limits": {
    "A": 250,
    "B": 250,
    "C": 250,
    "D": 250
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:**
- Unique index on `pl_no`

#### 2. `requests` Collection

Stores material requests.

```javascript
{
  "_id": ObjectId,
  "pl_no": "PL-001",               // References products.pl_no
  "requested_by": "A",             // Section: A, B, C, or D
  "requested_count": 50,           // Quantity requested
  "request_date": ISODate,
  "delivered_count": null,         // Null until delivered
  "delivered_date": null,          // Null until delivered
  "status": "pending",             // "pending" or "delivered"
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:**
- Compound index on `(pl_no, requested_by)`
- Index on `request_date`

---

## 🔒 Business Rules (STRICT ENFORCEMENT)

### Rule 1: Section Limit

**Formula:**
```
(existing_section_total + new_request) <= section_limit
```

**Example:**
- Section A limit: 250
- Already requested: 200
- New request: 100
- Result: **BLOCKED** (200 + 100 = 300 > 250)

### Rule 2: Yearly Limit (EAR)

**Formula:**
```
(total_all_sections + new_request) <= min(EAR, global_limit)
```

**Example:**
- EAR: 1000
- Global Limit: 1000
- Already requested (all sections): 950
- New request: 100
- Result: **BLOCKED** (950 + 100 = 1050 > 1000)

### Rule 3: Delivered Quantity

**Important:** Delivered quantities do NOT affect limits.

Limits are calculated based on **REQUESTED** quantities only.

---

## 🖥️ User Interface

### Navigation

The sidebar provides access to 4 main pages:

1. **📦 Add PL Number** - Define new products with limits
2. **📝 Add Request** - Submit material requests (with validation)
3. **📊 View PL Summary** - Monitor usage vs. limits
4. **📋 View Requests** - View and manage all requests

### Adding a PL Number

1. Navigate to "Add PL Number"
2. Fill in:
   - PL Number (unique identifier)
   - Product Name
   - EAR (yearly limit)
   - Global Limit (≤ EAR)
   - Section limits for A, B, C, D
3. Click "Add PL Number"

**Validation:**
- PL No. must be unique
- All values must be positive
- Global limit ≤ EAR
- Sum of section limits should ≤ global limit

### Adding a Request

1. Navigate to "Add Request"
2. Select PL Number
3. Select your section (A/B/C/D)
4. Enter requested quantity
5. Click "Validate & Submit Request"

**The system will:**
- ✅ Accept if all rules pass
- ❌ Block if any rule fails (with detailed error message)

### Viewing Summary

1. Navigate to "View PL Summary"
2. Select a PL Number
3. View:
   - Yearly usage vs. EAR
   - Section-wise breakdown
   - Remaining capacity
   - Visual progress bars

### Managing Requests

1. Navigate to "View Requests"
2. Filter by PL Number, Section, or Status
3. View all requests in table format
4. Update delivery information for pending requests

---

## 🎯 Usage Examples

### Example 1: Successful Request

**Setup:**
- PL-001, Section A limit: 250
- Currently requested: 100

**Request:**
- Section: A
- Quantity: 50

**Result:** ✅ APPROVED
- New total: 150/250
- Remaining: 100

### Example 2: Section Limit Exceeded

**Setup:**
- PL-001, Section B limit: 200
- Currently requested: 180

**Request:**
- Section: B
- Quantity: 50

**Result:** ❌ BLOCKED
```
❌ SECTION LIMIT EXCEEDED
Section B limit: 200
Already requested: 180
New request: 50
Would total: 230
❌ REQUEST BLOCKED - Exceeds limit by 30
```

### Example 3: Yearly Limit Exceeded

**Setup:**
- PL-001, EAR: 1000
- Section A: 300, B: 300, C: 300, D: 50
- Total requested: 950

**Request:**
- Section: D
- Quantity: 100

**Result:** ❌ BLOCKED
```
❌ YEARLY LIMIT EXCEEDED
EAR (Yearly Limit): 1000
Global Limit: 1000
Effective Limit: 1000
Already requested (all sections): 950
New request: 100
Would total: 1050
❌ REQUEST BLOCKED - Exceeds limit by 50
```

---

## 🔧 Troubleshooting

### Database Connection Issues

**Error:** "Database Connection Failed"

**Solutions:**
1. Check `.env` file exists and has correct connection string
2. Verify MongoDB Atlas IP whitelist includes your IP
3. Confirm database user credentials are correct
4. Test connection string in MongoDB Compass

### Import Errors

**Error:** "ModuleNotFoundError"

**Solution:**
```bash
pip install -r requirements.txt
```

### Port Already in Use

**Error:** "Port 8501 is already in use"

**Solution:**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

### Validation Always Failing

**Check:**
1. Ensure PL Number exists
2. Verify section limits are set correctly
3. Check current usage in "View PL Summary"

---

## 🧪 Testing the System

### Test Scenario 1: Basic Flow

1. Add PL Number: PL-TEST-001
   - EAR: 100
   - Section limits: A:25, B:25, C:25, D:25
2. Add requests:
   - Section A: 20 (✅ Should pass)
   - Section A: 10 (❌ Should fail - exceeds 25)
   - Section B: 25 (✅ Should pass)
   - Section C: 25 (✅ Should pass)
   - Section D: 30 (❌ Should fail - exceeds yearly limit)

### Test Scenario 2: Multiple Requests

1. Add multiple small requests for one section
2. Watch the limit approach
3. Try to exceed - should be blocked

### Test Scenario 3: Delivery Updates

1. Submit and approve a request
2. Update delivery information
3. Verify limits are still based on requested quantity

---

## 📝 Code Structure

### `app.py` - Main Application

- Streamlit UI components
- Page routing
- Form handling
- Display logic

### `business_logic.py` - Business Rules

**Classes:**
- `PLNumberManager`: CRUD operations for PL Numbers
- `RequestManager`: Request validation and creation
- `ValidationError`: Custom exception

**Key Methods:**
- `validate_request()`: Enforces ALL business rules
- `create_request()`: Only saves if validation passes
- `get_pl_summary()`: Calculates usage statistics

### `database.py` - Database Layer

- MongoDB connection management
- Collection access
- Index creation
- Singleton pattern for connection

---

## 🔐 Security Considerations

### Current Implementation

- No authentication (internal tool)
- Database credentials in `.env` file
- Local deployment only

### Production Recommendations

1. **Add Authentication:**
   ```python
   import streamlit_authenticator as stauth
   ```

2. **Environment Security:**
   - Never commit `.env` to version control
   - Use `.gitignore` to exclude sensitive files

3. **Database Security:**
   - Use MongoDB Atlas IP whitelist
   - Rotate database credentials regularly
   - Use read-only users for reporting

4. **Audit Logging:**
   - Log all request attempts (approved/rejected)
   - Track who made changes to PL Numbers

---

## 📈 Future Enhancements

### Potential Features

1. **User Authentication & Roles**
   - Admin: Can modify PL Numbers
   - User: Can only submit requests

2. **Email Notifications**
   - Alert when limits are approaching
   - Notify on request approval/rejection

3. **Reporting & Analytics**
   - Export to Excel/PDF
   - Usage trends and forecasting
   - Section-wise consumption patterns

4. **Approval Workflow**
   - Multi-level approval for large requests
   - Manager review for specific thresholds

5. **API Integration**
   - REST API for external systems
   - Webhook notifications

6. **Advanced Filtering**
   - Date range filters
   - Custom reports
   - Dashboard with charts

---

## 🐛 Known Limitations

1. **No Request Modification:** Once created, requests cannot be edited
2. **No Request Deletion:** Requests are permanent (by design)
3. **Single Database:** No replication or backup in current setup
4. **No Concurrency Control:** Race conditions possible with simultaneous requests

---

## 📞 Support

### Common Issues

**Q: Can I override a blocked request?**
A: No. This is by design. The system enforces limits strictly.

**Q: What if I need to increase limits?**
A: Admin users can edit PL Numbers to increase limits, but this doesn't affect past requests.

**Q: Can I delete a request?**
A: No. Requests are permanent to maintain audit trail.

**Q: Why was my request blocked?**
A: The error message shows exactly which limit was exceeded and by how much.

---

## 📄 License

Internal use only. Not for public distribution.

---

## 👥 Credits

Developed as a production-grade internal tool for material request management with strict business rule enforcement.

---

## 🔄 Changelog

### Version 1.0.0 (Initial Release)
- Complete PL Number management
- Strict request validation
- Real-time summary views
- Delivery tracking
- MongoDB Atlas integration
- Clean, production-ready code
