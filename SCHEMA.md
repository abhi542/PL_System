# Database Schema Documentation

## Overview

The PL Request Management System uses MongoDB Atlas with two primary collections:
- `products` - Stores PL Number definitions with limits
- `requests` - Stores material requests with validation

---

## Collection: `products`

### Purpose
Stores PL Number (Product) definitions with fixed yearly and section-wise limits.

### Schema

```javascript
{
  "_id": ObjectId,                    // MongoDB generated unique identifier
  "pl_no": String,                    // Unique PL Number (uppercase)
  "product_name": String,             // Product/material name
  "ear": Number,                      // Estimated Annual Requirement (yearly limit)
  "global_limit": Number,             // Global limit (≤ EAR)
  "section_limits": {                 // Fixed limits per section
    "A": Number,                      // Section A limit
    "B": Number,                      // Section B limit
    "C": Number,                      // Section C limit
    "D": Number                       // Section D limit
  },
  "created_at": ISODate,              // Document creation timestamp
  "updated_at": ISODate               // Last update timestamp (optional)
}
```

### Field Specifications

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `_id` | ObjectId | Yes | Auto-generated | MongoDB document ID |
| `pl_no` | String | Yes | Unique, Non-empty | Unique identifier (e.g., "PL-001") |
| `product_name` | String | Yes | Non-empty | Product name |
| `ear` | Number | Yes | > 0 | Estimated Annual Requirement |
| `global_limit` | Number | Yes | > 0, ≤ EAR | Maximum yearly allocation |
| `section_limits.A` | Number | Yes | ≥ 0 | Section A limit |
| `section_limits.B` | Number | Yes | ≥ 0 | Section B limit |
| `section_limits.C` | Number | Yes | ≥ 0 | Section C limit |
| `section_limits.D` | Number | Yes | ≥ 0 | Section D limit |
| `created_at` | ISODate | Yes | Valid date | Creation timestamp |
| `updated_at` | ISODate | No | Valid date | Update timestamp |

### Constraints

1. **Uniqueness**: `pl_no` must be unique across all documents
2. **EAR vs Global Limit**: `global_limit` ≤ `ear`
3. **Section Limits**: Sum of section limits should ≤ `global_limit` (warning, not enforced)
4. **Positive Values**: All numeric fields must be positive (except section limits can be 0)

### Indexes

```javascript
// Unique index on pl_no for fast lookups and uniqueness enforcement
db.products.createIndex({ "pl_no": 1 }, { unique: true })
```

### Example Document

```javascript
{
  "_id": ObjectId("657a1b2c3d4e5f6g7h8i9j0k"),
  "pl_no": "PL-001",
  "product_name": "Widget Type A",
  "ear": 1000,
  "global_limit": 1000,
  "section_limits": {
    "A": 250,
    "B": 250,
    "C": 250,
    "D": 250
  },
  "created_at": ISODate("2025-01-15T10:30:00Z"),
  "updated_at": ISODate("2025-01-20T14:45:00Z")
}
```

### Operations

#### Insert
```javascript
db.products.insertOne({
  "pl_no": "PL-002",
  "product_name": "Component XYZ",
  "ear": 500,
  "global_limit": 480,
  "section_limits": {
    "A": 120,
    "B": 120,
    "C": 120,
    "D": 120
  },
  "created_at": new Date()
})
```

#### Query
```javascript
// Find by PL Number
db.products.findOne({ "pl_no": "PL-001" })

// Get all products
db.products.find().sort({ "pl_no": 1 })

// Find products with high EAR
db.products.find({ "ear": { $gte: 1000 } })
```

#### Update
```javascript
// Update limits (admin operation)
db.products.updateOne(
  { "pl_no": "PL-001" },
  {
    $set: {
      "ear": 1200,
      "global_limit": 1200,
      "section_limits.A": 300,
      "updated_at": new Date()
    }
  }
)
```

---

## Collection: `requests`

### Purpose
Stores material requests submitted by sections with delivery tracking.

### Schema

```javascript
{
  "_id": ObjectId,                    // MongoDB generated unique identifier
  "pl_no": String,                    // References products.pl_no
  "requested_by": String,             // Section: "A", "B", "C", or "D"
  "requested_count": Number,          // Quantity requested
  "request_date": ISODate,            // Date of request
  "delivered_count": Number | null,   // Quantity delivered (null if not delivered)
  "delivered_date": ISODate | null,   // Date of delivery (null if not delivered)
  "status": String,                   // "pending" or "delivered"
  "created_at": ISODate,              // Document creation timestamp
  "updated_at": ISODate               // Last update timestamp (optional)
}
```

