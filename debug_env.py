import os
from pathlib import Path

print("--- DEBUGGING ENVIRONMENT ---")
print(f"CWD: {os.getcwd()}")

env_path = Path(".env")
print(f".env exists? {env_path.exists()}")

if env_path.exists():
    print(".env content:")
    print(env_path.read_text())

print("\n--- OS.ENVIRON BEFORE LOAD ---")
print(f"EMAIL_USER: {os.environ.get('EMAIL_USER')}")

print("\n--- PYDANTIC SETTINGS ---")
try:
    from app.core.config import settings
    print(f"Settings.EMAIL_USER: {settings.EMAIL_USER}")
    print(f"Settings.EMAIL_HOST: {settings.EMAIL_HOST}")
except Exception as e:
    print(f"Error loading settings: {e}")
