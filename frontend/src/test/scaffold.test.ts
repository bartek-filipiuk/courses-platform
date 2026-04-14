import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const ROOT = path.resolve(__dirname, "../..");

describe("Frontend Scaffold", () => {
	describe("Directory structure", () => {
		it("has src/app directory with App Router", () => {
			expect(fs.existsSync(path.join(ROOT, "src/app"))).toBe(true);
		});

		it("has layout.tsx in app directory", () => {
			expect(fs.existsSync(path.join(ROOT, "src/app/layout.tsx"))).toBe(true);
		});

		it("has globals.css in app directory", () => {
			expect(fs.existsSync(path.join(ROOT, "src/app/globals.css"))).toBe(true);
		});

		it("has src/lib directory for utilities", () => {
			expect(fs.existsSync(path.join(ROOT, "src/lib"))).toBe(true);
		});
	});

	describe("Dark theme setup", () => {
		it("layout.tsx has dark class on html element", () => {
			const layout = fs.readFileSync(
				path.join(ROOT, "src/app/layout.tsx"),
				"utf-8",
			);
			expect(layout).toContain("dark");
		});

		it("globals.css has NDQS dark background color #0A0A0B", () => {
			const css = fs.readFileSync(
				path.join(ROOT, "src/app/globals.css"),
				"utf-8",
			);
			expect(css.toLowerCase()).toContain("#0a0a0b");
		});

		it("globals.css has NDQS surface color #141416", () => {
			const css = fs.readFileSync(
				path.join(ROOT, "src/app/globals.css"),
				"utf-8",
			);
			expect(css.toLowerCase()).toContain("#141416");
		});
	});

	describe("Fonts", () => {
		it("layout.tsx imports Geist Sans font", () => {
			const layout = fs.readFileSync(
				path.join(ROOT, "src/app/layout.tsx"),
				"utf-8",
			);
			expect(layout).toContain("Geist");
		});

		it("layout.tsx imports JetBrains Mono font", () => {
			const layout = fs.readFileSync(
				path.join(ROOT, "src/app/layout.tsx"),
				"utf-8",
			);
			expect(layout).toContain("JetBrains_Mono");
		});
	});

	describe("Metadata", () => {
		it("layout.tsx has NDQS title", () => {
			const layout = fs.readFileSync(
				path.join(ROOT, "src/app/layout.tsx"),
				"utf-8",
			);
			expect(layout).toContain("NDQS");
		});
	});

	describe("CSP Headers in next.config", () => {
		it("next.config.ts has security headers configured", () => {
			const config = fs.readFileSync(
				path.join(ROOT, "next.config.ts"),
				"utf-8",
			);
			expect(config).toContain("X-Frame-Options");
			expect(config).toContain("X-Content-Type-Options");
			expect(config).toContain("Referrer-Policy");
		});
	});

	describe("cn utility", () => {
		it("has cn utility in src/lib/utils.ts", () => {
			expect(fs.existsSync(path.join(ROOT, "src/lib/utils.ts"))).toBe(true);
		});

		it("cn utility exports a function", async () => {
			const { cn } = await import("@/lib/utils");
			expect(typeof cn).toBe("function");
		});

		it("cn merges classes correctly", async () => {
			const { cn } = await import("@/lib/utils");
			const result = cn("px-2 py-1", "px-4");
			expect(result).toContain("px-4");
			expect(result).not.toContain("px-2");
		});
	});
});
