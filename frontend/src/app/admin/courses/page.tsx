"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useAuthMutate } from "@/lib/use-api";
import { Button, Input, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";

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
			toast.success("Course created successfully!");
			setForm(EMPTY_FORM);
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to create course");
		} finally {
			setSaving(false);
		}
	};

	return (
		<div className="min-h-screen bg-bg-base p-8">
			<div className="max-w-3xl mx-auto">
				<h1 className="text-3xl font-bold text-text-primary mb-2">Create Course</h1>
				<p className="text-text-secondary mb-8">Define a new operation for your students.</p>

				{message && (
					<div
						className={cn(
							"mb-6 p-4 rounded-xl border",
							message.type === "success"
								? "border-accent-success/30 bg-accent-success/10 text-accent-success"
								: "border-accent-error/30 bg-accent-error/10 text-accent-error",
						)}
					>
						{message.text}
					</div>
				)}

				<form onSubmit={handleSubmit} className="space-y-6">
					{/* Title */}
					<div>
						<label htmlFor="title" className="block text-sm font-medium text-text-secondary mb-2">
							Title *
						</label>
						<Input
							id="title"
							type="text"
							required
							value={form.title}
							onChange={(e) => setForm({ ...form, title: e.target.value })}
							placeholder="e.g. Fullstack Web Development"
						/>
					</div>

					{/* Narrative title */}
					<div>
						<label htmlFor="narrative_title" className="block text-sm font-medium text-text-secondary mb-2">
							Narrative Title
						</label>
						<Input
							id="narrative_title"
							type="text"
							value={form.narrative_title}
							onChange={(e) => setForm({ ...form, narrative_title: e.target.value })}
							placeholder="e.g. Operation: Skynet Breaker"
						/>
					</div>

					{/* Description */}
					<div>
						<label htmlFor="description" className="block text-sm font-medium text-text-secondary mb-2">
							Description
						</label>
						<Textarea
							id="description"
							rows={4}
							value={form.description}
							onChange={(e) => setForm({ ...form, description: e.target.value })}
							placeholder="What is this course about?"
						/>
					</div>

					{/* Game Master persona */}
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label htmlFor="persona_name" className="block text-sm font-medium text-text-secondary mb-2">
								Game Master Name
							</label>
							<Input
								id="persona_name"
								type="text"
								value={form.persona_name}
								onChange={(e) => setForm({ ...form, persona_name: e.target.value })}
								placeholder="e.g. ORACLE"
							/>
						</div>
						<div>
							<label htmlFor="model_id" className="block text-sm font-medium text-text-secondary mb-2">
								LLM Model (OpenRouter)
							</label>
							<Input
								id="model_id"
								type="text"
								value={form.model_id}
								onChange={(e) => setForm({ ...form, model_id: e.target.value })}
								placeholder="anthropic/claude-sonnet-4-6"
							/>
						</div>
					</div>

					{/* Persona prompt */}
					<div>
						<label htmlFor="persona_prompt" className="block text-sm font-medium text-text-secondary mb-2">
							Game Master System Prompt
						</label>
						<Textarea
							id="persona_prompt"
							rows={6}
							value={form.persona_prompt}
							onChange={(e) => setForm({ ...form, persona_prompt: e.target.value })}
							className="font-mono text-sm"
							placeholder="You are ORACLE, a rogue AI fragment..."
						/>
					</div>

					{/* Cover image URL */}
					<div>
						<label htmlFor="cover_image_url" className="block text-sm font-medium text-text-secondary mb-2">
							Cover Image URL
						</label>
						<Input
							id="cover_image_url"
							type="url"
							value={form.cover_image_url}
							onChange={(e) => setForm({ ...form, cover_image_url: e.target.value })}
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
							className="w-4 h-4 rounded border-border-default bg-bg-base text-accent-primary focus:ring-accent-primary"
						/>
						<label htmlFor="is_published" className="text-sm text-text-secondary">
							Publish immediately (visible in catalog)
						</label>
					</div>

					{/* Submit */}
					<Button
						type="submit"
						disabled={saving}
						loading={saving}
						size="lg"
						className="w-full"
					>
						{saving ? "Creating..." : "Create Course"}
					</Button>
				</form>
			</div>
		</div>
	);
}
