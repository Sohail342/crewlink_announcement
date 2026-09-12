"use client";

import Link from "next/link";

import { useAuth } from "./AuthProvider";
import { Button } from "./Button";

export function RequireLeadership({ children }) {
  const { ready, user, logout } = useAuth();

  if (!ready) {
    return <p className="muted">Loading…</p>;
  }

  if (!user) {
    return null;
  }

  if (user.role !== "LEADERSHIP") {
    return (
      <main className="page">
        <h1>Leadership only</h1>
        <p>
          This UI is for union leadership. Members cannot send announcements
          from here. Access is enforced by the API.
        </p>
        <div className="row">
          <Button type="button" onClick={logout}>
            Log out
          </Button>
          <Link href="/login">Back to login</Link>
        </div>
      </main>
    );
  }

  return children;
}
