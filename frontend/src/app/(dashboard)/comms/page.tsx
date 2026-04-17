"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, Send } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { getDevToken } from "@/lib/dev-auth";
import { cn } from "@/lib/utils";
import TopBar from "@/components/TopBar";

interface CommsEntry {
	id: string;
	quest_id: string | null;
	message_type: "briefing" | "evaluation" | "hint" | "system";
	content: string;
	created_at: string;
}

interface EnrollmentLite {
	course_id: string;
	title: string;
	narrative_title: string | null;
	persona_name: string | null;
	total_quests: number;
	completed_quests: number;
}

interface ActiveQuestResponse {
	active_quest: {
		quest_id: string;
		title: string;
		sort_order: number;
		state: string;
	} | null;
}

function formatClock(iso: string): string {
	try {
		return new Date(iso).toLocaleTimeString("en", { hour12: false });
	} catch {
		return "--:--:--";
	}
}

function GMMessage({ entry, personaName }: { entry: CommsEntry; personaName: string }) {
	const label =
		entry.message_type === "hint"
			? `${personaName.toUpperCase()} · HINT`
			: `${personaName.toUpperCase()} · CONTROL`;
	return (
		<div className="flex gap-3 mb-[18px]">
			<div
				className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
				style={{
					background: "radial-gradient(circle at 40% 30%, rgba(229,181,92,0.2), rgba(124,58,237,0.2))",
					border: "1px solid rgba(229,181,92,0.4)",
					color: "#E5B55C",
					boxShadow: "0 0 14px rgba(229,181,92,0.25)",
				}}
			>
				<Eye className="w-4 h-4" />
			</div>
			<div className="flex-1 min-w-0">
				<div className="flex items-center gap-2.5 mb-1.5">
					<span
						className="mono"
						style={{ fontSize: 11, color: "#E5B55C", letterSpacing: "0.12em" }}
					>
						{label}
					</span>
					<span className="mono text-[10px] text-text-muted">{formatClock(entry.created_at)}</span>
				</div>
				<div
					className="mono whitespace-pre-wrap"
					style={{
						padding: "12px 16px",
						borderRadius: 10,
						background: "rgba(124,58,237,0.06)",
						borderLeft: "2px solid #7C3AED",
						fontSize: 13.5,
						lineHeight: 1.7,
						color: "#CBD5E1",
					}}
				>
					{entry.content}
				</div>
			</div>
		</div>
	);
}

function SystemMessage({ entry }: { entry: CommsEntry }) {
	const text = entry.content.toLowerCase();
	const success = text.includes("pass") || text.includes("mint") || text.includes("complet");
	return (
		<div className="flex items-center gap-3 my-4">
			<div
				className="flex-1 h-px"
				style={{
					background:
						"linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)",
				}}
			/>
			<span className={cn("badge", success ? "badge-success" : "badge-muted")}>
				<span className="dot" />
				{entry.content.slice(0, 64).toUpperCase()}
			</span>
			<span className="mono text-[10px] text-text-muted">{formatClock(entry.created_at)}</span>
			<div
				className="flex-1 h-px"
				style={{
					background:
						"linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)",
				}}
			/>
		</div>
	);
}

export default function CommsLogPage() {
	return (
		<Suspense
			fallback={
				<div className="min-h-screen flex items-center justify-center">
					<div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
				</div>
			}
		>
			<CommsLogContent />
		</Suspense>
	);
}

