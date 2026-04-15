import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

describe("Stage 5 pages", () => {
	it("comms log page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/(dashboard)/comms/page.tsx"))).toBe(true);
	});

	it("profile page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/(dashboard)/profile/page.tsx"))).toBe(true);
	});

	it("admin analytics page exists", () => {
		expect(existsSync(resolve(__dirname, "../app/admin/analytics/page.tsx"))).toBe(true);
	});
});
