/**
 * Dev auth — auto-fetches JWT from backend /api/auth/dev/auto-token.
 * Production would use NextAuth session.
 */

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
