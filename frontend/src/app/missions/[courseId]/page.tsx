"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { ApiError } from "@/lib/api-client";
import { useAuthFetch, useAuthMutate } from "@/lib/use-api";
import { Button } from "@/components/ui";
import GlassCard from "@/components/GlassCard";
import type { CourseDetail } from "@/types";

export default function CoursePage() {
	const params = useParams();
	const courseId = params.courseId as string;
	const { data: course, loading, error } = useAuthFetch<CourseDetail>(`/api/courses/${courseId}`);
	const [enrolling, setEnrolling] = useState(false);
	const [enrolled, setEnrolled] = useState(false);
	const [enrollError, setEnrollError] = useState<string | null>(null);
	const mutate = useAuthMutate();

	const handleEnroll = async () => {
		setEnrolling(true);
		setEnrollError(null);
		try {
			await mutate(`/api/courses/${courseId}/enroll`, { method: "POST" });
			setEnrolled(true);
		} catch (e) {
			if (e instanceof ApiError && e.status === 409) {
				setEnrolled(true);
			} else {
				setEnrollError(e instanceof Error ? e.message : "Enrollment failed");
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
			<div className="min-h-screen bg-bg-base p-8">
				<div className="max-w-4xl mx-auto">
					<div className="h-8 w-48 bg-bg-elevated rounded animate-pulse mb-4" />
					<div className="h-64 bg-bg-elevated rounded-2xl animate-pulse" />
				</div>
			</div>
		);
	}

	if (error || !course) {
		return (
			<div className="min-h-screen bg-bg-base flex items-center justify-center">
				<p className="text-accent-error">{error || "Course not found"}</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-4xl mx-auto">
				{/* Header */}
				{course.narrative_title && (
					<p className="text-sm font-mono text-accent-primary uppercase tracking-wider mb-2">
						{course.narrative_title}
					</p>
				)}
				<h1 className="text-4xl font-bold text-text-primary mb-4">{course.title}</h1>

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
				<GlassCard className="mb-6 p-8">
					<h2 className="text-lg font-semibold text-text-primary mb-4">Mission Briefing</h2>
					<p className="text-text-secondary whitespace-pre-line leading-relaxed">
						{course.description || "No description available."}
					</p>
				</GlassCard>

				{/* Game Master info */}
				{course.persona_name && (
					<GlassCard className="mb-6">
						<div className="flex items-center gap-3">
							<div className="w-10 h-10 rounded-full bg-accent-primary/20 flex items-center justify-center">
								<span className="text-accent-primary font-mono text-sm">GM</span>
							</div>
							<div>
								<p className="text-text-primary font-medium">{course.persona_name}</p>
								<p className="text-xs text-text-secondary">Game Master</p>
							</div>
						</div>
					</GlassCard>
				)}

				{/* Enroll error */}
				{enrollError && (
					<div className="mb-4 rounded-xl border border-accent-error/30 bg-accent-error/5 p-4">
						<p className="text-sm text-accent-error">{enrollError}</p>
					</div>
				)}

				{/* Actions */}
				<div className="flex gap-4">
					{enrolled ? (
						<Button
							variant="primary"
							size="lg"
							disabled
							className="bg-accent-success/20 text-accent-success border border-accent-success/30 hover:bg-accent-success/20"
						>
							Enrolled
						</Button>
					) : (
						<Button
							variant="primary"
							size="lg"
							onClick={handleEnroll}
							loading={enrolling}
						>
							Accept Mission
						</Button>
					)}

					{enrolled && (
						<Button
							variant="secondary"
							size="lg"
							onClick={handleDownloadStarterPack}
						>
							Download Starter Pack
						</Button>
					)}
				</div>
			</div>
		</div>
	);
}
