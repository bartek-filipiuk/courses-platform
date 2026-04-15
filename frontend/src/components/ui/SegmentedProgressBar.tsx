import { cn } from "@/lib/utils";

interface SegmentedProgressBarProps {
	total: number;
	completed: number;
	active?: number;
	className?: string;
}

export function SegmentedProgressBar({
	total,
	completed,
	active,
	className,
}: SegmentedProgressBarProps) {
	return (
		<div className={cn("flex items-center gap-1.5", className)}>
			{Array.from({ length: total }, (_, i) => {
				const isCompleted = i < completed;
				const isActive = active !== undefined ? i === active : i === completed;

				return (
					<div
						key={i}
						className={cn(
							"h-2 flex-1 rounded-sm transition-all duration-300",
							isCompleted &&
								"bg-accent-primary shadow-[0_0_8px_rgba(229,181,92,0.5)]",
							isActive &&
								!isCompleted &&
								"bg-accent-primary/60 animate-pulse",
							!isCompleted && !isActive && "bg-bg-surface-active",
						)}
					/>
				);
			})}
		</div>
	);
}
