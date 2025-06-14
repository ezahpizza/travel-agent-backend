from fastapi import Depends, HTTPException, status, Request
from services.subscription_service import (
    get_subscription, get_usage, increment_usage, get_month_str
)
from datetime import datetime, timezone

BASIC_LIMIT = 15

async def paywall_dependency(request: Request):
    userid = request.query_params.get("userid")
    if not userid and request.method == "POST":
        try:
            data = await request.json()
            userid = data.get("userid")
        except Exception:
            userid = None
    if not userid:
        raise HTTPException(status_code=400, detail="Missing userid")
    sub = await get_subscription(userid)
    now = datetime.now(timezone.utc)
    month = get_month_str(now)
    plan = sub["plan"] if sub and sub["status"] == "active" and sub["end_date"] > now.isoformat() else "basic"
    if plan == "paid":
        return  # Unlimited
    # Basic plan: enforce POST limit
    if request.method == "POST":
        usage = await get_usage(userid, month)
        if usage >= BASIC_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Free plan limit reached ({BASIC_LIMIT} POST calls/month). Please upgrade."
            )
        await increment_usage(userid, month)
