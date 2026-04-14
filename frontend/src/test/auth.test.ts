import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const ROOT = path.resolve(__dirname, "../..");
const SRC = path.join(ROOT, "src");

describe("Auth Frontend", () => {
	describe("NextAuth config", () => {
		it("has auth config file", () => {
			const exists =
				fs.existsSync(path.join(SRC, "lib/auth.ts")) ||
				fs.existsSync(path.join(SRC, "auth.ts"));
			expect(exists).toBe(true);
		});

		it("auth config exports auth handlers", () => {
			const authFile = fs.existsSync(path.join(SRC, "lib/auth.ts"))
				? fs.readFileSync(path.join(SRC, "lib/auth.ts"), "utf-8")
				: fs.readFileSync(path.join(SRC, "auth.ts"), "utf-8");
			expect(authFile).toContain("GitHub");
		});
	});

	describe("Login page", () => {
		it("has login page at app/login/page.tsx", () => {
			expect(
				fs.existsSync(path.join(SRC, "app/login/page.tsx")),
			).toBe(true);
		});

		it("login page contains GitHub login button text", () => {
			const page = fs.readFileSync(
				path.join(SRC, "app/login/page.tsx"),
				"utf-8",
			);
			expect(page.toLowerCase()).toContain("github");
		});
	});

	describe("Auth API route", () => {
		it("has NextAuth API route handler", () => {
			const exists =
				fs.existsSync(
					path.join(SRC, "app/api/auth/[...nextauth]/route.ts"),
				);
			expect(exists).toBe(true);
		});
	});

	describe("Environment config", () => {
		it("has .env.local.example with auth vars", () => {
			const envFile = path.join(ROOT, ".env.local.example");
			expect(fs.existsSync(envFile)).toBe(true);
			const content = fs.readFileSync(envFile, "utf-8");
			expect(content).toContain("AUTH_SECRET");
			expect(content).toContain("AUTH_GITHUB_ID");
			expect(content).toContain("AUTH_GITHUB_SECRET");
		});
	});
});
