import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

def delete_group(rg_name):
    print(f"Deleting resource group: {rg_name}")
    try:
        # Use --no-wait to return immediately
        subprocess.run(["az", "group", "delete", "--name", rg_name, "--yes", "--no-wait"], check=True)
        print(f"Started deletion for: {rg_name}")
    except Exception as e:
        print(f"Failed to delete {rg_name}: {e}")

def main():
    try:
        # List all resource groups matching SerwoTest
        result = subprocess.run(
            ["az", "group", "list", "--query", "[?contains(name, 'SerwoTest')].name", "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        groups = json.loads(result.stdout)
        print(f"Found {len(groups)} resource groups to delete.")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(delete_group, groups)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
