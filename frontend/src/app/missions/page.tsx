"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import { getDevToken } from "@/lib/dev-auth";
import { useAuthFetch, useAuthMutate } from "@/lib/use-api";
import { SkeletonCard } from "@/components/ShimmerSkeleton";
import TopBar from "@/components/TopBar";
import CourseCover, { coverAmbient } from "@/components/CourseCover";
import CourseIntroModal from "@/components/CourseIntroModal";
import { cn } from "@/lib/utils";
import type { Course } from "@/types";
import { toast } from "sonner";

type Filter = "all" | "enrolled" | "available";

interface EnrollmentLite {
	course_id: string;
	completed_quests: number;
	total_quests: number;
}

function Stat({ label, value }: { label: string; value: string | number }) {
	return (
		<span>
			<span className="text-text-primary">{value}</span> {label}
		</span>
	);
}

function difficultyFromCourse(course: Course): { label: string; variant: "success" | "purple" | "gold" | "error" } {
	// Until we have a real difficulty field, derive from title length as a stable placeholder.
	const hash = course.title.length % 4;
	if (hash === 0) return { label: "Beginner", variant: "success" };
	if (hash === 1) return { label: "Intermediate", variant: "purple" };
	if (hash === 2) return { label: "Advanced", variant: "gold" };
	return { label: "Expert", variant: "error" };
}

function CourseCard({
	course,
	enrollment,
	onOpen,
	delay,
}: {
	course: Course;
	enrollment?: EnrollmentLite;
	onOpen: () => void;
	delay: number;
}) {
	const ambient = coverAmbient(course.id);
	const diff = difficultyFromCourse(course);
	const enrolled = Boolean(enrollment);
	const total = enrollment?.total_quests ?? 9;
	const done = enrollment?.completed_quests ?? 0;

	return (
		<button
			type="button"
			onClick={onOpen}
			className="glass slide-up text-left group"
			style={{
				padding: 0,
				overflow: "hidden",
				animationDelay: `${delay}ms`,
				boxShadow: "0 8px 32px rgba(0,0,0,0.36)",
			}}
		>
			<div className="relative">
				<CourseCover courseId={course.id} coverImageUrl={course.cover_image_url} />
				<div className="absolute top-4 right-4">
					<span className={cn("badge", `badge-${diff.variant}`)}>
						<span className="dot" />
						{diff.label}
					</span>
				</div>
			</div>

			<div className="px-[22px] py-5">
				{course.narrative_title && (
					<div
						className="mono"
						style={{
							fontSize: 10,
							letterSpacing: "0.15em",
							color: ambient,
							textTransform: "uppercase",
							marginBottom: 8,
						}}
					>
						{course.narrative_title}
					</div>
				)}
				<h3 className="text-[20px] font-semibold text-text-primary tracking-[-0.015em] mb-2 line-clamp-1">
					{course.title}
				</h3>
				<p className="text-[13.5px] leading-[1.55] text-text-secondary line-clamp-2 mb-4">
					{course.description}
				</p>

				<div className="flex items-center justify-between pt-3.5 border-t border-border-subtle text-[11.5px] text-text-secondary">
					<div className="flex gap-3.5">
						<Stat label="Quests" value={total} />
						{course.persona_name && (
							<span className="mono" style={{ color: ambient, letterSpacing: "0.1em", textTransform: "uppercase" }}>
								{course.persona_name}
							</span>
						)}
					</div>
					{enrolled ? (
						<div className="flex items-center gap-2.5">
							<div className="segbar" style={{ width: 72 }}>
								{Array.from({ length: total }).map((_, i) => (
									<div
										key={i}
										className={cn(
											"seg",
											i < done && "done",
											i === done && "active",
										)}
									/>
								))}
							</div>
							<span className="mono text-[10px] tracking-[0.1em] text-accent-primary">
								CONTINUE →
							</span>
						</div>
					) : (
						<span className="mono text-[10px] tracking-[0.1em] uppercase text-text-secondary">
							Accept mission →
						</span>
					)}
				</div>
			</div>
		</button>
	);
}

