"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { api, errorMessage } from "../lib/api";
import { AnnouncementList } from "./AnnouncementList";
import { ErrorBanner } from "./ErrorBanner";
import { Header } from "./Header";
import { useAuth } from "./AuthProvider";

const POLL_MS = 5000;

export function Dashboard() {
  const { token } = useAuth();
  const [locals, setLocals] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [countsById, setCountsById] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [sendingId, setSendingId] = useState(null);

  const load = useCallback(async () => {
    const [localsRes, announcementsRes] = await Promise.all([
      api("/api/locals/", { token }),
      api("/api/announcements/", { token }),
    ]);

    if (!localsRes.ok) {
      throw new Error(errorMessage(localsRes.data, localsRes.status));
    }
    if (!announcementsRes.ok) {
      throw new Error(errorMessage(announcementsRes.data, announcementsRes.status));
    }

    const localRows = localsRes.data;
    const announcementRows = announcementsRes.data;
    setLocals(localRows);
    setAnnouncements(announcementRows);

    const countable = announcementRows.filter(
      (row) => row.status !== "draft",
    );
    const countEntries = await Promise.all(
      countable.map(async (row) => {
        const result = await api(`/api/announcements/${row.id}/counts/`, {
          token,
        });
        return [row.id, result.ok ? result.data : null];
      }),
    );
    setCountsById(Object.fromEntries(countEntries));
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        await load();
        if (!cancelled) {
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    refresh();
    const timer = window.setInterval(refresh, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [load]);

  return (
    <main className="page">
      <Header localName={locals[0]?.name} />
      <ErrorBanner message={error} />
      <div className="toolbar">
        <h1>Announcements</h1>
        <Link href="/new">Create announcement</Link>
      </div>
      <section>
        <h2>Sent and drafts</h2>
        <p className="muted">
          Counts refresh every few seconds after send. Sending is asynchronous.
        </p>
        <AnnouncementList
          announcements={announcements}
          countsById={countsById}
          loading={loading}
          sendingId={sendingId}
          onSendDraft={async (announcement) => {
            setSendingId(announcement.id);
            setError("");
            try {
              const result = await api(
                `/api/announcements/${announcement.id}/send/`,
                { method: "POST", token, body: {} },
              );
              if (!result.ok) {
                throw new Error(errorMessage(result.data, result.status));
              }
              await load();
            } catch (err) {
              setError(err.message);
            } finally {
              setSendingId(null);
            }
          }}
        />
      </section>
    </main>
  );
}
