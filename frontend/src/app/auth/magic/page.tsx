"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { setRefreshToken, setToken } from "@/lib/session";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Status = "verifying" | "error" | "resend-sent";

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
	const [resendEmail, setResendEmail] = useState("");
	const [resending, setResending] = useState(false);

	useEffect(() => {
		// Pre-fill email from query param if present (e.g. passed from login page)
		const emailParam = searchParams.get("email");
		if (emailParam) setResendEmail(emailParam);
	}, [searchParams]);

	async function handleResend(e: React.FormEvent<HTMLFormElement>) {
		e.preventDefault();
		if (resending) return;
		setResending(true);
		try {
			await fetch(`${API_BASE_URL}/api/auth/magic/request`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ email: resendEmail }),
			});
		} catch {
			// Mirror the login page's no-leak contract — always show success.
		} finally {
			setStatus("resend-sent");
			setResending(false);
		}
	}

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
				) : status === "resend-sent" ? (
					<div className="space-y-4">
						<div className="rounded-lg border border-accent-primary/30 bg-accent-primary/5 p-6">
							<p className="font-mono text-sm font-medium text-accent-primary">
								Sprawdź mail — wysłaliśmy nowy link logowania (ważny 15 min)
							</p>
							<p className="mt-3 text-xs text-text-secondary">
								Wysłaliśmy wiadomość na{" "}
								<span className="font-mono text-text-primary break-all">
									{resendEmail}
								</span>
								, jeśli ten adres jest zarejestrowany.
							</p>
						</div>
						<a
							href="/login"
							className="font-mono text-xs text-text-secondary underline-offset-4 transition-colors hover:text-accent-primary hover:underline"
						>
							Wróć do logowania
						</a>
					</div>
				) : (
					<div className="space-y-4">
						<div className="rounded-lg border border-accent-primary/30 bg-accent-primary/5 p-6">
							<p className="font-mono text-sm font-medium text-accent-primary">
								Link wygasł lub jest nieprawidłowy
							</p>
						</div>
						<form onSubmit={handleResend} className="space-y-3">
							<div className="space-y-1">
								<label
									htmlFor="resend-email"
									className="block font-mono text-xs tracking-wide text-text-secondary"
								>
									EMAIL
								</label>
								<input
									id="resend-email"
									name="email"
									type="email"
									required
									autoComplete="email"
									value={resendEmail}
									onChange={(e) => setResendEmail(e.target.value)}
									disabled={resending}
									placeholder="ty@przyklad.pl"
									className="input mono w-full disabled:opacity-50"
								/>
							</div>
							<button
								type="submit"
								disabled={resending}
								className="btn btn-primary flex w-full items-center justify-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
							>
								{resending ? (
									<>
										<span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
										Wysyłanie…
									</>
								) : (
									"Wyślij nowy link"
								)}
							</button>
						</form>
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
