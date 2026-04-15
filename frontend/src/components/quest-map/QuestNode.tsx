"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Lock, Zap, Code, Loader, CheckCircle, AlertTriangle, Trophy } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const STATE_STYLES: Record<string, { bg: string; border: string; text: string; glow?: string }> = {
	LOCKED: { bg: "bg-bg-surface-active", border: "border-border-subtle", text: "text-text-muted" },
	AVAILABLE: { bg: "bg-bg-surface", border: "border-accent-primary/50", text: "text-text-primary", glow: "shadow-glow-gold" },
	IN_PROGRESS: { bg: "bg-bg-surface", border: "border-accent-info", text: "text-text-primary", glow: "shadow-glow-purple" },
	EVALUATING: { bg: "bg-bg-surface", border: "border-accent-warning", text: "text-text-primary" },
	COMPLETED: { bg: "bg-bg-surface", border: "border-accent-success", text: "text-text-primary" },
	FAILED_ATTEMPT: { bg: "bg-bg-surface", border: "border-accent-warning", text: "text-text-primary" },
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
				px-5 py-4 rounded-2xl border-2 min-w-[180px] transition-all duration-300 cursor-pointer
				hover:scale-105 backdrop-blur-xl
				${styles.bg} ${styles.border} ${styles.glow || ""}
				${state === "AVAILABLE" ? "animate-border-pulse" : ""}
			`}
		>
			<Handle type="target" position={Position.Top} className="!bg-accent-primary !w-3 !h-3" />

			<div className="flex items-center gap-2 mb-1">
				<IconComponent className="w-4 h-4" />
				<span className={`text-sm font-semibold ${styles.text}`}>
					{nodeData.title}
				</span>
			</div>

			<div className="flex items-center gap-2 mt-2">
				<span className="text-xs text-text-secondary font-mono">{nodeData.evaluationType}</span>
				{nodeData.hasArtifact && (
					<Trophy className="w-3 h-3 text-accent-warning" />
				)}
			</div>

			<Handle type="source" position={Position.Bottom} className="!bg-accent-primary !w-3 !h-3" />
		</div>
	);
}
