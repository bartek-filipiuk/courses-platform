/**
 * Shimmer skeleton loader with gradient animation.
 * Replaces basic animate-pulse with a polished shimmer effect.
 */

interface SkeletonProps {
	className?: string;
	variant?: "text" | "card" | "circle" | "avatar";
}

export default function ShimmerSkeleton({ className = "", variant = "text" }: SkeletonProps) {
	const base = "relative overflow-hidden bg-[#1C1C1F] before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-[#2A2A2E]/50 before:to-transparent before:animate-shimmer";

	const variants: Record<string, string> = {
		text: "h-4 rounded-md",
		card: "h-48 rounded-2xl",
		circle: "w-10 h-10 rounded-full",
		avatar: "w-12 h-12 rounded-xl",
	};

	return <div className={`${base} ${variants[variant]} ${className}`} />;
}

export function SkeletonCard() {
	return (
		<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-6 space-y-4">
			<ShimmerSkeleton variant="text" className="w-1/3 h-3" />
			<ShimmerSkeleton variant="text" className="w-2/3 h-5" />
			<ShimmerSkeleton variant="text" className="w-full h-3" />
			<ShimmerSkeleton variant="text" className="w-4/5 h-3" />
			<div className="flex justify-between pt-2">
				<ShimmerSkeleton variant="text" className="w-20 h-3" />
				<ShimmerSkeleton variant="text" className="w-16 h-3" />
			</div>
		</div>
	);
}

export function SkeletonStats() {
	return (
		<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 space-y-2">
			<ShimmerSkeleton variant="text" className="w-16 h-3" />
			<ShimmerSkeleton variant="text" className="w-24 h-8" />
			<ShimmerSkeleton variant="text" className="w-20 h-3" />
		</div>
	);
}
