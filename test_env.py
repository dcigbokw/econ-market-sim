import os
from dotenv import load_dotenv

# Load the vault
load_dotenv()

# Attempt to retrieve the key
my_key = os.getenv("FRED_API_KEY")

if my_key:
    print("✅ Environment is secure and key is loaded!")
    print(f"Key preview: {my_key[:4]}...{my_key[-4:]}") 
else:
    print("❌ Failed to load key. Check your .env file.")