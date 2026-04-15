"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";

interface CommsEntry {
	id: string;
	quest_id: string | null;
	message_type: string;
	content: string;
	created_at: string;
}

const TYPE_COLORS: Record<string, string> = {
	briefing: "text-[#3B82F6]",
	evaluation: "text-[#22C55E]",
	hint: "text-[#F59E0B]",
	system: "text-[#A1A1AA]",
};

const TYPE_LABELS: Record<string, string> = {
	briefing: "BRIEFING",
	evaluation: "EVAL",
	hint: "HINT",
	system: "SYS",
};

export default function CommsLogPage() {
	const [entries, setEntries] = useState<CommsEntry[]>([]);
	const [loading, setLoading] = useState(true);
	const [filter, setFilter] = useState<string>("");

	useEffect(() => {
		const params = new URLSearchParams({ per_page: "100" });
		if (filter) params.set("message_type", filter);

		// TODO: get courseId from context/route
		apiClient<{ items: CommsEntry[] }>(`/api/courses/demo/comms-log?${params}`, { token: "demo" })
			.then((res) => setEntries(res.items))
			.catch(() => setEntries([]))
			.finally(() => setLoading(false));
	}, [filter]);

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-4xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Comms Log</h1>
				<p className="text-[#A1A1AA] mb-6">Communication history with Game Master.</p>

				{/* Filters */}
				<div className="flex gap-2 mb-6">
					{["", "briefing", "evaluation", "hint", "system"].map((t) => (
						<button
							key={t}
							type="button"
							onClick={() => setFilter(t)}
							className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${
								filter === t
									? "bg-[#6366F1] text-white"
									: "text-[#A1A1AA] bg-[#141416] hover:text-white"
							}`}
						>
							{t || "All"}
						</button>
					))}
				</div>

				{/* Terminal-style log */}
				<div className="rounded-2xl border border-[#2A2A2E] bg-[#0A0A0B] p-1">
					<div className="bg-[#141416] rounded-xl p-4 font-mono text-sm max-h-[600px] overflow-y-auto space-y-3">
						{loading ? (
							<div className="text-[#A1A1AA] animate-pulse">Loading transmissions...</div>
						) : entries.length === 0 ? (
							<div className="text-[#A1A1AA]">No transmissions yet.</div>
						) : (
							entries.map((entry) => (
								<div key={entry.id} className="flex gap-3">
									<span className="text-[#A1A1AA] text-xs shrink-0 pt-0.5 w-16">
										{new Date(entry.created_at).toLocaleTimeString("en", { hour12: false })}
									</span>
									<span className={`text-xs font-bold shrink-0 w-12 pt-0.5 ${TYPE_COLORS[entry.message_type] || "text-white"}`}>
										[{TYPE_LABELS[entry.message_type] || entry.message_type}]
									</span>
									<span className="text-[#FAFAFA] whitespace-pre-wrap">{entry.content}</span>
								</div>
							))
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
