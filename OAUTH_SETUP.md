# Gmail OAuth 2.0 Setup Guide

This app uses **secure OAuth 2.0** for Gmail authentication (compliant with 2025+ security standards).

## Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Click "Select a Project" → "New Project"
3. Name it: `GroceryBot` (or any name)
4. Click "Create"

## Step 2: Enable Gmail API

1. In the sidebar, search for "Gmail API"
2. Click the Gmail API result
3. Click "Enable"
4. Wait for it to be enabled (~30 seconds)

## Step 3: Create OAuth Credentials

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, click "Configure consent screen" first:
   - User Type: "External"
   - Click "Create"
   - Fill in App name: `GroceryBot`
   - User support email: your email
   - Click "Save and continue" (skip optional fields)
   - Click "Save and continue" again
4. Back to "Create OAuth client ID":
   - Application type: **Desktop application**
   - Name: `GroceryBot`
   - Click "Create"

## Step 4: Download and Save Credentials

1. Click the download icon (⬇️) next to your newly created credential
2. A JSON file downloads
3. **Save it as: `gmail_credentials.json`** in the same folder as `main.py`

## Step 5: First Run - Authorize App

```bash
python main.py
```

1. A browser window opens automatically
2. Sign in with your Gmail account
3. Grant permission: "GroceryBot wants to access your Gmail"
4. Close the browser tab
5. App continues and sends email

**That's it!** Tokens are saved automatically. Future runs won't prompt for auth.

## Troubleshooting

### "gmail_credentials.json not found"
- Make sure the file is in the same directory as `main.py`
- Filename must be exactly: `gmail_credentials.json`

### "OAuth consent screen not configured"
- Go back to Step 3, click "Configure consent screen"
- Mark it as "External" → save

### "Invalid client"
- Delete `gmail_token.pickle` if it exists
- Regenerate credentials (Step 3-4)
- Try again

### Still getting SMTP auth errors?
- Delete `gmail_token.pickle`
- Delete old `gmail_credentials.json`
- Redo Steps 1-5

## Fallback: SMTP (If OAuth Unavailable)

If you can't set up OAuth, the app falls back to SMTP with app password:

1. Enable 2FA on your Gmail: https://myaccount.google.com/security
2. Generate app password: https://myaccount.google.com/apppasswords
3. Select "Mail" → "Windows Computer"
4. Add to `.env`: `GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx`

**Note:** Google deprecated this method in 2025. OAuth is preferred.

---

Questions? Check the [CLAUDE.md](CLAUDE.md) for more context.
