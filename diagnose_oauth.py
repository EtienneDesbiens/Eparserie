#!/usr/bin/env python
"""Diagnose OAuth and Gmail API issues."""
import json
import os

print("=== GroceryBot OAuth Diagnostic ===\n")

# 1. Check credentials file
print("1. Checking gmail_credentials.json...")
if not os.path.exists("gmail_credentials.json"):
    print("   ✗ gmail_credentials.json NOT FOUND")
    print("   → Download from Google Cloud Console → Credentials → OAuth client ID")
    exit(1)

with open("gmail_credentials.json") as f:
    creds = json.load(f)
    project_id = creds.get("installed", {}).get("project_id", "UNKNOWN")
    client_id = creds.get("installed", {}).get("client_id", "UNKNOWN")
    print(f"   ✓ Found credentials")
    print(f"   Project ID: {project_id}")
    print(f"   Client ID: {client_id[:30]}...")

# 2. Check .env
print("\n2. Checking .env...")
if not os.path.exists(".env"):
    print("   ✗ .env NOT FOUND")
    exit(1)

with open(".env") as f:
    env = {}
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v

    gmail = env.get("GMAIL_ADDRESS")
    print(f"   ✓ GMAIL_ADDRESS: {gmail}")
    if not gmail:
        print("   ✗ GMAIL_ADDRESS is empty")
        exit(1)

# 3. Check Google libraries
print("\n3. Checking Google libraries...")
try:
    import google
    import google_auth_oauthlib
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    print("   ✓ All libraries installed")
except ImportError as e:
    print(f"   ✗ Missing library: {e}")
    exit(1)

# 4. Try OAuth flow
print("\n4. Testing OAuth flow...")
print("   This will open a browser for authorization...")
try:
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    flow = InstalledAppFlow.from_client_secrets_file(
        "gmail_credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    print(f"   ✓ OAuth successful!")
    print(f"   Token: {creds.token[:20]}...")

    # 5. Try Gmail API
    print("\n5. Testing Gmail API...")
    service = build("gmail", "v1", credentials=creds)

    # Get user profile (lightweight test)
    profile = service.users().getProfile(userId="me").execute()
    print(f"   ✓ Gmail API working!")
    print(f"   Email: {profile.get('emailAddress')}")
    print(f"   Messages: {profile.get('messagesTotal')}")

    # 6. Try sending test email
    print("\n6. Attempting test email send...")
    from email.mime.text import MIMEText
    import base64

    msg = MIMEText("This is a test email from GroceryBot OAuth setup.")
    msg['Subject'] = "GroceryBot OAuth Test"
    msg['From'] = gmail
    msg['To'] = gmail

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    send_message = {'raw': raw}

    result = service.users().messages().send(userId="me", body=send_message).execute()
    print(f"   ✓ Test email sent!")
    print(f"   Message ID: {result['id']}")
    print("\n✅ All checks passed! OAuth is working correctly.")

except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")
    print("\n❌ Diagnosis failed. Check:")
    print("   1. Gmail API is enabled in Google Cloud Console")
    print("   2. Billing is enabled on the project")
    print("   3. OAuth consent screen is configured")
    exit(1)
