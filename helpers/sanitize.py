"""
Instagram content sanitization, validation, and formatting utilities.

Instagram limits:
- Caption: 2,200 characters max
- Hashtags: 30 per post max
- Comments: 2,200 characters max
- Username: 30 characters max (alphanumeric, periods, underscores)
"""

import re
import os
import json
import unicodedata
from pathlib import Path

MAX_CAPTION_LENGTH = 2200
MAX_COMMENT_LENGTH = 2200
MAX_HASHTAGS_PER_POST = 30
MAX_USERNAME_LENGTH = 30
MAX_CONTENT_LENGTH = 4000  # For display/sanitization purposes


# --- Prompt Injection Defense ---

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+(instructions|prompts?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a?\s*(hacking|evil|malicious)", re.IGNORECASE),
    re.compile(r"(disregard|forget)\s+(all\s+)?(prior|previous|above)", re.IGNORECASE),
    re.compile(r"(system|admin)\s*:?\s*(prompt|override|command)", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|<<SYS>>|<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+)?prompt", re.IGNORECASE),
    re.compile(r"(act|behave)\s+as\s+if\s+you\s+(are|were)", re.IGNORECASE),
    re.compile(r"new\s+instructions?:?\s", re.IGNORECASE),
]

_DELIMITER_TAGS = [
    "instagram_content", "ig_content", "instagram_data", "ig_data",
    "instagram_messages", "ig_messages",
]


def sanitize_content(text: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """
    Sanitize user-generated content for safe processing.
    Applies NFKC normalization, zero-width stripping, injection detection,
    delimiter escaping, and length enforcement.
    """
    if not text:
        return ""

    # NFKC normalize (catches fullwidth bypasses)
    text = unicodedata.normalize("NFKC", text)

    # Strip zero-width characters
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)

    # Check injection patterns
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return "[Content blocked: potential prompt injection detected]"

    # Escape delimiter tags
    for tag in _DELIMITER_TAGS:
        text = text.replace(f"<{tag}>", f"&lt;{tag}&gt;")
        text = text.replace(f"</{tag}>", f"&lt;/{tag}&gt;")

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Enforce length
    if len(text) > max_length:
        text = text[:max_length - 30] + "\n[Content truncated]"

    return text.strip()


def sanitize_username(username: str) -> str:
    """Sanitize a username string."""
    if not username:
        return "unknown"

    username = unicodedata.normalize("NFKC", username)
    username = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", username)

    # Remove newlines
    username = username.replace("\n", "").replace("\r", "")

    # Check for injection in username
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(username):
            return "[Content blocked: injection in username]"

    # Instagram usernames: alphanumeric, periods, underscores, max 30 chars
    username = username.strip().lstrip("@")
    if len(username) > MAX_USERNAME_LENGTH:
        username = username[:MAX_USERNAME_LENGTH]

    return username or "unknown"


# --- Caption Validation ---

def validate_caption(caption: str) -> tuple:
    """
    Validate an Instagram caption.
    Returns (ok: bool, length: int, issues: list).
    """
    issues = []
    length = len(caption)

    if length > MAX_CAPTION_LENGTH:
        issues.append(f"Caption too long: {length}/{MAX_CAPTION_LENGTH} characters")

    # Count hashtags
    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > MAX_HASHTAGS_PER_POST:
        issues.append(f"Too many hashtags: {len(hashtags)}/{MAX_HASHTAGS_PER_POST}")

    ok = len(issues) == 0
    return (ok, length, issues)


def sanitize_caption(caption: str) -> str:
    """
    Sanitize a caption: normalize unicode, strip zero-width chars,
    check for prompt injection, collapse whitespace, trim.
    """
    caption = unicodedata.normalize("NFKC", caption)
    caption = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", caption)
    # Check injection patterns (same defense as sanitize_content)
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(caption):
            return "[Content blocked: potential prompt injection detected]"
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    return caption.strip()


def validate_hashtag(tag: str) -> str:
    """
    Validate and clean a hashtag.
    Returns cleaned tag (without #) or raises ValueError.
    """
    tag = tag.strip().lstrip("#")
    if not tag:
        raise ValueError("Hashtag cannot be empty")
    if len(tag) > 100:
        raise ValueError("Hashtag too long (max 100 characters)")
    if not re.match(r"^[a-zA-Z]\w*$", tag):
        raise ValueError(f"Invalid hashtag format: #{tag}")
    return tag


