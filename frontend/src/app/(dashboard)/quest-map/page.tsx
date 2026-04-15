"use client";

import { useCallback, useMemo, useState } from "react";
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

export default function QuestMapPage() {
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
				style: { stroke: "#6366F1", strokeWidth: 2 },
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
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<p className="text-[#A1A1AA]">Select a course to view quest map.</p>
			</div>
		);
	}

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<div className="w-8 h-8 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	return (
		<div className="h-screen bg-[#0A0A0B] flex">
			{/* Map */}
			<div className="flex-1">
				<ReactFlow
					nodes={nodes}
					edges={edges}
					nodeTypes={nodeTypes}
					onNodeClick={onNodeClick}
					fitView
					className="bg-[#0A0A0B]"
				>
					<Background color="#2A2A2E" gap={20} />
					<Controls className="!bg-[#141416] !border-[#2A2A2E] !rounded-xl" />
					<MiniMap
						className="!bg-[#141416] !border-[#2A2A2E] !rounded-xl"
						nodeColor={(n) => {
							const state = (n.data as Record<string, unknown>)?.state as string;
							if (state === "COMPLETED") return "#22C55E";
							if (state === "AVAILABLE") return "#6366F1";
							if (state === "IN_PROGRESS") return "#3B82F6";
							return "#2A2A2E";
						}}
					/>
				</ReactFlow>
			</div>

			{/* Quest Detail Panel (slide-in) */}
			{selectedQuest && (
				<div className="w-96 border-l border-[#2A2A2E] bg-[#141416] p-6 overflow-y-auto">
					<div className="flex justify-between items-start mb-4">
						<h2 className="text-xl font-bold text-white">{selectedQuest.title}</h2>
						<button
							type="button"
							onClick={() => setSelectedQuest(null)}
							className="text-[#A1A1AA] hover:text-white"
						>
							&times;
						</button>
					</div>

					<div className="space-y-4">
						<div>
							<span className="text-xs text-[#A1A1AA] uppercase">Status</span>
							<p className="text-sm text-white font-mono">{selectedQuest.state}</p>
						</div>

						<div>
							<span className="text-xs text-[#A1A1AA] uppercase">Type</span>
							<p className="text-sm text-white font-mono">{selectedQuest.evaluation_type}</p>
						</div>

						{selectedQuest.skills.length > 0 && (
							<div>
								<span className="text-xs text-[#A1A1AA] uppercase">Skills</span>
								<div className="flex flex-wrap gap-1 mt-1">
									{selectedQuest.skills.map((s) => (
										<span key={s} className="px-2 py-0.5 text-xs bg-[#6366F1]/20 text-[#6366F1] rounded-full">
											{s}
										</span>
									))}
								</div>
							</div>
						)}

						{selectedQuest.state !== "LOCKED" && (
							<a
								href={`/quest/${selectedQuest.id}`}
								className="block w-full text-center py-2 rounded-xl bg-[#6366F1] text-white font-medium hover:bg-[#5558E6] transition-all"
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
