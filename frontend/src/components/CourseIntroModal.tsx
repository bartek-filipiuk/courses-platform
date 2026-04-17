"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import type { Course } from "@/types";
import CourseCover, { coverAmbient } from "./CourseCover";

interface Props {
	course: Course;
	onAccept: () => void;
	onClose: () => void;
	accepting?: boolean;
}

/**
 * Modal shown when a student clicks an unenrolled course card.
 * Gives briefing, persona, and an "Accept Mission" CTA before committing.
 */
export default function CourseIntroModal({ course, onAccept, onClose, accepting }: Props) {
	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if (e.key === "Escape") onClose();
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [onClose]);

	const ambient = coverAmbient(course.id);

	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center p-4 fade-in"
			style={{ background: "rgba(5,5,10,0.75)", backdropFilter: "blur(6px)" }}
			onClick={onClose}
		>
			<div
				className="glass slide-up w-full max-w-[620px] max-h-[86vh] overflow-auto"
				onClick={(e) => e.stopPropagation()}
				style={{ padding: 0 }}
			>
				<div className="relative">
					<CourseCover courseId={course.id} coverImageUrl={course.cover_image_url} />
					<button
						type="button"
						onClick={onClose}
						aria-label="Close"
						className="absolute top-3 right-3 w-8 h-8 rounded-lg flex items-center justify-center text-text-secondary hover:text-text-primary transition-colors"
						style={{
							background: "rgba(5,5,10,0.6)",
							border: "1px solid rgba(255,255,255,0.08)",
						}}
					>
						<X className="w-4 h-4" />
					</button>
				</div>

				<div className="px-7 py-6">
					{course.narrative_title && (
						<div
							className="mono"
							style={{
								fontSize: 11,
								letterSpacing: "0.15em",
								color: ambient,
								textTransform: "uppercase",
								marginBottom: 10,
							}}
						>
							// {course.narrative_title}
						</div>
					)}
					<h2 className="text-[26px] font-semibold text-text-primary tracking-[-0.02em] mb-3">
						{course.title}
					</h2>
					{course.description && (
						<p className="text-[14px] leading-[1.65] text-text-secondary whitespace-pre-line mb-5">
							{course.description}
						</p>
					)}
					<div className="flex items-center gap-2.5 pt-4 border-t border-border-subtle mb-6">
						<div
							className="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-bold text-bg-base"
							style={{ background: "linear-gradient(135deg, #7C3AED, #E5B55C)" }}
						>
							{course.persona_name?.[0]?.toUpperCase() ?? "GM"}
						</div>
						<div className="text-[13px]">
							<span className="text-text-primary font-medium">
								{course.persona_name ?? "Game Master"}
							</span>
							<span className="text-text-muted"> · Your guide</span>
						</div>
					</div>

					<div className="flex items-center gap-3">
						<button
							type="button"
							onClick={onAccept}
							disabled={accepting}
							className="btn btn-primary flex-1 disabled:opacity-60 disabled:cursor-not-allowed"
						>
							{accepting ? "Accepting…" : "Accept Mission"}
						</button>
						<button type="button" onClick={onClose} className="btn btn-ghost">
							Cancel
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}