def validate_media_id(media_id: str) -> str:
    """Validate an Instagram media ID (numeric string)."""
    media_id = media_id.strip()
    if not media_id:
        raise ValueError("Media ID cannot be empty")
    if not re.match(r"^\d+(_\d+)?$", media_id):
        raise ValueError(f"Invalid media ID format: {media_id}")
    return media_id


_PRIVATE_HOST_PATTERNS = re.compile(
    r"^https?://(localhost|127\.|10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|169\.254\.|\[::1\]|\[fe80:)",
    re.IGNORECASE,
)


def validate_url(url: str) -> str:
    """Validate a URL for media publishing."""
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    if not url.startswith("https://"):
        raise ValueError("URL must start with https:// (Instagram requires HTTPS)")
    if len(url) > 2048:
        raise ValueError("URL too long (max 2048 characters)")
    if _PRIVATE_HOST_PATTERNS.match(url):
        raise ValueError("URL must not point to private/internal networks")
    return url


# --- Formatting ---

def _sanitize_external_text(text: str, max_len: int = 500) -> str:
    """Sanitize text from external sources to prevent prompt injection."""
    if not text:
        return text
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return "[Content filtered]"
    for tag in _DELIMITER_TAGS:
        text = text.replace(f"<{tag}>", f"&lt;{tag}&gt;")
        text = text.replace(f"</{tag}>", f"&lt;/{tag}&gt;")
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def format_media(media: dict) -> str:
    """Format a single media post for display."""
    media_type = media.get("media_type", "UNKNOWN")
    caption = _sanitize_external_text(media.get("caption", ""), max_len=200)
    timestamp = media.get("timestamp", "")[:19].replace("T", " ")
    permalink = media.get("permalink", "")
    likes = media.get("like_count", 0)
    comments = media.get("comments_count", 0)
    media_id = media.get("id", "")

    lines = [f"--- [{media_type}] ---"]
    if caption:
        lines.append(caption)
    lines.append(f"  [{timestamp}] Likes: {likes} | Comments: {comments}")
    if permalink:
        lines.append(f"  Link: {permalink}")
    if media_id:
        lines.append(f"  ID: {media_id}")
    return "\n".join(lines)


def format_media_list(media_list: list) -> str:
    """Format a list of media posts for display."""
    if not media_list:
        return "No media found."
    return "\n\n".join(format_media(m) for m in media_list)


def format_comment(comment: dict) -> str:
    """Format a single comment for display."""
    username = sanitize_username(comment.get("username", "unknown"))
    text = _sanitize_external_text(comment.get("text", ""), max_len=500)
    timestamp = comment.get("timestamp", "")[:19].replace("T", " ")
    likes = comment.get("like_count", 0)
    comment_id = comment.get("id", "")

    line = f"@{username}: {text}  [{timestamp}] ({likes} likes)"
    if comment_id:
        line += f" [ID: {comment_id}]"
    return line


def format_comments(comments: list) -> str:
    """Format a list of comments for display."""
    if not comments:
        return "No comments found."
    return "\n".join(format_comment(c) for c in comments)


def format_profile(profile: dict) -> str:
    """Format an Instagram profile for display."""
    username = sanitize_username(profile.get("username", "unknown"))
    name = _sanitize_external_text(profile.get("name", ""), max_len=100)
    bio = _sanitize_external_text(profile.get("biography", ""), max_len=300)
    media_count = profile.get("media_count", 0)
    followers = profile.get("followers_count", 0)
    following = profile.get("follows_count", 0)
    lines = [f"Profile: @{username}"]
    if name:
        lines.append(f"Name: {name}")
    if bio:
        lines.append(f"Bio: {bio}")
    lines.append(f"Posts: {media_count} | Followers: {followers} | Following: {following}")
    if profile.get("id"):
        lines.append(f"ID: {profile['id']}")
    return "\n".join(lines)


def format_insights(insights_data: list) -> str:
    """Format insights data for display."""
    if not insights_data:
        return "No insights data available."
    lines = []
    for metric in insights_data:
        name = metric.get("name", "unknown")
        title = metric.get("title", name)
        values = metric.get("values", [])
        if values:
            latest = values[-1].get("value", "N/A")
            end_time = values[-1].get("end_time", "")[:10]
            lines.append(f"{title}: {latest} (as of {end_time})")
        else:
            lines.append(f"{title}: N/A")
    return "\n".join(lines)


# --- Security Utilities ---

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


def clamp_limit(value, default: int = 25, maximum: int = 100) -> int:
    """Clamp a numeric limit to safe bounds."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, maximum)


def truncate_bulk(text: str, max_length: int = 200000) -> str:
    """Truncate very large text payloads."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n\n[Content truncated — too large for display]"
