import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      <nav className="flex items-center justify-between px-8 py-6 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-gradient-to-br from-accent to-accent2" />
          <span className="font-semibold tracking-tight">PayRecover AI</span>
        </div>
        <Link
          href="/login"
          className="text-sm px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition"
        >
          Sign in
        </Link>
      </nav>

      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-24">
        <span className="text-xs uppercase tracking-widest text-accent mb-4">
          Autonomous payment recovery
        </span>
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight max-w-3xl">
          An AI agent that recovers your{" "}
          <span className="bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">
            failed payments
          </span>{" "}
          automatically.
        </h1>
        <p className="mt-6 max-w-xl text-slate-400">
          Every failed or abandoned checkout is analyzed in real time. The agent diagnoses
          the failure, picks the right recovery strategy, and reaches out to the customer —
          with full visibility into its reasoning.
        </p>
        <div className="mt-10 flex gap-4">
          <Link
            href="/login"
            className="px-6 py-3 rounded-lg bg-accent text-ink font-medium hover:opacity-90 transition"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 rounded-lg border border-white/10 hover:bg-white/5 transition"
          >
            View demo dashboard
          </Link>
        </div>

        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full text-left">
          {[
            {
              title: "Diagnose",
              body: "The agent reasons about why each payment failed — technical, method-specific, or abandonment.",
            },
            {
              title: "Decide",
              body: "Picks one of four strategies: instant retry, alternate method nudge, discount recovery, or manual review.",
            },
            {
              title: "Act",
              body: "Generates a personalized recovery message and link, logged with full reasoning for every action.",
            },
          ].map((f) => (
            <div key={f.title} className="p-6 rounded-xl bg-panel border border-white/5">
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
