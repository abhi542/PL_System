# Quick Start Guide

Get the PL Request Management System running in **5 minutes**.

---

## Step 1: Prerequisites Check ✅

Make sure you have:
- [ ] Python 3.8+ installed (`python --version`)
- [ ] pip installed (`pip --version`)
- [ ] MongoDB Atlas account (free tier) - [Sign up here](https://www.mongodb.com/cloud/atlas)

---

## Step 2: MongoDB Atlas Setup (3 minutes) ☁️

### A. Create Cluster
1. Log into [MongoDB Atlas](https://cloud.mongodb.com)
2. Click "Build a Database"
3. Choose **FREE** (M0 Sandbox)
4. Select cloud provider & region
5. Click "Create"

### B. Setup Database Access
1. Go to "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `pl_admin`
5. Password: `SecurePass123!` (or generate one)
6. Database User Privileges: **"Atlas Admin"**
7. Click "Add User"

### C. Setup Network Access
1. Go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for testing)
4. Click "Confirm"

### D. Get Connection String
1. Go to "Database" (left sidebar)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string
5. **Replace `<password>` with your actual password**

Example:
```
mongodb+srv://pl_admin:SecurePass123!@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

---

## Step 3: Install Application (1 minute) 💻

```bash
# Navigate to project directory
cd pl_request_system

# Install dependencies
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed streamlit-1.31.0 pymongo-4.6.1 python-dotenv-1.0.0 pandas-2.2.0
```

---

## Step 4: Configure Environment (30 seconds) ⚙️

Create `.env` file in project root:

```bash
# For Linux/Mac
echo 'MONGODB_URI=mongodb+srv://pl_admin:SecurePass123!@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=pl_request_system' > .env

# For Windows (PowerShell)
@"
MONGODB_URI=mongodb+srv://pl_admin:SecurePass123!@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=pl_request_system
"@ | Out-File -FilePath .env -Encoding UTF8
```

**Or manually create `.env` file:**
```
MONGODB_URI=mongodb+srv://your_user:your_password@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=pl_request_system
```

⚠️ **Important:** Replace with YOUR actual connection string!

---

## Step 5: Run Application (10 seconds) 🚀

```bash
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

The app will automatically open in your browser! 🎉

---

## Step 6: Verify Installation ✅

### Test 1: Database Connection
- You should see "✅ Database Connected" in the sidebar
- If you see an error, check your `.env` file

### Test 2: Add a PL Number
1. Click "📦 Add PL Number" in sidebar
2. Fill in:
   - PL Number: `TEST-001`
   - Product Name: `Test Widget`
   - EAR: `100`
   - Global Limit: `100`
   - Section Limits: A: 25, B: 25, C: 25, D: 25
3. Click "Add PL Number"
4. Should see: "✅ PL Number 'TEST-001' added successfully!"

### Test 3: Add a Request
1. Click "📝 Add Request" in sidebar
2. Select: TEST-001
3. Section: A
4. Quantity: 20
5. Click "Validate & Submit Request"
6. Should see: "✅ REQUEST SAVED"

### Test 4: View Summary
1. Click "📊 View PL Summary"
2. Select: TEST-001
3. Should see usage: Section A: 20/25

---

## Common Issues & Solutions 🔧

### Issue 1: "Database Connection Failed"

**Cause:** Wrong connection string or network issue

**Solution:**
```bash
# Check .env file exists
ls -la .env

# View contents (Linux/Mac)
cat .env

# Test connection string manually
python -c "from database import get_database; db = get_database(); print('Connected!' if db.connected else 'Failed')"
```

### Issue 2: "ModuleNotFoundError"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Issue 3: "Port 8501 already in use"

**Cause:** Another Streamlit app is running

**Solution:**
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Or use different port
streamlit run app.py --server.port 8502
```

### Issue 4: "Authentication failed"

**Cause:** Wrong username/password in connection string

**Solution:**
1. Go to MongoDB Atlas → Database Access
2. Reset user password
3. Update `.env` with new password
4. Restart application

---

## Next Steps 🎯

### Add Real Data
1. Go to "Add PL Number"
2. Add your actual products with real limits
3. Start managing requests!

### Explore Features
- **View PL Summary**: Monitor usage vs. limits
- **View Requests**: Track all requests and deliveries
- **Test Validation**: Try to exceed limits (it will block!)

### Customize
- Edit section names in `business_logic.py` if needed
- Modify UI colors in `app.py` custom CSS
- Add your company logo

---

## Testing the Strict Validation 🧪

Try these to verify the system blocks violations:

### Test Case 1: Exceed Section Limit
1. Add PL: `DEMO-001` with Section A limit: 50
2. Request 1: Section A, Qty: 40 → ✅ Should pass
3. Request 2: Section A, Qty: 20 → ❌ Should BLOCK (40+20=60 > 50)

### Test Case 2: Exceed Yearly Limit
1. Add PL: `DEMO-002` with EAR: 100
2. Request: Section A: 30, B: 30, C: 30 (total: 90)
3. Next request: Section D: 20 → ❌ Should BLOCK (90+20=110 > 100)

### Test Case 3: Multiple Small Requests
1. Add PL: `DEMO-003` with Section A limit: 100
2. Submit 10 requests of 10 each
3. 11th request of 10 → ❌ Should BLOCK (100+10 > 100)

---

## Production Deployment Checklist 📋

Before going live:
- [ ] Change MongoDB password to strong password
- [ ] Restrict IP whitelist to specific IPs (not 0.0.0.0/0)
- [ ] Enable MongoDB Atlas backup
- [ ] Add `.env` to `.gitignore`
- [ ] Test all validation rules thoroughly
- [ ] Train users on the system
- [ ] Set up monitoring alerts
- [ ] Document your section naming conventions
- [ ] Create admin user guide

---

## Getting Help 📞

### Documentation
- `README.md` - Complete documentation
- `SCHEMA.md` - Database structure
- Code comments - Inline explanations

### Testing
- Try all features with test data first
- Verify strict validation works
- Test edge cases (limits of 0, very large numbers)

### Troubleshooting
1. Check `.env` file configuration
2. Verify MongoDB Atlas network access
3. Look at terminal output for errors
4. Check MongoDB Atlas logs

---

## Success Checklist ✅

You're ready to use the system when:
- [x] Application opens at localhost:8501
- [x] Sidebar shows "Database Connected"
- [x] Can add a PL Number successfully
- [x] Can submit a valid request
- [x] System BLOCKS requests that exceed limits
- [x] Can view summaries and requests

---

## Congratulations! 🎉

Your PL Request Management System is now running!

The system will:
- ✅ Enforce ALL limits strictly
- ✅ Block ANY request that violates rules
- ✅ Track all requests permanently
- ✅ Provide real-time usage monitoring

**Remember:** This system has NO overrides. If a limit is exceeded, the request is BLOCKED. This is by design.

Happy managing! 📦
