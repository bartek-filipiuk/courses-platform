"use client";

import { Check, Loader2, Lock, Target } from "lucide-react";
import type { ComponentType } from "react";
import { cn } from "@/lib/utils";
import { NODE_HEIGHT, NODE_WIDTH, type NodePosition } from "./layout";

export type QuestState =
	| "LOCKED"
	| "AVAILABLE"
	| "IN_PROGRESS"
	| "COMPLETED"
	| "FAILED_ATTEMPT";

interface QuestNodeData {
	id: string;
	title: string;
	sortOrder: number;
	state: QuestState;
}

interface Props {
	quest: QuestNodeData;
	position: NodePosition;
	selected: boolean;
	onClick(): void;
}

interface StyleSpec {
	bg: string;
	border: string;
	color: string;
	label: string;
	icon: ComponentType<{ className?: string }>;
	iconSpin?: boolean;
}

const STYLE: Record<QuestState, StyleSpec> = {
	COMPLETED: {
		bg: "rgba(16,185,129,0.08)",
		border: "rgba(16,185,129,0.4)",
		color: "#10B981",
		label: "COMPLETE",
		icon: Check,
	},
	IN_PROGRESS: {
		bg: "rgba(229,181,92,0.1)",
		border: "rgba(229,181,92,0.6)",
		color: "#E5B55C",
		label: "IN PROGRESS",
		icon: Loader2,
		iconSpin: true,
	},
	AVAILABLE: {
		bg: "rgba(255,255,255,0.04)",
		border: "rgba(229,181,92,0.32)",
		color: "#F8FAFC",
		label: "AVAILABLE",
		icon: Target,
	},
	LOCKED: {
		bg: "rgba(255,255,255,0.02)",
		border: "rgba(255,255,255,0.06)",
		color: "#475569",
		label: "LOCKED",
		icon: Lock,
	},
	FAILED_ATTEMPT: {
		bg: "rgba(239,68,68,0.08)",
		border: "rgba(239,68,68,0.4)",
		color: "#EF4444",
		label: "RETRY",
		icon: Target,
	},
};

export default function QuestNode({ quest, position, selected, onClick }: Props) {
	const s = STYLE[quest.state];
	const isLocked = quest.state === "LOCKED";
	const Icon = s.icon;

	const animation =
		quest.state === "AVAILABLE"
			? "node-pulse 2.4s ease-in-out infinite"
			: quest.state === "IN_PROGRESS"
				? "node-glow 2s ease-in-out infinite"
				: undefined;

	return (
		<button
			type="button"
			onClick={() => !isLocked && onClick()}
			disabled={isLocked}
			className={cn(
				"absolute text-left transition-all duration-200 ease-out",
				isLocked
					? "cursor-not-allowed opacity-60"
					: "cursor-pointer hover:scale-[1.04]",
			)}
			style={{
				left: position.x,
				top: position.y,
				width: NODE_WIDTH,
				height: NODE_HEIGHT,
				transform: "translate(-50%, -50%)",
				borderRadius: 14,
				background: s.bg,
				border: `1px solid ${selected ? "#E5B55C" : s.border}`,
				backdropFilter: "blur(10px)",
				WebkitBackdropFilter: "blur(10px)",
				padding: "12px 14px",
				boxShadow: selected
					? "0 0 30px rgba(229,181,92,0.45)"
					: "0 8px 24px rgba(0,0,0,0.3)",
				animation,
			}}
		>
			<div className="flex items-center justify-between mb-2">
				<span
					className="mono"
					style={{ fontSize: 10, letterSpacing: "0.15em", color: "#94A3B8" }}
				>
					QUEST {String(quest.sortOrder).padStart(2, "0")}
				</span>
				<Icon
					className={cn("w-[14px] h-[14px]", s.iconSpin && "animate-spin")}
					style={{ color: s.color }}
				/>
			</div>
			<div
				className="line-clamp-1"
				style={{
					fontSize: 13.5,
					fontWeight: 500,
					color: isLocked ? "#64748B" : "#F8FAFC",
					lineHeight: 1.25,
					marginBottom: 6,
				}}
			>
				{quest.title}
			</div>
			<div
				className="mono"
				style={{
					fontSize: 9,
					letterSpacing: "0.15em",
					color: s.color,
					textTransform: "uppercase",
				}}
			>
				{s.label}
			</div>

			<span
				className="absolute top-1/2 -translate-y-1/2 rounded-full"
				style={{
					left: -4,
					width: 8,
					height: 8,
					background: "#0B0B15",
					border: `1.5px solid ${s.border}`,
				}}
			/>
			<span
				className="absolute top-1/2 -translate-y-1/2 rounded-full"
				style={{
					right: -4,
					width: 8,
					height: 8,
					background: "#0B0B15",
					border: `1.5px solid ${s.border}`,
				}}
			/>
		</button>
	);
}
