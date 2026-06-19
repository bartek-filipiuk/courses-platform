/**
 * Session token store for the NDQS pilot.
 *
 * The magic-link flow is the session source: after a user clicks their link the
 * backend JWT is persisted here under `ndqs_token`, and the long-lived refresh
 * token under `ndqs_refresh`. Pages that need to call the authenticated API read
 * the access token via `getToken()`; the refresh token is used to rotate the
 * pair when the access token expires (see `refreshAccessToken` in dev-auth.ts).
 *
 * All access is guarded with `typeof window !== "undefined"` so these helpers are
 * safe to import from Server Components / during SSR (they simply no-op there).
 */

const KEY = "ndqs_token";
const REFRESH_KEY = "ndqs_refresh";

export function setToken(t: string): void {
	if (typeof window !== "undefined") {
		localStorage.setItem(KEY, t);
	}
}

export function getToken(): string | null {
	return typeof window !== "undefined" ? localStorage.getItem(KEY) : null;
}

export function clearToken(): void {
	if (typeof window !== "undefined") {
		localStorage.removeItem(KEY);
	}
}

export function setRefreshToken(t: string): void {
	if (typeof window !== "undefined") {
		localStorage.setItem(REFRESH_KEY, t);
	}
}

export function getRefreshToken(): string | null {
	return typeof window !== "undefined"
		? localStorage.getItem(REFRESH_KEY)
		: null;
}

export function clearRefreshToken(): void {
	if (typeof window !== "undefined") {
		localStorage.removeItem(REFRESH_KEY);
	}
}

/** Clears BOTH the access token and the refresh token — a clean logout. */
export function clearSession(): void {
	clearToken();
	clearRefreshToken();
}
