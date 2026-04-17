"use client";

import { Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export type ArtifactTier = "common" | "rare" | "epic" | "legendary";

interface TierSpec {
	a: string;
	b: string;
	glow: string;
}

const TIERS: Record<ArtifactTier, TierSpec> = {
	common:    { a: "#64748B", b: "#94A3B8", glow: "rgba(148,163,184,0.2)" },
	rare:      { a: "#3B82F6", b: "#60A5FA", glow: "rgba(59,130,246,0.25)" },
	epic:      { a: "#7C3AED", b: "#A78BFA", glow: "rgba(124,58,237,0.3)" },
	legendary: { a: "#E5B55C", b: "#F3C570", glow: "rgba(229,181,92,0.4)" },
};

interface Props {
	tier: ArtifactTier;
	code: string;
	name: string;
	description?: string | null;
	source: string;
	acquired: string;
	delay?: number;
}

export default function ArtifactCard({
	tier,
	code,
	name,
	description,
	source,
	acquired,
	delay = 0,
}: Props) {
	const t = TIERS[tier];
	return (
		<div
			className="glass slide-up"
			style={{
				padding: 0,
				overflow: "hidden",
				borderColor: `${t.a}40`,
				animationDelay: `${delay}ms`,
			}}
		>
			<div
				className="relative"
				style={{
					padding: "28px 20px 20px",
					background: `radial-gradient(circle at 50% 30%, ${t.a}22, transparent 70%)`,
				}}
			>
				<div
					className="mx-auto mb-3.5 flex items-center justify-center"
					style={{
						width: 72,
						height: 72,
						borderRadius: 12,
						transform: "rotate(45deg)",
						background: `linear-gradient(135deg, ${t.a}, ${t.b})`,
						boxShadow: `0 0 32px ${t.glow}`,
					}}
				>
					<span
						className="mono font-semibold text-bg-base"
						style={{ transform: "rotate(-45deg)", fontSize: 22 }}
					>
						◆
					</span>
				</div>
				<div
					className="mono text-center uppercase mb-1.5"
					style={{
						fontSize: 10,
						letterSpacing: "0.2em",
						color: t.b,
					}}
				>
					{tier}
				</div>
				<div
					className="mono text-center mb-1"
					style={{
						fontSize: 11,
						color: "#E5B55C",
						letterSpacing: "0.12em",
					}}
				>
					{code}
				</div>
				<div className="text-center text-[15px] font-medium text-text-primary">
					{name}
				</div>
			</div>
			<div
				className="px-5 pt-3.5 pb-[18px] border-t border-border-subtle"
			>
				{description && (
					<p
						className="text-[12.5px] leading-[1.55] text-text-secondary mb-2.5"
						style={{ minHeight: 38 }}
					>
						{description}
					</p>
				)}
				<div
					className="mono flex justify-between"
					style={{
						fontSize: 10,
						color: "#475569",
						letterSpacing: "0.1em",
					}}
				>
					<span>FROM: {source}</span>
					<span>◷ {acquired}</span>
				</div>
			</div>
		</div>
	);
}

interface LockedProps {
	code: string;
	delay?: number;
}

export function LockedArtifact({ code, delay = 0 }: LockedProps) {
	return (
		<div
			className="slide-up"
			style={{
				padding: 0,
				overflow: "hidden",
				borderRadius: 16,
				border: "1px dashed rgba(255,255,255,0.08)",
				background: "rgba(255,255,255,0.015)",
				opacity: 0.6,
				animationDelay: `${delay}ms`,
			}}
		>
			<div className="stripes" style={{ padding: "28px 20px 20px" }}>
				<div
					className="mx-auto mb-3.5 flex items-center justify-center"
					style={{
						width: 72,
						height: 72,
						borderRadius: 12,
						transform: "rotate(45deg)",
						background: "rgba(255,255,255,0.03)",
						border: "1px dashed rgba(255,255,255,0.1)",
						color: "#475569",
					}}
				>
					<Lock
						className="w-5 h-5"
						style={{ transform: "rotate(-45deg)" }}
					/>
				</div>
				<div
					className="mono text-center uppercase mb-1"
					style={{
						fontSize: 10,
						letterSpacing: "0.2em",
						color: "#475569",
					}}
				>
					LOCKED
				</div>
				<div
					className={cn(
						"mono text-center",
					)}
					style={{
						fontSize: 11,
						color: "#64748B",
						letterSpacing: "0.12em",
					}}
				>
					{code}
				</div>
			</div>
			<div
				className="text-center text-[11px] pt-2.5 pb-4 px-5 text-text-muted"
				style={{ borderTop: "1px dashed rgba(255,255,255,0.05)" }}
			>
				Complete the corresponding quest to reveal
			</div>
		</div>
	);
}

export function tierForSortOrder(sortOrder: number, totalQuests: number): ArtifactTier {
	const pct = sortOrder / Math.max(totalQuests, 1);
	if (pct >= 0.78) return "legendary";
	if (pct >= 0.56) return "epic";
	if (pct >= 0.34) return "rare";
	return "common";
}
