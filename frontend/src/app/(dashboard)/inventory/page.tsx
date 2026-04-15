"use client";

import { Trophy } from "lucide-react";
import { useAuthFetch } from "@/lib/use-api";

interface Artifact {
	id: string;
	name: string;
	description: string | null;
	icon_url: string | null;
	quest_title: string;
	acquired_at: string;
}

export default function InventoryPage() {
	const { data: artifacts, loading } = useAuthFetch<Artifact[]>("/api/users/me/artifacts");

	if (loading) {
		return (
			<div className="min-h-screen bg-bg-base p-8">
				<h1 className="text-3xl font-bold text-text-primary mb-8">Inventory</h1>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{[1, 2, 3].map((i) => (
						<div key={i} className="h-32 rounded-2xl bg-bg-elevated animate-pulse" />
					))}
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-5xl mx-auto">
				<h1 className="text-3xl font-bold text-text-primary mb-2">Inventory</h1>
				<p className="text-text-secondary mb-8">Artifacts collected from completed quests.</p>

				{(artifacts || []).length === 0 ? (
					<div className="text-center py-20 border border-dashed border-border-default rounded-2xl">
						<p className="text-text-secondary text-lg">No artifacts yet.</p>
						<p className="text-text-muted text-sm mt-1">Complete quests to earn artifacts.</p>
					</div>
				) : (
					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{(artifacts || []).map((artifact) => (
							<div
								key={artifact.id}
								className="rounded-2xl border border-border-default bg-bg-elevated p-5 hover:border-accent-warning/50 transition-all duration-200 cursor-pointer hover:translate-y-[-1px]"
							>
								<div className="flex items-start gap-3">
									<div className="w-10 h-10 rounded-xl bg-accent-warning/20 flex items-center justify-center shrink-0">
										<Trophy className="w-5 h-5 text-accent-warning" />
									</div>
									<div>
										<h3 className="text-text-primary font-semibold text-sm">{artifact.name}</h3>
										{artifact.description && (
											<p className="text-text-secondary text-xs mt-1 line-clamp-2">{artifact.description}</p>
										)}
									</div>
								</div>
								<div className="mt-3 pt-3 border-t border-border-default flex justify-between">
									<span className="text-xs text-text-secondary font-mono">{artifact.quest_title}</span>
									<span className="text-xs text-text-secondary">
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
