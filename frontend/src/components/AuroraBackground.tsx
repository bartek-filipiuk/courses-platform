"use client";

export function AuroraBackground() {
	return (
		<div className="fixed inset-0 -z-10 overflow-hidden bg-bg-base pointer-events-none">
			{/* Gradient Orb 1: Purple (top-left) */}
			<div
				className="absolute -top-[40%] -left-[20%] w-[60%] h-[60%] rounded-full bg-accent-secondary/15 blur-[120px] animate-aurora will-change-transform"
			/>

			{/* Gradient Orb 2: Gold (bottom-right) */}
			<div
				className="absolute -bottom-[30%] -right-[15%] w-[50%] h-[50%] rounded-full bg-accent-primary/[0.08] blur-[100px] animate-aurora will-change-transform"
				style={{ animationDelay: "10s", animationDirection: "alternate-reverse" }}
			/>

			{/* Gradient Orb 3: Blue (center) */}
			<div
				className="absolute top-[30%] left-[40%] w-[30%] h-[30%] rounded-full bg-accent-info/[0.05] blur-[80px] animate-aurora will-change-transform"
				style={{ animationDelay: "5s" }}
			/>
		</div>
	);
}
