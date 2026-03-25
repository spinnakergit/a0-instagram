---
name: "instagram-research"
description: "Research Instagram content via hashtags, insights, and feed analysis."
version: "1.0.0"
author: "AgentZero Instagram Plugin"
license: "MIT"
tags: ["instagram", "research", "insights", "analytics"]
triggers:
  - "instagram research"
  - "instagram analytics"
  - "instagram insights"
  - "search instagram hashtag"
  - "instagram trends"
allowed_tools:
  - instagram_search
  - instagram_insights
  - instagram_read
  - instagram_profile
metadata:
  complexity: "intermediate"
  category: "research"
---

# Instagram Research Skill

Research Instagram content through hashtag discovery, insights analysis, and feed exploration.

## Workflow

### Step 1: Check Account Performance
```json
{"tool": "instagram_insights", "args": {"action": "account", "period": "week"}}
```

### Step 2: Research a Hashtag
```json
{"tool": "instagram_search", "args": {"action": "hashtag", "query": "photography", "sort": "top"}}
```

### Step 3: Analyze a Specific Post
```json
{"tool": "instagram_insights", "args": {"action": "media", "media_id": "17895695668004550"}}
```

### Step 4: Review Recent Feed
```json
{"tool": "instagram_read", "args": {"action": "feed", "max_results": "20"}}
```

## Tips
- Hashtag search is limited to 30 unique tags per 7-day window
- Account insights support multiple periods: day, week, days_28, month, lifetime
- Use "top" sort for hashtag search to find high-engagement content
- Combine insights with feed data for a comprehensive analysis
