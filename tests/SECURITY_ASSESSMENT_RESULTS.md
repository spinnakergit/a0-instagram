# Security Assessment Results: Instagram Integration Plugin

| Field | Value |
|-------|-------|
| **Date** | 2026-03-24 |
| **Assessor** | Claude Code (Stage 3a white-box) |
| **Target** | `a0-instagram/` (Instagram Integration Plugin) |
| **Version** | 1.0.0 |
| **Stages Completed** | 3a (white-box source review) |
| **Files Reviewed** | 39 (all .py, .html, .yaml, .sh, .md in source tree) |
| **Plugin Type** | Social Media (Instagram Graph API v21.0) |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 3 |
| Informational | 4 |
| **Total** | **10** |

**Overall Verdict: PASS** — No critical or high-severity vulnerabilities. All Medium and Low findings remediated.

---

## Detailed Findings

### VULN-02: Access token leaked in exception messages

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Location** | `helpers/instagram_auth.py` `is_authenticated()`, `helpers/instagram_client.py` `_request()` |
| **Description** | Exception messages from HTTP libraries can include the full URL with query parameters, which contains the `access_token`. These raw exception strings were returned to the caller without redaction, potentially exposing the token in error displays, logs, or LLM context. |
| **Recommendation** | Scan exception strings for the token value and replace with `[REDACTED]` before returning. |
| **Status** | **Fixed** — Both `instagram_auth.py` and `instagram_client.py` now redact the token from exception messages. |

---

### VULN-03: URL validation allows HTTP and private network SSRF

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Location** | `helpers/sanitize.py` `validate_url()` |
| **Description** | The `validate_url()` function accepted `http://` URLs and did not block private/internal network ranges (`127.0.0.1`, `10.x`, `192.168.x`, `169.254.x`, `[::1]`, etc.). While Instagram's API itself requires HTTPS, an attacker could craft a URL that triggers a server-side request to internal services before the API rejects it. |
| **Recommendation** | Require `https://` scheme. Add regex to block private network host patterns. |
| **Status** | **Fixed** — `validate_url()` now requires `https://` and blocks private/internal network ranges via `_PRIVATE_HOST_PATTERNS` regex. |

---

### VULN-09: External content displayed without sanitization

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Location** | `helpers/sanitize.py` `format_media()`, `format_comment()`, `format_profile()` |
| **Description** | Formatting functions rendered captions, comment text, usernames, bios, and display names from Instagram API responses directly into the LLM context without sanitization. An attacker could craft an Instagram caption containing prompt injection payloads (e.g., "Ignore all previous instructions...") that would be processed by the LLM when the agent reads posts or comments. |
| **Recommendation** | Apply injection detection, NFKC normalization, zero-width stripping, and delimiter escaping to all external text before inclusion in LLM context. |
| **Status** | **Fixed** — Created `_sanitize_external_text()` helper and applied to all format functions: `format_media()` (caption), `format_comment()` (username + text), `format_profile()` (username + name + bio). |

---

### VULN-04: comment_id not validated in reply and delete operations

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Location** | `tools/instagram_comment.py` `_reply_comment()`, `_delete_comment()` |
| **Description** | The `_reply_comment()` and `_delete_comment()` methods did not validate `comment_id` format before passing it to API calls. While `_list_comments()` and `_post_comment()` both validated `media_id`, the comment operations accepted arbitrary strings. A malformed ID would simply produce an API error, but consistent validation prevents unexpected payloads from reaching the API layer. |
| **Recommendation** | Apply `validate_media_id()` to `comment_id` in both methods. |
| **Status** | **Fixed** — Both `_reply_comment()` and `_delete_comment()` now validate `comment_id` with `validate_media_id()`. |

---

