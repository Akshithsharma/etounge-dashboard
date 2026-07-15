"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabaseClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STRATEGY_LABELS: Record<string, string> = {
  instant_retry_link: "Instant retry link",
  alternate_method_nudge: "Alternate method nudge",
  discount_recovery: "Discount recovery",
  manual_review: "Flagged for manual review",
};

const SAMPLE_FAILURES = [
  {
    customer_name: "Rahul Sharma",
    customer_email: "rahul@example.com",
    amount: 2499,
    failure_reason: "Payment gateway timeout during bank authorization",
    payment_method: "card",
  },
  {
    customer_name: "Priya Nair",
    customer_email: "priya@example.com",
    amount: 899,
    failure_reason: "Insufficient funds in account",
    payment_method: "card",
  },
  {
    customer_name: "Arjun Mehta",
    customer_email: "arjun@example.com",
    amount: 4999,
    failure_reason: "Incorrect UPI PIN entered",
    payment_method: "upi",
  },
  {
    customer_name: "Sneha Reddy",
    customer_email: "sneha@example.com",
    amount: 1299,
    failure_reason: "Checkout abandoned, no payment attempted",
    payment_method: "netbanking",
  },
  {
    customer_name: "Unknown User",
    customer_email: "flagged@example.com",
    amount: 15999,
    failure_reason: "Multiple rapid failed attempts, suspected fraud pattern",
    payment_method: "card",
  },
];

type RecoveryEvent = {
  id: string;
  customer_name: string;
  amount: number;
  currency: string;
  failure_reason: string;
  payment_method: string;
  agent_reasoning: string;
  strategy: string;
  recovery_message: string;
  recovery_link: string;
  status: string;
  created_at: string;
};

export default function Dashboard() {
  const [events, setEvents] = useState<RecoveryEvent[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [userEmail, setUserEmail] = useState<string>("");
  const router = useRouter();
  const supabase = createClient();
  const merchantId = "demo-merchant";

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) {
        router.push("/login");
      } else {
        setUserEmail(data.user.email || "");
      }
    });
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refresh() {
    try {
      const [evRes, statRes] = await Promise.all([
        fetch(`${API_URL}/recoveries?merchant_id=${merchantId}`),
        fetch(`${API_URL}/stats?merchant_id=${merchantId}`),
      ]);
      if (evRes.ok) setEvents(await evRes.json());
      if (statRes.ok) setStats(await statRes.json());
    } catch (e) {
      console.error(e);
    }
  }

  async function simulateFailure() {
    setLoading(true);
    const sample =
      SAMPLE_FAILURES[Math.floor(Math.random() * SAMPLE_FAILURES.length)];
    try {
      await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...sample, merchant_id: merchantId }),
      });
      await refresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <main className="min-h-screen">
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-gradient-to-br from-accent to-accent2" />
          <span className="font-semibold tracking-tight">PayRecover AI</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <span>{userEmail}</span>
          <button
            onClick={handleSignOut}
            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition"
          >
            Sign out
          </button>
        </div>
      </nav>

      <div className="px-8 py-8 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold">Recovery agent activity</h1>
            <p className="text-sm text-slate-400 mt-1">
              Live feed of the AI agent diagnosing and recovering failed payments.
            </p>
          </div>
          <button
            onClick={simulateFailure}
            disabled={loading}
            className="px-4 py-2.5 rounded-lg bg-accent text-ink text-sm font-medium hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "Agent working…" : "Simulate a failed payment"}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            label="Total events handled"
            value={stats?.total_events ?? "—"}
          />
          <StatCard
            label="Revenue recovered (est.)"
            value={
              stats
                ? `₹${stats.estimated_revenue_at_risk_recovered.toLocaleString()}`
                : "—"
            }
          />
          <StatCard
            label="Most used strategy"
            value={
              stats?.by_strategy
                ? Object.entries(stats.by_strategy).sort(
                    (a: any, b: any) => b[1] - a[1]
                  )[0]?.[0]
                  ? STRATEGY_LABELS[
                      Object.entries(stats.by_strategy).sort(
                        (a: any, b: any) => b[1] - a[1]
                      )[0][0]
                    ]
                  : "—"
                : "—"
            }
          />
        </div>

        <div className="space-y-4">
          {events.length === 0 && (
            <div className="text-center py-16 text-slate-500 border border-dashed border-white/10 rounded-xl">
              No events yet. Click "Simulate a failed payment" to watch the agent work.
            </div>
          )}
          {events.map((ev) => (
            <div
              key={ev.id}
              className="bg-panel border border-white/5 rounded-xl p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-medium">{ev.customer_name}</div>
                  <div className="text-xs text-slate-500">
                    ₹{ev.amount.toLocaleString()} · {ev.payment_method} ·{" "}
                    {new Date(ev.created_at).toLocaleString()}
                  </div>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full ${
                    ev.status === "flagged"
                      ? "bg-amber-500/10 text-amber-400"
                      : "bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  {STRATEGY_LABELS[ev.strategy] || ev.strategy}
                </span>
              </div>

              <div className="text-sm text-slate-400 mb-2">
                <span className="text-slate-500">Failure reason: </span>
                {ev.failure_reason}
              </div>

              <div className="bg-ink/60 rounded-lg p-3 mb-2 border border-white/5">
                <div className="text-xs text-accent mb-1">Agent reasoning</div>
                <div className="text-sm text-slate-300">{ev.agent_reasoning}</div>
              </div>

              <div className="bg-ink/60 rounded-lg p-3 border border-white/5">
                <div className="text-xs text-accent2 mb-1">
                  Recovery message sent
                </div>
                <div className="text-sm text-slate-300">{ev.recovery_message}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-panel border border-white/5 rounded-xl p-5">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}
