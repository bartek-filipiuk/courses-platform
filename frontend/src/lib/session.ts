/**
 * Session token store for the NDQS pilot.
 *
 * The magic-link flow is the session source: after a user clicks their link the
 * backend JWT is persisted here under `ndqs_token`. Pages that need to call the
 * authenticated API read it via `getToken()`.
 *
 * All access is guarded with `typeof window !== "undefined"` so these helpers are
 * safe to import from Server Components / during SSR (they simply no-op there).
 */

const KEY = "ndqs_token";

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
