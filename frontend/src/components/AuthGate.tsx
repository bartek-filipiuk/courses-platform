"use client";

/**
 * AuthGate – client-side auth guard (Task B12).
 *
 * Wraps route-group layouts so unauthenticated users are redirected to /login,
 * and non-admin users are redirected away from admin routes.
 *
 * Hydration-safe: the auth check runs inside `useEffect` (client-only), so the
 * SSR pass renders nothing — no server/client mismatch. A `mounted` flag gates
 * the real children from rendering until the client side has checked the token.
 *
 * JWT decode reuses the same pattern as `getTokenExpiry` in dev-auth.ts (B5):
 * split on ".", base64-decode the middle segment, JSON.parse. Any failure is
 * caught and treated as "not admin".
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken } from "@/lib/session";

interface Props {
	children: React.ReactNode;
	/** When true, the token must carry `role:"admin"` or the user is redirected to /. */
	requireAdmin?: boolean;
}

/** Safely decode the JWT payload and return the `role` claim (or null on failure). */
function getTokenRole(token: string): string | null {
	try {
		const segment = token.split(".")[1];
		if (!segment) return null;
		const json = JSON.parse(atob(segment)) as { role?: string };
		return typeof json.role === "string" ? json.role : null;
	} catch {
		return null;
	}
}

export default function AuthGate({ children, requireAdmin = false }: Props) {
	const router = useRouter();
	// `mounted` starts false so SSR renders null (no hydration mismatch).
	const [mounted, setMounted] = useState(false);
	// `allowed` tracks whether this client passed the auth checks.
	const [allowed, setAllowed] = useState(false);

	useEffect(() => {
		const token = getToken();

		if (!token) {
			router.replace("/login");
			setMounted(true); // mark mounted so we stop rendering the null shell
			return;
		}

		if (requireAdmin) {
			const role = getTokenRole(token);
			if (role !== "admin") {
				router.replace("/");
				setMounted(true);
				return;
			}
		}

		setAllowed(true);
		setMounted(true);
	}, [router, requireAdmin]);

	if (!mounted || !allowed) return null;

	return <>{children}</>;
}
