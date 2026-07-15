import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PayRecover AI",
  description: "Autonomous AI agent that recovers failed payments in real time.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-ink text-slate-100 antialiased">{children}</body>
    </html>
  );
}
