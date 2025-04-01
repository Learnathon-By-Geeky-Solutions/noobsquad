import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'

describe('LandingPage', () => {
  it('renders the landing title and description', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    )

    expect(screen.getByText(/Pair, Learn, and Grow with UHub/i)).toBeInTheDocument()
    expect(screen.getByText(/Join a thriving university community/i)).toBeInTheDocument()
  })

  it('has a "Get Started" button linking to /signup', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    )

    const button = screen.getByRole('link', { name: /Get Started/i })
    expect(button).toBeInTheDocument()
    expect(button.getAttribute('href')).toBe('/signup')
  })

  it('renders the footer', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    )

    expect(screen.getByText(/© 2025 UHub/i)).toBeInTheDocument()
  })
})
