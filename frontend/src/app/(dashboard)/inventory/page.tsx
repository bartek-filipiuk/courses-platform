"use client";

import { useMemo, useState } from "react";
import { useAuthFetch } from "@/lib/use-api";
import TopBar from "@/components/TopBar";
import ArtifactCard, {
	LockedArtifact,
	tierForSortOrder,
	type ArtifactTier,
} from "@/components/inventory/ArtifactCard";

interface Artifact {
	id: string;
	name: string;
	description: string | null;
	icon_url: string | null;
	quest_title: string;
	acquired_at: string;
}

interface EnrollmentLite {
	course_id: string;
	title: string;
	narrative_title: string | null;
	total_quests: number;
	completed_quests: number;
}

interface QuestListItem {
	id: string;
	title: string;
	sort_order: number;
	state: string;
	has_artifact: boolean;
}

type ScopeKey = "all" | string;

function codeFromQuest(sortOrder: number, courseHint?: string): string {
	const course = (courseHint ?? "OP").slice(0, 3).toUpperCase();
	return `${course}-${String(sortOrder).padStart(2, "0")}`;
}

function formatDate(iso: string): string {
	try {
		return new Date(iso).toLocaleDateString(undefined, {
			month: "short",
			day: "numeric",
		});
	} catch {
		return "—";
	}
}

