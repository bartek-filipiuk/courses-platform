"use client";

import type { ReactNode } from "react";

interface GlassCardProps {
	children: ReactNode;
	className?: string;
	variant?: "default" | "elevated" | "interactive";
	onClick?: () => void;
}

const variantStyles = {
	default: "backdrop-blur-xl bg-[#141416]/70 border border-[#2A2A2E]/50",
	elevated: "backdrop-blur-xl bg-[#141416]/80 border border-[#2A2A2E]/60 shadow-lg shadow-black/20",
	interactive: "backdrop-blur-xl bg-[#141416]/70 border border-[#2A2A2E]/50 cursor-pointer transition-all duration-200 hover:translate-y-[-2px] hover:shadow-[0_0_20px_rgba(99,102,241,0.15)] hover:border-[#6366F1]/30",
};

export default function GlassCard({ children, className = "", variant = "default", onClick }: GlassCardProps) {
	return (
		<div
			className={`rounded-2xl p-6 ${variantStyles[variant]} ${className}`}
			onClick={onClick}
			onKeyDown={onClick ? (e) => e.key === "Enter" && onClick() : undefined}
			role={onClick ? "button" : undefined}
			tabIndex={onClick ? 0 : undefined}
		>
			{children}
		</div>
	);
}
