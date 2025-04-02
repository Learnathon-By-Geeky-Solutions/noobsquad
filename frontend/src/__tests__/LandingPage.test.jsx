import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import LandingPage from "../pages/LandingPage";
import { ChatProvider } from "../context/ChatContext";  // Import ChatProvider

// ✅ Mock Navbar component to isolate test
vi.mock("../components/Navbar", () => {
  return {
    default: () => <div data-testid="navbar">Navbar</div>
  };
});

describe("LandingPage", () => {
  it("renders the LandingPage with all key elements", () => {
    render(
      <MemoryRouter>
        <ChatProvider>  {/* Wrap LandingPage with ChatProvider */}
          <LandingPage />
        </ChatProvider>
      </MemoryRouter>
    );

    // Check Navbar renders
    expect(screen.getByTestId("navbar")).toBeInTheDocument();

    // Check heading
    expect(
      screen.getByText("Pair, Learn, and Grow with UHub")
    ).toBeInTheDocument();

    // Check description
    expect(
      screen.getByText(
        /Join a thriving university community platform/i
      )
    ).toBeInTheDocument();

    // Check "Get Started" button
    const getStartedBtn = screen.getByRole("link", { name: /Get Started/i });
    expect(getStartedBtn).toBeInTheDocument();
    expect(getStartedBtn.getAttribute("href")).toBe("/signup");

    // Check footer
    expect(
      screen.getByText("© 2025 UHub. All rights reserved.")
    ).toBeInTheDocument();
  });
});
