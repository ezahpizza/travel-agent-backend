from config import settings
import stripe
from datetime import datetime, timezone
from db.connection import get_db

stripe.api_key = settings.STRIPE_API_KEY
STRIPE_PRICE_ID = settings.STRIPE_PRICE_ID
PAID_PLAN_PRICE = 199  # $1.99 in cents

def get_month_str(dt=None):
    if not dt:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m")

async def get_subscription(userid: str):
    db = get_db()
    return db.subscriptions.find_one({"userid": userid})

async def set_subscription(userid: str, plan: str, status: str, start_date, end_date, stripe_session_id=None, stripe_payment_intent=None):
    db = get_db()
    db.subscriptions.update_one(
        {"userid": userid},
        {"$set": {
            "plan": plan,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "stripe_session_id": stripe_session_id,
            "stripe_payment_intent": stripe_payment_intent,
            "last_verified": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

async def get_usage(userid: str, month: str):
    db = get_db()
    usage = db.usage.find_one({"userid": userid, "month": month})
    return usage["post_count"] if usage else 0

async def increment_usage(userid: str, month: str):
    db = get_db()
    db.usage.update_one(
        {"userid": userid, "month": month},
        {"$inc": {"post_count": 1}},
        upsert=True
    )

async def create_stripe_checkout_session(userid: str, success_url: str, cancel_url: str):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": STRIPE_PRICE_ID,
            "quantity": 1,
        }],
        mode="payment",
        customer_email=None,  # Optionally pass user's email
        metadata={"userid": userid},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session

async def verify_stripe_payment(session_id: str):
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        return session
    return None
