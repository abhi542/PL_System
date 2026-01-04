
import pandas as pd
import os
from business_logic import PLNumberManager, ValidationError

def import_pl_data_from_excel(file_path):
    """
    Import PL data from Excel file.
    Accepts file_path (str) or file buffer (BytesIO)
    """
    
    # Handle string path check
    if isinstance(file_path, str):
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        # Normalize path
        file_source = file_path
    else:
        # Assume it's a file buffer
        file_source = file_path
        
    try:
        print(f"Reading Excel file...")
        df = pd.read_excel(file_source)
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        required_cols = ['PL', 'DESCRIPTION', 'WSC']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return False
            
        pl_manager = PLNumberManager()
        success_count = 0
        error_count = 0
        
        print(f"Found {len(df)} rows. Starting import...")
        
        for index, row in df.iterrows():
            try:
                pl_no = str(row['PL']).strip()
                if pd.isna(pl_no) or pl_no == 'nan' or not pl_no:
                    continue
                    
                product_name = str(row['DESCRIPTION']).strip() if not pd.isna(row['DESCRIPTION']) else "No Description"
                
                # Handle EAR (WSC)
                try:
                    ear_val = row['WSC']
                    if pd.isna(ear_val):
                        ear = 1000 # Default per requirement
                    else:
                         ear = int(float(ear_val))
                except ValueError:
                    ear = 1000
                
                if ear <= 0:
                    ear = 1000 # Fallback
                
                # Global Limit: Default 1000, but cap at EAR if EAR < 1000
                global_limit = min(1000, ear)
                
                # Section Limits: Rule says initialize to 0
                section_limits = {
                    'EMS': 0,
                    'EMR': 0,
                    'EWFPS': 0,
                    'EGS': 0,
                    'Shift EMS': 0,
                    'Shift EMR': 0,
                    'Shift EWFPS': 0
                }
                
                # Upsert Logic: Check if exists, if so update updates, else add
                existing = pl_manager.get_pl_number(pl_no)
                
                if existing:
                    # Update (keep existing section limits? OR Reset? User said "replace A B C D... and fill with 0")
                    # Assuming we reset to 0 as per instruction "fill them with 0"
                    
                    # But if we update, we might overwrite running data if limits were changed manually?
                    # User instructions: "deleted in mongo myself... replace... fill with 0".
                    # So we can just add. 
                    
                    # Implementing update just in case, but essentially resetting limits as requested.
                    pl_manager.update_pl_number(
                        pl_no=pl_no,
                        ear=ear,
                        global_limit=global_limit,
                        section_limits=section_limits
                    )
                    # print(f"Updated {pl_no}") # Verbose
                else:
                    pl_manager.add_pl_number(
                        pl_no=pl_no,
                        product_name=product_name,
                        ear=ear,
                        global_limit=global_limit,
                        section_limits=section_limits
                    )
                    # print(f"Added {pl_no}") # Verbose
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error row {index} (PL: {pl_no}): {str(e)}")
                error_count += 1
                
        print("\nImport Summary:")
        print(f"✅ Successfully processed: {success_count}")
        print(f"❌ Errors: {error_count}")
        return True
        
    except Exception as e:
        print(f"❌ Critical error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test run
    file_path = r"d:\Abhinav\Coding\test_pl_no\excel_data\RWF Stock Summary.xlsx"
    import_pl_data_from_excel(file_path)