export default function InventoryPage() {
	const { data: artifacts } = useAuthFetch<Artifact[]>("/api/users/me/artifacts");
	const { data: enrollments } = useAuthFetch<EnrollmentLite[]>(
		"/api/users/me/enrollments",
	);

	const [scope, setScope] = useState<ScopeKey>("all");

	// When the first enrollment arrives, default the scope to it so the
	// "locked" placeholders are populated immediately.
	const defaultedScope: ScopeKey = useMemo(() => {
		if (scope !== "all") return scope;
		if (enrollments && enrollments.length > 0) return enrollments[0].course_id;
		return "all";
	}, [scope, enrollments]);

	// Fetch quests only for the focused course (for locked placeholders + tier mapping).
	const focusedCourseId = defaultedScope === "all" ? null : defaultedScope;
	const { data: focusedQuests } = useAuthFetch<QuestListItem[]>(
		`/api/courses/${focusedCourseId}/quests`,
		{ skip: !focusedCourseId },
	);

	const focusedEnrollment = enrollments?.find((e) => e.course_id === defaultedScope) ?? null;
	const totalQuests = focusedEnrollment?.total_quests ?? focusedQuests?.length ?? 9;

	// Build a quest_title → sort_order map for tier derivation.
	const sortOrderByTitle = useMemo(() => {
		const m = new Map<string, number>();
		for (const q of focusedQuests ?? []) m.set(q.title, q.sort_order);
		return m;
	}, [focusedQuests]);

	// Artifacts visible in the current scope. When scope is "all" we show
	// every artifact but don't render locked placeholders (we don't know
	// the chain for all courses).
	const visibleArtifacts = useMemo(() => {
		if (!artifacts) return [] as Artifact[];
		if (defaultedScope === "all") return artifacts;
		// Match by quest title presence in the focused course.
		return artifacts.filter((a) => sortOrderByTitle.has(a.quest_title));
	}, [artifacts, defaultedScope, sortOrderByTitle]);

	const lockedQuests = useMemo(() => {
		if (!focusedQuests) return [] as QuestListItem[];
		return focusedQuests
			.filter((q) => q.state !== "COMPLETED")
			.sort((a, b) => a.sort_order - b.sort_order);
	}, [focusedQuests]);

	const collectedCount = visibleArtifacts.length;
	const totalCount = defaultedScope === "all"
		? (artifacts?.length ?? 0) + lockedQuests.length  // approx — only focused locks known
		: totalQuests;
	const pct = totalCount > 0 ? Math.round((collectedCount / totalCount) * 100) : 0;

	const narrativeLabel = (() => {
		if (defaultedScope === "all") return "ALL OPERATIONS";
		return (
			focusedEnrollment?.narrative_title ??
			focusedEnrollment?.title ??
			"OPERATION"
		);
	})();

	return (
		<div className="flex flex-col h-screen">
			<TopBar
				breadcrumb={[
					{ label: "Command Center" },
					{ label: "Inventory", mono: true },
				]}
			/>

			<div className="flex-1 overflow-y-auto">
				<div className="px-12 py-9 max-w-[1400px] mx-auto">
					<header className="mb-7">
						<div
							className="mini-label"
							style={{ color: "var(--accent-primary)", marginBottom: 10 }}
						>
							// INVENTORY · {narrativeLabel.toUpperCase()}
						</div>
						<div className="flex items-end justify-between flex-wrap gap-4">
							<div>
								<h1 className="text-[30px] font-semibold tracking-[-0.02em] mb-1.5">
									Artifacts acquired
								</h1>
								<p className="text-[14px] text-text-secondary">
									{collectedCount} z {totalCount} artefaktów odblokowanych · każdy to klucz do kolejnej ścieżki
								</p>
							</div>
							<div className="flex gap-4 items-center">
								<div className="text-right">
									<div
										className="mono"
										style={{ fontSize: 24, fontWeight: 500, color: "#E5B55C" }}
									>
										{collectedCount}
										<span style={{ color: "#475569", fontWeight: 300 }}>
											/{totalCount}
										</span>
									</div>
									<div className="mini-label mt-0.5">COLLECTED</div>
								</div>
								<div className="w-px h-10 bg-border-subtle" />
								<div className="text-right">
									<div
										className="mono"
										style={{ fontSize: 24, fontWeight: 500, color: "#10B981" }}
									>
										{pct}%
									</div>
									<div className="mini-label mt-0.5">PROGRESS</div>
								</div>
							</div>
						</div>
					</header>

					{enrollments && enrollments.length > 0 && (
						<div className="flex gap-2 flex-wrap mb-6">
							<button
								type="button"
								className="btn btn-sm btn-ghost"
								onClick={() => setScope("all")}
								style={
									defaultedScope === "all"
										? {
												background: "rgba(229,181,92,0.08)",
												color: "#E5B55C",
												borderColor: "rgba(229,181,92,0.22)",
											}
										: undefined
								}
							>
								All operations
							</button>
							{enrollments.map((e) => {
								const active = defaultedScope === e.course_id;
								return (
									<button
										key={e.course_id}
										type="button"
										className="btn btn-sm btn-ghost"
										onClick={() => setScope(e.course_id)}
										style={
											active
												? {
														background: "rgba(229,181,92,0.08)",
														color: "#E5B55C",
														borderColor: "rgba(229,181,92,0.22)",
													}
												: undefined
										}
									>
										{(e.narrative_title ?? e.title)
											.replace(/^Operation: /i, "")
											.replace(/^Operacja: /i, "")}
									</button>
								);
							})}
						</div>
					)}

					{!artifacts ? (
						<div className="grid gap-5 [grid-template-columns:repeat(auto-fill,minmax(240px,1fr))]">
							{[1, 2, 3, 4].map((i) => (
								<div
									key={i}
									className="rounded-2xl h-[240px] bg-bg-elevated animate-pulse"
								/>
							))}
						</div>
					) : visibleArtifacts.length === 0 && lockedQuests.length === 0 ? (
						<div className="text-center py-20 border border-dashed border-border-default rounded-2xl">
							<p className="text-text-secondary text-lg">No artifacts yet.</p>
							<p className="text-text-muted text-sm mt-1">
								Ukończ pierwszy quest, żeby odblokować pierwszy klucz.
							</p>
						</div>
					) : (
						<div className="grid gap-[18px] [grid-template-columns:repeat(auto-fill,minmax(240px,1fr))]">
							{visibleArtifacts.map((a, i) => {
								const sortOrder = sortOrderByTitle.get(a.quest_title) ?? 1;
								const tier: ArtifactTier =
									defaultedScope === "all"
										? "legendary"
										: tierForSortOrder(sortOrder, totalQuests);
								return (
									<ArtifactCard
										key={a.id}
										tier={tier}
										code={codeFromQuest(sortOrder, narrativeLabel)}
										name={a.name}
										description={a.description}
										source={a.quest_title}
										acquired={formatDate(a.acquired_at)}
										delay={i * 80}
									/>
								);
							})}
							{defaultedScope !== "all" &&
								lockedQuests.map((q, i) => (
									<LockedArtifact
										key={q.id}
										code={codeFromQuest(q.sort_order, narrativeLabel)}
										delay={(visibleArtifacts.length + i) * 80}
									/>
								))}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
