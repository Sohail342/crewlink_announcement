"use client";

import Link from "next/link";

import { useAuth } from "./AuthProvider";
import { Button } from "./Button";

export function Header({ localName }) {
  const { user, logout } = useAuth();

  return (
    <header className="header">
      <div>
        <Link href="/" className="brand">
          CrewLink
        </Link>
        {localName ? <span className="muted"> · {localName}</span> : null}
      </div>
      <div className="row">
        <span className="muted">{user?.email}</span>
        <Button type="button" variant="secondary" onClick={logout}>
          Log out
        </Button>
      </div>
    </header>
  );
}
