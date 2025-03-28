from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64
import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json


# Reload .env file
load_dotenv(override=True)
# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
PRODUCT_KEY = os.getenv('PRODUCT_KEY')  # Your device's product key

def verify_product_key_exists():
    """Verify that the product key exists in Supabase"""
    if not all([SUPABASE_URL, SUPABASE_KEY, PRODUCT_KEY]):
        raise ValueError("Missing required environment variables (SUPABASE_URL, SUPABASE_KEY, or PRODUCT_KEY)")

    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    params = {
        "product_key": f"eq.{PRODUCT_KEY}",
        "select": "id,product_key"
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Failed to verify product key: {response.text}")
    
    products = response.json()
    if not products:
        raise Exception(f"Product key '{PRODUCT_KEY}' not found in database")
    
    return True

def generate_key_pair():
    """Generate a new RSA key pair"""
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

def update_env_file(private_key_pem):
    """Update .env file with private key"""
    env_path = Path('.env')
    
    # Read existing .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_content[key] = value

    # Convert private key PEM to base64 for storage
    private_key_base64 = base64.b64encode(private_key_pem).decode('utf-8')
    
    # Update private key in env_content
    env_content['PRIVATE_KEY'] = private_key_base64
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

def update_supabase_public_key(public_key_pem):
    """Update public key in Supabase products table"""
    if not all([SUPABASE_URL, SUPABASE_KEY, PRODUCT_KEY]):
        raise ValueError("Missing required environment variables (SUPABASE_URL, SUPABASE_KEY, or PRODUCT_KEY)")

    # Convert public key to base64
    public_key_base64 = base64.b64encode(public_key_pem).decode('utf-8')
    
    # Prepare the request
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Update the product record
    params = {"product_key": f"eq.{PRODUCT_KEY}"}
    data = {"public_key": public_key_base64}
    
    response = requests.patch(url, headers=headers, json=data, params=params)
    
    if response.status_code != 204:  # Supabase returns 204 on successful PATCH
        raise Exception(f"Failed to update public key in Supabase: {response.text}")

    # Verify the update
    verify_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    verify_params = {
        "product_key": f"eq.{PRODUCT_KEY}",
        "select": "product_key,public_key"
    }
    
    verify_response = requests.get(url, headers=verify_headers, params=verify_params)
    if verify_response.status_code != 200:
        raise Exception("Failed to verify public key update")
    
    result = verify_response.json()
    if not result or not result[0].get('public_key'):
        raise Exception("Public key was not properly updated in database")
    
    print(f"Public key successfully updated for product key: {PRODUCT_KEY}")

def main():
    try:
        print(f"Verifying product key {PRODUCT_KEY} in database...")
        verify_product_key_exists()
        
        print("Generating new RSA key pair...")
        private_key_pem, public_key_pem = generate_key_pair()
        
        print("Updating private key in .env file...")
        update_env_file(private_key_pem)
        
        print("Updating public key in Supabase...")
        update_supabase_public_key(public_key_pem)
        
        print("Successfully generated and stored key pair!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 