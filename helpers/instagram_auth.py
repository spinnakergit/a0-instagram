"""
Instagram Graph API authentication and token management.

Instagram Business/Creator accounts use long-lived access tokens obtained via
Facebook Login. Tokens are initially short-lived (~1 hour), then exchanged for
long-lived tokens (~60 days), which can be refreshed before expiry.

Authentication flow:
1. User creates a Facebook App and adds Instagram Graph API product
2. Generates a User Access Token with required permissions
3. Exchanges short-lived token for long-lived token
4. Plugin stores the long-lived token in config
5. Token is refreshed automatically when nearing expiry

Required permissions:
- instagram_basic
- instagram_content_publish
- instagram_manage_comments
- instagram_manage_insights
"""

import os
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger("instagram_auth")

BASE_URL = "https://graph.facebook.com/v21.0"
GRAPH_URL = "https://graph.facebook.com/v21.0"
RATE_LIMIT_PER_HOUR = 200


def get_instagram_config(agent=None):
    """Load plugin config through A0's plugin config system."""
    try:
        from helpers import plugins
        return plugins.get_plugin_config("instagram", agent=agent) or {}
    except Exception:
        config_path = Path(__file__).parent.parent / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}


def _data_dir(config: dict) -> Path:
    """Get the data directory for storing token metadata."""
    try:
        from helpers import plugins
        plugin_dir = plugins.get_plugin_dir("instagram")
        data_dir = Path(plugin_dir) / "data"
    except Exception:
        data_dir = Path("/a0/usr/plugins/instagram/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _usage_path(config: dict) -> Path:
    """Path to the usage tracking file."""
    return _data_dir(config) / "usage.json"


def _token_meta_path(config: dict) -> Path:
    """Path to token metadata (saved_at timestamp, etc.)."""
    return _data_dir(config) / "token_meta.json"


def secure_write_json(path: Path, data: dict):
    """Atomic write with 0o600 permissions."""
    tmp = path.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        os.unlink(str(tmp))
        raise
    os.replace(str(tmp), str(path))


def _read_json(path: Path) -> dict:
    """Read a JSON file, return empty dict if missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_access_token(config: dict) -> str:
    """Get the Instagram access token from config."""
    return config.get("access_token", "").strip()


def get_ig_user_id(config: dict) -> str:
    """Get the Instagram Business/Creator account user ID from config."""
    return config.get("ig_user_id", "").strip()


def has_credentials(config: dict) -> bool:
    """Check if access token and user ID are configured."""
    return bool(get_access_token(config) and get_ig_user_id(config))


def get_auth_params(config: dict) -> dict:
    """Get query parameters with access_token for API requests."""
    token = get_access_token(config)
    if not token:
        return {}
    return {"access_token": token}


# --- Authentication Status ---

def is_authenticated(config: dict) -> tuple:
    """
    Check if credentials are valid by attempting to get the user profile.
    Returns (authenticated: bool, info: str).
    """
    if not has_credentials(config):
        if not get_access_token(config):
            return (False, "No access token configured")
        if not get_ig_user_id(config):
            return (False, "No Instagram User ID configured")
        return (False, "Missing credentials")

    try:
        import requests

        token = get_access_token(config)
        ig_user_id = get_ig_user_id(config)

        resp = requests.get(
            f"{BASE_URL}/{ig_user_id}",
            params={
                "fields": "id,username",
                "access_token": token,
            },
            timeout=10,
        )

        if resp.status_code == 200:
            data = resp.json()
            username = data.get("username", "unknown")
            info = f"@{username} (connected)"
            return (True, info)
        elif resp.status_code == 190:
            return (False, "Access token expired or invalid")
        else:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
            return (False, f"API error ({resp.status_code}): {detail}")
    except Exception as e:
        err = str(e)
        # Redact token from error messages to prevent leakage
        if token and token in err:
            err = err.replace(token, "[REDACTED]")
        return (False, err)


# --- Token Refresh ---

def refresh_long_lived_token(config: dict) -> dict:
    """
    Refresh a long-lived token (valid for 60 days, refreshable within last 24h of validity).
    Returns {"access_token": "...", "token_type": "bearer", "expires_in": ...} or {"error": "..."}.
    """
    import requests

    token = get_access_token(config)
    if not token:
        return {"error": "No access token to refresh"}

    try:
        resp = requests.get(
            f"{GRAPH_URL}/oauth/access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": token,
            },
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            # Save token metadata
            meta = {
                "refreshed_at": int(time.time()),
                "expires_in": data.get("expires_in", 5184000),
            }
            secure_write_json(_token_meta_path(config), meta)
            logger.info("Long-lived token refreshed successfully")
            return data
        else:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
            return {"error": f"Token refresh failed ({resp.status_code}): {detail}"}
    except Exception as e:
        return {"error": f"Token refresh request failed: {e}"}


# --- Usage Tracking ---

def get_usage(config: dict) -> dict:
    """Get current hour's usage stats (Instagram limits 200 calls/user/hour)."""
    current_hour = time.strftime("%Y-%m-%d-%H")
    usage = _read_json(_usage_path(config))
    if usage.get("hour") != current_hour:
        usage = {
            "hour": current_hour,
            "api_calls": 0,
            "posts_published": 0,
            "comments_posted": 0,
            "media_deleted": 0,
        }
        secure_write_json(_usage_path(config), usage)
    return usage


def increment_usage(config: dict, field: str = "api_calls"):
    """Increment a usage counter for the current hour."""
    usage = get_usage(config)
    usage[field] = usage.get(field, 0) + 1
    secure_write_json(_usage_path(config), usage)


def check_rate_limit(config: dict) -> tuple:
    """
    Check if we're approaching the rate limit.
    Returns (ok: bool, remaining: int).
    """
    usage = get_usage(config)
    calls = usage.get("api_calls", 0)
    remaining = RATE_LIMIT_PER_HOUR - calls
    return (remaining > 0, remaining)
