const PUSH_PREVIEW_MAX = 120;
const TITLE_MAX = 255;

export function buildDraftFromNote(note) {
  const trimmed = note.trim();
  if (!trimmed) {
    return null;
  }
  const firstLine = trimmed.split(/\r?\n/)[0].trim();
  return {
    title: firstLine.slice(0, TITLE_MAX),
    body: trimmed,
    push_preview: trimmed.replace(/\s+/g, " ").slice(0, PUSH_PREVIEW_MAX),
  };
}

export { PUSH_PREVIEW_MAX };
