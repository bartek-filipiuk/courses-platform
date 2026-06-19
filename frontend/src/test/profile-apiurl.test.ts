import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC = path.resolve(__dirname, "..");

describe("Profile quickstart API URL", () => {
	it("profile quickstart is not hardcoded to localhost:8002", () => {
		const src = fs.readFileSync(
			path.join(SRC, "app/(dashboard)/profile/page.tsx"),
			"utf-8",
		);
		expect(src).not.toContain("localhost:8002");
		expect(src).toContain("NEXT_PUBLIC_API_URL");
	});
});
