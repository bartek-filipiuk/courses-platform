"use client";

import { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

const buttonVariants = cva(
	"relative inline-flex items-center justify-center font-medium transition-all duration-300 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none",
	{
		variants: {
			variant: {
				primary:
					"bg-accent-primary text-text-on-accent hover:bg-accent-primary-hover hover:shadow-glow-gold-strong rounded-lg",
				secondary:
					"bg-bg-surface border border-border-default text-text-primary backdrop-blur-sm hover:bg-bg-surface-hover hover:border-border-default rounded-lg",
				danger:
					"bg-accent-error/10 text-accent-error border border-accent-error/30 hover:bg-accent-error/20 hover:border-accent-error/50 rounded-lg",
				ghost:
					"bg-transparent text-text-secondary hover:text-text-primary hover:bg-bg-surface-hover rounded-lg",
			},
			size: {
				sm: "px-3 py-1.5 text-sm gap-1.5",
				md: "px-5 py-2.5 text-sm gap-2",
				lg: "px-6 py-3 text-base gap-2",
			},
		},
		defaultVariants: {
			variant: "primary",
			size: "md",
		},
	},
);

interface ButtonProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement>,
		VariantProps<typeof buttonVariants> {
	loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
	({ className, variant, size, loading, children, disabled, ...props }, ref) => {
		return (
			<button
				className={cn(buttonVariants({ variant, size, className }))}
				ref={ref}
				disabled={disabled || loading}
				{...props}
			>
				{loading && <Loader2 className="w-4 h-4 animate-spin" />}
				{variant === "primary" && (
					<div className="absolute -inset-1 bg-accent-primary rounded-lg blur-md opacity-0 group-hover:opacity-30 transition duration-300 pointer-events-none" />
				)}
				{children}
			</button>
		);
	},
);

Button.displayName = "Button";

export { Button, buttonVariants };
