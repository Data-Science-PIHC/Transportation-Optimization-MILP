import snowflake.connector
from config.snowflake_config import SNOWFLAKE_CONFIG
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_warehouse_data():
    """Test warehouse data query with sample warehouse codes"""
    try:
        # Create connection
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_CONFIG['user'],
            password=SNOWFLAKE_CONFIG['password'],
            account=SNOWFLAKE_CONFIG['account'],
            warehouse=SNOWFLAKE_CONFIG['warehouse']
        )
        logger.info("Successfully connected to Snowflake")
        
        # Test warehouse codes from route data
        test_warehouse_codes = ['D101', 'D723', 'D278']
        warehouse_codes_str = "'" + "','".join(test_warehouse_codes) + "'"
        
        # Read the SQL query
        with open('query/current_stok_lini2.sql', 'r') as f:
            query = f.read().format(warehouse_codes=warehouse_codes_str)
        
        # Create cursor
        cursor = conn.cursor()
        
        try:
            # Execute query
            logger.info("Executing warehouse data query...")
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            logger.info(f"Columns in result: {columns}")
            
            # Fetch and display results
            results = cursor.fetchall()
            logger.info(f"Found {len(results)} warehouse records")
            
            # Convert to DataFrame for easier viewing
            df = pd.DataFrame(results, columns=columns)
            
            # Display first few rows
            logger.info("\nFirst few records:")
            print(df.head())
            
            # Check data types
            logger.info("\nData types:")
            print(df.dtypes)
            
            return df
            
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error testing warehouse data: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        df = test_warehouse_data()
        if df is not None:
            print("\nWarehouse data test successful!")
    except Exception as e:
        print(f"Error during warehouse data test: {str(e)}")
