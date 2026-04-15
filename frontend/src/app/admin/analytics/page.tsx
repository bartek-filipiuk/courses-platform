"use client";

import { useState } from "react";
import { useAuthMutate } from "@/lib/use-api";
import { Button, Input } from "@/components/ui";

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

	const STATE_COLORS: Record<string, string> = {
		COMPLETED: "bg-accent-success",
		IN_PROGRESS: "bg-accent-info",
		AVAILABLE: "bg-accent-primary",
		LOCKED: "bg-border-default",
		FAILED_ATTEMPT: "bg-accent-warning",
		EVALUATING: "bg-accent-warning/50",
	};

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-4xl mx-auto">
				<h1 className="text-3xl font-bold text-text-primary mb-2">Course Analytics</h1>
				<p className="text-text-secondary mb-6">View metrics for a course.</p>

				<div className="flex gap-3 mb-8">
					<Input
						type="text"
						value={courseId}
						onChange={(e) => setCourseId(e.target.value)}
						placeholder="Course UUID"
					/>
					<Button
						type="button"
						onClick={loadAnalytics}
						disabled={loading || !courseId}
						size="lg"
						loading={loading}
						className="shrink-0"
					>
						{loading ? "Loading..." : "Load"}
					</Button>
				</div>

				{error && <p className="text-accent-error mb-4">{error}</p>}

				{analytics && (
					<div className="space-y-6">
						{/* Key metrics */}
						<div className="grid grid-cols-3 gap-4">
							<div className="rounded-2xl border border-border-default bg-bg-elevated p-5 text-center">
								<p className="text-3xl font-bold text-text-primary">{analytics.total_submissions}</p>
								<p className="text-xs text-text-secondary mt-1">Total Submissions</p>
							</div>
							<div className="rounded-2xl border border-border-default bg-bg-elevated p-5 text-center">
								<p className="text-3xl font-bold text-text-primary">{analytics.avg_attempts_to_complete}</p>
								<p className="text-xs text-text-secondary mt-1">Avg Attempts to Pass</p>
							</div>
							<div className="rounded-2xl border border-border-default bg-bg-elevated p-5 text-center">
								<p className="text-3xl font-bold text-text-primary">{analytics.total_hints_used}</p>
								<p className="text-xs text-text-secondary mt-1">Total Hints Used</p>
							</div>
						</div>

						{/* State distribution */}
						<div className="rounded-2xl border border-border-default bg-bg-elevated p-5">
							<p className="text-sm text-text-secondary mb-4">Quest State Distribution</p>
							<div className="space-y-2">
								{Object.entries(analytics.state_distribution).map(([state, count]) => {
									const total = Object.values(analytics.state_distribution).reduce((a, b) => a + b, 0);
									const pct = total > 0 ? (count / total) * 100 : 0;
									return (
										<div key={state} className="flex items-center gap-3">
											<span className="text-xs text-text-secondary w-32 font-mono">{state}</span>
											<div className="flex-1 h-5 bg-bg-surface-active rounded-full overflow-hidden">
												<div
													className={`h-full rounded-full ${STATE_COLORS[state] || "bg-accent-primary"}`}
													style={{ width: `${pct}%` }}
												/>
											</div>
											<span className="text-sm text-text-primary w-10 text-right">{count}</span>
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
