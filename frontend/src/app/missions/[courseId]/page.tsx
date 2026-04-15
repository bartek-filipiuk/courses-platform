"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import type { CourseDetail } from "@/types";

export default function CoursePage() {
	const params = useParams();
	const courseId = params.courseId as string;
	const [course, setCourse] = useState<CourseDetail | null>(null);
	const [loading, setLoading] = useState(true);
	const [enrolling, setEnrolling] = useState(false);
	const [enrolled, setEnrolled] = useState(false);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		apiClient<CourseDetail>(`/api/courses/${courseId}`, { token: "demo" })
			.then(setCourse)
			.catch((e) => setError(e.message))
			.finally(() => setLoading(false));
	}, [courseId]);

	const handleEnroll = async () => {
		setEnrolling(true);
		try {
			await apiClient(`/api/courses/${courseId}/enroll`, {
				method: "POST",
				token: "demo",
			});
			setEnrolled(true);
		} catch (e) {
			if (e instanceof ApiError && e.status === 409) {
				setEnrolled(true);
			} else {
				setError(e instanceof Error ? e.message : "Enrollment failed");
			}
		} finally {
			setEnrolling(false);
		}
	};

	const handleDownloadStarterPack = () => {
		const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/courses/${courseId}/starter-pack`;
		window.open(url, "_blank");
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] p-8">
				<div className="max-w-4xl mx-auto">
					<div className="h-8 w-48 bg-[#141416] rounded animate-pulse mb-4" />
					<div className="h-64 bg-[#141416] rounded-2xl animate-pulse" />
				</div>
			</div>
		);
	}

	if (error || !course) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<p className="text-red-400">{error || "Course not found"}</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-4xl mx-auto">
				{/* Header */}
				{course.narrative_title && (
					<p className="text-sm font-mono text-[#6366F1] uppercase tracking-wider mb-2">
						{course.narrative_title}
					</p>
				)}
				<h1 className="text-4xl font-bold text-white mb-4">{course.title}</h1>

				{/* Cover image */}
				{course.cover_image_url && (
					<div className="mb-8 h-64 rounded-2xl overflow-hidden">
						<img
							src={course.cover_image_url}
							alt={course.title}
							className="w-full h-full object-cover"
						/>
					</div>
				)}

				{/* Description */}
				<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-8 mb-6">
					<h2 className="text-lg font-semibold text-white mb-4">Mission Briefing</h2>
					<p className="text-[#A1A1AA] whitespace-pre-line leading-relaxed">
						{course.description || "No description available."}
					</p>
				</div>

				{/* Game Master info */}
				{course.persona_name && (
					<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-6 mb-6">
						<div className="flex items-center gap-3">
							<div className="w-10 h-10 rounded-full bg-[#6366F1]/20 flex items-center justify-center">
								<span className="text-[#6366F1] font-mono text-sm">GM</span>
							</div>
							<div>
								<p className="text-white font-medium">{course.persona_name}</p>
								<p className="text-xs text-[#A1A1AA]">Game Master</p>
							</div>
						</div>
					</div>
				)}

				{/* Actions */}
				<div className="flex gap-4">
					<button
						type="button"
						onClick={handleEnroll}
						disabled={enrolling || enrolled}
						className={`px-8 py-3 rounded-xl font-medium transition-all ${
							enrolled
								? "bg-[#22C55E]/20 text-[#22C55E] border border-[#22C55E]/30"
								: "bg-[#6366F1] text-white hover:bg-[#5558E6] active:scale-[0.98]"
						} disabled:opacity-50`}
					>
						{enrolled ? "Enrolled" : enrolling ? "Enrolling..." : "Accept Mission"}
					</button>

					{enrolled && (
						<button
							type="button"
							onClick={handleDownloadStarterPack}
							className="px-8 py-3 rounded-xl font-medium border border-[#2A2A2E] text-white hover:bg-[#1C1C1F] transition-all"
						>
							Download Starter Pack
						</button>
					)}
				</div>
			</div>
		</div>
	);
}
