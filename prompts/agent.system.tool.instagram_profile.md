## instagram_profile
View Instagram profile information.

**Arguments:**
- **action** (string): "me" (default) or "lookup"
- **username** (string): Instagram handle for lookup (e.g. "natgeo" or "@natgeo"). Uses Business Discovery — only works for Business/Creator accounts.
- **user_id** (string): Instagram User ID for lookup (numeric ID). Use when you have the numeric ID.

When the user asks to look up a profile by handle/username, prefer `username` over `user_id`.

~~~json
{"action": "me"}
~~~
~~~json
{"action": "lookup", "username": "natgeo"}
~~~
~~~json
{"action": "lookup", "user_id": "17841400123456789"}
~~~
