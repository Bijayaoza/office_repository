import pandas as pd
import sqlalchemy
from sqlalchemy import text, exc

def import_wage_determinations():
    # Step 1: Read Excel File
    excel_data = pd.read_excel("/home/lenovo/database_practice/Wage-Determination (1).xlsx")
    excel_data = excel_data[['W-D', 'STATE']].rename(columns={
        'W-D': 'wd_number',
        'STATE': 'states'
    })
    
    # Step 2: Clean and Prepare Data
    excel_data['states'] = excel_data['states'].str.upper().str.strip()
    
    # Step 3: Connect to Database
    engine = sqlalchemy.create_engine("mysql+pymysql://root:Pv_20[02]Np@develop-220.gsa-cs.com/dbWageDetermination")

    # Step 4: Get WD Mappings
    wd_mapping = pd.read_sql("SELECT id, wd_number FROM wage_determination", engine)
    wd_mapping = wd_mapping.set_index('wd_number')['id'].to_dict()
    
    # Step 5: Get State Mappings
    state_df = pd.read_sql("SELECT id, UPPER(name) AS state_name FROM state", engine)
    state_mapping = state_df.set_index('state_name')['id'].to_dict()
    
    # Step 6: Collect all unique states from Excel
    all_states = set()
    for state_string in excel_data['states'].dropna():
        states = [s.strip() for s in state_string.split(',')]
        all_states.update(states)
    
    # Step 7: Identify and insert missing states
    missing_states = [state for state in all_states if state not in state_mapping]
    
    if missing_states:
        # Bulk insert missing states
        with engine.begin() as conn:
            # Insert new states
            insert_stmt = text("""
                INSERT IGNORE INTO state (name) 
                VALUES (:state)
            """)
            
            try:
                conn.execute(
                    insert_stmt,
                    [{"state": state} for state in missing_states]
                )
                print(f"Inserted {len(missing_states)} new states")
            except exc.SQLAlchemyError as e:
                print(f"Error inserting states: {str(e)}")
        
        # Refresh state mapping
        state_df = pd.read_sql("SELECT id, UPPER(name) AS state_name FROM state", engine)
        state_mapping = state_df.set_index('state_name')['id'].to_dict()
    
    # Step 8: Process associations
    associations = []
    for index, row in excel_data.iterrows():
        wd = row['wd_number']
        state_string = row['states']
        
        if pd.isna(wd) or pd.isna(state_string):
            continue
            
        wd_id = wd_mapping.get(wd)
        if not wd_id:
            print(f"Warning: WD number {wd} not found in database")
            continue
            
        for state in state_string.split(','):
            state = state.strip()
            state_id = state_mapping.get(state)
            
            if not state_id:
                # Shouldn't happen after bulk insert, but log if it does
                print(f"Critical: State {state} still missing after insertion")
                continue
                
            associations.append({
                'wd_id': wd_id,
                'state_id': state_id
            })
    
    # Step 9: Save to Database
    if associations:
        result_df = pd.DataFrame(associations)
        result_df.to_sql(
            'wd_state_assoc',
            engine,
            if_exists='append',
            index=False
        )
        print(f"Successfully inserted {len(result_df)} associations")
    else:
        print("No valid records to insert")

if __name__ == "__main__":
    import_wage_determinations()