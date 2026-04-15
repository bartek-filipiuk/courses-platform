"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";

interface Artifact {
	id: string;
	name: string;
	description: string | null;
	icon_url: string | null;
	quest_title: string;
	acquired_at: string;
}

export default function InventoryPage() {
	const [artifacts, setArtifacts] = useState<Artifact[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		apiClient<Artifact[]>("/api/users/me/artifacts", { token: "demo" })
			.then(setArtifacts)
			.catch(console.error)
			.finally(() => setLoading(false));
	}, []);

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] p-8">
				<h1 className="text-3xl font-bold text-white mb-8">Inventory</h1>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{[1, 2, 3].map((i) => (
						<div key={i} className="h-32 rounded-2xl bg-[#141416] animate-pulse" />
					))}
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-5xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Inventory</h1>
				<p className="text-[#A1A1AA] mb-8">Artifacts collected from completed quests.</p>

				{artifacts.length === 0 ? (
					<div className="text-center py-20 border border-dashed border-[#2A2A2E] rounded-2xl">
						<p className="text-[#A1A1AA] text-lg">No artifacts yet.</p>
						<p className="text-[#A1A1AA]/60 text-sm mt-1">Complete quests to earn artifacts.</p>
					</div>
				) : (
					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{artifacts.map((artifact) => (
							<div
								key={artifact.id}
								className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-5 hover:border-[#F59E0B]/50 transition-colors"
							>
								<div className="flex items-start gap-3">
									<div className="w-10 h-10 rounded-xl bg-[#F59E0B]/20 flex items-center justify-center shrink-0">
										<span className="text-lg">🏆</span>
									</div>
									<div>
										<h3 className="text-white font-semibold text-sm">{artifact.name}</h3>
										{artifact.description && (
											<p className="text-[#A1A1AA] text-xs mt-1 line-clamp-2">{artifact.description}</p>
										)}
									</div>
								</div>
								<div className="mt-3 pt-3 border-t border-[#2A2A2E] flex justify-between">
									<span className="text-xs text-[#A1A1AA] font-mono">{artifact.quest_title}</span>
									<span className="text-xs text-[#A1A1AA]">
										{new Date(artifact.acquired_at).toLocaleDateString()}
									</span>
								</div>
							</div>
						))}
					</div>
				)}
			</div>
		</div>
	);
}
