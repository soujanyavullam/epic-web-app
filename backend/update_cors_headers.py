#!/usr/bin/env python3
"""
Update CORS headers in Lambda functions to restrict access to specific domains.
"""

import json
import os
import re

def update_cors_headers(file_path: str, allowed_domain: str = "https://your-domain.com"):
    """Update CORS headers in a Python file."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace all instances of Access-Control-Allow-Origin: '*'
    # with the specific domain
    old_pattern = r"'Access-Control-Allow-Origin': '\*'"
    new_pattern = f"'Access-Control-Allow-Origin': '{allowed_domain}'"
    
    updated_content = re.sub(old_pattern, new_pattern, content)
    
    # Also replace any instances without quotes
    old_pattern2 = r"'Access-Control-Allow-Origin': \*"
    new_pattern2 = f"'Access-Control-Allow-Origin': '{allowed_domain}'"
    
    updated_content = re.sub(old_pattern2, new_pattern2, updated_content)
    
    if updated_content != content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print(f"✅ Updated CORS headers in {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed in {file_path}")
        return False

def main():
    """Update CORS headers in all Lambda function files."""
    
    # Get domain from user or use default
    domain = input("Enter your domain (e.g., https://your-app.com) or press Enter for default: ").strip()
    if not domain:
        domain = "https://your-domain.com"
    
    print(f"🔒 Updating CORS headers to restrict access to: {domain}")
    print("=" * 60)
    
    # Files to update
    files_to_update = [
        "lambda_minimal/query_handler.py",
        "lambda_minimal/upload_handler.py", 
        "lambda_minimal/repo_documentation_generator.py",
        "src/query_handler.py",
        "src/upload_handler.py",
        "src/list_books.py"
    ]
    
    updated_count = 0
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_cors_headers(file_path, domain):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("=" * 60)
    print(f"✅ Updated {updated_count} files with restricted CORS headers")
    print(f"🔒 Access now restricted to: {domain}")
    print("\n📋 Next steps:")
    print("1. Run: ./deploy_lambda_updates.sh")
    print("2. Test the API endpoints")
    print("3. Deploy security measures if needed: ./deploy_secure_api.sh")

if __name__ == "__main__":
    main() 