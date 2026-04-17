"use client";

/**
 * Aurora backdrop — 3 staggered orbs (purple / gold / blue).
 * Uses `.aurora-*` classes from globals.css so the exact sizes, blur,
 * opacities, and animation timings match the NDQS design bundle.
 */
export function AuroraBackground() {
	return (
		<>
			<div className="aurora-bg">
				<div className="aurora-orb purple" />
				<div className="aurora-orb gold" />
				<div className="aurora-orb blue" />
			</div>
			<div className="noise-overlay" />
		</>
	);
}
