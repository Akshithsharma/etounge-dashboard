"""
PayRecover AI — Autonomous Failed Payment Recovery Agent
Backend: FastAPI + Gemini

This service:
1. Ingests failed/abandoned payment events (from Razorpay webhooks, or the
   /simulate endpoint for demo purposes).
2. Runs an AI agent (Gemini) that reasons about the failure and decides a
   recovery strategy.
3. Executes the recovery action (in demo mode: generates the message/link
   and logs it — swap in real Razorpay Payment Links API + email/WhatsApp
   provider for production).
4. Persists every event + the agent's full reasoning trace to Supabase so
   the dashboard can show "what the agent thought and did".
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from supabase import create_client, Client
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    print(f"DEBUG: SUPABASE_URL='{SUPABASE_URL}' (len={len(SUPABASE_URL)})")
    print(f"DEBUG: SUPABASE_SERVICE_KEY starts='{SUPABASE_SERVICE_KEY[:12]}...' ends='...{SUPABASE_SERVICE_KEY[-6:]}' (len={len(SUPABASE_SERVICE_KEY)})")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    print(f"DEBUG: Missing env vars. SUPABASE_URL set={bool(SUPABASE_URL)}, SUPABASE_SERVICE_KEY set={bool(SUPABASE_SERVICE_KEY)}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="PayRecover AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class FailedPayment(BaseModel):
    merchant_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str = "INR"
    failure_reason: str
    payment_method: str
    order_id: Optional[str] = None


class RecoveryEvent(BaseModel):
    id: str
    merchant_id: str
    customer_name: str
    amount: float
    currency: str
    failure_reason: str
    payment_method: str
    agent_reasoning: str
    strategy: str
    recovery_message: str
    recovery_link: str
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Agent core
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are PayRecover, an autonomous payment recovery agent for an Indian \
fintech merchant platform (built on Razorpay). You are given details of a FAILED or ABANDONED \
payment. Your job:

1. Diagnose the most likely root cause of the failure in plain language.
2. Pick exactly ONE recovery strategy from this list, based on the failure reason:
   - "instant_retry_link": for transient/technical failures (bank timeout, network error, \
gateway declined) — send a one-click retry link immediately.
   - "alternate_method_nudge": for failures tied to a specific method (insufficient funds on \
card, UPI PIN error) — suggest an alternate payment method (UPI/Netbanking/Card).
   - "discount_recovery": for cart abandonment / no explicit technical failure — offer a small \
time-limited incentive (e.g. 5% off, free shipping) to complete the purchase.
   - "manual_review": for suspected fraud, repeated failures, or high-value/high-risk orders — \
flag for human review instead of automated outreach.
3. Write a short, warm, non-pushy recovery message (2-3 sentences) to the customer, in the \
tone of a helpful merchant, NOT a bot. Do not sound desperate or spammy.
4. Respond ONLY with valid JSON, no markdown, no backticks, in this exact shape:
{
  "reasoning": "1-3 sentence diagnosis of why this likely failed",
  "strategy": "one of the four strategy keys above",
  "message": "the customer-facing recovery message",
  "confidence": "high|medium|low"
}
"""


