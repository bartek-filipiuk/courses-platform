import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC = path.resolve(__dirname, "..");

describe("GitHub button gate + magic-link resend", () => {
	it("login page gates the GitHub button behind NEXT_PUBLIC_GITHUB_OAUTH", () => {
		const src = fs.readFileSync(
			path.join(SRC, "app/login/page.tsx"),
			"utf-8",
		);
		expect(src).toContain("NEXT_PUBLIC_GITHUB_OAUTH");
	});

	it("magic page contains a resend affordance that calls magic/request", () => {
		const src = fs.readFileSync(
			path.join(SRC, "app/auth/magic/page.tsx"),
			"utf-8",
		);
		expect(src).toContain("magic/request");
	});
});
