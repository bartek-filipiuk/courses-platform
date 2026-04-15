"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { getDevToken } from "@/lib/dev-auth";
import { cn } from "@/lib/utils";

interface CommsEntry {
	id: string;
	quest_id: string | null;
	message_type: string;
	content: string;
	created_at: string;
}

const TYPE_COLORS: Record<string, string> = {
	briefing: "text-accent-info",
	evaluation: "text-accent-success",
	hint: "text-accent-warning",
	system: "text-text-secondary",
};

const TYPE_LABELS: Record<string, string> = {
	briefing: "BRIEFING",
	evaluation: "EVAL",
	hint: "HINT",
	system: "SYS",
};

export default function CommsLogPage() {
	return (
		<Suspense fallback={<div className="min-h-screen bg-bg-base p-8"><div className="text-text-secondary animate-pulse">Loading...</div></div>}>
			<CommsLogContent />
		</Suspense>
	);
}

function CommsLogContent() {
	const searchParams = useSearchParams();
	const courseId = searchParams.get("courseId");
	const [entries, setEntries] = useState<CommsEntry[]>([]);
	const [loading, setLoading] = useState(true);
	const [filter, setFilter] = useState<string>("");

	useEffect(() => {
		if (!courseId) { setLoading(false); return; }
		const params = new URLSearchParams({ per_page: "100" });
		if (filter) params.set("message_type", filter);

		(async () => {
			try {
				const token = await getDevToken();
				const res = await apiClient<{ items: CommsEntry[] }>(
					`/api/courses/${courseId}/comms-log?${params}`, { token }
				);
				setEntries(res.items);
			} catch { setEntries([]); }
			finally { setLoading(false); }
		})();
	}, [filter, courseId]);

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-4xl mx-auto">
				<h1 className="text-3xl font-bold text-text-primary mb-2">Comms Log</h1>
				<p className="text-text-secondary mb-6">Communication history with Game Master.</p>

				{/* Filters */}
				<div className="flex gap-2 mb-6">
					{["", "briefing", "evaluation", "hint", "system"].map((t) => (
						<button
							key={t}
							type="button"
							onClick={() => setFilter(t)}
							className={cn(
								"px-3 py-1.5 text-xs rounded-lg font-medium transition-colors",
								filter === t
									? "bg-accent-primary text-text-on-accent"
									: "text-text-secondary bg-bg-elevated hover:text-text-primary"
							)}
						>
							{t || "All"}
						</button>
					))}
				</div>

				{/* Terminal-style log */}
				<div className="rounded-2xl border border-border-default bg-bg-base p-1">
					<div className="bg-bg-elevated rounded-xl p-4 font-mono text-sm max-h-[600px] overflow-y-auto space-y-3">
						{loading ? (
							<div className="text-text-secondary animate-pulse">Loading transmissions...</div>
						) : entries.length === 0 ? (
							<div className="text-text-secondary">No transmissions yet.</div>
						) : (
							entries.map((entry) => (
								<div key={entry.id} className="flex gap-3">
									<span className="text-text-secondary text-xs shrink-0 pt-0.5 w-16">
										{new Date(entry.created_at).toLocaleTimeString("en", { hour12: false })}
									</span>
									<span className={cn("text-xs font-bold shrink-0 w-12 pt-0.5", TYPE_COLORS[entry.message_type] || "text-text-primary")}>
										[{TYPE_LABELS[entry.message_type] || entry.message_type}]
									</span>
									<span className="text-text-primary whitespace-pre-wrap">{entry.content}</span>
								</div>
							))
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
