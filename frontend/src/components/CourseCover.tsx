"use client";

/**
 * Abstract cover placeholder for a course — matches the NDQS design bundle's
 * Marketplace card (NEXUS grid, FILE label, central glyph, coordinates,
 * REC indicator, bottom-to-base fade). Patterns are picked deterministically
 * from the course id so the same course always gets the same cover.
 *
 * If the course has a real cover_image_url, we render that instead.
 */

type PatternKey = "nexus" | "cipher" | "phantom" | "vault";

interface Pattern {
	grad: [string, string, string];
	glyph: string;
	label: string;
	ambient: string;
}

const PATTERNS: Record<PatternKey, Pattern> = {
	nexus:   { grad: ["#1E1B4B", "#7C3AED", "#05050A"], glyph: "NX-7", label: "NEXUS GRID", ambient: "#7C3AED" },
	cipher:  { grad: ["#3F2A07", "#E5B55C", "#05050A"], glyph: "∑-07", label: "SIGNAL·07",  ambient: "#E5B55C" },
	phantom: { grad: ["#0C1F3F", "#3B82F6", "#05050A"], glyph: "φ-Λ",  label: "PHANTOM",    ambient: "#3B82F6" },
	vault:   { grad: ["#064E3B", "#10B981", "#05050A"], glyph: "V-13", label: "VAULT·XIII", ambient: "#10B981" },
};

const ORDER: PatternKey[] = ["nexus", "cipher", "phantom", "vault"];

function pickPatternKey(seed: string): PatternKey {
	// Simple deterministic hash → pattern index
	let h = 0;
	for (let i = 0; i < seed.length; i++) {
		h = (h * 31 + seed.charCodeAt(i)) | 0;
	}
	return ORDER[Math.abs(h) % ORDER.length];
}

interface Props {
	courseId: string;
	coverImageUrl?: string | null;
	className?: string;
}

export default function CourseCover({ courseId, coverImageUrl, className }: Props) {
	if (coverImageUrl) {
		return (
			<div
				className={className}
				style={{
					position: "relative",
					aspectRatio: "16 / 8",
					borderRadius: "14px 14px 0 0",
					overflow: "hidden",
				}}
			>
				{/* eslint-disable-next-line @next/next/no-img-element */}
				<img
					src={coverImageUrl}
					alt=""
					style={{ width: "100%", height: "100%", objectFit: "cover" }}
				/>
				<div
					style={{
						position: "absolute",
						inset: 0,
						background: "linear-gradient(180deg, transparent 40%, rgba(5,5,10,0.85) 100%)",
					}}
				/>
			</div>
		);
	}

	const p = PATTERNS[pickPatternKey(courseId)];
	return (
		<div
			className={className}
			style={{
				position: "relative",
				aspectRatio: "16 / 8",
				borderRadius: "14px 14px 0 0",
				overflow: "hidden",
				background: `radial-gradient(120% 100% at 20% 20%, ${p.grad[1]}33, transparent 60%), radial-gradient(80% 80% at 90% 80%, ${p.grad[0]}55, transparent 60%), #05050A`,
			}}
		>
			{/* Vertical grid */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background:
						"repeating-linear-gradient(90deg, transparent 0, transparent 22px, rgba(255,255,255,0.03) 22px, rgba(255,255,255,0.03) 23px)",
				}}
			/>
			{/* Horizontal grid */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background:
						"repeating-linear-gradient(0deg, transparent 0, transparent 22px, rgba(255,255,255,0.03) 22px, rgba(255,255,255,0.03) 23px)",
				}}
			/>
			{/* Top-left: FILE label */}
			<div
				className="mono"
				style={{
					position: "absolute",
					left: 20,
					top: 18,
					fontSize: 10,
					letterSpacing: "0.2em",
					color: "rgba(255,255,255,0.4)",
					textTransform: "uppercase",
				}}
			>
				FILE // {p.label}
			</div>
			{/* Top-right: REC */}
			<div
				className="mono"
				style={{
					position: "absolute",
					right: 20,
					top: 18,
					fontSize: 10,
					letterSpacing: "0.15em",
					color: p.ambient,
					textTransform: "uppercase",
					opacity: 0.85,
				}}
			>
				● REC
			</div>
			{/* Central glyph */}
			<div
				className="mono"
				style={{
					position: "absolute",
					left: "50%",
					top: "50%",
					transform: "translate(-50%, -50%)",
					fontSize: 44,
					fontWeight: 300,
					letterSpacing: "0.05em",
					color: "#F8FAFC",
					textShadow: `0 0 40px ${p.ambient}66`,
				}}
			>
				{p.glyph}
			</div>
			{/* Bottom: coordinates + encryption label */}
			<div
				className="mono"
				style={{
					position: "absolute",
					left: 20,
					bottom: 16,
					right: 20,
					display: "flex",
					justifyContent: "space-between",
					fontSize: 10,
					letterSpacing: "0.15em",
					color: "rgba(255,255,255,0.35)",
				}}
			>
				<span>LAT 51.107 · LON 17.038</span>
				<span>ENC-AES-256</span>
			</div>
			{/* Bottom fade to base */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background:
						"linear-gradient(180deg, transparent 40%, rgba(5,5,10,0.85) 100%)",
				}}
			/>
		</div>
	);
}

export function coverAmbient(courseId: string): string {
	return PATTERNS[pickPatternKey(courseId)].ambient;
}
