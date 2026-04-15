"use client";

import { useState } from "react";
import { useAuthMutate } from "@/lib/use-api";

interface Analytics {
	course_id: string;
	state_distribution: Record<string, number>;
	avg_attempts_to_complete: number;
	total_hints_used: number;
	total_submissions: number;
}

export default function AdminAnalyticsPage() {
	const [courseId, setCourseId] = useState("");
	const [analytics, setAnalytics] = useState<Analytics | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const mutate = useAuthMutate("admin");

	const loadAnalytics = async () => {
		if (!courseId) return;
		setLoading(true);
		setError(null);
		try {
			const data = await mutate<Analytics>(`/api/admin/analytics/${courseId}`);
			setAnalytics(data);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load");
		} finally {
			setLoading(false);
		}
	};

	const inputClass = "w-full rounded-xl border border-[#2A2A2E] bg-[#0A0A0B] px-4 py-3 text-white placeholder-[#A1A1AA]/50 focus:border-[#6366F1] focus:outline-none";

	const STATE_COLORS: Record<string, string> = {
		COMPLETED: "bg-[#22C55E]",
		IN_PROGRESS: "bg-[#3B82F6]",
		AVAILABLE: "bg-[#6366F1]",
		LOCKED: "bg-[#2A2A2E]",
		FAILED_ATTEMPT: "bg-[#F59E0B]",
		EVALUATING: "bg-[#F59E0B]/50",
	};

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-4xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Course Analytics</h1>
				<p className="text-[#A1A1AA] mb-6">View metrics for a course.</p>

				<div className="flex gap-3 mb-8">
					<input
						type="text"
						value={courseId}
						onChange={(e) => setCourseId(e.target.value)}
						className={inputClass}
						placeholder="Course UUID"
					/>
					<button
						type="button"
						onClick={loadAnalytics}
						disabled={loading || !courseId}
						className="px-6 py-3 rounded-xl bg-[#6366F1] text-white font-medium hover:bg-[#5558E6] disabled:opacity-50 shrink-0"
					>
						{loading ? "Loading..." : "Load"}
					</button>
				</div>

				{error && <p className="text-red-400 mb-4">{error}</p>}

				{analytics && (
					<div className="space-y-6">
						{/* Key metrics */}
						<div className="grid grid-cols-3 gap-4">
							<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 text-center">
								<p className="text-3xl font-bold text-white">{analytics.total_submissions}</p>
								<p className="text-xs text-[#A1A1AA] mt-1">Total Submissions</p>
							</div>
							<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 text-center">
								<p className="text-3xl font-bold text-white">{analytics.avg_attempts_to_complete}</p>
								<p className="text-xs text-[#A1A1AA] mt-1">Avg Attempts to Pass</p>
							</div>
							<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 text-center">
								<p className="text-3xl font-bold text-white">{analytics.total_hints_used}</p>
								<p className="text-xs text-[#A1A1AA] mt-1">Total Hints Used</p>
							</div>
						</div>

						{/* State distribution */}
						<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5">
							<p className="text-sm text-[#A1A1AA] mb-4">Quest State Distribution</p>
							<div className="space-y-2">
								{Object.entries(analytics.state_distribution).map(([state, count]) => {
									const total = Object.values(analytics.state_distribution).reduce((a, b) => a + b, 0);
									const pct = total > 0 ? (count / total) * 100 : 0;
									return (
										<div key={state} className="flex items-center gap-3">
											<span className="text-xs text-[#A1A1AA] w-32 font-mono">{state}</span>
											<div className="flex-1 h-5 bg-[#1C1C1F] rounded-full overflow-hidden">
												<div
													className={`h-full rounded-full ${STATE_COLORS[state] || "bg-[#6366F1]"}`}
													style={{ width: `${pct}%` }}
												/>
											</div>
											<span className="text-sm text-white w-10 text-right">{count}</span>
										</div>
									);
								})}
							</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
