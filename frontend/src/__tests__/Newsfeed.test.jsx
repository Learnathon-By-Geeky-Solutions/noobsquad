// Newsfeed.test.jsx
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Newsfeed from "../pages/Newsfeed";

// Mock the CreatePost and Feed components to isolate testing for Newsfeed
vi.mock("../components/CreatePost", () => ({
  __esModule: true,
  default: vi.fn(() => <div>Mocked CreatePost</div>),
}));

vi.mock("../components/Feed", () => ({
  __esModule: true,
  default: vi.fn(() => <div>Mocked Feed</div>),
}));

describe("Newsfeed Component", () => {
  it("renders CreatePost and Feed components", () => {
    render(<Newsfeed />);

    // Check if the mocked CreatePost and Feed components render
    expect(screen.getByText("Mocked CreatePost")).toBeInTheDocument();
    expect(screen.getByText("Mocked Feed")).toBeInTheDocument();
  });

  it("displays the correct layout", () => {
    render(<Newsfeed />);

    // Check if the wrapper div is present and has the correct styles
    const container = screen.getByText("Mocked CreatePost").parentElement;
    expect(container).toHaveClass("max-w-2xl");
    expect(container).toHaveClass("mx-auto");
    expect(container).toHaveClass("p-4");
  });
});
