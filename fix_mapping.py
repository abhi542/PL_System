from database import get_database
from pymongo import MongoClient

def fix_section_mapping():
    """
    HOTFIX: Remap section limits due to Excel vs App column mismatch.
    
    Excel Order: EMS, EMR, EWFPS, EGS
    App Order:   EMR, EWFPS, EMS, EGS
    
    Current State (Wrong):
    DB['section_limits']['EMR']   holds value intended for EMS
    DB['section_limits']['EWFPS'] holds value intended for EMR
    DB['section_limits']['EMS']   holds value intended for EWFPS
    DB['section_limits']['EGS']   holds value intended for EGS (Correct)
    
    Desired State (Correct):
    DB['section_limits']['EMS']   should get value from Current DB['section_limits']['EMR']
    DB['section_limits']['EMR']   should get value from Current DB['section_limits']['EWFPS']
    DB['section_limits']['EWFPS'] should get value from Current DB['section_limits']['EMS']
    """
    
    print("Starting Data Repair...")
    db = get_database()
    products_col = db.get_products_collection()
    
    all_products = list(products_col.find({}))
    print(f"Found {len(all_products)} products to process.")
    
    count = 0
    for p in all_products:
        limits = p.get('section_limits', {})
        
        # Safe get with default 0, though schema enforcement should mean they exist
        current_emr_val = limits.get('EMR', 0)     # Actually EMS
        current_ewfps_val = limits.get('EWFPS', 0) # Actually EMR
        current_ems_val = limits.get('EMS', 0)     # Actually EWFPS
        current_egs_val = limits.get('EGS', 0)     # Actually EGS (Correct)
        
        # Swap logic
        new_limits = {
            'EMS': current_emr_val,      # Move EMR slot (EMS val) to EMS key
            'EMR': current_ewfps_val,    # Move EWFPS slot (EMR val) to EMR key
            'EWFPS': current_ems_val,    # Move EMS slot (EWFPS val) to EWFPS key
            'EGS': current_egs_val       # Keep same
        }
        
        # Update in DB
        products_col.update_one(
            {'_id': p['_id']},
            {'$set': {'section_limits': new_limits}}
        )
        count += 1
        
        if count % 50 == 0:
            print(f"Processed {count}...")
            
    print(f"✅ Repair Complete! Updated {count} records.")

if __name__ == "__main__":
    fix_section_mapping()
