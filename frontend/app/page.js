"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Dashboard } from "../components/Dashboard";
import { RequireLeadership } from "../components/RequireLeadership";
import { useAuth } from "../components/AuthProvider";

export default function HomePage() {
  const { ready, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login");
    }
  }, [ready, user, router]);

  if (!ready || !user) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  return (
    <RequireLeadership>
      <Dashboard />
    </RequireLeadership>
  );
}
