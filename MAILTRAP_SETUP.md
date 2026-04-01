# Mailtrap SMTP Setup Guide

Mailtrap is a free email testing service. Perfect for GroceryBot!

## Step 1: Sign Up (Free)

1. Go to: https://mailtrap.io/
2. Click **"Sign Up"** (top right)
3. Enter email, create password
4. Verify email
5. Done! You're logged in

## Step 2: Create an Inbox

1. In the dashboard, click **"Projects"** (left sidebar)
2. Click **"+ New Project"**
3. Name it: `GroceryBot`
4. Click **"Create Project"**
5. Click **"+ New Inbox"**
6. Name it: `Demo` (or any name)
7. Click **"Create Inbox"**

## Step 3: Get SMTP Credentials

1. Click on your inbox
2. Click **"Integrations"** (top tabs)
3. Look for **"SMTP"** section
4. You'll see:
   - **Username:** (copy this)
   - **Password:** (copy this)

## Step 4: Add to .env

1. Open `.env` in your editor
2. Fill in:
   ```
   MAILTRAP_USERNAME=your_username_from_step_3
   MAILTRAP_PASSWORD=your_password_from_step_3
   EMAIL_FROM=noreply@grocerybot.local
   EMAIL_RECIPIENT=your-email@example.com
   ```
3. Save

## Step 5: Run GroceryBot

```bash
python main.py
```

You should see:
```
✓ Email sent successfully to your-email@example.com via Mailtrap
```

## Step 6: View Email

1. Go back to: https://mailtrap.io/
2. Click your inbox
3. You'll see the email with:
   - HTML rendering
   - Full headers
   - Attachments (if any)

## That's It! 🎉

Now GroceryBot can send emails without any OAuth setup!

### Notes

- **Free tier:** 500 test emails/month (more than enough)
- **Emails won't reach your real inbox** — they go to Mailtrap
- **Great for testing** — see exactly how emails look
- **When ready for production:** upgrade Mailtrap account to send real emails

## Troubleshooting

### "Connection refused"
- Check SMTP host is: `live.smtp.mailtrap.io`
- Check port is: `587`
- Check username/password are correct (copy from Integrations tab)

### "Credentials invalid"
- Go to Mailtrap → Integrations → SMTP
- Copy username and password again
- Make sure no extra spaces
- Update `.env` and try again

### "Email not appearing"
- Check you're looking at the right inbox
- Refresh the page
- Check your console for error messages

---

Questions? See [CLAUDE.md](CLAUDE.md) for more context.
