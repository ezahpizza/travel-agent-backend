# Standard Library Imports
from datetime import datetime, timedelta, timezone

# Third-Party Imports
from fastapi import APIRouter, HTTPException, Request

# Application-Specific Imports
from services.subscription_service import (
    create_stripe_checkout_session,
    verify_stripe_payment,
    set_subscription,
    get_subscription,
    get_usage,
    get_month_str,
)

router = APIRouter()

@router.post("/create-session")
async def create_session(request: Request):
    data = await request.json()
    userid = data.get("userid")
    success_url = data.get("success_url")
    cancel_url = data.get("cancel_url")
    if not userid or not success_url or not cancel_url:
        raise HTTPException(status_code=400, detail="Missing userid or redirect URLs")
    session = await create_stripe_checkout_session(userid, success_url, cancel_url)
    return {"session": session}

@router.post("/verify-payment")
async def verify_payment(request: Request):
    data = await request.json()
    userid = data.get("userid")
    session_id = data.get("session_id")
    if not all([userid, session_id]):
        raise HTTPException(status_code=400, detail="Missing payment info")
    session = await verify_stripe_payment(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=30)
    await set_subscription(userid, "paid", "active", now.isoformat(), end.isoformat(), session_id, session.payment_intent)
    return {"success": True}

@router.get("/status")
async def subscription_status(userid: str):
    sub = await get_subscription(userid)
    now = datetime.now(timezone.utc)
    plan = "basic"
    if sub and sub["status"] == "active" and sub["end_date"] > now.isoformat():
        plan = sub["plan"]
    month = get_month_str(now)
    usage = await get_usage(userid, month)
    return {"plan": plan, "usage_this_month": usage}
