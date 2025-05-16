import snowflake.connector
from config.snowflake_config import SNOWFLAKE_CONFIG, get_private_key
from cryptography.hazmat.primitives import serialization
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_snowflake_connection():
    """Test Snowflake connection and basic query"""
    try:
        # Create connection using private key
        private_key = get_private_key()
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_CONFIG['user'],
            account=SNOWFLAKE_CONFIG['account'],
            warehouse=SNOWFLAKE_CONFIG['warehouse'],
            private_key=pkb
        )
        logger.info("Successfully connected to Snowflake")
        
        # Create cursor
        cursor = conn.cursor()
        
        try:
            # Test query to get current version
            cursor.execute("SELECT current_version()")
            one_row = cursor.fetchone()
            logger.info(f"Snowflake version: {one_row[0]}")
            
            # Test query to list databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            logger.info(f"Available databases: {len(databases)}")
            
            # Print first 5 databases
            for db in databases[:5]:
                logger.info(f"Database: {db[1]}")
                
            return True
            
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        success = test_snowflake_connection()
        if success:
            print("Snowflake connection test successful!")
    except Exception as e:
        print(f"Error during Snowflake connection test: {str(e)}")
