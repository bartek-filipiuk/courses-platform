"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
	error?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
	({ className, error, ...props }, ref) => {
		return (
			<input
				ref={ref}
				className={cn(
					"w-full px-4 py-3 rounded-xl bg-bg-input border text-text-primary placeholder:text-text-muted font-sans text-sm transition-all duration-200 focus:outline-none focus:bg-bg-surface-hover",
					error
						? "border-border-error focus:border-border-error"
						: "border-border-default focus:border-border-active focus:shadow-[var(--glow-primary)]",
					className,
				)}
				{...props}
			/>
		);
	},
);

Input.displayName = "Input";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
	error?: boolean;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
	({ className, error, ...props }, ref) => {
		return (
			<textarea
				ref={ref}
				className={cn(
					"w-full px-4 py-3 rounded-xl bg-bg-input border text-text-primary placeholder:text-text-muted font-sans text-sm transition-all duration-200 focus:outline-none focus:bg-bg-surface-hover resize-vertical",
					error
						? "border-border-error focus:border-border-error"
						: "border-border-default focus:border-border-active focus:shadow-[var(--glow-primary)]",
					className,
				)}
				{...props}
			/>
		);
	},
);

Textarea.displayName = "Textarea";

export { Input, Textarea };
