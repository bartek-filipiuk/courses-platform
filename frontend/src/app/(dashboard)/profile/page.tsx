"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Eye, EyeOff, KeyRound, Plus, Trash2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { getDevToken } from "@/lib/dev-auth";
import { useAuthFetch, useAuthMutate } from "@/lib/use-api";
import TopBar from "@/components/TopBar";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface UserStats {
	total_quests: number;
	completed: number;
	in_progress: number;
	progress_pct: number;
	total_attempts: number;
	total_hints_used: number;
	quality_scores: Record<string, number> | null;
	streak_days: number;
}

interface ApiKeyItem {
	id: string;
	key_prefix: string;
	name: string;
	is_active: boolean;
	expires_at: string | null;
	created_at: string;
}

interface GeneratedKey {
	id: string;
	key: string;
	key_prefix: string;
	name: string;
}

function formatDate(iso: string): string {
	try {
		return new Date(iso).toLocaleString(undefined, {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch {
		return "—";
	}
}

function CodeBlock({ code }: { code: string }) {
	return (
		<pre
			className="mono"
			style={{
				padding: 16,
				borderRadius: 10,
				background: "rgba(0,0,0,0.4)",
				border: "1px solid rgba(255,255,255,0.06)",
				fontSize: 12.5,
				lineHeight: 1.75,
				color: "#CBD5E1",
				margin: 0,
				overflowX: "auto",
				whiteSpace: "pre",
			}}
		>
			{code}
		</pre>
	);
}

function KeyRow({
	apiKey,
	revealValue,
	onRevoke,
	onCopy,
}: {
	apiKey: ApiKeyItem;
	revealValue?: string;
	onRevoke(id: string): void;
	onCopy(text: string, label: string): void;
}) {
	const [shown, setShown] = useState(false);
	const displayed = revealValue && shown ? revealValue : "•".repeat(48);
	const canReveal = Boolean(revealValue);

	return (
		<div
			className="glass"
			style={{ padding: 18, marginBottom: 12, borderColor: apiKey.is_active ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)" }}
		>
			<div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
				<div>
					<div className="text-[14px] font-medium mb-0.5">{apiKey.name}</div>
					<div className="mono text-[11px] text-text-secondary">
						Created {formatDate(apiKey.created_at)}
						{apiKey.expires_at && ` · expires ${formatDate(apiKey.expires_at)}`}
					</div>
				</div>
				<span className={cn("badge", apiKey.is_active ? "badge-success" : "badge-error")}>
					<span className="dot" />
					{apiKey.is_active ? "ACTIVE" : "REVOKED"}
				</span>
			</div>

			<div
				className="mono flex items-center gap-2.5 overflow-hidden"
				style={{
					padding: "12px 14px",
					borderRadius: 10,
					background: "rgba(0,0,0,0.4)",
					border: "1px solid rgba(255,255,255,0.06)",
					fontSize: 13,
					color: "#E5B55C",
				}}
			>
				<span className="flex-1 truncate">
					{canReveal ? displayed : `${apiKey.key_prefix}${"•".repeat(40)}`}
				</span>
				{canReveal && (
					<button
						type="button"
						onClick={() => setShown((s) => !s)}
						className="btn btn-sm btn-ghost"
					>
						{shown ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
					</button>
				)}
				{canReveal && revealValue && (
					<button
						type="button"
						onClick={() => onCopy(revealValue, "API key copied")}
						className="btn btn-sm btn-ghost"
					>
						<Copy className="w-3.5 h-3.5" />
					</button>
				)}
			</div>

			{canReveal && (
				<div className="mt-2 text-[11px] text-accent-warning">
					Skopiuj teraz — po opuszczeniu strony klucz nie będzie możliwy do odczytu.
				</div>
			)}

			<div className="flex gap-2 mt-3.5">
				{apiKey.is_active && (
					<button
						type="button"
						onClick={() => onRevoke(apiKey.id)}
						className="btn btn-sm btn-ghost flex items-center gap-1.5"
						style={{ color: "#EF4444", borderColor: "rgba(239,68,68,0.3)" }}
					>
						<Trash2 className="w-3.5 h-3.5" />
						Revoke
					</button>
				)}
			</div>
		</div>
	);
}

export default function ProfilePage() {
	const { data: stats } = useAuthFetch<UserStats>("/api/users/me/stats");
	const { data: keys, loading: keysLoading } = useAuthFetch<ApiKeyItem[]>(
		"/api/auth/api-key/list",
	);
	const [localKeys, setLocalKeys] = useState<ApiKeyItem[] | null>(null);
	const [freshlyGenerated, setFreshlyGenerated] = useState<Record<string, string>>({});
	const [newKeyName, setNewKeyName] = useState("");
	const [generating, setGenerating] = useState(false);
	const mutate = useAuthMutate();

	useEffect(() => {
		if (keys) setLocalKeys(keys);
	}, [keys]);

	const displayKeys = localKeys ?? [];

	const copy = useCallback(async (text: string, label: string) => {
		try {
			await navigator.clipboard.writeText(text);
			toast.success(label);
		} catch {
			toast.error("Clipboard unavailable");
		}
	}, []);

	async function generate() {
		const name = newKeyName.trim() || `key-${new Date().toISOString().slice(0, 16)}`;
		setGenerating(true);
		try {
			const res = await mutate<GeneratedKey>("/api/auth/api-key/generate", {
				method: "POST",
				body: { name },
			});
			setFreshlyGenerated((prev) => ({ ...prev, [res.id]: res.key }));
			setLocalKeys((prev) => [
				{
					id: res.id,
					key_prefix: res.key_prefix,
					name: res.name,
					is_active: true,
					expires_at: null,
					created_at: new Date().toISOString(),
				},
				...(prev ?? []),
			]);
			setNewKeyName("");
			toast.success("API key generated — reveal to copy");
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Generation failed");
		} finally {
			setGenerating(false);
		}
	}

	async function revoke(id: string) {
		try {
			const token = await getDevToken("student");
			await apiClient(`/api/auth/api-key/revoke/${id}`, { method: "DELETE", token });
			setLocalKeys((prev) =>
				prev ? prev.map((k) => (k.id === id ? { ...k, is_active: false } : k)) : prev,
			);
			toast.success("API key revoked");
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Revoke failed");
		}
	}

	const statCards = stats
		? [
				{ label: "Progress", value: `${stats.progress_pct}%`, sub: `${stats.completed}/${stats.total_quests} quests` },
				{ label: "Streak", value: String(stats.streak_days), sub: "days" },
				{ label: "Attempts", value: String(stats.total_attempts), sub: "submissions" },
				{ label: "Hints used", value: String(stats.total_hints_used), sub: "across quests" },
			]
		: [];

	const qualityDims = stats?.quality_scores ? Object.entries(stats.quality_scores) : [];

	const quickstart = `# ~/.ndqs/config
export NDQS_API_KEY="ndqs_..."
export NDQS_API_URL="http://localhost:8002"

# Always pull the active quest first
curl -H "X-API-Key: $NDQS_API_KEY" \\
  "$NDQS_API_URL/api/users/me/active-quest"

# Submit an answer (text_answer)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"type":"text_answer","payload":{"answer":"..."}}'

# Submit an answer from a file (.md / .txt up to 100 KB)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit/file" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -F "file=@prd.md"`;

	return (
		<div className="flex flex-col h-screen">
			<TopBar
				breadcrumb={[
					{ label: "Command Center" },
					{ label: "Profile", mono: true },
				]}
			/>

			<div className="flex-1 overflow-y-auto">
				<div className="px-12 py-9 max-w-[1100px] mx-auto">
					{/* Stats */}
					<div
						className="mini-label"
						style={{ color: "var(--accent-primary)", marginBottom: 10 }}
					>
						// AGENT PROFILE · GHOST
					</div>
					<h1 className="text-[30px] font-semibold tracking-[-0.02em] mb-1.5">
						Statystyki operatora
					</h1>
					<p className="text-[14px] text-text-secondary mb-6">
						Twój wkład w misję — progres, jakość, użycie wskazówek.
					</p>

					<div className="grid [grid-template-columns:repeat(auto-fill,minmax(200px,1fr))] gap-4 mb-6">
						{statCards.map((card) => (
							<div
								key={card.label}
								className="glass"
								style={{ padding: 18 }}
							>
								<div className="mini-label mb-1.5">{card.label}</div>
								<div className="text-[28px] font-semibold text-text-primary leading-none">
									{card.value}
								</div>
								<div className="text-[11px] text-text-secondary mt-1.5">
									{card.sub}
								</div>
							</div>
						))}
					</div>

					{qualityDims.length > 0 && (
						<div className="glass mb-10" style={{ padding: 22 }}>
							<div className="mini-label mb-4">Quality scores (avg)</div>
							<div className="grid grid-cols-4 gap-4">
								{qualityDims.map(([dim, val]) => (
									<div key={dim} className="text-center">
										<div className="relative w-16 h-16 mx-auto mb-2">
											<svg viewBox="0 0 36 36" className="w-full h-full">
												<title>{dim}</title>
												<path
													d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
													fill="none"
													style={{ stroke: "var(--bg-surface-active)" }}
													strokeWidth="3"
												/>
												<path
													d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
													fill="none"
													style={{ stroke: "var(--accent-primary)" }}
													strokeWidth="3"
													strokeDasharray={`${val * 10}, 100`}
													strokeLinecap="round"
												/>
											</svg>
											<span className="absolute inset-0 flex items-center justify-center text-text-primary font-semibold text-sm">
												{val}
											</span>
										</div>
										<div className="text-[11px] text-text-secondary capitalize">
											{dim}
										</div>
									</div>
								))}
							</div>
						</div>
					)}

					{/* Credentials */}
					<div
						className="mini-label"
						style={{ color: "var(--accent-primary)", marginBottom: 10 }}
					>
						// CREDENTIALS
					</div>
					<h2 className="text-[24px] font-semibold tracking-[-0.02em] mb-1.5">
						API Keys
					</h2>
					<p className="text-[14px] text-text-secondary mb-5 max-w-[620px]">
						Użyj klucza w swoim agencie AI (Claude Code / Cursor / Windsurf) —
						komunikuje się z Game Masterem z Twojego IDE, bez klikania po UI.
					</p>

					<div className="glass mb-5" style={{ padding: 18 }}>
						<div className="flex items-end gap-2.5 flex-wrap">
							<label className="flex-1 min-w-[220px]">
								<div className="mini-label mb-1.5">New key name</div>
								<input
									type="text"
									className="input"
									placeholder="claude-code-laptop"
									value={newKeyName}
									onChange={(e) => setNewKeyName(e.target.value)}
								/>
							</label>
							<button
								type="button"
								onClick={generate}
								disabled={generating}
								className="btn btn-primary flex items-center gap-2 disabled:opacity-60"
							>
								{generating ? (
									<Check className="w-4 h-4" />
								) : (
									<Plus className="w-4 h-4" />
								)}
								Generate key
							</button>
						</div>
					</div>

					{keysLoading && !localKeys ? (
						<div className="text-text-secondary animate-pulse">
							Loading keys…
						</div>
					) : displayKeys.length === 0 ? (
						<div
							className="text-center py-10 rounded-2xl text-text-secondary"
							style={{
								border: "1px dashed rgba(255,255,255,0.08)",
								background: "rgba(255,255,255,0.015)",
							}}
						>
							<KeyRound className="w-6 h-6 mx-auto mb-2 text-text-muted" />
							No API keys yet. Generate one to unlock the API-first flow.
						</div>
					) : (
						<div>
							{displayKeys.map((k) => (
								<KeyRow
									key={k.id}
									apiKey={k}
									revealValue={freshlyGenerated[k.id]}
									onRevoke={revoke}
									onCopy={copy}
								/>
							))}
						</div>
					)}

					{/* Quickstart */}
					<div className="glass mt-10" style={{ padding: 22 }}>
						<div className="flex items-center justify-between mb-3">
							<div className="mini-label">Quickstart · CLAUDE.md integration</div>
							<button
								type="button"
								onClick={() => copy(quickstart, "Snippet copied")}
								className="btn btn-sm btn-ghost flex items-center gap-1.5"
							>
								<Copy className="w-3.5 h-3.5" />
								Copy
							</button>
						</div>
						<CodeBlock code={quickstart} />
						<p className="text-[12px] text-text-secondary mt-3">
							Pełny Starter Pack (CLAUDE.md, AGENTS.md, .env.example, README.md) pobierasz ze strony kursu
							na Marketplace. Asystent wczyta CLAUDE.md z roota projektu i będzie pracował w narracji misji.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
}
