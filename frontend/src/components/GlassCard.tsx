"use client";

import type { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const glassCardVariants = cva(
	"rounded-2xl p-6 transition-all duration-300 ease-out",
	{
		variants: {
			variant: {
				default:
					"bg-bg-surface backdrop-blur-[20px] border border-border-subtle shadow-glass",
				elevated:
					"bg-bg-elevated backdrop-blur-[30px] border border-border-subtle shadow-lg shadow-black/20",
				interactive:
					"bg-bg-surface backdrop-blur-[20px] border border-border-subtle shadow-glass cursor-pointer hover:bg-bg-surface-hover hover:border-border-default hover:-translate-y-1",
				active:
					"bg-bg-surface backdrop-blur-[20px] border border-border-active shadow-glow-gold",
				success:
					"bg-accent-success/5 backdrop-blur-[20px] border border-accent-success/30",
				locked:
					"bg-bg-surface backdrop-blur-[20px] border border-border-subtle opacity-50 pointer-events-none",
			},
		},
		defaultVariants: {
			variant: "default",
		},
	},
);

interface GlassCardProps extends VariantProps<typeof glassCardVariants> {
	children: ReactNode;
	className?: string;
	onClick?: () => void;
}

export default function GlassCard({
	children,
	className,
	variant = "default",
	onClick,
}: GlassCardProps) {
	return (
		<div
			className={cn(glassCardVariants({ variant }), className)}
			onClick={onClick}
			onKeyDown={onClick ? (e) => e.key === "Enter" && onClick() : undefined}
			role={onClick ? "button" : undefined}
			tabIndex={onClick ? 0 : undefined}
		>
			{children}
		</div>
	);
}

export { glassCardVariants };
