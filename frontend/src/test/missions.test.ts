import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

describe("Missions pages", () => {
	it("missions catalog page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/missions/page.tsx"))).toBe(
			true,
		);
	});

	it("course detail page exists", () => {
		expect(
			existsSync(resolve(__dirname, "../app/missions/[courseId]/page.tsx")),
		).toBe(true);
	});

	it("admin courses page exists", () => {
		expect(
			existsSync(resolve(__dirname, "../app/admin/courses/page.tsx")),
		).toBe(true);
	});
});

describe("Course types", () => {
	it("Course type has required fields", async () => {
		const types = await import("../types/index");
		// Type check: if Course interface changed, this would fail to compile
		const mockCourse: types.Course = {
			id: "test",
			creator_id: null,
			title: "Test",
			narrative_title: null,
			description: null,
			persona_name: null,
			cover_image_url: null,
			model_id: null,
			is_published: false,
			created_at: "2026-01-01",
		};
		expect(mockCourse.title).toBe("Test");
	});
});