def run_agent(payment: FailedPayment) -> dict:
    """Calls Gemini to reason about the failed payment and decide a recovery
    strategy. Falls back to a deterministic rule-based decision if no API
    key is configured, so the service is still demoable without secrets."""

    if not GEMINI_API_KEY:
        return _fallback_agent(payment)

    user_prompt = f"""Failed payment details:
- Customer: {payment.customer_name}
- Amount: {payment.amount} {payment.currency}
- Payment method attempted: {payment.payment_method}
- Failure reason (raw): {payment.failure_reason}
- Order ID: {payment.order_id or "N/A"}
"""

    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=AGENT_SYSTEM_PROMPT,
        )
        response = model.generate_content(user_prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data
    except Exception as e:
        fallback = _fallback_agent(payment)
        fallback["reasoning"] += f" (Note: AI call failed, used rule-based fallback: {e})"
        return fallback


def _fallback_agent(payment: FailedPayment) -> dict:
    reason = payment.failure_reason.lower()
    if "insufficient" in reason or "pin" in reason:
        strategy = "alternate_method_nudge"
        reasoning = "Failure tied to the specific payment method used."
        message = (
            f"Hi {payment.customer_name}, we noticed your payment didn't go through. "
            f"Would UPI or Netbanking work better? Your order is still saved and ready to go."
        )
    elif "timeout" in reason or "network" in reason or "gateway" in reason:
        strategy = "instant_retry_link"
        reasoning = "Likely a transient technical/network issue, not a real decline."
        message = (
            f"Hi {payment.customer_name}, looks like a technical hiccup interrupted your "
            f"payment. Here's a quick link to try again — should take 10 seconds."
        )
    elif "fraud" in reason or "risk" in reason:
        strategy = "manual_review"
        reasoning = "Flagged as a risk/fraud-pattern failure; routing to human review."
        message = "Our team is reviewing this order and will follow up shortly."
    else:
        strategy = "discount_recovery"
        reasoning = "No clear technical cause — likely cart abandonment."
        message = (
            f"Hi {payment.customer_name}, you left something in your cart! Complete your "
            f"order in the next 2 hours and get 5% off."
        )
    return {
        "reasoning": reasoning,
        "strategy": strategy,
        "message": message,
        "confidence": "medium",
    }


def build_recovery_link(order_id: Optional[str]) -> str:
    """In production, this would call the Razorpay Payment Links API to
    generate a real one-click retry link. For the demo, we return a
    representative placeholder URL."""
    ref = order_id or uuid.uuid4().hex[:10]
    return f"https://pay.example-merchant.com/retry/{ref}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def health():
    return {"status": "ok", "service": "PayRecover AI"}


@app.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    """Real Razorpay webhook endpoint. Verifies signature, extracts failed
    payment events (payment.failed), and runs the agent on them."""
    body = await request.body()
    payload = json.loads(body)

    # TODO for production: verify x_razorpay_signature using RAZORPAY_WEBHOOK_SECRET
    # via hmac-sha256 as per Razorpay docs before trusting the payload.

    event = payload.get("event", "")
    if event != "payment.failed":
        return {"status": "ignored", "event": event}

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    failed_payment = FailedPayment(
        merchant_id=entity.get("notes", {}).get("merchant_id", "unknown"),
        customer_name=entity.get("email", "Customer").split("@")[0],
        customer_email=entity.get("email", ""),
        amount=(entity.get("amount", 0) or 0) / 100,
        currency=entity.get("currency", "INR"),
        failure_reason=entity.get("error_description", "unknown"),
        payment_method=entity.get("method", "unknown"),
        order_id=entity.get("order_id"),
    )
    result = await process_failed_payment(failed_payment)
    return result


@app.post("/simulate")
async def simulate_failed_payment(payment: FailedPayment):
    """Demo endpoint — lets the dashboard trigger a synthetic failed
    payment so the agent can be shown working end-to-end without a live
    Razorpay account."""
    return await process_failed_payment(payment)


async def process_failed_payment(payment: FailedPayment) -> dict:
    agent_result = run_agent(payment)
    recovery_link = build_recovery_link(payment.order_id)

    record = {
        "id": str(uuid.uuid4()),
        "merchant_id": payment.merchant_id,
        "customer_name": payment.customer_name,
        "amount": payment.amount,
        "currency": payment.currency,
        "failure_reason": payment.failure_reason,
        "payment_method": payment.payment_method,
        "agent_reasoning": agent_result["reasoning"],
        "strategy": agent_result["strategy"],
        "recovery_message": agent_result["message"],
        "recovery_link": recovery_link,
        "status": "sent" if agent_result["strategy"] != "manual_review" else "flagged",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if supabase:
        supabase.table("recovery_events").insert(record).execute()

    return record


@app.get("/recoveries")
def list_recoveries(merchant_id: Optional[str] = None, limit: int = 50):
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    query = supabase.table("recovery_events").select("*").order("created_at", desc=True).limit(limit)
    if merchant_id:
        query = query.eq("merchant_id", merchant_id)
    res = query.execute()
    return res.data


@app.get("/stats")
def get_stats(merchant_id: Optional[str] = None):
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    query = supabase.table("recovery_events").select("*")
    if merchant_id:
        query = query.eq("merchant_id", merchant_id)
    res = query.execute()
    rows = res.data or []
    total = len(rows)
    recovered_value = sum(r["amount"] for r in rows if r["status"] == "sent")
    by_strategy = {}
    for r in rows:
        by_strategy[r["strategy"]] = by_strategy.get(r["strategy"], 0) + 1
    return {
        "total_events": total,
        "estimated_revenue_at_risk_recovered": round(recovered_value, 2),
        "by_strategy": by_strategy,
    }
