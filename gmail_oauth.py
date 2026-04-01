from __future__ import annotations
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth import default
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes - read/write access to send emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "gmail_token.pickle"
CREDENTIALS_FILE = "gmail_credentials.json"


def get_gmail_service(gmail_address: str) -> any:
    """
    Authenticate with Gmail using OAuth 2.0.
    First run will open a browser for user authentication.
    """
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"⚠ Token cache corrupted, will re-authenticate: {e}")
            creds = None

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"⚠ Token refresh failed, re-authenticating: {e}")
            creds = None

    # New authentication flow if no token
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

            # Save token for future runs
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"{CREDENTIALS_FILE} not found. "
                "Download OAuth credentials from Google Cloud Console and save as gmail_credentials.json"
            )

    return build("gmail", "v1", credentials=creds)


def send_email_oauth(
    html: str,
    gmail_address: str,
    recipient: str,
    subject: str = "Weekly Grocery Deals",
) -> None:
    """
    Send email using Gmail OAuth 2.0 API (secure method).
    Requires gmail_credentials.json from Google Cloud Console.
    """
    try:
        service = get_gmail_service(gmail_address)

        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_address
        msg["To"] = recipient

        # Plain text fallback
        msg.attach(MIMEText("Grocery deals this week. Enable HTML to view the full email.", "plain"))
        # HTML version
        msg.attach(MIMEText(html, "html"))

        # Create message for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        send_message = {"raw": raw_message}

        # Send via Gmail API
        service.users().messages().send(userId="me", body=send_message).execute()
        print(f"✓ Email sent successfully to {recipient}")

    except HttpError as error:
        print(f"✗ Gmail API error: {error}")
        raise


def setup_oauth_credentials() -> None:
    """
    Instructions for setting up OAuth credentials.
    User must do this once before first run.
    """
    print("""
    ===== Gmail OAuth 2.0 Setup =====

    1. Go to: https://console.cloud.google.com/
    2. Create a new project or select existing one
    3. Enable the Gmail API:
       - Search "Gmail API" → Click "Enable"
    4. Create OAuth 2.0 credentials:
       - Go to "Credentials" → "Create Credentials"
       - Select "OAuth client ID"
       - Choose "Desktop application"
       - Download JSON file
    5. Save the JSON file as: gmail_credentials.json
       (in the same directory as this script)
    6. Run your app - it will open a browser for login
    7. Authorize the app → tokens are saved automatically

    ===================================
    """)
