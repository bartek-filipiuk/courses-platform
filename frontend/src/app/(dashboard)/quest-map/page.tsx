"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthFetch } from "@/lib/use-api";
import QuestNode, { type QuestState } from "@/components/quest-map/QuestNode";
import QuestEdge from "@/components/quest-map/QuestEdge";
import QuestDetailPanel from "@/components/quest-map/QuestDetailPanel";
import { mapDimensions, questPosition } from "@/components/quest-map/layout";
import TopBar from "@/components/TopBar";

interface QuestListItem {
	id: string;
	title: string;
	sort_order: number;
	evaluation_type: string;
	state: QuestState;
	skills: string[];
	has_artifact: boolean;
}

interface CourseDetail {
	id: string;
	title: string;
	narrative_title: string | null;
	persona_name: string | null;
}

export default function QuestMapPage() {
	return (
		<Suspense
			fallback={
				<div className="min-h-screen flex items-center justify-center">
					<div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
				</div>
			}
		>
			<QuestMapContent />
		</Suspense>
	);
}

function QuestMapContent() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const courseId = searchParams.get("courseId");
	const questIdParam = searchParams.get("questId");

	const { data: quests } = useAuthFetch<QuestListItem[]>(
		`/api/courses/${courseId}/quests`,
		{ skip: !courseId },
	);
	const { data: course } = useAuthFetch<CourseDetail>(
		`/api/courses/${courseId}`,
		{ skip: !courseId },
	);

	const sortedQuests = useMemo(
		() => (quests ?? []).slice().sort((a, b) => a.sort_order - b.sort_order),
		[quests],
	);

	const [selectedId, setSelectedId] = useState<string | null>(null);
	useEffect(() => {
		if (!sortedQuests.length) return;
		if (questIdParam && sortedQuests.some((q) => q.id === questIdParam)) {
			setSelectedId(questIdParam);
			return;
		}
		if (selectedId && sortedQuests.some((q) => q.id === selectedId)) return;
		const inProgress = sortedQuests.find((q) => q.state === "IN_PROGRESS");
		const available = sortedQuests.find((q) => q.state === "AVAILABLE");
		setSelectedId(inProgress?.id ?? available?.id ?? null);
	}, [sortedQuests, questIdParam, selectedId]);

	const selectedQuest = sortedQuests.find((q) => q.id === selectedId) ?? null;

	const positions = useMemo(
		() => sortedQuests.map((_, idx) => questPosition(idx)),
		[sortedQuests],
	);
	const dims = mapDimensions(sortedQuests.length || 1);

	const summary = useMemo(() => {
		const counts = { completed: 0, inProgress: 0, available: 0, locked: 0, failed: 0 };
		for (const q of sortedQuests) {
			if (q.state === "COMPLETED") counts.completed++;
			else if (q.state === "IN_PROGRESS") counts.inProgress++;
			else if (q.state === "AVAILABLE") counts.available++;
			else if (q.state === "LOCKED") counts.locked++;
			else if (q.state === "FAILED_ATTEMPT") counts.failed++;
		}
		return counts;
	}, [sortedQuests]);

	function startQuest(questId: string) {
		router.push(`/quest/${questId}`);
	}

	const narrativeTitle = course?.narrative_title ?? course?.title ?? "Operation";

	return (
		<div className="flex flex-col h-screen">
			<TopBar
				breadcrumb={[
					{ label: "Command Center" },
					{ label: narrativeTitle },
					{ label: "Quest Map", mono: true },
				]}
			/>

			<div className="relative flex-1 overflow-hidden">
				<div className="relative z-[2] px-8 pt-5 pb-3">
					<div
						className="mini-label"
						style={{ color: "var(--accent-primary)", marginBottom: 6 }}
					>
						// OPERATION ROUTE · {narrativeTitle.toUpperCase()}
					</div>
					<div className="flex items-center justify-between gap-4 flex-wrap">
						<div>
							<h1 className="text-[26px] font-semibold tracking-[-0.02em]">Quest Map</h1>
							<div className="text-[13px] text-text-secondary mt-1">
								{sortedQuests.length} węzłów · {summary.completed} ukończone · {summary.inProgress} w trakcie ·{" "}
								{summary.available} dostępne · {summary.locked} zablokowane
								{summary.failed > 0 && ` · ${summary.failed} do poprawy`}
							</div>
						</div>
						<div className="flex gap-2">
							<LegendPill color="#E5B55C" glow label="In progress" />
							<LegendPill color="#10B981" label="Done" />
							<LegendPill color="rgba(255,255,255,0.15)" label="Locked" />
						</div>
					</div>
				</div>

				<div className="relative overflow-auto" style={{ height: "calc(100% - 90px)" }}>
					<div
						className="relative mx-auto my-5"
						style={{ width: dims.width, height: dims.height }}
					>
						<div
							className="absolute inset-0 pointer-events-none"
							style={{
								backgroundImage:
									"radial-gradient(circle at 1px 1px, rgba(255,255,255,0.06) 1px, transparent 0)",
								backgroundSize: "32px 32px",
								opacity: 0.6,
							}}
						/>

						<svg
							width={dims.width}
							height={dims.height}
							className="absolute inset-0 pointer-events-none"
						>
							<title>Quest connection map</title>
							{sortedQuests.map((q, i) => {
								if (i === 0) return null;
								const from = positions[i - 1];
								const to = positions[i];
								const active =
									sortedQuests[i - 1].state === "COMPLETED" && q.state !== "LOCKED";
								return (
									<QuestEdge
										key={`edge-${q.id}`}
										from={from}
										to={to}
										active={active}
										pathId={`edge-path-${q.id}`}
									/>
								);
							})}
						</svg>

						{sortedQuests.map((q, i) => (
							<QuestNode
								key={q.id}
								quest={{
									id: q.id,
									title: q.title,
									sortOrder: q.sort_order,
									state: q.state,
								}}
								position={positions[i]}
								selected={selectedId === q.id}
								onClick={() => setSelectedId(q.id)}
							/>
						))}

						<div
							className="mono absolute"
							style={{
								left: 40,
								top: 40,
								padding: "10px 14px",
								borderRadius: 8,
								background: "rgba(0,0,0,0.5)",
								border: "1px solid rgba(255,255,255,0.05)",
								fontSize: 10,
								letterSpacing: "0.15em",
								color: "#94A3B8",
							}}
						>
							ROUTE_ID: {(courseId ?? "—").slice(0, 8).toUpperCase()}
							<br />
							<span style={{ color: "#475569" }}>─────────────</span>
							<br />
							NODES: {sortedQuests.length} · GM: {course?.persona_name ?? "—"}
						</div>

						{sortedQuests.length > 0 && (
							<div
								className="mono absolute"
								style={{
									right: 40,
									bottom: 40,
									padding: "10px 14px",
									borderRadius: 8,
									background: "rgba(0,0,0,0.5)",
									border: "1px solid rgba(229,181,92,0.2)",
									fontSize: 10,
									letterSpacing: "0.15em",
									color: "#E5B55C",
								}}
							>
								FINAL NODE: {sortedQuests[sortedQuests.length - 1].title.toUpperCase()}
							</div>
						)}
					</div>
				</div>

				{selectedQuest && (
					<QuestDetailPanel
						quest={selectedQuest}
						onClose={() => setSelectedId(null)}
						onStartQuest={startQuest}
					/>
				)}

				{!courseId && (
					<div className="absolute inset-0 flex items-center justify-center text-text-secondary">
						Wybierz operację w Marketplace, żeby zobaczyć mapę questów.
					</div>
				)}
			</div>
		</div>
	);
}

function LegendPill({
	color,
	label,
	glow,
}: {
	color: string;
	label: string;
	glow?: boolean;
}) {
	return (
		<div
			className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px]"
			style={{
				background: "rgba(255,255,255,0.03)",
				border: "1px solid rgba(255,255,255,0.06)",
			}}
		>
			<span
				className="w-2 h-2 rounded-full"
				style={{
					background: color,
					boxShadow: glow ? `0 0 6px ${color}` : undefined,
				}}
			/>
			{label}
		</div>
	);
}
