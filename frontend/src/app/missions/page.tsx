"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { FadeInUp, StaggerContainer, StaggerItem } from "@/lib/motion";
import { SkeletonCard } from "@/components/ShimmerSkeleton";
import type { Course } from "@/types";

export default function MissionsPage() {
	const [courses, setCourses] = useState<Course[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		apiClient<Course[]>("/api/courses")
			.then(setCourses)
			.catch((e) => setError(e.message))
			.finally(() => setLoading(false));
	}, []);

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] p-8">
				<h1 className="text-3xl font-bold text-white mb-8">Missions</h1>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{[1, 2, 3].map((i) => (
						<SkeletonCard key={i} />
					))}
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<p className="text-red-400">Failed to load missions: {error}</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-7xl mx-auto">
				<FadeInUp>
				<h1 className="text-3xl font-bold text-white mb-2">Available Missions</h1>
				<p className="text-[#A1A1AA] mb-8">Choose your operation and begin the quest.</p>
				</FadeInUp>

				{courses.length === 0 ? (
					<div className="text-center py-20">
						<p className="text-[#A1A1AA] text-lg">No missions available yet.</p>
					</div>
				) : (
					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
						{courses.map((course) => (
							<Link key={course.id} href={`/missions/${course.id}`}>
								<div className="group relative rounded-2xl border border-[#2A2A2E] bg-[#141416] p-6 transition-all duration-300 hover:border-[#6366F1]/50 hover:shadow-lg hover:shadow-[#6366F1]/5 cursor-pointer">
									{/* Cover image */}
									{course.cover_image_url && (
										<div className="mb-4 h-32 rounded-xl overflow-hidden">
											<img
												src={course.cover_image_url}
												alt={course.title}
												className="w-full h-full object-cover"
											/>
										</div>
									)}

									{/* Narrative title */}
									{course.narrative_title && (
										<p className="text-xs font-mono text-[#6366F1] uppercase tracking-wider mb-2">
											{course.narrative_title}
										</p>
									)}

									{/* Title */}
									<h2 className="text-xl font-semibold text-white mb-2 group-hover:text-[#6366F1] transition-colors">
										{course.title}
									</h2>

									{/* Description */}
									{course.description && (
										<p className="text-sm text-[#A1A1AA] line-clamp-3 mb-4">
											{course.description}
										</p>
									)}

									{/* Footer */}
									<div className="flex items-center justify-between mt-auto pt-4 border-t border-[#2A2A2E]">
										{course.persona_name && (
											<span className="text-xs font-mono text-[#3B82F6]">
												GM: {course.persona_name}
											</span>
										)}
										<span className="text-xs text-[#22C55E] font-medium">
											Available
										</span>
									</div>
								</div>
							</Link>
						))}
					</div>
				)}
			</div>
		</div>
	);
}
