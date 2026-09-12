"use client";

import { AnnouncementCounts } from "./AnnouncementCounts";
import { Button } from "./Button";

export function AnnouncementList({
  announcements,
  countsById,
  loading,
  onSendDraft,
  sendingId,
}) {
  if (loading && announcements.length === 0) {
    return <p className="muted">Loading announcements…</p>;
  }

  if (announcements.length === 0) {
    return (
      <p className="muted">No announcements yet. Create one to send a callout.</p>
    );
  }

  return (
    <ul className="list">
      {announcements.map((announcement) => (
        <li key={announcement.id} className="card compact">
          <div className="row space">
            <h3>{announcement.title}</h3>
            <span className={`status status-${announcement.status}`}>
              {announcement.status}
            </span>
          </div>
          <p>{announcement.body}</p>
          <p className="muted">Preview: {announcement.push_preview}</p>
          <p className="muted">
            Ack required: {announcement.needs_ack ? "yes" : "no"}
          </p>
          {announcement.status === "draft" ? (
            <div className="row">
              <p className="muted">Counts appear after send.</p>
              {onSendDraft ? (
                <Button
                  type="button"
                  onClick={() => onSendDraft(announcement)}
                  disabled={sendingId === announcement.id}
                >
                  {sendingId === announcement.id ? "Sending…" : "Send"}
                </Button>
              ) : null}
            </div>
          ) : (
            <AnnouncementCounts
              counts={countsById[announcement.id]}
              loading={loading}
            />
          )}
        </li>
      ))}
    </ul>
  );
}
