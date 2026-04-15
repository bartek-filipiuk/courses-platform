"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "./api-client";
import { getDevToken } from "./dev-auth";

/**
 * Hook for authenticated API calls.
 * Auto-fetches dev token in development, uses NextAuth session in production.
 */
export function useAuthFetch<T>(
	path: string,
	options?: { role?: "student" | "admin"; skip?: boolean },
) {
	const [data, setData] = useState<T | null>(null);
	const [loading, setLoading] = useState(!options?.skip);
	const [error, setError] = useState<string | null>(null);
	const fetchedRef = useRef(false);

	useEffect(() => {
		if (options?.skip || fetchedRef.current) return;
		fetchedRef.current = true;

		(async () => {
			try {
				const token = await getDevToken(options?.role || "student");
				const result = await apiClient<T>(path, { token });
				setData(result);
			} catch (e) {
				setError(e instanceof Error ? e.message : "Failed to fetch");
			} finally {
				setLoading(false);
			}
		})();
	}, [path, options?.role, options?.skip]);

	return { data, loading, error };
}

/**
 * Returns an authenticated fetch function for mutations (POST, PUT, DELETE).
 */
export function useAuthMutate(role: "student" | "admin" = "student") {
	const tokenRef = useRef<string | null>(null);

	const mutate = useCallback(
		async <T>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> => {
			if (!tokenRef.current) {
				tokenRef.current = await getDevToken(role);
			}
			return apiClient<T>(path, { ...opts, token: tokenRef.current });
		},
		[role],
	);

	return mutate;
}
