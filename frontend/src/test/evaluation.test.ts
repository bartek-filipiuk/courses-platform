import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

describe("Evaluation frontend pages", () => {
	it("quest submit/feedback page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/quest/[questId]/page.tsx"))).toBe(true);
	});

	it("admin quests page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/admin/quests/page.tsx"))).toBe(true);
	});
});
