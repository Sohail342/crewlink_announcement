"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "../../components/Button";
import { ErrorBanner } from "../../components/ErrorBanner";
import { Field } from "../../components/Field";
import { useAuth } from "../../components/AuthProvider";

export default function LoginPage() {
  const { ready, user, login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (ready && user) {
      router.replace("/");
    }
  }, [ready, user, router]);

  async function handleSubmit(event) {
    event.preventDefault();
    const next = {};
    if (!email.trim()) {
      next.email = "Email is required.";
    }
    if (!password) {
      next.password = "Password is required.";
    }
    setFieldErrors(next);
    setError("");
    if (Object.keys(next).length) {
      return;
    }

    setSubmitting(true);
    try {
      await login(email.trim(), password);
      router.replace("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <h1>CrewLink</h1>
      <p className="muted">Sign in as leadership to send announcements.</p>
      <form className="card" onSubmit={handleSubmit}>
        <ErrorBanner message={error} />
        <Field id="email" label="Email" error={fieldErrors.email}>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </Field>
        <Field id="password" label="Password" error={fieldErrors.password}>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </main>
  );
}
