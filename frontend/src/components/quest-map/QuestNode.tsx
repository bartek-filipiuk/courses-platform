"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Lock, Zap, Code, Loader, CheckCircle, AlertTriangle, Trophy } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const STATE_STYLES: Record<string, { bg: string; border: string; text: string; glow?: string }> = {
	LOCKED: { bg: "bg-[#1C1C1F]", border: "border-[#2A2A2E]", text: "text-[#A1A1AA]/50" },
	AVAILABLE: { bg: "bg-[#141416]", border: "border-[#6366F1]", text: "text-white", glow: "shadow-[0_0_20px_rgba(99,102,241,0.3)]" },
	IN_PROGRESS: { bg: "bg-[#141416]", border: "border-[#3B82F6]", text: "text-white", glow: "shadow-[0_0_15px_rgba(59,130,246,0.2)]" },
	EVALUATING: { bg: "bg-[#141416]", border: "border-[#F59E0B]", text: "text-white" },
	COMPLETED: { bg: "bg-[#141416]", border: "border-[#22C55E]", text: "text-white" },
	FAILED_ATTEMPT: { bg: "bg-[#141416]", border: "border-[#F59E0B]", text: "text-white" },
};

const STATE_ICONS: Record<string, LucideIcon> = {
	LOCKED: Lock,
	AVAILABLE: Zap,
	IN_PROGRESS: Code,
	EVALUATING: Loader,
	COMPLETED: CheckCircle,
	FAILED_ATTEMPT: AlertTriangle,
};

interface QuestNodeData {
	title: string;
	state: string;
	hasArtifact: boolean;
	evaluationType: string;
	[key: string]: unknown;
}

export default function QuestNode({ data }: NodeProps) {
	const nodeData = data as QuestNodeData;
	const state = nodeData.state || "LOCKED";
	const styles = STATE_STYLES[state] || STATE_STYLES.LOCKED;
	const IconComponent = STATE_ICONS[state] || Lock;

	return (
		<div
			className={`
				px-5 py-4 rounded-2xl border-2 min-w-[180px] transition-all duration-300
				${styles.bg} ${styles.border} ${styles.glow || ""}
				${state === "AVAILABLE" ? "animate-pulse" : ""}
			`}
		>
			<Handle type="target" position={Position.Top} className="!bg-[#6366F1] !w-3 !h-3" />

			<div className="flex items-center gap-2 mb-1">
				<IconComponent className="w-4 h-4" />
				<span className={`text-sm font-semibold ${styles.text}`}>
					{nodeData.title}
				</span>
			</div>

			<div className="flex items-center gap-2 mt-2">
				<span className="text-xs text-[#A1A1AA] font-mono">{nodeData.evaluationType}</span>
				{nodeData.hasArtifact && (
					<Trophy className="w-3 h-3 text-[#F59E0B]" />
				)}
			</div>

			<Handle type="source" position={Position.Bottom} className="!bg-[#6366F1] !w-3 !h-3" />
		</div>
	);
}
