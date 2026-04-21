"use client";

import Link from "next/link";
import { Map, Trophy } from "lucide-react";
import { useAuthFetch } from "@/lib/use-api";
import GlassCard from "@/components/GlassCard";
import { FadeInUp, StaggerContainer, StaggerItem } from "@/lib/motion";

interface Enrollment {
	course_id: string;
	title: string;
	narrative_title: string | null;
	persona_name: string | null;
	cover_image_url: string | null;
	enrolled_at: string;
	total_quests: number;
	completed_quests: number;
	progress_pct: number;
}

export default function MyCoursesPage() {
	const { data: enrollments, loading } = useAuthFetch<Enrollment[]>("/api/users/me/enrollments");

	if (loading) {
		return (
			<div className="min-h-screen bg-bg-base p-8">
				<h1 className="text-3xl font-bold text-text-primary mb-8">My Courses</h1>
				<div className="space-y-4">
					{[1, 2].map((i) => (
						<div key={i} className="h-24 rounded-2xl bg-bg-elevated animate-pulse" />
					))}
				</div>
			</div>
		);
	}

	const items = enrollments || [];

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-4xl mx-auto">
				<FadeInUp>
					<h1 className="text-3xl font-bold text-text-primary mb-2">My Courses</h1>
					<p className="text-text-secondary mb-8">Your active operations.</p>
				</FadeInUp>

				{items.length === 0 ? (
					<div className="text-center py-20 border border-dashed border-border-default rounded-2xl">
						<p className="text-text-secondary text-lg">No enrollments yet.</p>
						<Link href="/missions" className="text-accent-primary hover:underline mt-2 inline-block">
							Browse missions
						</Link>
					</div>
				) : (
					<StaggerContainer className="space-y-4">
						{items.map((e) => (
							<StaggerItem key={e.course_id}>
								<GlassCard variant="interactive" className="flex items-center gap-6">
									<div className="flex-1">
										{e.narrative_title && (
											<p className="text-xs font-mono text-accent-primary uppercase tracking-wider mb-1">
												{e.narrative_title}
											</p>
										)}
										<h2 className="text-lg font-semibold text-text-primary">{e.title}</h2>
										<div className="flex items-center gap-4 mt-2">
											{e.persona_name && (
												<span className="text-xs text-text-secondary">GM: {e.persona_name}</span>
											)}
											<span className="text-xs text-text-secondary">
												{e.completed_quests}/{e.total_quests} quests
											</span>
										</div>
										{/* Progress bar */}
										<div className="mt-3 h-2 bg-bg-surface-active rounded-full overflow-hidden w-64">
											<div
												className="h-full bg-gradient-to-r from-accent-primary to-accent-success rounded-full transition-all"
												style={{ width: `${e.progress_pct}%` }}
											/>
										</div>
									</div>
									<div className="flex gap-2 shrink-0">
										<Link
											href={`/quest-map?courseId=${e.course_id}`}
											className="p-3 rounded-xl bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-colors"
											title="Quest Map"
										>
											<Map className="w-5 h-5" />
										</Link>
										<Link
											href={`/inventory`}
											className="p-3 rounded-xl bg-accent-warning/10 text-accent-warning hover:bg-accent-warning/20 transition-colors"
											title="Inventory"
										>
											<Trophy className="w-5 h-5" />
										</Link>
									</div>
								</GlassCard>
							</StaggerItem>
						))}
					</StaggerContainer>
				)}
			</div>
		</div>
	);
}
