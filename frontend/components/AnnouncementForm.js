"use client";

import { useEffect, useMemo, useState } from "react";

import { api, errorMessage } from "../lib/api";
import { PUSH_PREVIEW_MAX, buildDraftFromNote } from "../lib/draft";
import { Button } from "./Button";
import { ErrorBanner } from "./ErrorBanner";
import { Field } from "./Field";

export function AnnouncementForm({ token, locals, members, onChanged }) {
  const [note, setNote] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [pushPreview, setPushPreview] = useState("");
  const [needsAck, setNeedsAck] = useState(false);
  const [localId, setLocalId] = useState(locals[0]?.id ? String(locals[0].id) : "");
  const [classification, setClassification] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [draftId, setDraftId] = useState(null);

  useEffect(() => {
    if (!localId && locals[0]) {
      setLocalId(String(locals[0].id));
    }
  }, [localId, locals]);

  const classifications = useMemo(() => {
    const values = new Set(
      members
        .filter((member) => member.status === "active" && member.classification)
        .map((member) => member.classification),
    );
    return Array.from(values).sort();
  }, [members]);

  function validate() {
    const next = {};
    if (!title.trim()) {
      next.title = "Title is required.";
    }
    if (!body.trim()) {
      next.body = "Body is required.";
    }
    if (!pushPreview.trim()) {
      next.push_preview = "Push preview is required.";
    } else if (pushPreview.length > PUSH_PREVIEW_MAX) {
      next.push_preview = `Push preview must be ${PUSH_PREVIEW_MAX} characters or fewer.`;
    }
    if (!localId) {
      next.local = "Your account must belong to a local.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function generateDraft() {
    setFormError("");
    setStatusMessage("");
    const draft = buildDraftFromNote(note);
    if (!draft) {
      setFormError("Enter a leadership note before generating a draft.");
      return;
    }
    setTitle(draft.title);
    setBody(draft.body);
    setPushPreview(draft.push_preview);
    setStatusMessage("Draft generated. Review and edit before sending.");
  }

  async function saveDraftRecord() {
    const payload = {
      title: title.trim(),
      body: body.trim(),
      push_preview: pushPreview.trim(),
      needs_ack: needsAck,
    };
    const path = draftId
      ? `/api/announcements/${draftId}/`
      : "/api/announcements/";
    const { ok, status, data } = await api(path, {
      method: draftId ? "PATCH" : "POST",
      token,
      body: payload,
    });
    if (!ok) {
      throw new Error(errorMessage(data, status));
    }
    setDraftId(data.id);
    return data;
  }

  async function handleSaveDraft(event) {
    event.preventDefault();
    setFormError("");
    setStatusMessage("");
    if (!validate()) {
      return;
    }
    setSaving(true);
    try {
      const draft = await saveDraftRecord();
      setStatusMessage(`Draft #${draft.id} saved. Review it, then send.`);
      if (onChanged) {
        onChanged({ sent: false });
      }
    } catch (error) {
      setFormError(error.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleSend(event) {
    event.preventDefault();
    setFormError("");
    setStatusMessage("");
    if (!validate()) {
      return;
    }
    setSending(true);
    try {
      const draft = await saveDraftRecord();
      const payload = {};
      if (classification) {
        payload.classification = classification;
      }
      const { ok, status, data } = await api(
        `/api/announcements/${draft.id}/send/`,
        { method: "POST", token, body: payload },
      );
      if (!ok) {
        throw new Error(errorMessage(data, status));
      }
      setStatusMessage(data.detail || "sending to members");
      setNote("");
      setTitle("");
      setBody("");
      setPushPreview("");
      setNeedsAck(false);
      setClassification("");
      setDraftId(null);
      if (onChanged) {
        onChanged({ sent: true });
      }
    } catch (error) {
      setFormError(error.message);
    } finally {
      setSending(false);
    }
  }

  const busy = saving || sending;

  return (
    <form className="card" onSubmit={handleSend}>
      <h2>Create announcement</h2>
      <p className="muted">
        Enter a title and body, or paste a messy note and generate a draft.
        AI output is always a draft. Review it before sending. The API
        enforces local and leadership access.
      </p>

      <ErrorBanner message={formError} />
      {statusMessage ? <div className="banner ok">{statusMessage}</div> : null}

      <Field
        id="note"
        label="Leadership note (optional)"
        hint="Used only to generate a reviewable title, body, and push preview."
      >
        <textarea
          id="note"
          rows={4}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </Field>
      <div className="row">
        <Button type="button" variant="secondary" onClick={generateDraft} disabled={busy}>
          Generate draft
        </Button>
      </div>

      <Field id="title" label="Title" error={errors.title}>
        <input
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          maxLength={255}
        />
      </Field>
      <Field id="body" label="Body" error={errors.body}>
        <textarea
          id="body"
          rows={6}
          value={body}
          onChange={(event) => setBody(event.target.value)}
        />
      </Field>
      <Field
        id="push_preview"
        label="Push preview"
        hint={`Shown in the notification. Maximum ${PUSH_PREVIEW_MAX} characters.`}
        error={errors.push_preview}
      >
        <input
          id="push_preview"
          value={pushPreview}
          onChange={(event) => setPushPreview(event.target.value)}
          maxLength={PUSH_PREVIEW_MAX}
        />
      </Field>

      <Field
        id="local"
        label="Local"
        hint="You can only send to your own local."
        error={errors.local}
      >
        <select
          id="local"
          value={localId}
          onChange={(event) => setLocalId(event.target.value)}
          disabled={locals.length <= 1}
        >
          {locals.length === 0 ? (
            <option value="">No local assigned</option>
          ) : (
            locals.map((local) => (
              <option key={local.id} value={local.id}>
                {local.name}
              </option>
            ))
          )}
        </select>
      </Field>

      <Field
        id="classification"
        label="Work classification"
        hint="Entire local, or one classification. Only active members receive the send."
      >
        <select
          id="classification"
          value={classification}
          onChange={(event) => setClassification(event.target.value)}
        >
          <option value="">Entire local</option>
          {classifications.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </Field>

      <label className="check">
        <input
          type="checkbox"
          checked={needsAck}
          onChange={(event) => setNeedsAck(event.target.checked)}
        />
        Require acknowledgement
      </label>

      <div className="row">
        <Button type="button" variant="secondary" onClick={handleSaveDraft} disabled={busy}>
          {saving ? "Saving…" : "Save draft"}
        </Button>
        <Button type="submit" disabled={busy || !localId}>
          {sending ? "Sending…" : "Send announcement"}
        </Button>
      </div>
    </form>
  );
}
