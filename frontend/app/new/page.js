"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { AnnouncementForm } from "../../components/AnnouncementForm";
import { ErrorBanner } from "../../components/ErrorBanner";
import { Header } from "../../components/Header";
import { RequireLeadership } from "../../components/RequireLeadership";
import { useAuth } from "../../components/AuthProvider";
import { api, errorMessage } from "../../lib/api";

export default function NewAnnouncementPage() {
  const { ready, user, token } = useAuth();
  const router = useRouter();
  const [locals, setLocals] = useState([]);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login");
    }
  }, [ready, user, router]);

  useEffect(() => {
    if (!token || user?.role !== "LEADERSHIP") {
      return;
    }
    let cancelled = false;
    Promise.all([
      api("/api/locals/", { token }),
      api("/api/members/", { token }),
    ]).then(([localsRes, membersRes]) => {
      if (cancelled) {
        return;
      }
      if (!localsRes.ok) {
        setError(errorMessage(localsRes.data, localsRes.status));
      } else if (!membersRes.ok) {
        setError(errorMessage(membersRes.data, membersRes.status));
      } else {
        setLocals(localsRes.data);
        setMembers(membersRes.data);
      }
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [token, user]);

  if (!ready || !user) {
    return (
      <main className="page">
        <p className="muted">Loading…</p>
      </main>
    );
  }

  return (
    <RequireLeadership>
      <main className="page">
        <Header localName={locals[0]?.name} />
        <p>
          <Link href="/">Back to announcements</Link>
        </p>
        <ErrorBanner message={error} />
        {loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <AnnouncementForm
            token={token}
            locals={locals}
            members={members}
            onChanged={({ sent } = {}) => {
              if (sent) {
                router.push("/");
              }
            }}
          />
        )}
      </main>
    </RequireLeadership>
  );
}
