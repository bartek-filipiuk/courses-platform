"use client";

import { Download, Lightbulb, X } from "lucide-react";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { getDevToken } from "@/lib/dev-auth";
import { cn } from "@/lib/utils";
import type { QuestState } from "./QuestNode";

interface QuestListItem {
	id: string;
	title: string;
	sort_order: number;
	evaluation_type: string;
	state: QuestState;
	skills: string[];
	has_artifact: boolean;
}

interface BriefingResponse {
	id: string;
	title: string;
	briefing: string;
	evaluation_type: string;
	max_hints: number;
	skills: string[];
}

interface StatusResponse {
	quest_id: string;
	state: QuestState;
	hints_used: number;
	attempts: number;
}

const EVAL_LABELS: Record<string, string> = {
	text_answer: "TEXT SUBMISSION",
	url_check: "LIVE ENDPOINT",
	quiz: "MULTIPLE CHOICE",
	command_output: "COMMAND OUTPUT",
};

function stateBadge(state: QuestState) {
	if (state === "COMPLETED") return "badge-success";
	if (state === "FAILED_ATTEMPT") return "badge-error";
	if (state === "LOCKED") return "badge-muted";
	return "badge-gold";
}

interface Props {
	quest: QuestListItem;
	onClose(): void;
	onStartQuest(questId: string): void;
}

