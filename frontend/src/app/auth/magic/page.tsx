"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { setRefreshToken, setToken } from "@/lib/session";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Status = "verifying" | "error";

interface VerifyResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
	user_id: string;
}

function MagicCallback() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const [status, setStatus] = useState<Status>("verifying");

	useEffect(() => {
		const token = searchParams.get("token");

		if (!token) {
			setStatus("error");
			return;
		}

		let cancelled = false;

		(async () => {
			try {
				const resp = await fetch(
					`${API_BASE_URL}/api/auth/magic/verify?token=${encodeURIComponent(token)}`,
				);
				if (!resp.ok) throw new Error("verify failed");

				const data = (await resp.json()) as VerifyResponse;
				if (cancelled) return;

				setToken(data.access_token);
				if (data.refresh_token) {
					setRefreshToken(data.refresh_token);
				}
				router.replace("/missions");
			} catch {
				if (!cancelled) setStatus("error");
			}
		})();

		return () => {
			cancelled = true;
		};
	}, [searchParams, router]);

	return (
		<main className="flex min-h-screen flex-col items-center justify-center bg-bg-base px-4">
			<div className="w-full max-w-md space-y-8 rounded-xl border border-border-default bg-bg-elevated p-8 text-center">
				<div>
					<h1 className="font-mono text-2xl font-bold tracking-tight text-text-primary">
						{">"} NDQS Terminal
					</h1>
				</div>

				{status === "verifying" ? (
					<div className="flex flex-col items-center gap-4">
						<span className="h-8 w-8 animate-spin rounded-full border-2 border-accent-primary border-t-transparent" />
						<p className="font-mono text-sm text-text-secondary">Loguję…</p>
					</div>
				) : (
					<div className="space-y-4">
						<div className="rounded-lg border border-accent-primary/30 bg-accent-primary/5 p-6">
							<p className="font-mono text-sm font-medium text-accent-primary">
								Link wygasł lub jest nieprawidłowy — wróć na /login po nowy
							</p>
						</div>
						<a
							href="/login"
							className="btn btn-primary inline-flex w-full items-center justify-center"
						>
							Wróć do logowania
						</a>
					</div>
				)}
			</div>
		</main>
	);
}

export default function MagicPage() {
	return (
		<Suspense
			fallback={
				<main className="flex min-h-screen flex-col items-center justify-center bg-bg-base px-4">
					<span className="h-8 w-8 animate-spin rounded-full border-2 border-accent-primary border-t-transparent" />
				</main>
			}
		>
			<MagicCallback />
		</Suspense>
	);
}
