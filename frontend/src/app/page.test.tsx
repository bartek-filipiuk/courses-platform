import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("Home page", () => {
  it("renders the NDQS heading", () => {
    render(<Home />);
    const headings = screen.getAllByText(/NDQS/i);
    expect(headings.length).toBeGreaterThanOrEqual(1);
    expect(headings[0]).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    render(<Home />);
    const subtitles = screen.getAllByText(/Narrative-Driven Quest Sandbox/i);
    expect(subtitles.length).toBeGreaterThanOrEqual(1);
    expect(subtitles[0]).toBeInTheDocument();
  });

  it("has dark background styling", () => {
    render(<Home />);
    const mains = screen.getAllByRole("main");
    expect(mains[0].className).toContain("bg-[#0A0A0B]");
  });
});
