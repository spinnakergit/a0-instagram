# Instagram Integration Plugin -- Quick Start

## Prerequisites

- Agent Zero instance (Docker or local)
- Instagram Business or Creator account
- Facebook App with Instagram Graph API product
- Long-lived access token with required permissions

> **Need help setting up Instagram credentials?** See [SETUP.md](SETUP.md) for step-by-step instructions on creating a Facebook App, configuring permissions, generating tokens, and obtaining your Instagram User ID.

## Installation

```bash
# From inside the Agent Zero container:
cd /tmp
# Copy plugin files, then:
./install.sh

# Or manually:
cp -r a0-instagram/ /a0/usr/plugins/instagram/
ln -sf /a0/usr/plugins/instagram /a0/plugins/instagram
touch /a0/usr/plugins/instagram/.toggle-1
```

## Configuration

1. Open Agent Zero WebUI
2. Go to Settings > External Services > Instagram Integration
3. Enter your long-lived access token
4. Enter your Instagram User ID (numeric)
5. Click "Save Instagram Settings"
6. Click "Test Connection" on the dashboard

> **Where do I get these values?** The access token and User ID come from Facebook's Graph API Explorer. See [SETUP.md](SETUP.md) for the complete walkthrough including token exchange and User ID resolution.

## First Use

Ask the agent:
> "Show my Instagram profile"

Then try:
> "Show my recent Instagram posts"
> "Post this photo to Instagram: https://example.com/photo.jpg with caption: Hello world!"
> "Search Instagram for #photography"
> "Show my Instagram insights for this week"

## Example Workflows

### Publish Content
> "Post this photo to Instagram with the caption 'Sunset vibes' and hashtags #photography #sunset"

### Engage with Followers
> "Show me the comments on my latest Instagram post and reply to any questions"

### Analyze Performance
> "Get my Instagram account insights for this week and summarize the trends"

## Known Behaviors

- **Development Mode visibility:** When your Facebook App is in Development mode, API-created posts are only visible to users with a role on the app (admin, developer, tester).
- **Hashtag search requires App Review:** Instagram's Public Content Access feature requires Facebook approval before hashtag search works.
- **Business Discovery limitations:** Looking up users by username only works for Business/Creator accounts, not personal accounts.
- **Stories not publishable:** The Instagram Graph API does not support creating Stories. You can read existing stories but not publish new ones.
- **Media deletion not supported:** The API does not support deleting media posts. Posts must be deleted manually through the Instagram app.
- **Image URLs must be public HTTPS:** Media must be hosted at publicly accessible HTTPS URLs. The agent passes the URL directly to Instagram's servers.
- **Duplicate posts on retry:** If Agent Zero's framework retries a tool call after a transient error, posts or comments may be duplicated. Check for duplicates after errors.

## Troubleshooting

- **"No access token configured"** — Set the token in plugin settings (Settings > External Services > Instagram Integration)
- **"Invalid OAuth access token"** — Token may have expired (60-day lifespan); generate a new one via [SETUP.md](SETUP.md)
- **"Application does not have permission"** — Token missing required permissions; regenerate with all four scopes
- **"An unexpected error has occurred"** — Transient Instagram API error; retry the request
- **Hashtag search fails** — Requires Facebook App Review for Public Content Access feature
- **Rate limiting** — The plugin automatically handles rate limits (200 calls/hour); wait and retry
- **Plugin not visible after install** — Run `supervisorctl restart run_ui` inside the container
- **Posts not visible to other accounts** — App is in Development mode; add the account as a tester in App Roles