function CommsLogContent() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const courseIdFromUrl = searchParams.get("courseId");

	const [enrollment, setEnrollment] = useState<EnrollmentLite | null>(null);
	const [entries, setEntries] = useState<CommsEntry[]>([]);
	const [activeQuest, setActiveQuest] = useState<
		ActiveQuestResponse["active_quest"] | null
	>(null);
	const [loading, setLoading] = useState(true);

	const endRef = useRef<HTMLDivElement>(null);

	// Resolve course: from URL or first enrollment
	useEffect(() => {
		let cancelled = false;
		(async () => {
			try {
				const token = await getDevToken("student");
				let courseId = courseIdFromUrl;
				let enrollmentsList: EnrollmentLite[] | null = null;
				if (!courseId) {
					enrollmentsList = await apiClient<EnrollmentLite[]>("/api/users/me/enrollments", { token });
					courseId = enrollmentsList[0]?.course_id ?? null;
				}
				if (!courseId) {
					if (!cancelled) setLoading(false);
					return;
				}

				if (!enrollmentsList) {
					enrollmentsList = await apiClient<EnrollmentLite[]>("/api/users/me/enrollments", { token });
				}
				const mine = enrollmentsList.find((e) => e.course_id === courseId) ?? null;

				const [comms, active] = await Promise.all([
					apiClient<{ items: CommsEntry[] }>(
						`/api/courses/${courseId}/comms-log?per_page=200`,
						{ token },
					),
					apiClient<ActiveQuestResponse>(
						`/api/users/me/active-quest?course_id=${courseId}`,
						{ token },
					),
				]);
				if (cancelled) return;
				setEnrollment(mine);
				setEntries(comms.items);
				setActiveQuest(active.active_quest);
			} catch {
				if (!cancelled) setEntries([]);
			} finally {
				if (!cancelled) setLoading(false);
			}
		})();
		return () => {
			cancelled = true;
		};
	}, [courseIdFromUrl]);

	useEffect(() => {
		if (endRef.current) endRef.current.scrollTop = endRef.current.scrollHeight;
	}, [entries.length]);

	const personaName = enrollment?.persona_name ?? "GAME MASTER";
	const narrativeTitle = enrollment?.narrative_title ?? enrollment?.title ?? "Operation";

	const sortedEntries = useMemo(
		() =>
			entries
				.slice()
				.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()),
		[entries],
	);

	const lastHeartbeatLabel = sortedEntries.length
		? formatClock(sortedEntries[sortedEntries.length - 1].created_at)
		: "—";

	const canJumpToQuest = Boolean(activeQuest);

	return (
		<div className="flex flex-col h-screen">
			<TopBar
				breadcrumb={[
					{ label: "Command Center" },
					{ label: narrativeTitle },
					{ label: "Comms Log", mono: true },
				]}
			/>

			{/* Context strip */}
			<div
				className="flex items-center justify-between px-8 py-4 border-b border-border-subtle"
				style={{ background: "rgba(5,5,10,0.3)" }}
			>
				<div>
					<div className="mini-label" style={{ color: "#E5B55C", marginBottom: 4 }}>
						// COMMS LOG · CHANNEL 03
					</div>
					<div className="text-[18px] font-semibold">
						{activeQuest
							? `Quest ${String(activeQuest.sort_order).padStart(2, "0")} — ${activeQuest.title}`
							: "No active quest"}
					</div>
				</div>
				<div className="flex items-center gap-3">
					<div className="text-[11px] text-text-secondary text-right">
						<div className="mono tracking-[0.12em]">CHANNEL ENCRYPTED · AES-256</div>
						<div className="text-text-muted mt-0.5">
							Last heartbeat · {lastHeartbeatLabel}
						</div>
					</div>
					{activeQuest && (
						<span className="badge badge-gold">
							<span className="dot" />
							{activeQuest.state.replace("_", " ")}
						</span>
					)}
				</div>
			</div>

			{/* Messages */}
			<div
				ref={endRef}
				className="flex-1 overflow-y-auto px-10 py-6"
				style={{ maxWidth: 900, width: "100%", margin: "0 auto" }}
			>
				{loading ? (
					<div className="text-text-secondary animate-pulse">Loading transmissions…</div>
				) : sortedEntries.length === 0 ? (
					<div className="text-center py-20 text-text-secondary">
						No transmissions yet. Start a quest to begin the mission briefing.
					</div>
				) : (
					sortedEntries.map((e) =>
						e.message_type === "system" ? (
							<SystemMessage key={e.id} entry={e} />
						) : (
							<GMMessage key={e.id} entry={e} personaName={personaName} />
						),
					)
				)}
			</div>

			{/* Input strip — read-only pointer to the real submit path */}
			<div
				className="px-8 py-5 border-t border-border-subtle"
				style={{ background: "rgba(5,5,10,0.6)" }}
			>
				<div className="max-w-[900px] mx-auto">
					<div className="flex items-center gap-2.5 mb-2.5">
						<span className="mini-label">SUBMISSION PATH:</span>
						{(["URL_CHECK", "TEXT", "OUTPUT", "QUIZ"] as const).map((t) => (
							<span
								key={t}
								className="btn btn-sm btn-ghost mono"
								style={{
									padding: "4px 10px",
									fontSize: 10,
									letterSpacing: "0.1em",
									cursor: "default",
								}}
							>
								{t}
							</span>
						))}
					</div>
					<div className="relative flex items-start gap-2.5">
						<span
							className="mono absolute left-3.5 top-3.5 pointer-events-none"
							style={{ color: "#E5B55C", fontSize: 14 }}
						>
							$_
						</span>
						<input
							className="input mono"
							style={{ paddingLeft: 40, fontSize: 13.5 }}
							placeholder="Open Quest page or POST /api/quests/{id}/submit — this channel is read-only"
							disabled
						/>
						<button
							type="button"
							onClick={() =>
								activeQuest && router.push(`/quest/${activeQuest.quest_id}`)
							}
							disabled={!canJumpToQuest}
							className="btn btn-primary flex items-center gap-2 whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
						>
							<Send className="w-4 h-4" />
							Continue quest →
						</button>
					</div>
					<div className="flex justify-between mt-2 text-[11px] text-text-muted">
						<span className="mono">
							Read-only log · full submit flow lives in Quest page or API
						</span>
						<span className="mono">
							{sortedEntries.length} TRANSMISSIONS ARCHIVED
						</span>
					</div>
				</div>
			</div>
		</div>
	);
}
