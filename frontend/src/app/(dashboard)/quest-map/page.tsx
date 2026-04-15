"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
	ReactFlow,
	Background,
	Controls,
	MiniMap,
	type Node,
	type Edge,
	type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import QuestNode from "@/components/quest-map/QuestNode";
import { useAuthFetch } from "@/lib/use-api";

interface QuestItem {
	id: string;
	title: string;
	sort_order: number;
	evaluation_type: string;
	state: string;
	has_artifact: boolean;
	skills: string[];
}

const nodeTypes: NodeTypes = {
	quest: QuestNode,
};

const DS_COLORS = {
	success: '#10B981',
	primary: '#E5B55C',
	info: '#3B82F6',
	muted: 'rgba(255,255,255,0.12)',
};

export default function QuestMapPage() {
	return (
		<Suspense fallback={<div className="min-h-screen bg-bg-base flex items-center justify-center"><div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" /></div>}>
			<QuestMapContent />
		</Suspense>
	);
}

function QuestMapContent() {
	const searchParams = useSearchParams();
	const courseId = searchParams.get("courseId");
	const { data: quests, loading } = useAuthFetch<QuestItem[]>(
		`/api/courses/${courseId}/quests`,
		{ skip: !courseId },
	);
	const [selectedQuest, setSelectedQuest] = useState<QuestItem | null>(null);

	const questList = quests || [];

	const { nodes, edges } = useMemo(() => {
		const n: Node[] = questList.map((q, i) => ({
			id: q.id,
			type: "quest",
			position: { x: 250, y: i * 150 },
			data: {
				title: q.title,
				state: q.state,
				hasArtifact: q.has_artifact,
				evaluationType: q.evaluation_type,
			},
		}));

		const e: Edge[] = [];
		for (let i = 1; i < questList.length; i++) {
			e.push({
				id: `e-${questList[i - 1].id}-${questList[i].id}`,
				source: questList[i - 1].id,
				target: questList[i].id,
				animated: questList[i].state === "AVAILABLE",
				style: { stroke: "var(--accent-primary)", strokeWidth: 2 },
			});
		}

		return { nodes: n, edges: e };
	}, [questList]);

	const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
		const quest = questList.find((q) => q.id === node.id);
		setSelectedQuest(quest || null);
	}, [questList]);

	if (!courseId) {
		return (
			<div className="min-h-screen bg-bg-base flex items-center justify-center">
				<p className="text-text-secondary">Select a course to view quest map.</p>
			</div>
		);
	}

	if (loading) {
		return (
			<div className="min-h-screen bg-bg-base flex items-center justify-center">
				<div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	return (
		<div className="h-screen bg-bg-base flex">
			{/* Map */}
			<div className="flex-1">
				<ReactFlow
					nodes={nodes}
					edges={edges}
					nodeTypes={nodeTypes}
					onNodeClick={onNodeClick}
					fitView
					className="bg-bg-base"
				>
					<Background color="rgba(255,255,255,0.12)" gap={20} />
					<Controls className="!bg-bg-elevated !border-border-default !rounded-xl" />
					<MiniMap
						className="!bg-bg-elevated !border-border-default !rounded-xl"
						nodeColor={(n) => {
							const state = (n.data as Record<string, unknown>)?.state as string;
							if (state === "COMPLETED") return DS_COLORS.success;
							if (state === "AVAILABLE") return DS_COLORS.primary;
							if (state === "IN_PROGRESS") return DS_COLORS.info;
							return DS_COLORS.muted;
						}}
					/>
				</ReactFlow>
			</div>

			{/* Quest Detail Panel (slide-in) */}
			{selectedQuest && (
				<div className="w-96 border-l border-border-default bg-bg-elevated p-6 overflow-y-auto">
					<div className="flex justify-between items-start mb-4">
						<h2 className="text-xl font-bold text-text-primary">{selectedQuest.title}</h2>
						<button
							type="button"
							onClick={() => setSelectedQuest(null)}
							className="text-text-secondary hover:text-text-primary"
						>
							&times;
						</button>
					</div>

					<div className="space-y-4">
						<div>
							<span className="text-xs text-text-secondary uppercase">Status</span>
							<p className="text-sm text-text-primary font-mono">{selectedQuest.state}</p>
						</div>

						<div>
							<span className="text-xs text-text-secondary uppercase">Type</span>
							<p className="text-sm text-text-primary font-mono">{selectedQuest.evaluation_type}</p>
						</div>

						{selectedQuest.skills.length > 0 && (
							<div>
								<span className="text-xs text-text-secondary uppercase">Skills</span>
								<div className="flex flex-wrap gap-1 mt-1">
									{selectedQuest.skills.map((s) => (
										<span key={s} className="px-2 py-0.5 text-xs bg-accent-primary/20 text-accent-primary rounded-full">
											{s}
										</span>
									))}
								</div>
							</div>
						)}

						{selectedQuest.state !== "LOCKED" && (
							<a
								href={`/quest/${selectedQuest.id}`}
								className="block w-full text-center py-2 rounded-xl bg-accent-primary text-text-on-accent font-medium hover:bg-accent-primary-hover transition-all"
							>
								{selectedQuest.state === "COMPLETED" ? "View Debrief" : "Open Quest"}
							</a>
						)}
					</div>
				</div>
			)}
		</div>
	);
}
