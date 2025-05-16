import snowflake.connector
from config.snowflake_config import SNOWFLAKE_CONFIG, get_warehouse_codes
import pandas as pd

def create_snowflake_connection():
    """Create a Snowflake connection using private key authentication"""
    private_key = SNOWFLAKE_CONFIG.get('get_private_key')()
    
    pkb = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    return snowflake.connector.connect(
        user=SNOWFLAKE_CONFIG['user'],
        account=SNOWFLAKE_CONFIG['account'],
        warehouse=SNOWFLAKE_CONFIG['warehouse'],
        private_key=pkb
    )

def get_warehouse_data(route_data):
    """Get warehouse data from Snowflake with dynamic filtering"""
    # Get warehouse codes from route data
    warehouse_codes = get_warehouse_codes(route_data)
    
    # Format warehouse codes for SQL
    warehouse_codes_str = "'" + "','".join(warehouse_codes) + "'"
    
    # Read and format the SQL query
    with open('query/current_stok_lini2.sql', 'r') as f:
        query = f.read().format(warehouse_codes=warehouse_codes_str)
    
    # Connect to Snowflake
    conn = create_snowflake_connection()
    cursor = conn.cursor()
    try:
        # Execute query - Snowflake will handle cross-database references
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        return df
    finally:
        cursor.close()
        conn.close()

def get_route_data():
    """Read and process route data from CSV"""
    # Read route data
    route_data = pd.read_csv('dataset/list_rute.csv', delimiter=',')
    
    # Clean up the data
    # Remove any whitespace in column names
    route_data.columns = route_data.columns.str.strip()
    
    # Convert numeric columns
    numeric_cols = ['Kapasitas', 'Tarif Freight', 'Tarif Survey', 'Tarif Bongkar/Muat', 
                   'Tarif Pengantongan', 'Tarif Total', 'Lead Time', 'Rate Bongkar Muat (Ton/Hari)']
    for col in numeric_cols:
        if col in route_data.columns:
            # Remove commas and convert to numeric
            route_data[col] = pd.to_numeric(route_data[col].str.replace(',', ''), errors='coerce')
    
    # Validate the data
    route_data = validate_route_data(route_data)
    return route_data

def validate_route_data(route_data):
    """Validate route data has required columns and proper format"""
    # Required columns
    required_columns = [
        'Kode Gudang Lini 1', 'Kode Gudang Lini 2', 'Jenis Kendaraan', 
        'Kapasitas', 'Tarif Total', 'Lead Time', 'In bag/curah', 'Jenis Pupuk'
    ]
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in route_data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validate data types and ranges
    if not all(route_data['Kapasitas'] > 0):
        raise ValueError("Capacity values must be positive")
    
    if not all(route_data['Tarif Total'] > 0):
        raise ValueError("Total cost values must be positive")
    
    if not all(route_data['Lead Time'] > 0):
        raise ValueError("Lead time values must be positive")
    
    # Validate packaging type
    valid_packaging = ['In bag', 'Curah']
    invalid_packaging = ~route_data['In bag/curah'].isin(valid_packaging)
    if invalid_packaging.any():
        raise ValueError(f"Invalid packaging types found: {route_data.loc[invalid_packaging, 'In bag/curah'].unique()}")
    
    # Validate fertilizer types
    if not all(route_data['Jenis Pupuk'].isin(['Urea', 'NPK', 'Urea/NPK'])):
        raise ValueError("Invalid fertilizer types found")
    
    return route_data
