import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

describe("Quest Map pages", () => {
	it("quest map page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/(dashboard)/quest-map/page.tsx"))).toBe(true);
	});

	it("inventory page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/(dashboard)/inventory/page.tsx"))).toBe(true);
	});

	it("admin quest editor page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/admin/quests/page.tsx"))).toBe(true);
	});

	it("QuestNode component exists", () => {
		expect(existsSync(resolve(__dirname, "../components/quest-map/QuestNode.tsx"))).toBe(true);
	});
});
