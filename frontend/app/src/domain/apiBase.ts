export function normalizeApiBase(value: string): string {
  let normalized = value.trim();

  if (!normalized) return "";
  if (!/^https?:\/\//i.test(normalized)) {
    normalized = `https://${normalized}`;
  }

  return normalized.replace(/\/+$/, "").replace(/\/health$/i, "");
}

export function inferApiBaseFromLocation(location: Location): string {
  const { protocol, hostname } = location;

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return `${protocol}//${hostname}:8000`;
  }

  const codespacesBackend = hostname.match(/^(.*)-8000\.app\.github\.dev$/);
  if (codespacesBackend) {
    return `${protocol}//${hostname}`;
  }

  const codespacesMatch = hostname.match(/^(.*)-\d+\.app\.github\.dev$/);
  if (codespacesMatch) {
    return `${protocol}//${codespacesMatch[1]}-8000.app.github.dev`;
  }

  return "";
}
