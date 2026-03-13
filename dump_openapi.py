import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.api.main import app

def main():
    openapi_schema = app.openapi()
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

if __name__ == "__main__":
    main()
