/**
 * Tests for refresh-token rotation (Task B5).
 *
 * Covers:
 *  - refreshAccessToken rotates the pair (stores new access+refresh, returns new access)
 *  - refresh 401 -> clearSession + throws
 *  - getSessionToken triggers a refresh when the access token is expired and a refresh token exists
 *  - api-client 401-retry path (retry once, then clear)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "./api-client";
import { getSessionToken, refreshAccessToken } from "./dev-auth";
import {
	getRefreshToken,
	getToken,
	setRefreshToken,
	setToken,
} from "./session";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Build a minimal JWT with the given `exp` (seconds since epoch). */
function makeJwt(exp: number): string {
	const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
	const payload = btoa(JSON.stringify({ sub: "u1", exp }));
	return `${header}.${payload}.sig`;
}

const nowSec = () => Math.floor(Date.now() / 1000);

beforeEach(() => {
	localStorage.clear();
	vi.unstubAllGlobals();
});

afterEach(() => {
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

describe("refreshAccessToken", () => {
	it("rotates the pair (stores new access+refresh, returns new access)", async () => {
		localStorage.setItem("ndqs_refresh", "r1");
		const fetchMock = vi.fn().mockResolvedValue({
			ok: true,
			status: 200,
			json: async () => ({
				access_token: "a2",
				refresh_token: "r2",
				token_type: "bearer",
			}),
		});
		vi.stubGlobal("fetch", fetchMock);

		const a = await refreshAccessToken();

		expect(a).toBe("a2");
		expect(getToken()).toBe("a2");
		expect(getRefreshToken()).toBe("r2");

		// Posts to the refresh endpoint with the stored refresh token as Bearer.
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, init] = fetchMock.mock.calls[0];
		expect(url).toBe(`${API_BASE}/api/auth/refresh`);
		expect(init.method).toBe("POST");
		expect(init.headers.Authorization).toBe("Bearer r1");
	});

	it("clears the session and throws when refresh returns 401", async () => {
		setToken("a1");
		setRefreshToken("r1");
		const fetchMock = vi.fn().mockResolvedValue({
			ok: false,
			status: 401,
			json: async () => ({ detail: "Invalid refresh token" }),
		});
		vi.stubGlobal("fetch", fetchMock);

		await expect(refreshAccessToken()).rejects.toThrow();

		expect(getToken()).toBeNull();
		expect(getRefreshToken()).toBeNull();
	});

	it("throws (and clears) when there is no stored refresh token", async () => {
		setToken("a1");
		const fetchMock = vi.fn();
		vi.stubGlobal("fetch", fetchMock);

		await expect(refreshAccessToken()).rejects.toThrow();
		expect(fetchMock).not.toHaveBeenCalled();
		expect(getToken()).toBeNull();
	});
});

describe("getSessionToken expiry check", () => {
	it("refreshes when the access token is expired and a refresh token exists", async () => {
		// Access token already expired.
		setToken(makeJwt(nowSec() - 10));
		setRefreshToken("r1");

		const fetchMock = vi.fn().mockResolvedValue({
			ok: true,
			status: 200,
			json: async () => ({
				access_token: "fresh-access",
				refresh_token: "fresh-refresh",
				token_type: "bearer",
			}),
		});
		vi.stubGlobal("fetch", fetchMock);

		const token = await getSessionToken();

		expect(token).toBe("fresh-access");
		expect(fetchMock).toHaveBeenCalledTimes(1);
		expect(getRefreshToken()).toBe("fresh-refresh");
	});

	it("does NOT refresh a token that is comfortably in the future", async () => {
		const valid = makeJwt(nowSec() + 3600);
		setToken(valid);
		setRefreshToken("r1");

		const fetchMock = vi.fn();
		vi.stubGlobal("fetch", fetchMock);

		const token = await getSessionToken();

		expect(token).toBe(valid);
		expect(fetchMock).not.toHaveBeenCalled();
	});

	it("does NOT crash on a malformed access token (treats as needing refresh)", async () => {
		setToken("not-a-jwt");
		setRefreshToken("r1");

		const fetchMock = vi.fn().mockResolvedValue({
			ok: true,
			status: 200,
			json: async () => ({
				access_token: "recovered",
				refresh_token: "recovered-r",
				token_type: "bearer",
			}),
		});
		vi.stubGlobal("fetch", fetchMock);

		const token = await getSessionToken();

		expect(token).toBe("recovered");
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});
});

describe("api-client 401 retry", () => {
	it("refreshes once and retries on 401, succeeding the second time", async () => {
		setToken("stale");
		setRefreshToken("r1");

		const fetchMock = vi
			.fn()
			// 1st: the original request -> 401
			.mockResolvedValueOnce({
				ok: false,
				status: 401,
				json: async () => ({ detail: "expired" }),
			})
			// 2nd: the refresh call -> new pair
			.mockResolvedValueOnce({
				ok: true,
				status: 200,
				json: async () => ({
					access_token: "a2",
					refresh_token: "r2",
					token_type: "bearer",
				}),
			})
			// 3rd: the retried original request -> success
			.mockResolvedValueOnce({
				ok: true,
				status: 200,
				json: async () => ({ data: "ok" }),
			});
		vi.stubGlobal("fetch", fetchMock);

		const result = await apiClient<{ data: string }>("/api/courses", {
			token: "stale",
		});

		expect(result).toEqual({ data: "ok" });
		expect(fetchMock).toHaveBeenCalledTimes(3);
		// Retry used the freshly rotated access token.
		const retryInit = fetchMock.mock.calls[2][1];
		expect(retryInit.headers.Authorization).toBe("Bearer a2");
	});

	it("retries at most once: a second 401 clears the session and surfaces the error", async () => {
		setToken("stale");
		setRefreshToken("r1");

		const fetchMock = vi
			.fn()
			// 1st: original -> 401
			.mockResolvedValueOnce({
				ok: false,
				status: 401,
				json: async () => ({ detail: "expired" }),
			})
			// 2nd: refresh -> ok
			.mockResolvedValueOnce({
				ok: true,
				status: 200,
				json: async () => ({
					access_token: "a2",
					refresh_token: "r2",
					token_type: "bearer",
				}),
			})
			// 3rd: retried original -> 401 again (do NOT loop further)
			.mockResolvedValueOnce({
				ok: false,
				status: 401,
				json: async () => ({ detail: "still expired" }),
			});
		vi.stubGlobal("fetch", fetchMock);

		await expect(
			apiClient("/api/courses", { token: "stale" }),
		).rejects.toBeInstanceOf(ApiError);

		// Exactly 3 fetches: original + one refresh + one retry. No infinite loop.
		expect(fetchMock).toHaveBeenCalledTimes(3);
		expect(getToken()).toBeNull();
		expect(getRefreshToken()).toBeNull();
	});
});
