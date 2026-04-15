import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = path.resolve(__dirname, "../..");
const SRC = path.join(ROOT, "src");

describe("Frontend-Backend Integration", () => {
	describe("API client", () => {
		it("has api-client.ts in src/lib", () => {
			expect(fs.existsSync(path.join(SRC, "lib/api-client.ts"))).toBe(true);
		});

		it("api-client exports apiClient function", () => {
			const content = fs.readFileSync(
				path.join(SRC, "lib/api-client.ts"),
				"utf-8",
			);
			expect(content).toContain("apiClient");
			expect(content).toContain("NEXT_PUBLIC_API_URL");
		});
	});

	describe("Next.js proxy config", () => {
		it("next.config.ts has API rewrite/proxy rules", () => {
			const config = fs.readFileSync(
				path.join(ROOT, "next.config.ts"),
				"utf-8",
			);
			// Should have either rewrites or a proxy mention
			const hasProxy = config.includes("rewrites") || config.includes("proxy");
			expect(hasProxy).toBe(true);
		});
	});

	describe("Shared types", () => {
		it("has types directory or file", () => {
			const hasTypes =
				fs.existsSync(path.join(SRC, "types")) ||
				fs.existsSync(path.join(SRC, "types.ts"));
			expect(hasTypes).toBe(true);
		});

		it("types include User type", () => {
			const typesDir = path.join(SRC, "types");
			let content = "";
			if (fs.existsSync(path.join(typesDir, "index.ts"))) {
				content = fs.readFileSync(path.join(typesDir, "index.ts"), "utf-8");
			} else if (fs.existsSync(path.join(typesDir, "api.ts"))) {
				content = fs.readFileSync(path.join(typesDir, "api.ts"), "utf-8");
			}
			expect(content).toContain("User");
		});
	});

	describe("OpenAPI / Swagger", () => {
		it("backend main.py has docs enabled (no docs_url=None)", () => {
			const mainPy = fs.readFileSync(
				path.join(ROOT, "..", "backend", "app", "main.py"),
				"utf-8",
			);
			expect(mainPy).not.toContain("docs_url=None");
		});
	});
});