### Field Specifications

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `_id` | ObjectId | Yes | Auto-generated | MongoDB document ID |
| `pl_no` | String | Yes | Must exist in products | Reference to PL Number |
| `requested_by` | String | Yes | "A", "B", "C", or "D" | Requesting section |
| `requested_count` | Number | Yes | > 0 | Quantity requested |
| `request_date` | ISODate | Yes | Valid date | When request was made |
| `delivered_count` | Number/null | No | ≥ 0 if not null | Quantity delivered |
| `delivered_date` | ISODate/null | No | Valid date if not null | When delivered |
| `status` | String | Yes | "pending" or "delivered" | Request status |
| `created_at` | ISODate | Yes | Valid date | Creation timestamp |
| `updated_at` | ISODate | No | Valid date | Update timestamp |

### Constraints

1. **Valid Section**: `requested_by` must be one of: "A", "B", "C", "D"
2. **Valid PL Number**: `pl_no` must exist in `products` collection
3. **Positive Count**: `requested_count` > 0
4. **Valid Status**: `status` must be "pending" or "delivered"
5. **Delivery Logic**: If `delivered_count` is set, `delivered_date` should also be set

### Indexes

```javascript
// Compound index for efficient section-specific queries
db.requests.createIndex({ "pl_no": 1, "requested_by": 1 })

// Index on request_date for chronological queries
db.requests.createIndex({ "request_date": 1 })

// Index on status for filtering
db.requests.createIndex({ "status": 1 })
```

### Example Documents

**Pending Request:**
```javascript
{
  "_id": ObjectId("657b2c3d4e5f6g7h8i9j0k1l"),
  "pl_no": "PL-001",
  "requested_by": "A",
  "requested_count": 50,
  "request_date": ISODate("2025-01-15T09:00:00Z"),
  "delivered_count": null,
  "delivered_date": null,
  "status": "pending",
  "created_at": ISODate("2025-01-15T09:00:00Z")
}
```

**Delivered Request:**
```javascript
{
  "_id": ObjectId("657c3d4e5f6g7h8i9j0k1l2m"),
  "pl_no": "PL-001",
  "requested_by": "B",
  "requested_count": 75,
  "request_date": ISODate("2025-01-10T10:30:00Z"),
  "delivered_count": 75,
  "delivered_date": ISODate("2025-01-18T14:00:00Z"),
  "status": "delivered",
  "created_at": ISODate("2025-01-10T10:30:00Z"),
  "updated_at": ISODate("2025-01-18T14:00:00Z")
}
```

### Operations

#### Insert (with validation)
```javascript
// NOTE: In the application, this is ONLY done after validation
// Never insert directly - always use RequestManager.create_request()

db.requests.insertOne({
  "pl_no": "PL-001",
  "requested_by": "C",
  "requested_count": 30,
  "request_date": new Date(),
  "delivered_count": null,
  "delivered_date": null,
  "status": "pending",
  "created_at": new Date()
})
```

#### Query
```javascript
// Get all requests for a PL Number
db.requests.find({ "pl_no": "PL-001" }).sort({ "request_date": -1 })

// Get pending requests for a section
db.requests.find({
  "pl_no": "PL-001",
  "requested_by": "A",
  "status": "pending"
})

// Get requests within date range
db.requests.find({
  "request_date": {
    $gte: ISODate("2025-01-01"),
    $lte: ISODate("2025-01-31")
  }
})
```

#### Update (delivery)
```javascript
// Update delivery information
db.requests.updateOne(
  { "_id": ObjectId("657b2c3d4e5f6g7h8i9j0k1l") },
  {
    $set: {
      "delivered_count": 50,
      "delivered_date": new Date(),
      "status": "delivered",
      "updated_at": new Date()
    }
  }
)
```

---

## Aggregation Queries

### Calculate Section Total for Validation

```javascript
// Get total requested for Section A of PL-001
db.requests.aggregate([
  {
    $match: {
      "pl_no": "PL-001",
      "requested_by": "A"
    }
  },
  {
    $group: {
      "_id": null,
      "total_requested": { $sum: "$requested_count" }
    }
  }
])
```

### Calculate Yearly Total for Validation

```javascript
// Get total requested across all sections for PL-001
db.requests.aggregate([
  {
    $match: {
      "pl_no": "PL-001"
    }
  },
  {
    $group: {
      "_id": null,
      "total_requested": { $sum: "$requested_count" }
    }
  }
])
```

