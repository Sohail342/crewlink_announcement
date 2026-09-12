export function AnnouncementCounts({ counts, loading }) {
  if (loading && !counts) {
    return <p className="muted">Loading counts…</p>;
  }
  if (!counts) {
    return <p className="muted">Counts unavailable.</p>;
  }
  return (
    <dl className="counts">
      <div>
        <dt>Sent</dt>
        <dd>{counts.sent}</dd>
      </div>
      <div>
        <dt>Read</dt>
        <dd>{counts.read}</dd>
      </div>
      <div>
        <dt>Acknowledged</dt>
        <dd>{counts.acknowledged}</dd>
      </div>
    </dl>
  );
}
