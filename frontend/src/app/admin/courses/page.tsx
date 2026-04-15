"use client";

import { useState } from "react";
import { useAuthMutate } from "@/lib/use-api";

interface CourseForm {
	title: string;
	narrative_title: string;
	description: string;
	persona_name: string;
	persona_prompt: string;
	global_context: string;
	cover_image_url: string;
	model_id: string;
	is_published: boolean;
}

const EMPTY_FORM: CourseForm = {
	title: "",
	narrative_title: "",
	description: "",
	persona_name: "",
	persona_prompt: "",
	global_context: "",
	cover_image_url: "",
	model_id: "anthropic/claude-sonnet-4-6",
	is_published: false,
};

export default function AdminCoursesPage() {
	const [form, setForm] = useState<CourseForm>(EMPTY_FORM);
	const [saving, setSaving] = useState(false);
	const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
	const mutate = useAuthMutate("admin");

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setSaving(true);
		setMessage(null);

		try {
			const body = Object.fromEntries(
				Object.entries(form).filter(([, v]) => v !== ""),
			);
			await mutate("/api/admin/courses", { method: "POST", body });
			setMessage({ type: "success", text: "Course created successfully!" });
			setForm(EMPTY_FORM);
		} catch (e) {
			setMessage({
				type: "error",
				text: e instanceof Error ? e.message : "Failed to create course",
			});
		} finally {
			setSaving(false);
		}
	};

	const inputClass =
		"w-full rounded-xl border border-[#2A2A2E] bg-[#0A0A0B] px-4 py-3 text-white placeholder-[#A1A1AA]/50 focus:border-[#6366F1] focus:outline-none transition-colors";

	return (
		<div className="min-h-screen bg-[#0A0A0B] p-8">
			<div className="max-w-3xl mx-auto">
				<h1 className="text-3xl font-bold text-white mb-2">Create Course</h1>
				<p className="text-[#A1A1AA] mb-8">Define a new operation for your students.</p>

				{message && (
					<div
						className={`mb-6 p-4 rounded-xl border ${
							message.type === "success"
								? "border-[#22C55E]/30 bg-[#22C55E]/10 text-[#22C55E]"
								: "border-red-500/30 bg-red-500/10 text-red-400"
						}`}
					>
						{message.text}
					</div>
				)}

				<form onSubmit={handleSubmit} className="space-y-6">
					{/* Title */}
					<div>
						<label htmlFor="title" className="block text-sm font-medium text-[#A1A1AA] mb-2">
							Title *
						</label>
						<input
							id="title"
							type="text"
							required
							value={form.title}
							onChange={(e) => setForm({ ...form, title: e.target.value })}
							className={inputClass}
							placeholder="e.g. Fullstack Web Development"
						/>
					</div>

					{/* Narrative title */}
					<div>
						<label htmlFor="narrative_title" className="block text-sm font-medium text-[#A1A1AA] mb-2">
							Narrative Title
						</label>
						<input
							id="narrative_title"
							type="text"
							value={form.narrative_title}
							onChange={(e) => setForm({ ...form, narrative_title: e.target.value })}
							className={inputClass}
							placeholder="e.g. Operation: Skynet Breaker"
						/>
					</div>

					{/* Description */}
					<div>
						<label htmlFor="description" className="block text-sm font-medium text-[#A1A1AA] mb-2">
							Description
						</label>
						<textarea
							id="description"
							rows={4}
							value={form.description}
							onChange={(e) => setForm({ ...form, description: e.target.value })}
							className={inputClass}
							placeholder="What is this course about?"
						/>
					</div>

					{/* Game Master persona */}
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label htmlFor="persona_name" className="block text-sm font-medium text-[#A1A1AA] mb-2">
								Game Master Name
							</label>
							<input
								id="persona_name"
								type="text"
								value={form.persona_name}
								onChange={(e) => setForm({ ...form, persona_name: e.target.value })}
								className={inputClass}
								placeholder="e.g. ORACLE"
							/>
						</div>
						<div>
							<label htmlFor="model_id" className="block text-sm font-medium text-[#A1A1AA] mb-2">
								LLM Model (OpenRouter)
							</label>
							<input
								id="model_id"
								type="text"
								value={form.model_id}
								onChange={(e) => setForm({ ...form, model_id: e.target.value })}
								className={inputClass}
								placeholder="anthropic/claude-sonnet-4-6"
							/>
						</div>
					</div>

					{/* Persona prompt */}
					<div>
						<label htmlFor="persona_prompt" className="block text-sm font-medium text-[#A1A1AA] mb-2">
							Game Master System Prompt
						</label>
						<textarea
							id="persona_prompt"
							rows={6}
							value={form.persona_prompt}
							onChange={(e) => setForm({ ...form, persona_prompt: e.target.value })}
							className={`${inputClass} font-mono text-sm`}
							placeholder="You are ORACLE, a rogue AI fragment..."
						/>
					</div>

					{/* Cover image URL */}
					<div>
						<label htmlFor="cover_image_url" className="block text-sm font-medium text-[#A1A1AA] mb-2">
							Cover Image URL
						</label>
						<input
							id="cover_image_url"
							type="url"
							value={form.cover_image_url}
							onChange={(e) => setForm({ ...form, cover_image_url: e.target.value })}
							className={inputClass}
							placeholder="https://..."
						/>
					</div>

					{/* Published toggle */}
					<div className="flex items-center gap-3">
						<input
							id="is_published"
							type="checkbox"
							checked={form.is_published}
							onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
							className="w-4 h-4 rounded border-[#2A2A2E] bg-[#0A0A0B] text-[#6366F1] focus:ring-[#6366F1]"
						/>
						<label htmlFor="is_published" className="text-sm text-[#A1A1AA]">
							Publish immediately (visible in catalog)
						</label>
					</div>

					{/* Submit */}
					<button
						type="submit"
						disabled={saving}
						className="w-full py-3 rounded-xl bg-[#6366F1] text-white font-medium hover:bg-[#5558E6] active:scale-[0.99] transition-all disabled:opacity-50"
					>
						{saving ? "Creating..." : "Create Course"}
					</button>
				</form>
			</div>
		</div>
	);
}
