import logging
import json

logger = logging.getLogger(__name__)

RULE_TEMPLATES = [
    {
        "condition": lambda a, inv: a and a.get('topProducts') and any(p.get('growth', 0) > 30 for p in a['topProducts']),
        "build": lambda a, inv: {
            "title": "Accelerate Top Growth Products",
            "text": f"Products with 30%+ growth detected. Increase marketing and inventory allocation for high-performers to capture momentum.",
            "severity": "high", "category": "revenue", "metric": ">30% growth", "action": "Scale marketing spend",
        }
    },
    {
        "condition": lambda a, inv: a and a.get('topProducts') and any(p.get('growth', 0) < -5 for p in a['topProducts']),
        "build": lambda a, inv: {
            "title": "Declining Product Needs Attention",
            "text": "One or more products show negative growth. Investigate pricing, UI, and competitive positioning.",
            "severity": "medium", "category": "product", "metric": "Negative growth", "action": "Product review sprint",
        }
    },
    {
        "condition": lambda a, inv: inv and inv.get('inventoryItems') and any(
            float(i.get('stock', 0)) < float(i.get('reorderLevel', 50)) for i in inv['inventoryItems']
        ),
        "build": lambda a, inv: {
            "title": "Low Stock Alert",
            "text": "Some products are below reorder levels. Place orders now to avoid stockouts.",
            "severity": "high", "category": "inventory", "metric": "Below reorder level", "action": "Reorder now",
        }
    },
    {
        "condition": lambda a, inv: True,
        "build": lambda a, inv: {
            "title": "Upsell to Your Champions",
            "text": "High-value customers spend 4× more than average but may not use all product lines. Target with personalized upsell offers.",
            "severity": "medium", "category": "revenue", "metric": "4× avg spend", "action": "Launch upsell campaign",
        }
    },
    {
        "condition": lambda a, inv: True,
        "build": lambda a, inv: {
            "title": "Re-engage At-Risk Customers",
            "text": "Customers with no activity in 45+ days have higher churn probability. A targeted re-engagement campaign can recover lost revenue.",
            "severity": "high", "category": "retention", "metric": "45+ days inactive", "action": "Email campaign",
        }
    },
    {
        "condition": lambda a, inv: True,
        "build": lambda a, inv: {
            "title": "Weekend Sales Opportunity",
            "text": "Weekend conversion rates are typically 18% higher. Consider running promotions on Friday-Sunday to maximize revenue.",
            "severity": "low", "category": "marketing", "metric": "+18% weekend CVR", "action": "Schedule weekend promo",
        }
    },
]


def generate_recommendations(analytics: dict, inv_analytics: dict, use_ai: bool = False, api_key: str = '') -> list:
    recs = []
    for template in RULE_TEMPLATES:
        try:
            if template["condition"](analytics, inv_analytics):
                recs.append(template["build"](analytics, inv_analytics))
        except Exception:
            pass

    if use_ai and api_key:
        try:
            ai_recs = _call_claude(analytics, inv_analytics, api_key)
            recs = ai_recs + recs
        except Exception as e:
            logger.warning(f"Claude API call failed: {e}")

    return recs[:8]


def _call_claude(analytics: dict, inv_analytics: dict, api_key: str) -> list:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    summary = {
        "revenue": analytics.get('revenue', {}).get('total', 0) if analytics else 0,
        "topProducts": [p['name'] for p in (analytics or {}).get('topProducts', [])[:3]],
        "growthLeader": max(
            (analytics or {}).get('topProducts', [{}]),
            key=lambda p: p.get('growth', 0),
            default={}
        ).get('name', 'N/A'),
    }

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system="You are a business analytics AI. Return ONLY a JSON array of 3 recommendation objects with keys: title, text, severity (high/medium/low), category, metric, action.",
        messages=[{"role": "user", "content": f"Generate 3 business recommendations for this data: {json.dumps(summary)}"}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace('```json', '').replace('```', '').strip()
    return json.loads(raw)
