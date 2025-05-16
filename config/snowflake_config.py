import os
from cryptography.hazmat.primitives import serialization

SNOWFLAKE_CONFIG = {
    'account': 'bf59256.ap-southeast-3.aws',
    'user': '1250001',
    'warehouse': 'COMPUTE_WH',
    'private_key_path': 'config/rsa_key.p8',  # Update this path
    'private_key_passphrase': None  # Set if your private key is encrypted
}

def get_private_key():
    """Load and return the private key from file"""
    with open(SNOWFLAKE_CONFIG['private_key_path'], "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=SNOWFLAKE_CONFIG['private_key_passphrase'].encode() if SNOWFLAKE_CONFIG['private_key_passphrase'] else None
        )
    return private_key

# Add this to your .gitignore
GITIGNORE_CONTENT = """
config/snowflake_config.py
"""

# Create a function to get warehouse codes from route data
def get_warehouse_codes(route_data):
    """Extract unique warehouse codes from route data"""
    # Get unique warehouse codes from Lini 2
    lini2_warehouses = set(route_data['Kode Gudang Lini 2'].unique())
    return lini2_warehouses
