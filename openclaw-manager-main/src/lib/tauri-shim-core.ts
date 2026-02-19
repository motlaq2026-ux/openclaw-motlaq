export type InvokeArgs = Record<string, unknown> | undefined;

const WEB_MANAGER_FLAG = '__OPENCLAW_WEB_MANAGER__';
const MANAGER_TOKEN_KEY = 'openclaw_manager_api_token';
const LEGACY_TOKEN_KEY = 'openclaw_api_key';

declare global {
  interface Window {
    __OPENCLAW_WEB_MANAGER__?: boolean;
  }
}

if (typeof window !== 'undefined') {
  window[WEB_MANAGER_FLAG] = true;
}

function getStoredToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.localStorage.getItem(MANAGER_TOKEN_KEY) || window.localStorage.getItem(LEGACY_TOKEN_KEY);
}

function saveToken(token: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(MANAGER_TOKEN_KEY, token);
  // Keep legacy key for compatibility with existing frontend logic.
  window.localStorage.setItem(LEGACY_TOKEN_KEY, token);
}

function getAuthHeaders(token?: string | null): Record<string, string> {
  if (typeof window === 'undefined') {
    return {};
  }

  const finalToken = token ?? getStoredToken();
  if (!finalToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${finalToken}`,
    'X-API-Key': finalToken,
  };
}

async function requestCommand(cmd: string, args?: InvokeArgs, token?: string | null): Promise<Response> {
  const response = await fetch(`/api/command/${cmd}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(token),
    },
    body: JSON.stringify(args ?? {}),
  });
  return response;
}

export async function invoke<T>(cmd: string, args?: InvokeArgs): Promise<T> {
  let token = getStoredToken();
  let response = await requestCommand(cmd, args, token);

  // First-time auth flow: ask user for token and retry once when backend requires auth.
  if (response.status === 401 && typeof window !== 'undefined' && !token) {
    const userToken = window.prompt('Enter Manager API token');
    if (userToken && userToken.trim()) {
      token = userToken.trim();
      saveToken(token);
      response = await requestCommand(cmd, args, token);
    }
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    // ignored
  }

  if (!response.ok) {
    const errorMessage =
      typeof payload === 'object' && payload !== null && 'error' in payload
        ? String((payload as { error: unknown }).error)
        : response.status === 401
          ? 'Unauthorized: set a valid Manager API token.'
          : `Command failed (${response.status})`;
    throw new Error(errorMessage);
  }

  if (
    typeof payload === 'object' &&
    payload !== null &&
    'ok' in payload &&
    (payload as { ok: boolean }).ok === true &&
    'data' in payload
  ) {
    return (payload as { data: T }).data;
  }

  return payload as T;
}
