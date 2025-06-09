import pandas as pd
import sqlalchemy

def import_wage_determinations():
    # Step 1: Read Excel File
    # ------------------------
    # Load the Excel file with your wage determination data
    # We're reading two columns: 'W-D' (renamed to 'wd_number') and 'STATE' (renamed to 'states')
    excel_data = pd.read_excel("/home/lenovo/database_practice/Wage-Determination (1).xlsx")
    excel_data = excel_data[['W-D', 'STATE']].rename(columns={
        'W-D': 'wd_number',
        'STATE': 'states'
    })
    
    # Step 2: Clean and Prepare Data
    # ------------------------------
    # Convert state names to uppercase and remove extra spaces
    excel_data['states'] = excel_data['states'].str.upper().str.strip()
    
    # Step 3: Connect to Database
    # ---------------------------
    engine = sqlalchemy.create_engine("mysql+pymysql://root:Pv_20[02]Np@develop-220.gsa-cs.com/dbWageDetermination")

    # Step 4: Get WD Mappings
    # ------------------------
    # Fetch all wd_number → id mappings from wage_determination table
    wd_mapping = pd.read_sql("SELECT id, wd_number FROM wage_determination", engine)
    wd_mapping = wd_mapping.set_index('wd_number')['id'].to_dict()
    
    # Step 5: Get State Mappings
    # --------------------------
    # Fetch all state_name → id mappings from state table
    # state_mapping = pd.read_sql("SELECT id, UPPER(state_name) AS state_name FROM state", engine)
    state_mapping = pd.read_sql("SELECT id, UPPER(name) AS state_name FROM state", engine)

    state_mapping = state_mapping.set_index('state_name')['id'].to_dict()
    
    # Step 6: Process Each Row
    # ------------------------
    # Prepare list to store our final results
    associations = []
    
    for index, row in excel_data.iterrows():
        wd = row['wd_number']
        state_string = row['states']
        
        # Skip if missing essential data
        if pd.isna(wd) or pd.isna(state_string):
            continue
            
        # Get WD ID from mapping
        wd_id = wd_mapping.get(wd)
        if not wd_id:
            print(f"Warning: WD number {wd} not found in database")
            continue
            
        # Split states and process each one
        for state in state_string.split(','):
            state = state.strip()  # Remove extra spaces
            
            # Get state ID from mapping
            state_id = state_mapping.get(state)
            if not state_id:
                print(f"Warning: State {state} not found in database")
                continue
                
            # Add to our results
            associations.append({
                'wd_id': wd_id,
                'state_id': state_id
            })
    
    # Step 7: Save to Database
    # ------------------------
    # Convert results to DataFrame
    if associations:
        result_df = pd.DataFrame(associations)
        
        # Insert into wd_state_association table
        result_df.to_sql(
            # 'wd_state_association',
            'wd_state_assoc',  # ✅ correct table name

            engine,
            if_exists='append',
            index=False
        )
        print(f"Successfully inserted {len(result_df)} records")
    else:
        print("No valid records to insert")

# Run the process
if __name__ == "__main__":
    import_wage_determinations()