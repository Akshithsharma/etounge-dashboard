# PayRecover AI

**An autonomous AI agent that recovers failed payments in real time — it diagnoses
why a payment failed, decides a recovery strategy, and acts, with full visibility
into its own reasoning.**

Every business loses revenue to failed and abandoned checkouts, and most of that
recovery work today is either manual or a blunt "retry email for everyone." This
agent treats each failure as a distinct case: it reads the failure signal, reasons
about the likely root cause, and picks one of four targeted responses — an instant
retry link, an alternate payment method nudge, a time-limited discount, or a flag
for human review when something looks risky.

It's built on the same shape of problem Razorpay's own Agent Studio ships
(dispute response, failed-payment recovery) — as an independent, working, deployed
prototype: real webhook integration, a real LLM reasoning loop, a real auth'd
dashboard, not a mockup.

**Live demo:** _add your deployed Vercel URL here_
**Stack:** Next.js 15 (App Router) + Tailwind + Supabase Auth (frontend) ·
FastAPI + Gemini (backend agent) · Supabase Postgres (data + RLS).

---

### What makes this "agentic" rather than a form with an LLM call bolted on

- The agent receives **unstructured, real-world failure data** (Razorpay's raw
  `error_description` strings) — not a clean dropdown of failure types.
- It has to **choose between competing strategies**, each with different
  downstream actions, based on judgment about the failure, not a lookup table.
- It **explains itself**: every action is logged with the reasoning that led to
  it, visible in the dashboard — the same transparency bar production agent
  systems (like Razorpay's) are held to.
- It's wired to **real infrastructure**: an actual Razorpay webhook contract in,
  an actual Payment Links integration point out (see "Going from demo to real
  Razorpay integration" below) — not a closed demo loop.

---

## 1. Set up Supabase

1. Create a project at https://supabase.com.
2. Go to SQL Editor → paste the contents of `supabase_schema.sql` → run it.
3. Go to Project Settings → API and copy:
   - `Project URL` → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (backend only — never expose to frontend)
4. Go to Authentication → Providers → make sure Email is enabled. For a fast demo,
   turn off "Confirm email" under Authentication → Settings so signup logs straight in.

## 2. Get a Gemini API key

Go to https://aistudio.google.com/app/apikey, create a key → `GEMINI_API_KEY`.
(The backend also works without this key — it falls back to a rule-based agent —
but the real Gemini reasoning is what makes this a genuine agentic demo.)

## 3. Deploy the backend (Render)

1. Push the `backend/` folder to a GitHub repo (or the whole project — Render can
   point at a subdirectory).
2. On https://render.com → New → Web Service → connect the repo.
3. Root directory: `backend`. Render will detect the `Dockerfile` automatically.
4. Add environment variables from `backend/.env.example` (real values).
5. Deploy. Note the resulting URL, e.g. `https://payrecover-api.onrender.com`.

## 4. Deploy the frontend (Vercel)

1. Push `frontend/` to GitHub (or same repo, set root directory to `frontend`).
2. On https://vercel.com → New Project → import the repo, root directory `frontend`.
3. Add environment variables from `frontend/.env.local.example`, using your real
   Supabase values and the Render backend URL for `NEXT_PUBLIC_API_URL`.
4. Deploy.

## 5. Try it

1. Visit your Vercel URL → Sign up with any email/password.
2. You'll land on `/dashboard`.
3. Click **"Simulate a failed payment"** — this fires a synthetic failed-payment
   event at the backend, the agent (Gemini) reasons about it, picks a recovery
   strategy, and the dashboard updates live with the agent's reasoning + message.

## 6. Going from demo to real Razorpay integration

The `/webhook/razorpay` endpoint in `backend/main.py` is already wired to parse
real Razorpay `payment.failed` webhook events — you just need to:

1. In the Razorpay Dashboard → Settings → Webhooks, add your Render URL +
   `/webhook/razorpay`, subscribe to `payment.failed`.
2. Set `RAZORPAY_WEBHOOK_SECRET` and uncomment/implement the HMAC-SHA256
   signature verification noted in the code (Razorpay's docs show the exact
   recipe) before trusting incoming payloads in production.
3. Replace `build_recovery_link()` with a real call to the Razorpay Payment
   Links API to generate a genuine one-click retry link, and wire the
   `recovery_message` into an actual email/WhatsApp send (e.g. via Resend,
   Twilio, or WhatsApp Business API).

## Project structure

```
payrecover-ai/
├── backend/              FastAPI + Gemini agent
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/             Next.js 15 app
│   ├── app/
│   │   ├── page.tsx          landing page
│   │   ├── login/page.tsx    Supabase auth
│   │   └── dashboard/page.tsx live agent activity feed
│   ├── lib/
│   ├── middleware.ts     route protection
│   └── .env.local.example
└── supabase_schema.sql   DB schema + RLS policies
```

## Why this is a strong Razorpay AI Builder showcase

- It's a **working agentic system**, not a wrapper: the agent reasons about
  unstructured failure data and picks between four distinct strategies —
  the same shape of problem as Razorpay's own Dispute Responder / recovery agents.
- It's **built directly on Razorpay's own webhook model** — the `/webhook/razorpay`
  route is real, not hypothetical.
- It demonstrates full-loop ownership: problem framing → architecture → auth →
  agent logic → dashboard → deployment, solo, in line with what the role asks for.
