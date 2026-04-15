"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";

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
			await apiClient("/api/admin/quests", { method: "POST", body, token: "admin-token" });
			setMessage({ type: "success", text: "Quest created!" });
			setForm(EMPTY_FORM);
		} catch (e) {
			setMessage({ type: "error", text: e instanceof Error ? e.message : "Failed" });
		} finally {
			setSaving(false);
		}
	};

	const inputClass = "w-full rounded-xl border border-[#2A2A2E] bg-[#0A0A0B] px-4 py-3 text-white placeholder-[#A1A1AA]/50 focus:border-[#6366F1] focus:outline-none transition-colors";
	const tabClass = (t: string) => `px-4 py-2 text-sm font-medium rounded-lg transition-colors ${tab === t ? "bg-[#6366F1] text-white" : "text-[#A1A1AA] hover:text-white"}`;

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-3xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Create Quest</h1>
				<p className="text-[#A1A1AA] mb-6">Add a new quest to a course.</p>

				{message && (
					<div className={`mb-6 p-4 rounded-xl border ${message.type === "success" ? "border-[#22C55E]/30 bg-[#22C55E]/10 text-[#22C55E]" : "border-red-500/30 bg-red-500/10 text-red-400"}`}>
						{message.text}
					</div>
				)}

				{/* Tabs */}
				<div className="flex gap-2 mb-6">
					<button type="button" className={tabClass("story")} onClick={() => setTab("story")}>Story</button>
					<button type="button" className={tabClass("tech")} onClick={() => setTab("tech")}>Technical</button>
					<button type="button" className={tabClass("artifact")} onClick={() => setTab("artifact")}>Artifact</button>
				</div>

				<form onSubmit={handleSubmit} className="space-y-5">
					{tab === "story" && (
						<>
							<div>
								<label htmlFor="course_id" className="block text-sm text-[#A1A1AA] mb-2">Course ID *</label>
								<input id="course_id" required value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} className={inputClass} placeholder="UUID of the course" />
							</div>
							<div className="grid grid-cols-2 gap-4">
								<div>
									<label htmlFor="title" className="block text-sm text-[#A1A1AA] mb-2">Quest Title *</label>
									<input id="title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputClass} placeholder="e.g. Dark Network" />
								</div>
								<div>
									<label htmlFor="sort_order" className="block text-sm text-[#A1A1AA] mb-2">Order</label>
									<input id="sort_order" type="number" min={0} value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} className={inputClass} />
								</div>
							</div>
							<div>
								<label htmlFor="briefing" className="block text-sm text-[#A1A1AA] mb-2">Briefing (narrative) *</label>
								<textarea id="briefing" required rows={6} value={form.briefing} onChange={(e) => setForm({ ...form, briefing: e.target.value })} className={`${inputClass} font-mono text-sm`} placeholder="Ghost — your mission..." />
							</div>
							<div>
								<label htmlFor="success_response" className="block text-sm text-[#A1A1AA] mb-2">Success Response</label>
								<textarea id="success_response" rows={3} value={form.success_response} onChange={(e) => setForm({ ...form, success_response: e.target.value })} className={`${inputClass} font-mono text-sm`} placeholder="Good work, Ghost..." />
							</div>
						</>
					)}

					{tab === "tech" && (
						<>
							<div>
								<label htmlFor="evaluation_type" className="block text-sm text-[#A1A1AA] mb-2">Evaluation Type *</label>
								<select id="evaluation_type" value={form.evaluation_type} onChange={(e) => setForm({ ...form, evaluation_type: e.target.value })} className={inputClass}>
									{EVAL_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
								</select>
							</div>
							<div>
								<label htmlFor="skills" className="block text-sm text-[#A1A1AA] mb-2">Skills (comma-separated)</label>
								<input id="skills" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} className={inputClass} placeholder="REST API, Docker, SQL" />
							</div>
							<div>
								<label htmlFor="max_hints" className="block text-sm text-[#A1A1AA] mb-2">Max Hints</label>
								<input id="max_hints" type="number" min={0} max={10} value={form.max_hints} onChange={(e) => setForm({ ...form, max_hints: Number(e.target.value) })} className={inputClass} />
							</div>
						</>
					)}

					{tab === "artifact" && (
						<>
							<p className="text-sm text-[#A1A1AA]">Completing this quest awards an artifact that can unlock other quests.</p>
							<div>
								<label htmlFor="artifact_name" className="block text-sm text-[#A1A1AA] mb-2">Artifact Name</label>
								<input id="artifact_name" value={form.artifact_name} onChange={(e) => setForm({ ...form, artifact_name: e.target.value })} className={inputClass} placeholder="e.g. BLUEPRINT-8K2F" />
							</div>
							<div>
								<label htmlFor="artifact_description" className="block text-sm text-[#A1A1AA] mb-2">Artifact Description</label>
								<textarea id="artifact_description" rows={3} value={form.artifact_description} onChange={(e) => setForm({ ...form, artifact_description: e.target.value })} className={inputClass} placeholder="The blueprint of NEXUS network" />
							</div>
						</>
					)}

					<button type="submit" disabled={saving} className="w-full py-3 rounded-xl bg-[#6366F1] text-white font-medium hover:bg-[#5558E6] active:scale-[0.99] transition-all disabled:opacity-50">
						{saving ? "Creating..." : "Create Quest"}
					</button>
				</form>
			</div>
		</div>
	);
}
