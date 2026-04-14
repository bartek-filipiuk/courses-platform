const API_BASE_URL =
	process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

	const requestHeaders: Record<string, string> = {
		"Content-Type": "application/json",
		...headers,
	};

	if (token) {
		requestHeaders.Authorization = `Bearer ${token}`;
	}
	if (apiKey) {
		requestHeaders["X-API-Key"] = apiKey;
	}

	const response = await fetch(`${API_BASE_URL}${path}`, {
		method,
		headers: requestHeaders,
		body: body ? JSON.stringify(body) : undefined,
	});

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
