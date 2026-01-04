from database import get_database

def migrate_shift_limits():
    """
    Migrate products to include new Shift limits.
    Adds:
    - 'Shift EMS': 0
    - 'Shift EMR': 0
    - 'Shift EWFPS': 0
    
    to 'section_limits' dictionary for all products.
    """
    
    print("Starting Shift Limits Migration...")
    db = get_database()
    products_col = db.get_products_collection()
    
    all_products = list(products_col.find({}))
    print(f"Found {len(all_products)} products to check.")
    
    count = 0
    for p in all_products:
        limits = p.get('section_limits', {})
        
        updated = False
        
        # Add new keys if missing
        new_keys = ['Shift EMS', 'Shift EMR', 'Shift EWFPS']
        for key in new_keys:
            if key not in limits:
                limits[key] = 0
                updated = True
        
        if updated:
            products_col.update_one(
                {'_id': p['_id']},
                {'$set': {'section_limits': limits}}
            )
            count += 1
            if count % 50 == 0:
                print(f"Updated {count} records...")
            
    print(f"✅ Migration Complete! Updated {count} records.")

if __name__ == "__main__":
    migrate_shift_limits()