export default function QuestDetailPanel({ quest, onClose, onStartQuest }: Props) {
	const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
	const [status, setStatus] = useState<StatusResponse | null>(null);
	const [hint, setHint] = useState<string | null>(null);
	const [hintLoading, setHintLoading] = useState(false);
	const [loadError, setLoadError] = useState<string | null>(null);

	// Fetch briefing + status when quest id changes.
	useEffect(() => {
		let cancelled = false;
		setBriefing(null);
		setStatus(null);
		setHint(null);
		setLoadError(null);
		(async () => {
			try {
				const token = await getDevToken("student");
				const [b, s] = await Promise.all([
					apiClient<BriefingResponse>(`/api/quests/${quest.id}/briefing`, { token }),
					apiClient<StatusResponse>(`/api/quests/${quest.id}/status`, { token }),
				]);
				if (!cancelled) {
					setBriefing(b);
					setStatus(s);
				}
			} catch (e) {
				if (!cancelled) {
					setLoadError(e instanceof Error ? e.message : "Failed to load briefing");
				}
			}
		})();
		return () => {
			cancelled = true;
		};
	}, [quest.id]);

	// ESC closes the panel.
	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if (e.key === "Escape") onClose();
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [onClose]);

	async function requestHint() {
		setHintLoading(true);
		setHint(null);
		try {
			const token = await getDevToken("student");
			const res = await apiClient<{ hint: string; hints_used: number; hints_remaining: number }>(
				`/api/quests/${quest.id}/hint`,
				{
					method: "POST",
					token,
					body: { context: "" },
				},
			);
			setHint(res.hint);
			if (status) {
				setStatus({ ...status, hints_used: res.hints_used });
			}
		} catch (e) {
			setHint(e instanceof Error ? e.message : "Could not fetch hint");
		} finally {
			setHintLoading(false);
		}
	}

	function downloadBriefing() {
		if (!briefing) return;
		const md = `# ${briefing.title}\n\n## Briefing\n\n${briefing.briefing}\n\n---\nEvaluation type: ${briefing.evaluation_type}\n`;
		const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `quest-${String(quest.sort_order).padStart(2, "0")}-briefing.md`;
		document.body.appendChild(a);
		a.click();
		a.remove();
		URL.revokeObjectURL(url);
	}

	const disabledStart = quest.state === "LOCKED" || quest.state === "COMPLETED";
	const hintsLeft = briefing ? briefing.max_hints - (status?.hints_used ?? 0) : 0;

	return (
		<div
			className="absolute top-0 right-0 bottom-0 z-20 overflow-y-auto border-l border-border-subtle"
			style={{
				width: 440,
				background: "rgba(12,12,20,0.92)",
				backdropFilter: "blur(24px)",
				WebkitBackdropFilter: "blur(24px)",
				boxShadow: "-20px 0 60px rgba(0,0,0,0.5)",
				animation: "panel-slide-in 0.3s cubic-bezier(.2,.8,.2,1)",
			}}
		>
			{/* Header */}
			<div className="px-7 py-5 border-b border-border-subtle">
				<div className="flex justify-between items-start mb-3">
					<span
						className="mono"
						style={{ fontSize: 10, letterSpacing: "0.18em", color: "#E5B55C" }}
					>
						// QUEST {String(quest.sort_order).padStart(2, "0")} ·{" "}
						{EVAL_LABELS[quest.evaluation_type] ?? quest.evaluation_type.toUpperCase()}
					</span>
					<button
						type="button"
						onClick={onClose}
						aria-label="Close panel"
						className="text-text-secondary hover:text-text-primary transition-colors"
					>
						<X className="w-4 h-4" />
					</button>
				</div>
				<h2 className="text-[22px] font-semibold tracking-[-0.02em] mb-2">{quest.title}</h2>
				<div className="flex gap-1.5 flex-wrap">
					<span className={cn("badge", stateBadge(quest.state))}>
						<span className="dot" />
						{quest.state.replace("_", " ")}
					</span>
					{quest.skills.map((skill) => (
						<span
							key={skill}
							className="mono"
							style={{
								fontSize: 10,
								padding: "3px 8px",
								borderRadius: 4,
								background: "rgba(255,255,255,0.04)",
								color: "#94A3B8",
								border: "1px solid rgba(255,255,255,0.06)",
							}}
						>
							{skill}
						</span>
					))}
				</div>
			</div>

			{/* Briefing */}
			<div className="px-7 py-5 border-b border-border-subtle">
				<div className="mini-label mb-2.5">Mission Briefing</div>
				{loadError ? (
					<p className="text-sm text-accent-error">{loadError}</p>
				) : briefing ? (
					<div
						className="mono whitespace-pre-wrap leading-relaxed"
						style={{
							padding: "14px 16px",
							borderRadius: 10,
							background: "rgba(0,0,0,0.4)",
							border: "1px solid rgba(124,58,237,0.2)",
							borderLeftWidth: 2,
							borderLeftColor: "#7C3AED",
							fontSize: 13,
							color: "#CBD5E1",
						}}
					>
						{briefing.briefing}
					</div>
				) : (
					<div className="h-24 stripes rounded-lg animate-pulse" />
				)}
			</div>

			{/* Reward Artifact */}
			{quest.has_artifact && (
				<div className="px-7 py-5 border-b border-border-subtle">
					<div className="mini-label mb-3">Reward Artifact</div>
					<div
						className="flex items-center gap-3 p-3 rounded-[10px]"
						style={{
							background: "rgba(229,181,92,0.05)",
							border: "1px solid rgba(229,181,92,0.15)",
						}}
					>
						<div
							className="w-11 h-11 rounded-lg flex items-center justify-center mono text-accent-primary"
							style={{
								background: "linear-gradient(135deg, rgba(229,181,92,0.2), rgba(124,58,237,0.2))",
								border: "1px solid rgba(229,181,92,0.3)",
								fontSize: 14,
							}}
						>
							◆
						</div>
						<div>
							<div
								className="mono text-accent-primary"
								style={{ fontSize: 12, letterSpacing: "0.1em" }}
							>
								Unlocks the next quest
							</div>
							<div className="text-[11px] text-text-secondary mt-0.5">
								Minted on pass — artefakt dodany do Inventory
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Actions */}
			<div className="px-7 py-5">
				<div className="flex items-center justify-between mb-3.5">
					<div className="mini-label">Actions</div>
					<span className="mono text-[10px] text-text-secondary">
						{briefing ? `${hintsLeft}/${briefing.max_hints} HINTS LEFT` : "—"}
					</span>
				</div>
				<div className="flex flex-col gap-2">
					<button
						type="button"
						onClick={() => onStartQuest(quest.id)}
						disabled={disabledStart}
						className={cn(
							"btn btn-primary flex items-center justify-center gap-2",
							disabledStart && "opacity-40 cursor-not-allowed",
						)}
					>
						{quest.state === "IN_PROGRESS" || quest.state === "FAILED_ATTEMPT"
							? "Continue Quest"
							: quest.state === "COMPLETED"
								? "View Submission"
								: "Start Quest"}
						<span>→</span>
					</button>
					<button
						type="button"
						onClick={downloadBriefing}
						disabled={!briefing}
						className="btn btn-ghost btn-sm flex items-center justify-center gap-2 disabled:opacity-40"
					>
						<Download className="w-3.5 h-3.5" />
						Download Briefing (.md)
					</button>
					<button
						type="button"
						onClick={requestHint}
						disabled={!briefing || hintsLeft <= 0 || hintLoading}
						className="btn btn-ghost btn-sm flex items-center justify-center gap-2 disabled:opacity-40"
					>
						<Lightbulb className="w-3.5 h-3.5" />
						{hintLoading ? "Asking GM…" : "Request hint"}
					</button>
				</div>
				{hint && (
					<div
						className="mt-4 rounded-xl p-4 text-sm leading-relaxed"
						style={{
							background: "rgba(124,58,237,0.08)",
							border: "1px solid rgba(124,58,237,0.25)",
							color: "#E9D5FF",
						}}
					>
						<div className="mini-label mb-1" style={{ color: "#A78BFA" }}>
							Hint
						</div>
						{hint}
					</div>
				)}
			</div>
		</div>
	);
}
