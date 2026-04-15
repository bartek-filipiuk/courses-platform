"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useAuthFetch, useAuthMutate } from "@/lib/use-api";
import { Button, Input, Textarea } from "@/components/ui";
import GlassCard from "@/components/GlassCard";

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
			<div className="min-h-screen bg-bg-base flex items-center justify-center">
				<div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	if (!quest) {
		return (
			<div className="min-h-screen bg-bg-base flex items-center justify-center">
				<p className="text-accent-error">Quest not found or locked.</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-4xl mx-auto">
				{/* Briefing */}
				<div className="mb-8">
					<div className="flex items-center gap-2 mb-4">
						{quest.skills.map((s) => (
							<span key={s} className="px-2 py-0.5 text-xs bg-accent-primary/20 text-accent-primary rounded-full">{s}</span>
						))}
					</div>
					<h1 className="text-3xl font-bold text-text-primary mb-4">{quest.title}</h1>
					<GlassCard>
						<pre className="font-mono text-sm text-accent-success whitespace-pre-wrap leading-relaxed">
							{quest.briefing}
						</pre>
					</GlassCard>
				</div>

				{/* Submit form */}
				<GlassCard className="mb-6">
					<h2 className="text-lg font-semibold text-text-primary mb-4">Submit Answer</h2>

					{quest.evaluation_type === "text_answer" && (
						<Textarea rows={6} value={answer} onChange={(e) => setAnswer(e.target.value)} className="font-mono text-sm" placeholder="Your answer..." />
					)}

					{quest.evaluation_type === "url_check" && (
						<Input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://your-app.com/api/health" />
					)}

					{quest.evaluation_type === "quiz" && (
						<Input type="text" value={selectedOption} onChange={(e) => setSelectedOption(e.target.value)} placeholder="Option ID (e.g. opt_1)" />
					)}

					{quest.evaluation_type === "command_output" && (
						<div className="space-y-3">
							<Input type="text" value={command} onChange={(e) => setCommand(e.target.value)} placeholder="Command (e.g. docker ps)" />
							<Textarea rows={4} value={output} onChange={(e) => setOutput(e.target.value)} className="font-mono text-sm" placeholder="Paste command output..." />
						</div>
					)}

					<div className="flex gap-3 mt-4">
						<Button variant="primary" size="lg" onClick={handleSubmit} loading={submitting}>
							{submitting ? "Evaluating..." : "Submit"}
						</Button>
						<Button variant="secondary" size="lg" onClick={handleHint} disabled={hintLoading}>
							{hintLoading ? "..." : `Hint (${quest.max_hints} left)`}
						</Button>
					</div>
				</GlassCard>

				{/* Hint */}
				{hintText && (
					<div className="rounded-2xl border border-accent-warning/30 bg-accent-warning/5 p-6 mb-6">
						<p className="text-sm font-mono text-accent-warning">{hintText}</p>
					</div>
				)}

				{/* Result / Feedback */}
				{result && (
					<div className={`rounded-2xl border p-6 ${result.passed ? "border-accent-success/30 bg-accent-success/5" : "border-accent-error/30 bg-accent-error/5"}`}>
						<div className="flex items-center gap-3 mb-4">
							<span className={`text-2xl ${result.passed ? "text-accent-success" : "text-accent-error"}`}>
								{result.passed ? "PASS" : "FAIL"}
							</span>
							{result.execution_time_ms && (
								<span className="text-xs text-text-secondary">{result.execution_time_ms}ms</span>
							)}
						</div>

						<pre className="font-mono text-sm text-text-primary whitespace-pre-wrap leading-relaxed mb-4">
							{result.narrative_response}
						</pre>

						{result.passed && result.quality_scores && (
							<div className="grid grid-cols-4 gap-3 pt-4 border-t border-border-default">
								{Object.entries(result.quality_scores).map(([key, value]) => (
									<div key={key} className="text-center">
										<div className="text-2xl font-bold text-text-primary">{value}</div>
										<div className="text-xs text-text-secondary capitalize">{key}</div>
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
