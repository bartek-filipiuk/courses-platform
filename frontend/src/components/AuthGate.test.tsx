/**
 * AuthGate – client auth-gate component (Task B12).
 *
 * Guards dashboard / missions / admin route groups.
 * Redirects to /login when no token is present.
 * Redirects to / when requireAdmin is set but the token carries role != "admin".
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock next/navigation BEFORE importing the component.
const replaceMock = vi.fn();
vi.mock("next/navigation", () => ({
	useRouter: () => ({ replace: replaceMock }),
}));

import AuthGate from "./AuthGate";

/** Build a minimal JWT payload with the given claims. */
function makeJwt(claims: Record<string, unknown>): string {
	const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
	const payload = btoa(JSON.stringify(claims));
	return `${header}.${payload}.sig`;
}

const STUDENT_TOKEN = makeJwt({ sub: "u1", role: "student", exp: 9999999999 });
const ADMIN_TOKEN = makeJwt({ sub: "u2", role: "admin", exp: 9999999999 });

beforeEach(() => {
	localStorage.clear();
	replaceMock.mockClear();
});

afterEach(() => {
	vi.clearAllMocks();
});

describe("AuthGate", () => {
	describe("no token present", () => {
		it("redirects to /login when no token", () => {
			localStorage.removeItem("ndqs_token");
			render(
				<AuthGate>
					<div>secret</div>
				</AuthGate>,
			);
			expect(replaceMock).toHaveBeenCalledWith("/login");
		});

		it("does NOT render children when no token", () => {
			localStorage.removeItem("ndqs_token");
			render(
				<AuthGate>
					<div>secret</div>
				</AuthGate>,
			);
			expect(screen.queryByText("secret")).not.toBeInTheDocument();
		});
	});

	describe("valid token (no requireAdmin)", () => {
		it("renders children when a token is present", () => {
			localStorage.setItem("ndqs_token", STUDENT_TOKEN);
			render(
				<AuthGate>
					<div>secret</div>
				</AuthGate>,
			);
			expect(screen.getByText("secret")).toBeInTheDocument();
		});

		it("does NOT redirect when a token is present", () => {
			localStorage.setItem("ndqs_token", STUDENT_TOKEN);
			render(
				<AuthGate>
					<div>secret</div>
				</AuthGate>,
			);
			expect(replaceMock).not.toHaveBeenCalled();
		});
	});

	describe("requireAdmin", () => {
		it("redirects to / when token has role=student", () => {
			localStorage.setItem("ndqs_token", STUDENT_TOKEN);
			render(
				<AuthGate requireAdmin>
					<div>admin area</div>
				</AuthGate>,
			);
			expect(replaceMock).toHaveBeenCalledWith("/");
		});

		it("does NOT render children when role=student", () => {
			localStorage.setItem("ndqs_token", STUDENT_TOKEN);
			render(
				<AuthGate requireAdmin>
					<div>admin area</div>
				</AuthGate>,
			);
			expect(screen.queryByText("admin area")).not.toBeInTheDocument();
		});

		it("renders children when token has role=admin", () => {
			localStorage.setItem("ndqs_token", ADMIN_TOKEN);
			render(
				<AuthGate requireAdmin>
					<div>admin area</div>
				</AuthGate>,
			);
			expect(screen.getByText("admin area")).toBeInTheDocument();
		});

		it("does NOT redirect when token has role=admin", () => {
			localStorage.setItem("ndqs_token", ADMIN_TOKEN);
			render(
				<AuthGate requireAdmin>
					<div>admin area</div>
				</AuthGate>,
			);
			expect(replaceMock).not.toHaveBeenCalled();
		});

		it("redirects to / when token is malformed (cannot decode role)", () => {
			localStorage.setItem("ndqs_token", "not-a-real-jwt");
			render(
				<AuthGate requireAdmin>
					<div>admin area</div>
				</AuthGate>,
			);
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
	});
});
