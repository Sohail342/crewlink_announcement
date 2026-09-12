export async function api(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return { ok: true, status: 204, data: null };
  }

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  return { ok: response.ok, status: response.status, data };
}

export function errorMessage(data, status) {
  if (!data) {
    return `Request failed (${status})`;
  }
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map(itemMessage).join(" ");
  }
  if (typeof data === "object") {
    const parts = Object.entries(data).map(([field, value]) => {
      return `${field}: ${itemMessage(value)}`;
    });
    if (parts.length) {
      return parts.join(" ");
    }
  }
  return `Request failed (${status})`;
}

function itemMessage(value) {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(itemMessage).join(" ");
  }
  if (value && typeof value === "object" && value.string) {
    return value.string;
  }
  return JSON.stringify(value);
}
