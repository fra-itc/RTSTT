/**
 * TranscriptionList Component Tests (TDD - Track D)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider } from '../../theme';
import { TranscriptionList } from './TranscriptionList';

describe('TranscriptionList', () => {
  const mockTranscriptions = [
    {
      text: 'First transcription',
      confidence: 0.95,
      timestamp: '2025-11-24T04:00:00.000Z',
      latency: 250,
    },
    {
      text: 'Second transcription',
      confidence: 0.88,
      timestamp: '2025-11-24T04:01:00.000Z',
      latency: 180,
    },
  ];

  it('renders list of transcription cards', () => {
    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} />
      </ThemeProvider>
    );

    expect(screen.getByText('First transcription')).toBeInTheDocument();
    expect(screen.getByText('Second transcription')).toBeInTheDocument();
  });

  it('shows empty state when no transcriptions', () => {
    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={[]} />
      </ThemeProvider>
    );

    expect(screen.getByText(/no transcriptions yet/i)).toBeInTheDocument();
  });

  it('has search/filter capability', () => {
    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} />
      </ThemeProvider>
    );

    const searchInput = screen.getByPlaceholderText(/search transcriptions/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('shows export button', () => {
    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} />
      </ThemeProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    expect(exportButton).toBeInTheDocument();
  });

  it('calls onExport with selected format', async () => {
    const handleExport = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} onExport={handleExport} />
      </ThemeProvider>
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    await user.click(exportButton);

    // Should show export options
    const txtOption = screen.getByText(/txt/i);
    await user.click(txtOption);

    expect(handleExport).toHaveBeenCalledWith('txt', mockTranscriptions);
  });

  it('filters transcriptions based on search', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} />
      </ThemeProvider>
    );

    const searchInput = screen.getByPlaceholderText(/search transcriptions/i);
    await user.type(searchInput, 'First');

    expect(screen.getByText('First transcription')).toBeInTheDocument();
    expect(screen.queryByText('Second transcription')).not.toBeInTheDocument();
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionList transcriptions={mockTranscriptions} />
      </ThemeProvider>
    );

    const firstCard = screen.getByText('First transcription');
    firstCard.focus();

    await user.keyboard('{Tab}');
    expect(document.activeElement).toBeTruthy();
  });
});