export default function MissionsPage() {
	const router = useRouter();
	const [courses, setCourses] = useState<Course[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [filter, setFilter] = useState<Filter>("all");
	const [introCourse, setIntroCourse] = useState<Course | null>(null);
	const [accepting, setAccepting] = useState(false);
	const mutate = useAuthMutate();

	const { data: enrollments } = useAuthFetch<EnrollmentLite[]>(
		"/api/users/me/enrollments",
	);
	const enrollmentById = useMemo(() => {
		const map = new Map<string, EnrollmentLite>();
		for (const e of enrollments ?? []) map.set(e.course_id, e);
		return map;
	}, [enrollments]);

	useEffect(() => {
		apiClient<Course[]>("/api/courses")
			.then(setCourses)
			.catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
			.finally(() => setLoading(false));
	}, []);

	const visible = useMemo(() => {
		if (filter === "all") return courses;
		return courses.filter((c) => {
			const isEnrolled = enrollmentById.has(c.id);
			return filter === "enrolled" ? isEnrolled : !isEnrolled;
		});
	}, [courses, filter, enrollmentById]);

	async function openCourse(course: Course) {
		const enrolled = enrollmentById.has(course.id);
		if (enrolled) {
			router.push(`/quest-map?courseId=${course.id}`);
		} else {
			setIntroCourse(course);
		}
	}

	async function acceptMission() {
		if (!introCourse) return;
		setAccepting(true);
		try {
			await mutate(`/api/courses/${introCourse.id}/enroll`, { method: "POST" });
			toast.success("Mission accepted");
			router.push(`/quest-map?courseId=${introCourse.id}`);
		} catch (e) {
			if (e instanceof ApiError && e.status === 409) {
				// Already enrolled — just jump to map.
				router.push(`/quest-map?courseId=${introCourse.id}`);
				return;
			}
			toast.error(e instanceof Error ? e.message : "Enrollment failed");
		} finally {
			setAccepting(false);
		}
	}

	return (
		<div className="flex flex-col h-screen">
			<TopBar
				breadcrumb={[
					{ label: "Command Center" },
					{ label: "Marketplace", mono: true },
				]}
			/>
			<div className="flex-1 overflow-auto">
				<div className="px-12 py-9 max-w-[1400px] mx-auto">
					<header className="mb-8 max-w-[780px]">
						<div
							className="mini-label"
							style={{ color: "var(--accent-primary)", marginBottom: 10 }}
						>
							// MARKETPLACE · {courses.length} ACTIVE OPERATIONS
						</div>
						<h1 className="text-[34px] font-semibold leading-[1.15] tracking-[-0.025em] mb-2">
							Wybierz misję, Operatywie.
						</h1>
						<p className="text-[15px] text-text-secondary leading-[1.6] max-w-[620px]">
							Każda operacja to kurs IT opakowany w scenariusz. Kod piszesz w swoim IDE z własnym agentem AI —
							platforma ocenia efekty, Game Master prowadzi fabułę.
						</p>
					</header>

					<div className="flex gap-2.5 mb-6 flex-wrap">
						{(
							[
								["all", "All operations"],
								["enrolled", "Enrolled"],
								["available", "Available"],
							] as const
						).map(([key, label]) => {
							const active = filter === key;
							return (
								<button
									key={key}
									type="button"
									onClick={() => setFilter(key)}
									className="btn btn-sm btn-ghost"
									style={
										active
											? {
													background: "rgba(229,181,92,0.08)",
													color: "var(--accent-primary)",
													borderColor: "rgba(229,181,92,0.22)",
												}
											: undefined
									}
								>
									{label}
								</button>
							);
						})}
					</div>

					{loading ? (
						<div className="grid gap-5 [grid-template-columns:repeat(auto-fill,minmax(380px,1fr))]">
							{[1, 2, 3].map((i) => (
								<SkeletonCard key={i} />
							))}
						</div>
					) : error ? (
						<p className="text-accent-error">Failed to load missions: {error}</p>
					) : visible.length === 0 ? (
						<div className="text-center py-20 text-text-secondary">
							No missions match this filter.
						</div>
					) : (
						<div className="grid gap-5 [grid-template-columns:repeat(auto-fill,minmax(380px,1fr))]">
							{visible.map((course, i) => (
								<CourseCard
									key={course.id}
									course={course}
									enrollment={enrollmentById.get(course.id)}
									onOpen={() => openCourse(course)}
									delay={i * 80}
								/>
							))}
						</div>
					)}

					<div
						className="mono text-center text-[12px] mt-14"
						style={{ color: "var(--text-muted)" }}
					>
						─── END OF TRANSMISSION ───
					</div>
				</div>
			</div>

			{introCourse && (
				<CourseIntroModal
					course={introCourse}
					onAccept={acceptMission}
					onClose={() => setIntroCourse(null)}
					accepting={accepting}
				/>
			)}
		</div>
	);
}