### Get Summary by Section

```javascript
// Get breakdown by section for PL-001
db.requests.aggregate([
  {
    $match: { "pl_no": "PL-001" }
  },
  {
    $group: {
      "_id": "$requested_by",
      "total_requested": { $sum: "$requested_count" },
      "total_delivered": { $sum: "$delivered_count" },
      "request_count": { $sum: 1 }
    }
  },
  {
    $sort: { "_id": 1 }
  }
])
```

### Monthly Request Summary

```javascript
// Get monthly request summary
db.requests.aggregate([
  {
    $group: {
      "_id": {
        "year": { $year: "$request_date" },
        "month": { $month: "$request_date" },
        "pl_no": "$pl_no"
      },
      "total_requested": { $sum: "$requested_count" },
      "request_count": { $sum: 1 }
    }
  },
  {
    $sort: {
      "_id.year": -1,
      "_id.month": -1
    }
  }
])
```

---

## Data Integrity Rules

### Enforced at Application Level

1. **Section Limit Validation**
   - Before inserting a request, calculate: `section_total + new_request`
   - Must be ≤ `products.section_limits[section]`
   - If violated, request is BLOCKED (not saved)

2. **Yearly Limit Validation**
   - Before inserting a request, calculate: `yearly_total + new_request`
   - Must be ≤ `min(products.ear, products.global_limit)`
   - If violated, request is BLOCKED (not saved)

3. **Delivered Quantity Independence**
   - `delivered_count` does NOT affect limit calculations
   - Limits are based solely on `requested_count`

### Not Enforced (Application Logic Only)

- Foreign key constraint (`pl_no` reference)
- Transaction rollback (MongoDB single-document atomicity only)
- Concurrent request handling (application handles sequentially)

---

## Backup and Maintenance

### Recommended Backup Strategy

```javascript
// Export collections
mongoexport --uri="mongodb+srv://..." --collection=products --out=products_backup.json
mongoexport --uri="mongodb+srv://..." --collection=requests --out=requests_backup.json

// Import collections
mongoimport --uri="mongodb+srv://..." --collection=products --file=products_backup.json
mongoimport --uri="mongodb+srv://..." --collection=requests --file=requests_backup.json
```

### Maintenance Queries

```javascript
// Check for orphaned requests (PL Numbers that don't exist)
db.requests.aggregate([
  {
    $lookup: {
      from: "products",
      localField: "pl_no",
      foreignField: "pl_no",
      as: "product"
    }
  },
  {
    $match: {
      "product": { $size: 0 }
    }
  }
])

// Get statistics
db.products.countDocuments()
db.requests.countDocuments()
db.requests.countDocuments({ "status": "pending" })
db.requests.countDocuments({ "status": "delivered" })
```

---

## Migration Considerations

### Future Schema Changes

If you need to add fields or modify the schema:

1. **Add Optional Fields**: Add with default values
   ```javascript
   db.products.updateMany(
     {},
     { $set: { "new_field": "default_value" } }
   )
   ```

2. **Rename Fields**: Use `$rename` operator
   ```javascript
   db.products.updateMany(
     {},
     { $rename: { "old_field": "new_field" } }
   )
   ```

3. **Add Indexes**: Create new indexes without downtime
   ```javascript
   db.requests.createIndex({ "new_field": 1 })
   ```

---

## Performance Considerations

### Index Usage
- All validation queries use indexed fields
- Compound index on `(pl_no, requested_by)` optimizes section queries
- Date index supports chronological filtering

### Query Optimization
- Use aggregation pipelines for complex calculations
- Limit result sets with pagination
- Use projections to return only needed fields

### Scaling
- MongoDB Atlas auto-scaling handles increased load
- Consider sharding if data exceeds cluster capacity
- Monitor with MongoDB Atlas performance advisor

---

## Security

### Access Control

Recommended role-based access:
- **Admin**: Full read/write access to both collections
- **User**: Read on `products`, read/write on `requests`
- **Viewer**: Read-only access to both collections

### Data Validation

All validation is performed at the application level in `business_logic.py`:
- Never bypass `RequestManager.create_request()`
- Never insert directly into `requests` collection
- Always use provided API methods

---

## Conclusion

This schema design ensures:
- ✅ Data integrity through application-level validation
- ✅ Efficient queries with proper indexing
- ✅ Clear separation of product definitions and requests
- ✅ Audit trail with timestamps
- ✅ Scalability with MongoDB Atlas

For questions or modifications, refer to `business_logic.py` for implementation details.
