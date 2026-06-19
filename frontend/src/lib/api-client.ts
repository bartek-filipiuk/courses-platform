import { refreshAccessToken } from "./dev-auth";
import { clearSession } from "./session";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiClientOptions {
	method?: string;
	body?: unknown;
	headers?: Record<string, string>;
	token?: string;
	apiKey?: string;
}

export async function apiClient<T>(
	path: string,
	options: ApiClientOptions = {},
): Promise<T> {
	const { method = "GET", body, headers = {}, token, apiKey } = options;

	/** Issues the request with the given bearer token (refreshed on retry). */
	const send = (bearer: string | undefined): Promise<Response> => {
		const requestHeaders: Record<string, string> = {
			"Content-Type": "application/json",
			...headers,
		};
		if (bearer) {
			requestHeaders.Authorization = `Bearer ${bearer}`;
		}
		if (apiKey) {
			requestHeaders["X-API-Key"] = apiKey;
		}
		return fetch(`${API_BASE_URL}${path}`, {
			method,
			headers: requestHeaders,
			body: body ? JSON.stringify(body) : undefined,
		});
	};

	let response = await send(token);

	// On a 401, attempt a single refresh-and-retry. The `attempted` guard makes
	// this strictly once — a second 401 (or a failed refresh) falls through to
	// the error path below, so there is no infinite refresh loop.
	if (response.status === 401) {
		let refreshedToken: string | undefined;
		try {
			refreshedToken = await refreshAccessToken();
		} catch {
			// Refresh failed; refreshAccessToken already cleared the session.
			refreshedToken = undefined;
		}

		if (refreshedToken) {
			response = await send(refreshedToken);
			if (response.status === 401) {
				// Retry still unauthorized -> clean logout, surface the error.
				clearSession();
			}
		}
	}

	if (!response.ok) {
		const error = await response.json().catch(() => ({
			detail: response.statusText,
		}));
		throw new ApiError(response.status, error.detail || "Unknown error");
	}

	return response.json() as Promise<T>;
}

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string,
	) {
		super(message);
		this.name = "ApiError";
	}
}
