"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useAuthFetch, useAuthMutate } from "@/lib/use-api";

interface QuestBriefing {
	id: string;
	title: string;
	briefing: string;
	evaluation_type: string;
	max_hints: number;
	skills: string[];
}

interface EvalResult {
	passed: boolean;
	narrative_response: string;
	quality_scores: Record<string, number> | null;
	execution_time_ms: number | null;
}

export default function QuestPage() {
	const params = useParams();
	const questId = params.questId as string;
	const { data: quest, loading } = useAuthFetch<QuestBriefing>(`/api/quests/${questId}/briefing`);
	const mutate = useAuthMutate();

	const [submitting, setSubmitting] = useState(false);
	const [result, setResult] = useState<EvalResult | null>(null);
	const [answer, setAnswer] = useState("");
	const [selectedOption, setSelectedOption] = useState("");
	const [url, setUrl] = useState("");
	const [command, setCommand] = useState("");
	const [output, setOutput] = useState("");
	const [hintText, setHintText] = useState<string | null>(null);
	const [hintLoading, setHintLoading] = useState(false);

	const handleSubmit = async () => {
		if (!quest) return;
		setSubmitting(true);
		setResult(null);

		let payload: Record<string, unknown> = {};
		if (quest.evaluation_type === "text_answer") payload = { answer };
		else if (quest.evaluation_type === "url_check") payload = { url };
		else if (quest.evaluation_type === "quiz") payload = { selected_option_id: selectedOption };
		else if (quest.evaluation_type === "command_output") payload = { command, output };

		try {
			const res = await mutate<EvalResult>(`/api/quests/${questId}/submit`, {
				method: "POST",
				body: { type: quest.evaluation_type, payload },
			});
			setResult(res);
		} catch (e) {
			setResult({
				passed: false,
				narrative_response: e instanceof Error ? e.message : "Submission failed",
				quality_scores: null,
				execution_time_ms: null,
			});
		} finally {
			setSubmitting(false);
		}
	};

	const handleHint = async () => {
		setHintLoading(true);
		try {
			const res = await mutate<{ hint: string }>(`/api/quests/${questId}/hint`, {
				method: "POST",
				body: { context: answer || url || output || "" },
			});
			setHintText(res.hint);
		} catch {
			setHintText("Unable to get hint right now.");
		} finally {
			setHintLoading(false);
		}
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<div className="w-8 h-8 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	if (!quest) {
		return (
			<div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
				<p className="text-red-400">Quest not found or locked.</p>
			</div>
		);
	}

	const inputClass = "w-full rounded-xl border border-[#2A2A2E] bg-[#0A0A0B] px-4 py-3 text-white placeholder-[#A1A1AA]/50 focus:border-[#6366F1] focus:outline-none transition-colors";

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-4xl mx-auto">
				{/* Briefing */}
				<div className="mb-8">
					<div className="flex items-center gap-2 mb-4">
						{quest.skills.map((s) => (
							<span key={s} className="px-2 py-0.5 text-xs bg-[#6366F1]/20 text-[#6366F1] rounded-full">{s}</span>
						))}
					</div>
					<h1 className="text-3xl font-bold text-white mb-4">{quest.title}</h1>
					<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-6">
						<pre className="font-mono text-sm text-[#22C55E] whitespace-pre-wrap leading-relaxed">
							{quest.briefing}
						</pre>
					</div>
				</div>

				{/* Submit form */}
				<div className="rounded-2xl border border-[#2A2A2E] bg-[#141416] p-6 mb-6">
					<h2 className="text-lg font-semibold text-white mb-4">Submit Answer</h2>

					{quest.evaluation_type === "text_answer" && (
						<textarea rows={6} value={answer} onChange={(e) => setAnswer(e.target.value)} className={`${inputClass} font-mono text-sm`} placeholder="Your answer..." />
					)}

					{quest.evaluation_type === "url_check" && (
						<input type="url" value={url} onChange={(e) => setUrl(e.target.value)} className={inputClass} placeholder="https://your-app.com/api/health" />
					)}

					{quest.evaluation_type === "quiz" && (
						<input type="text" value={selectedOption} onChange={(e) => setSelectedOption(e.target.value)} className={inputClass} placeholder="Option ID (e.g. opt_1)" />
					)}

					{quest.evaluation_type === "command_output" && (
						<div className="space-y-3">
							<input type="text" value={command} onChange={(e) => setCommand(e.target.value)} className={inputClass} placeholder="Command (e.g. docker ps)" />
							<textarea rows={4} value={output} onChange={(e) => setOutput(e.target.value)} className={`${inputClass} font-mono text-sm`} placeholder="Paste command output..." />
						</div>
					)}

					<div className="flex gap-3 mt-4">
						<button type="button" onClick={handleSubmit} disabled={submitting}
							className="px-6 py-3 rounded-xl bg-[#6366F1] text-white font-medium hover:bg-[#5558E6] disabled:opacity-50 transition-all">
							{submitting ? "Evaluating..." : "Submit"}
						</button>
						<button type="button" onClick={handleHint} disabled={hintLoading}
							className="px-6 py-3 rounded-xl border border-[#2A2A2E] text-[#A1A1AA] hover:text-white hover:bg-[#1C1C1F] disabled:opacity-50 transition-all">
							{hintLoading ? "..." : `Hint (${quest.max_hints} left)`}
						</button>
					</div>
				</div>

				{/* Hint */}
				{hintText && (
					<div className="rounded-2xl border border-[#F59E0B]/30 bg-[#F59E0B]/5 p-6 mb-6">
						<p className="text-sm font-mono text-[#F59E0B]">{hintText}</p>
					</div>
				)}

				{/* Result / Feedback */}
				{result && (
					<div className={`rounded-2xl border p-6 ${result.passed ? "border-[#22C55E]/30 bg-[#22C55E]/5" : "border-red-500/30 bg-red-500/5"}`}>
						<div className="flex items-center gap-3 mb-4">
							<span className={`text-2xl ${result.passed ? "text-[#22C55E]" : "text-red-400"}`}>
								{result.passed ? "PASS" : "FAIL"}
							</span>
							{result.execution_time_ms && (
								<span className="text-xs text-[#A1A1AA]">{result.execution_time_ms}ms</span>
							)}
						</div>

						<pre className="font-mono text-sm text-[#FAFAFA] whitespace-pre-wrap leading-relaxed mb-4">
							{result.narrative_response}
						</pre>

						{result.passed && result.quality_scores && (
							<div className="grid grid-cols-4 gap-3 pt-4 border-t border-[#2A2A2E]">
								{Object.entries(result.quality_scores).map(([key, value]) => (
									<div key={key} className="text-center">
										<div className="text-2xl font-bold text-white">{value}</div>
										<div className="text-xs text-[#A1A1AA] capitalize">{key}</div>
									</div>
								))}
							</div>
						)}
					</div>
				)}
			</div>
		</div>
	);
}
