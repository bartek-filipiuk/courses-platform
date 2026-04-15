"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useAuthMutate } from "@/lib/use-api";
import { Button, Input, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";

interface QuestForm {
	course_id: string;
	sort_order: number;
	title: string;
	briefing: string;
	evaluation_type: string;
	skills: string;
	success_response: string;
	max_hints: number;
	artifact_name: string;
	artifact_description: string;
}

const EMPTY_FORM: QuestForm = {
	course_id: "",
	sort_order: 0,
	title: "",
	briefing: "",
	evaluation_type: "text_answer",
	skills: "",
	success_response: "",
	max_hints: 3,
	artifact_name: "",
	artifact_description: "",
};

const EVAL_TYPES = [
	{ value: "text_answer", label: "Text Answer (LLM Judge)" },
	{ value: "url_check", label: "URL Check (HTTP)" },
	{ value: "quiz", label: "Quiz (Deterministic)" },
	{ value: "command_output", label: "Command Output (Pattern + LLM)" },
];

export default function AdminQuestsPage() {
	const [form, setForm] = useState<QuestForm>(EMPTY_FORM);
	const [tab, setTab] = useState<"story" | "tech" | "artifact">("story");
	const [saving, setSaving] = useState(false);
	const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
	const mutate = useAuthMutate("admin");

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setSaving(true);
		setMessage(null);
		try {
			const body: Record<string, unknown> = {
				course_id: form.course_id,
				sort_order: form.sort_order,
				title: form.title,
				briefing: form.briefing,
				evaluation_type: form.evaluation_type,
				skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
				success_response: form.success_response || undefined,
				max_hints: form.max_hints,
			};
			if (form.artifact_name) {
				body.artifact_name = form.artifact_name;
				body.artifact_description = form.artifact_description || undefined;
			}
			await mutate("/api/admin/quests", { method: "POST", body });
			toast.success("Quest created!");
			setForm(EMPTY_FORM);
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to create quest");
		} finally {
			setSaving(false);
		}
	};

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-3xl mx-auto">
				<h1 className="text-3xl font-bold text-text-primary mb-2">Create Quest</h1>
				<p className="text-text-secondary mb-6">Add a new quest to a course.</p>

				{message && (
					<div className={cn(
						"mb-6 p-4 rounded-xl border",
						message.type === "success"
							? "border-accent-success/30 bg-accent-success/10 text-accent-success"
							: "border-accent-error/30 bg-accent-error/10 text-accent-error",
					)}>
						{message.text}
					</div>
				)}

				{/* Tabs */}
				<div className="flex gap-2 mb-6">
					<button
						type="button"
						className={cn(
							"px-4 py-2 text-sm font-medium rounded-lg transition-colors",
							tab === "story"
								? "bg-accent-primary text-text-on-accent"
								: "text-text-secondary hover:text-text-primary",
						)}
						onClick={() => setTab("story")}
					>
						Story
					</button>
					<button
						type="button"
						className={cn(
							"px-4 py-2 text-sm font-medium rounded-lg transition-colors",
							tab === "tech"
								? "bg-accent-primary text-text-on-accent"
								: "text-text-secondary hover:text-text-primary",
						)}
						onClick={() => setTab("tech")}
					>
						Technical
					</button>
					<button
						type="button"
						className={cn(
							"px-4 py-2 text-sm font-medium rounded-lg transition-colors",
							tab === "artifact"
								? "bg-accent-primary text-text-on-accent"
								: "text-text-secondary hover:text-text-primary",
						)}
						onClick={() => setTab("artifact")}
					>
						Artifact
					</button>
				</div>

				<form onSubmit={handleSubmit} className="space-y-5">
					{tab === "story" && (
						<>
							<div>
								<label htmlFor="course_id" className="block text-sm text-text-secondary mb-2">Course ID *</label>
								<Input id="course_id" required value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} placeholder="UUID of the course" />
							</div>
							<div className="grid grid-cols-2 gap-4">
								<div>
									<label htmlFor="title" className="block text-sm text-text-secondary mb-2">Quest Title *</label>
									<Input id="title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Dark Network" />
								</div>
								<div>
									<label htmlFor="sort_order" className="block text-sm text-text-secondary mb-2">Order</label>
									<Input id="sort_order" type="number" min={0} value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} />
								</div>
							</div>
							<div>
								<label htmlFor="briefing" className="block text-sm text-text-secondary mb-2">Briefing (narrative) *</label>
								<Textarea id="briefing" required rows={6} value={form.briefing} onChange={(e) => setForm({ ...form, briefing: e.target.value })} className="font-mono text-sm" placeholder="Ghost — your mission..." />
							</div>
							<div>
								<label htmlFor="success_response" className="block text-sm text-text-secondary mb-2">Success Response</label>
								<Textarea id="success_response" rows={3} value={form.success_response} onChange={(e) => setForm({ ...form, success_response: e.target.value })} className="font-mono text-sm" placeholder="Good work, Ghost..." />
							</div>
						</>
					)}

					{tab === "tech" && (
						<>
							<div>
								<label htmlFor="evaluation_type" className="block text-sm text-text-secondary mb-2">Evaluation Type *</label>
								<select
									id="evaluation_type"
									value={form.evaluation_type}
									onChange={(e) => setForm({ ...form, evaluation_type: e.target.value })}
									className="w-full rounded-xl border border-border-default bg-bg-base px-4 py-3 text-text-primary placeholder:text-text-muted focus:border-border-active focus:outline-none transition-colors"
								>
									{EVAL_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
								</select>
							</div>
							<div>
								<label htmlFor="skills" className="block text-sm text-text-secondary mb-2">Skills (comma-separated)</label>
								<Input id="skills" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="REST API, Docker, SQL" />
							</div>
							<div>
								<label htmlFor="max_hints" className="block text-sm text-text-secondary mb-2">Max Hints</label>
								<Input id="max_hints" type="number" min={0} max={10} value={form.max_hints} onChange={(e) => setForm({ ...form, max_hints: Number(e.target.value) })} />
							</div>
						</>
					)}

					{tab === "artifact" && (
						<>
							<p className="text-sm text-text-secondary">Completing this quest awards an artifact that can unlock other quests.</p>
							<div>
								<label htmlFor="artifact_name" className="block text-sm text-text-secondary mb-2">Artifact Name</label>
								<Input id="artifact_name" value={form.artifact_name} onChange={(e) => setForm({ ...form, artifact_name: e.target.value })} placeholder="e.g. BLUEPRINT-8K2F" />
							</div>
							<div>
								<label htmlFor="artifact_description" className="block text-sm text-text-secondary mb-2">Artifact Description</label>
								<Textarea id="artifact_description" rows={3} value={form.artifact_description} onChange={(e) => setForm({ ...form, artifact_description: e.target.value })} placeholder="The blueprint of NEXUS network" />
							</div>
						</>
					)}

					<Button
						type="submit"
						disabled={saving}
						loading={saving}
						size="lg"
						className="w-full"
					>
						{saving ? "Creating..." : "Create Quest"}
					</Button>
				</form>
			</div>
		</div>
	);
}