### VULN-06: Username parameter not validated in Business Discovery

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Location** | `helpers/instagram_client.py` `get_user_by_username()` |
| **Description** | The `get_user_by_username()` method accepted any string as a username and interpolated it directly into the Graph API fields parameter. While the Graph API would reject malformed usernames, injecting special characters could potentially manipulate the fields query string. |
| **Recommendation** | Validate username format (alphanumeric, periods, underscores, max 30 chars) before interpolation. |
| **Status** | **Fixed** — Added `re.match(r"^[a-zA-Z0-9._]{1,30}$", username)` validation. |

---

### VULN-08: sanitize_caption() missing injection check

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Location** | `helpers/sanitize.py` `sanitize_caption()` |
| **Description** | The `sanitize_caption()` function performed NFKC normalization and zero-width stripping but did not check against `_INJECTION_PATTERNS`. A caption containing prompt injection text would pass through to the API. While this is the write path (user-authored content), defense-in-depth requires checking all text that enters the LLM context. |
| **Recommendation** | Add injection pattern check consistent with `sanitize_content()`. |
| **Status** | **Fixed** — Added injection pattern check loop to `sanitize_caption()`. |

---

### INFO-01: Rate limiter uses local counter, not API headers

| Field | Detail |
|-------|--------|
| **Severity** | Informational |
| **Location** | `helpers/instagram_client.py` `InstagramRateLimiter` |
| **Description** | The rate limiter tracks calls locally rather than using the `x-app-usage` header values from API responses. The `update_from_headers()` method logs usage data but doesn't adjust the counter. This works for single-instance deployments but would under-count in multi-instance scenarios. |
| **Status** | **Accepted** — Single-instance is the expected deployment model for Agent Zero plugins. |

---

### INFO-02: Token refresh requires manual intervention

| Field | Detail |
|-------|--------|
| **Severity** | Informational |
| **Location** | `helpers/instagram_auth.py` `refresh_long_lived_token()` |
| **Description** | Long-lived tokens expire after 60 days. The refresh function exists but is not called automatically. Users must manually trigger a refresh or generate a new token. |
| **Status** | **Accepted** — Documented in SETUP.md. Automatic refresh would require background scheduling not available in the A0 plugin framework. |

---

### INFO-03: Stories not publishable via API

| Field | Detail |
|-------|--------|
| **Severity** | Informational |
| **Location** | Plugin scope |
| **Description** | The Instagram Graph API does not support creating Stories. The `get_stories()` method can read existing stories but there is no publish capability. |
| **Status** | **Accepted** — Documented as Known Behavior. |

---

### INFO-04: Media deletion not supported by API

| Field | Detail |
|-------|--------|
| **Severity** | Informational |
| **Location** | `tools/instagram_manage.py` `_delete_media()` |
| **Description** | The Instagram Graph API does not support deleting media posts (neither organic nor API-published). The tool now returns a clear limitation message instead of attempting the API call. |
| **Status** | **Accepted** — Tool updated to return informative message. Documented as Known Behavior. |

---

## Attack Surface Review

| Category | Status | Notes |
|----------|--------|-------|
| **CSRF Protection** | PASS | Both API handlers return `requires_csrf() -> True` |
| **Token Masking** | PASS | Config API masks tokens in GET responses (`token[:3] + "****" + token[-3:]`) |
| **Token Persistence** | PASS | `secure_write_json()` uses `os.open()` with `0o600` permissions |
| **Input Validation** | PASS | All IDs validated with `validate_media_id()`; URLs require HTTPS + block private ranges |
| **Prompt Injection** | PASS | 8 regex patterns + NFKC normalization + zero-width stripping on both write and read paths |
| **Information Disclosure** | PASS | Token redacted from all error paths; generic errors for external-facing messages |
| **WebUI Security** | PASS | `data-ig=` attributes (no bare IDs); `globalThis.fetchApi || fetch` for CSRF; password input for token |
| **Rate Limiting** | PASS | 190-call safety buffer with async lock; 429 retry with backoff |
| **Dependency Security** | PASS | Only `aiohttp` and `requests` (well-maintained, no known CVEs) |
