/**
 * Dev auth — auto-fetches JWT from backend /api/auth/dev/auto-token.
 * Production would use NextAuth session.
 *
 * Also home to refresh-token rotation: `refreshAccessToken()` swaps the stored
 * refresh token for a fresh access+refresh pair, and `getSessionToken()`
 * proactively refreshes when the access token is at/near expiry so learners are
 * not logged out at the 15-minute access-token boundary.
 */

import {
	clearSession,
	getRefreshToken,
	getToken,
	setRefreshToken,
	setToken,
} from "./session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Refresh when the access token is within this many seconds of expiry. */
const EXPIRY_SKEW_SECONDS = 60;

const tokenCache: Record<string, string> = {};

export async function getDevToken(
	role: "student" | "admin" = "student",
): Promise<string> {
	if (tokenCache[role]) return tokenCache[role];

	const resp = await fetch(`${API_URL}/api/auth/dev/auto-token?role=${role}`);
	if (!resp.ok) throw new Error("Dev auth unavailable");

	const data = await resp.json();
	tokenCache[role] = data.access_token;
	return data.access_token;
}

/**
 * Exchanges the stored refresh token for a fresh access+refresh pair.
 *
 * On success both new tokens are persisted and the new access token is returned.
 * On any failure (no refresh token, non-2xx response, network error) the whole
 * session is cleared so the user is cleanly logged out rather than stuck with a
 * dead access token, and the error is re-thrown for the caller to handle.
 */
export async function refreshAccessToken(): Promise<string> {
	const refreshToken = getRefreshToken();
	if (!refreshToken) {
		clearSession();
		throw new Error("No refresh token");
	}

	let resp: Response;
	try {
		resp = await fetch(`${API_URL}/api/auth/refresh`, {
			method: "POST",
			headers: { Authorization: `Bearer ${refreshToken}` },
		});
	} catch (err) {
		clearSession();
		throw err;
	}

	if (!resp.ok) {
		clearSession();
		throw new Error(`Refresh failed: ${resp.status}`);
	}

	const data = await resp.json();
	setToken(data.access_token);
	setRefreshToken(data.refresh_token);
	return data.access_token;
}

/**
 * Reads the `exp` (seconds since epoch) out of a JWT's payload.
 *
 * Returns `null` for any token we cannot decode (malformed, not a JWT, missing
 * `exp`). Callers treat `null` as "we don't know when this expires" and fall
 * back to refreshing — we never throw here.
 */
function getTokenExpiry(token: string): number | null {
	try {
		const payload = token.split(".")[1];
		if (!payload) return null;
		const json = JSON.parse(atob(payload)) as { exp?: number };
		return typeof json.exp === "number" ? json.exp : null;
	} catch {
		return null;
	}
}

/** True when the token is missing/expired/within the skew window of expiry. */
function isExpiredOrNearExpiry(token: string): boolean {
	const exp = getTokenExpiry(token);
	if (exp === null) return true; // undecodable -> refresh to be safe
	const nowSeconds = Math.floor(Date.now() / 1000);
	return exp - nowSeconds <= EXPIRY_SKEW_SECONDS;
}

/**
 * Resolves the bearer token for authenticated API calls.
 *
 * Prefers the magic-link session (`getToken()`). If that access token is at or
 * near expiry and a refresh token exists, rotates the pair first and returns the
 * fresh access token. Only when there is no session AND we are not in production
 * do we fall back to the dev auto-token — a convenience for local development
 * that must never leak into prod.
 */
export async function getSessionToken(
	role: "student" | "admin" = "student",
): Promise<string> {
	const sessionToken = getToken();
	if (sessionToken) {
		if (getRefreshToken() && isExpiredOrNearExpiry(sessionToken)) {
			return refreshAccessToken();
		}
		return sessionToken;
	}

	if (process.env.NODE_ENV !== "production") {
		return getDevToken(role);
	}

	throw new Error("Not authenticated");
}
