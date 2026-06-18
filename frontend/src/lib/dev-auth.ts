/**
 * Dev auth — auto-fetches JWT from backend /api/auth/dev/auto-token.
 * Production would use NextAuth session.
 */

import { getToken } from "./session";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const tokenCache: Record<string, string> = {};

export async function getDevToken(role: "student" | "admin" = "student"): Promise<string> {
	if (tokenCache[role]) return tokenCache[role];

	const resp = await fetch(`${API_URL}/api/auth/dev/auto-token?role=${role}`);
	if (!resp.ok) throw new Error("Dev auth unavailable");

	const data = await resp.json();
	tokenCache[role] = data.access_token;
	return data.access_token;
}

/**
 * Resolves the bearer token for authenticated API calls.
 *
 * Prefers the magic-link session (`getToken()`). Only when there is no session
 * AND we are not in production do we fall back to the dev auto-token — a
 * convenience for local development that must never leak into prod.
 */
export async function getSessionToken(
	role: "student" | "admin" = "student",
): Promise<string> {
	const sessionToken = getToken();
	if (sessionToken) return sessionToken;

	if (process.env.NODE_ENV !== "production") {
		return getDevToken(role);
	}

	throw new Error("Not authenticated");
}
