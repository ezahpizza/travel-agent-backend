# Example MongoDB schema documentation for subscriptions and usage collections

# subscriptions collection
# {
#     "userid": "user123",
#     "plan": "basic" or "paid",
#     "status": "active" or "expired",
#     "start_date": "2025-06-01T00:00:00Z",
#     "end_date": "2025-06-30T23:59:59Z",
#     "razorpay_payment_id": "...",  # for paid plan
#     "razorpay_order_id": "...",    # for paid plan
#     "last_verified": "2025-06-01T00:00:00Z"
# }

# usage collection
# {
#     "userid": "user123",
#     "month": "2025-06",
#     "post_count": 7
# }
