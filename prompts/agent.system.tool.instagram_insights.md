## instagram_insights
View account and media insights from Instagram.

**Requires:** Business/Creator account with instagram_manage_insights permission

**Arguments:**
- **action** (string): "account" (default) or "media"
- **media_id** (string): Media ID (required for "media" action)
- **period** (string): Time period for account insights: "day" (default), "week", "days_28", "month", "lifetime"
- **metrics** (string): Comma-separated metric names (optional, uses defaults if omitted)

Account metrics: impressions, reach, follower_count, profile_views
Media metrics: impressions, reach, engagement, saved

~~~json
{"action": "account", "period": "week"}
~~~
~~~json
{"action": "account", "metrics": "impressions,reach,follower_count"}
~~~
~~~json
{"action": "media", "media_id": "17895695668004550"}
~~~
