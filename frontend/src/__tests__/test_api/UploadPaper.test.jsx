import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import UploadPaper from '../../api/UploadPaper'; // Adjust path as needed
import api from '../../api'; // Matches the component's import
import { BrowserRouter as Router } from 'react-router-dom';

// Mock API module
vi.mock('../../api', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('UploadPaper Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders form correctly', () => {
    render(
      <Router>
        <UploadPaper />
      </Router>
    );

    expect(screen.getByText('Upload Research Paper')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Author')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Research Field')).toBeInTheDocument();
    expect(screen.getByLabelText('Upload PDF File (Max 5MB)')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
  });

  it('displays error message when file size exceeds 5MB', async () => {
    render(
      <Router>
        <UploadPaper />
      </Router>
    );

    const fileInput = screen.getByLabelText('Upload PDF File (Max 5MB)');
    
    const largeFile = new File([new Blob(['a'.repeat(6 * 1024 * 1024)])], 'largefile.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(fileInput, { target: { files: [largeFile] } });

    await new Promise(resolve => setTimeout(resolve, 100)); // Wait for the file size check

    expect(screen.getByText('File size exceeds 5MB. Please select a smaller file.')).toBeInTheDocument();
  });
});
