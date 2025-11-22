# Slack Bot Setup Guide

This guide walks you through setting up the MWD Agent Slack bot for your workspace.

## Prerequisites

- A Slack workspace where you have admin permissions
- The MWD Agent application deployed and accessible via a public URL
- Access to environment variables configuration

## Step 1: Create a Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **Create New App**
3. Choose **From scratch**
4. Enter:
   - **App Name**: `MWD Agent` (or your preferred name)
   - **Workspace**: Select your workspace
5. Click **Create App**

## Step 2: Configure Bot Token Scopes

1. In the left sidebar, click **OAuth & Permissions**
2. Scroll to **Scopes** section
3. Under **Bot Token Scopes**, add the following:

### Required Scopes

| Scope | Purpose |
|-------|---------|
| `app_mentions:read` | Receive @mentions of the bot |
| `channels:history` | Read messages in public channels |
| `channels:read` | View basic channel info |
| `chat:write` | Send messages as the bot |
| `files:read` | Access file info and content |
| `groups:history` | Read messages in private channels |
| `groups:read` | View basic private channel info |
| `im:history` | Read direct messages |
| `im:read` | View basic DM info |
| `im:write` | Start direct messages |
| `reactions:read` | View emoji reactions |
| `reactions:write` | Add emoji reactions |
| `users:read` | View user info |

## Step 3: Install App to Workspace

1. In **OAuth & Permissions**, click **Install to Workspace**
2. Review the permissions and click **Allow**
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
4. Save this as `SLACK_BOT_TOKEN` in your environment

## Step 4: Get Signing Secret

1. Go to **Basic Information** in the left sidebar
2. Scroll to **App Credentials**
3. Copy the **Signing Secret**
4. Save this as `SLACK_SIGNING_SECRET` in your environment

## Step 5: Enable Event Subscriptions

1. Go to **Event Subscriptions** in the left sidebar
2. Toggle **Enable Events** to On
3. Enter your **Request URL**: `https://your-domain.com/slack/events`
4. Wait for Slack to verify the URL (your server must respond to the challenge)

### Subscribe to Bot Events

Add these events under **Subscribe to bot events**:

| Event | Description |
|-------|-------------|
| `app_mention` | Triggered when bot is @mentioned |
| `message.channels` | Messages in public channels |
| `message.groups` | Messages in private channels |
| `message.im` | Direct messages to the bot |
| `file_shared` | When files are uploaded |

5. Click **Save Changes**

## Step 6: Enable Interactivity

1. Go to **Interactivity & Shortcuts** in the left sidebar
2. Toggle **Interactivity** to On
3. Set **Request URL**: `https://your-domain.com/slack/interact`
4. Click **Save Changes**

## Step 7: Configure Environment Variables

Add these to your `.env` file:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Optional - for automated features
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_REMINDER_CHANNEL=C0123456789
SLACK_DIGEST_CHANNEL=C0123456789
```

### Finding Channel IDs

To get a channel ID:
1. Open Slack in a web browser
2. Navigate to the channel
3. The URL will be: `https://app.slack.com/client/TXXXXX/CXXXXXXX`
4. The `CXXXXXXX` part is the channel ID

## Step 8: Test the Integration

### Test Basic Messaging

1. Start your MWD Agent server
2. Invite the bot to a channel: `/invite @MWD Agent`
3. Mention the bot: `@MWD Agent hello`
4. You should see:
   - A thinking emoji reaction appear
   - A response message
   - A checkmark reaction when complete

### Test Quick Actions

Send a POST request to trigger the quick actions menu:

```bash
curl -X POST https://your-domain.com/slack/quick-actions \
  -H "Content-Type: application/json" \
  -d '{"channel": "C0123456789"}'
```

### Test Reminders

```bash
curl -X POST https://your-domain.com/slack/reminders \
  -H "Content-Type: application/json" \
  -d '{"channel": "C0123456789"}'
```

### Test Digest

```bash
curl -X POST https://your-domain.com/slack/digest \
  -H "Content-Type: application/json" \
  -d '{"channel": "C0123456789", "digest_type": "daily"}'
```

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/slack/events` | POST | Main event handler (messages, mentions, files) |
| `/slack/interact` | POST | Interactive components (buttons, modals) |
| `/slack/reminders` | POST | Manually trigger deadline reminders |
| `/slack/digest` | POST | Manually trigger activity digest |
| `/slack/quick-actions` | POST | Send quick actions menu |

## Automated Schedules

When the bot is running, these automated tasks are scheduled:

| Task | Schedule | Description |
|------|----------|-------------|
| Deadline Reminders | Daily 9:00 AM | Check Notion for upcoming deadlines |
| Daily Digest | Daily 6:00 PM | Summary of day's activity |
| Weekly Digest | Friday 5:00 PM | Summary of week's activity |

## Troubleshooting

### Bot doesn't respond

1. Check the server logs for errors
2. Verify `SLACK_BOT_TOKEN` is correct
3. Ensure the bot is invited to the channel
4. Check that Event Subscriptions are enabled

### Signature verification failed

1. Verify `SLACK_SIGNING_SECRET` is correct
2. Ensure your server clock is synchronized (NTP)
3. Check that the request isn't being modified by a proxy

### Interactive buttons don't work

1. Verify Interactivity is enabled
2. Check the Request URL is correct
3. Ensure the `/slack/interact` endpoint is accessible

### File uploads not detected

1. Ensure `file_shared` event is subscribed
2. Verify `files:read` scope is added
3. Check that the bot has access to the channel

## Security Best Practices

1. **Never commit tokens** - Use environment variables
2. **Verify signatures** - The bot automatically verifies all incoming requests
3. **Use HTTPS** - All webhook URLs must use HTTPS
4. **Limit channel access** - Only invite the bot to necessary channels
5. **Monitor usage** - Check Slack API usage in your app dashboard

## Features Overview

### Conversational AI
- Mention the bot with any request
- Maintains thread context
- Routes to appropriate AI based on request type

### Quick Actions
- New Branding Strategy
- Website Plan
- Social Media Strategy
- Research Topic
- Meeting Notes
- Email Drafting
- Project Folder Creation
- Competitor Analysis
- Client Portal Building

### Automated Updates
- Deadline reminders from Notion
- Daily/weekly activity digests
- Project status updates

### File Handling
- Documents: Summarization, key point extraction
- Spreadsheets: Data analysis suggestions
- Images: Description, OCR capabilities
- Media: Transcription options

## Next Steps

After setup is complete:

1. Test each feature in a private channel first
2. Configure Notion integration for deadline reminders
3. Set up Supabase for conversation persistence
4. Customize the quick action modal options as needed
5. Adjust scheduled task times in `main.py` if needed

## Support

For issues with this integration:
- Check the [MWD Agent Repository](https://github.com/HouseOfVibes/mwd-agent)
- Review the `integrations/slack_bot.py` and `integrations/slack_features.py` files
