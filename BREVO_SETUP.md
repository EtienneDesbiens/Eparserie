# Brevo SMTP Setup Guide

Brevo (formerly Sendinblue) is a free email service with better limits than competitors.

## Why Brevo?

✅ **Free tier:** 300 emails/day (plenty for daily GroceryBot runs)
✅ **No OAuth:** Just email + password
✅ **Professional:** Production-ready, trusted by thousands
✅ **Simple:** 5-minute setup

## Step 1: Sign Up (Free)

1. Go to: https://www.brevo.com/
2. Click **"Sign Up Free"** (top right)
3. Enter email, create password
4. Verify email
5. Done! Dashboard loads

## Step 2: Get SMTP Credentials

1. Click your profile icon (top right)
2. Go to **"Settings"** → **"SMTP & API"**
3. You'll see:
   - **SMTP Server:** `smtp-relay.brevo.com`
   - **SMTP Port:** `587`
   - **Email:** your-email@example.com (the one you signed up with)
   - **SMTP Password:** (click "Generate" if not shown)
4. Copy the SMTP password

## Step 3: Add to .env

1. Open `.env` in your editor
2. Fill in:
   ```
   BREVO_EMAIL=your-email@example.com
   BREVO_API_KEY=the_password_from_step_2
   EMAIL_FROM=noreply@grocerybot.local
   EMAIL_RECIPIENT=recipient@example.com
   ```
3. Save

## Step 4: Run GroceryBot

```bash
python main.py
```

You should see:
```
✓ Email sent successfully to recipient@example.com via Brevo
```

## Step 5: View Sent Emails (Optional)

1. Go to: https://www.brevo.com/
2. Click **"Transactional"** (left menu)
3. See all sent emails with delivery status

## That's It! 🎉

Now GroceryBot sends emails via Brevo!

### Notes

- **Free tier:** 300 emails/day (way more than needed)
- **Emails reach real inboxes** — not a testing service like Mailtrap
- **No daily limits** for outgoing emails
- **Production ready** — can scale up when needed

## Troubleshooting

### "Connection refused"
- Check SMTP host is: `smtp-relay.brevo.com`
- Check port is: `587`
- Check email/password are correct

### "Authentication failed"
- Go to Brevo → Settings → SMTP & API
- Check SMTP Password (not your account password!)
- Regenerate if needed
- Copy again and update `.env`

### "Email not sending"
- Check you're using correct email (the one you signed up with)
- Verify SMTP password hasn't expired
- Check internet connection

### "Too many emails"
- Brevo free tier: 300 emails/day
- GroceryBot sends 1 email/day
- You're well within limits

---

Need help? See [CLAUDE.md](CLAUDE.md) for more context.
