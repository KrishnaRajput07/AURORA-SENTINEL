import sys
import os
sys.path.append(os.getcwd())
from backend.api.main import app

print("Registered Routes:")
for route in app.routes:
    print(f"{route.path} [{route.name}]")
