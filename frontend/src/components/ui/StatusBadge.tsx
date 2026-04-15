import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
	"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider border",
	{
		variants: {
			status: {
				available:
					"bg-accent-primary/10 text-accent-primary border-accent-primary/20",
				in_progress:
					"bg-accent-primary/10 text-accent-primary border-accent-primary/20",
				completed:
					"bg-accent-success/10 text-accent-success border-accent-success/20",
				locked:
					"bg-bg-surface text-text-muted border-border-subtle",
				failed:
					"bg-accent-error/10 text-accent-error border-accent-error/20",
				evaluating:
					"bg-accent-warning/10 text-accent-warning border-accent-warning/20",
			},
		},
		defaultVariants: {
			status: "locked",
		},
	},
);

const dotVariants: Record<string, string> = {
	available: "bg-accent-primary",
	in_progress: "bg-accent-primary animate-pulse",
	completed: "bg-accent-success",
	locked: "bg-text-muted",
	failed: "bg-accent-error",
	evaluating: "bg-accent-warning animate-pulse",
};

interface StatusBadgeProps extends VariantProps<typeof badgeVariants> {
	label: string;
	className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
	const dot = dotVariants[status ?? "locked"];
	return (
		<span className={cn(badgeVariants({ status }), className)}>
			<span className={cn("w-1.5 h-1.5 rounded-full", dot)} />
			{label}
		</span>
	);
}
