"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";

const API_BASE_URL =
	process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
	const [email, setEmail] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [sent, setSent] = useState(false);

	async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
		e.preventDefault();
		if (submitting) return;
		setSubmitting(true);

		try {
			await fetch(`${API_BASE_URL}/api/auth/magic/request`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ email }),
			});
		} catch {
			// Swallow network errors: we never reveal whether the address exists,
			// so a failed request looks identical to a successful one to the user.
		} finally {
			// Always show success — mirror the backend's no-leak contract.
			setSent(true);
			setSubmitting(false);
		}
	}

	return (
		<main className="flex min-h-screen flex-col items-center justify-center bg-bg-base px-4">
			<div className="w-full max-w-md space-y-8 rounded-xl border border-border-default bg-bg-elevated p-8">
				<div className="text-center">
					<h1 className="font-mono text-2xl font-bold tracking-tight text-text-primary">
						{">"} NDQS Terminal
					</h1>
					<p className="mt-2 text-sm text-text-secondary">
						Authenticate to begin your mission
					</p>
				</div>

				{sent ? (
					<div className="space-y-4 text-center">
						<div className="rounded-lg border border-accent-primary/30 bg-accent-primary/5 p-6">
							<p className="font-mono text-sm font-medium text-accent-primary">
								Sprawdź mail — wysłaliśmy link logowania (ważny 15 min)
							</p>
							<p className="mt-3 text-xs text-text-secondary">
								Wysłaliśmy wiadomość na{" "}
								<span className="font-mono text-text-primary break-all">
									{email}
								</span>
								, jeśli ten adres jest zarejestrowany. Kliknij link, aby
								kontynuować.
							</p>
						</div>
						<button
							type="button"
							onClick={() => {
								setSent(false);
								setEmail("");
							}}
							className="font-mono text-xs text-text-secondary underline-offset-4 transition-colors hover:text-accent-primary hover:underline"
						>
							Użyj innego adresu
						</button>
					</div>
				) : (
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="space-y-2">
							<label
								htmlFor="email"
								className="block font-mono text-xs tracking-wide text-text-secondary"
							>
								EMAIL
							</label>
							<input
								id="email"
								name="email"
								type="email"
								required
								autoComplete="email"
								value={email}
								onChange={(e) => setEmail(e.target.value)}
								disabled={submitting}
								placeholder="ty@przyklad.pl"
								className="input mono w-full disabled:opacity-50"
							/>
						</div>

						<button
							type="submit"
							disabled={submitting}
							className="btn btn-primary flex w-full items-center justify-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
						>
							{submitting ? (
								<>
									<span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Wysyłanie…
								</>
							) : (
								"Wyślij link logowania"
							)}
						</button>

						<p className="text-center font-mono text-xs text-text-muted">
							Wyślemy Ci jednorazowy link logowania (ważny 15 min). Bez hasła.
						</p>
					</form>
				)}

				<div className="flex items-center gap-3">
					<div className="h-px flex-1 bg-border-default" />
					<span className="font-mono text-[10px] tracking-[0.12em] text-text-muted">
						LUB
					</span>
					<div className="h-px flex-1 bg-border-default" />
				</div>

				<button
					type="button"
					onClick={() => signIn("github", { callbackUrl: "/" })}
					className="flex w-full items-center justify-center gap-3 rounded-lg border border-border-default bg-bg-surface-active px-4 py-3 text-sm font-medium text-text-primary transition-colors hover:bg-accent-primary/10 hover:text-accent-primary"
				>
					<svg
						className="h-5 w-5"
						fill="currentColor"
						viewBox="0 0 24 24"
						aria-label="GitHub logo"
					>
						<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
					</svg>
					Sign in with GitHub
				</button>
			</div>
		</main>
	);
}
