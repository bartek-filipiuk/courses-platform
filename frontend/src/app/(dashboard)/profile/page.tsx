"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";

interface UserStats {
	total_quests: number;
	completed: number;
	in_progress: number;
	progress_pct: number;
	total_attempts: number;
	total_hints_used: number;
	quality_scores: Record<string, number> | null;
	streak_days: number;
}

export default function ProfilePage() {
	const [stats, setStats] = useState<UserStats | null>(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		apiClient<UserStats>("/api/users/me/stats", { token: "demo" })
			.then(setStats)
			.catch(console.error)
			.finally(() => setLoading(false));
	}, []);

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] p-8">
				<h1 className="text-3xl font-bold text-white mb-8">Profile</h1>
				<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
					{[1, 2, 3, 4].map((i) => (
						<div key={i} className="h-24 rounded-2xl bg-[#141416] animate-pulse" />
					))}
				</div>
			</div>
		);
	}

	if (!stats) return null;

	const statCards = [
		{ label: "Progress", value: `${stats.progress_pct}%`, sub: `${stats.completed}/${stats.total_quests} quests` },
		{ label: "Streak", value: `${stats.streak_days}`, sub: "days" },
		{ label: "Attempts", value: `${stats.total_attempts}`, sub: "total submissions" },
		{ label: "Hints", value: `${stats.total_hints_used}`, sub: "hints used" },
	];

	const qualityDims = stats.quality_scores
		? Object.entries(stats.quality_scores)
		: [];

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-5xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Profile</h1>
				<p className="text-[#A1A1AA] mb-8">Your mission statistics.</p>

				{/* Stat cards */}
				<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
					{statCards.map((card) => (
						<div key={card.label} className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5">
							<p className="text-xs text-[#A1A1AA] uppercase tracking-wider mb-1">{card.label}</p>
							<p className="text-3xl font-bold text-white">{card.value}</p>
							<p className="text-xs text-[#A1A1AA] mt-1">{card.sub}</p>
						</div>
					))}
				</div>

				{/* Progress bar */}
				<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 mb-8">
					<p className="text-sm text-[#A1A1AA] mb-3">Overall Progress</p>
					<div className="h-3 bg-[#1C1C1F] rounded-full overflow-hidden">
						<div
							className="h-full bg-gradient-to-r from-[#6366F1] to-[#22C55E] rounded-full transition-all duration-700"
							style={{ width: `${stats.progress_pct}%` }}
						/>
					</div>
					<div className="flex justify-between mt-2 text-xs text-[#A1A1AA]">
						<span>{stats.completed} completed</span>
						<span>{stats.in_progress} in progress</span>
						<span>{stats.total_quests - stats.completed - stats.in_progress} remaining</span>
					</div>
				</div>

				{/* Quality scores */}
				{qualityDims.length > 0 && (
					<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5">
						<p className="text-sm text-[#A1A1AA] mb-4">Quality Scores (avg)</p>
						<div className="grid grid-cols-4 gap-4">
							{qualityDims.map(([dim, val]) => (
								<div key={dim} className="text-center">
									<div className="relative w-16 h-16 mx-auto mb-2">
										<svg viewBox="0 0 36 36" className="w-full h-full">
											<path
												d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
												fill="none"
												stroke="#1C1C1F"
												strokeWidth="3"
											/>
											<path
												d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
												fill="none"
												stroke="#6366F1"
												strokeWidth="3"
												strokeDasharray={`${val * 10}, 100`}
												strokeLinecap="round"
											/>
										</svg>
										<span className="absolute inset-0 flex items-center justify-center text-white font-bold text-sm">
											{val}
										</span>
									</div>
									<p className="text-xs text-[#A1A1AA] capitalize">{dim}</p>
								</div>
							))}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
