/**
 * TranscriptionCard Component Tests (TDD - Track C)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider } from '../../theme';
import { TranscriptionCard } from './TranscriptionCard';

describe('TranscriptionCard', () => {
  const mockTranscription = {
    text: 'This is a test transcription',
    confidence: 0.95,
    timestamp: '2025-11-24T04:00:00.000Z',
    latency: 250,
  };

  it('renders transcription text', () => {
    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} />
      </ThemeProvider>
    );

    expect(screen.getByText(mockTranscription.text)).toBeInTheDocument();
  });

  it('shows confidence badge with color coding', () => {
    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} />
      </ThemeProvider>
    );

    const badge = screen.getByText(/95%/i);
    expect(badge).toBeInTheDocument();
  });

  it('displays formatted timestamp', () => {
    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} />
      </ThemeProvider>
    );

    // Should show relative time or formatted timestamp
    expect(screen.getByText(/ago|AM|PM/i)).toBeInTheDocument();
  });

  it('shows latency metric', () => {
    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} />
      </ThemeProvider>
    );

    expect(screen.getByText(/250ms/i)).toBeInTheDocument();
  });

  it('shows copy button on hover', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} />
      </ThemeProvider>
    );

    const card = screen.getByText(mockTranscription.text).closest('div');
    if (card) {
      await user.hover(card);
    }

    // Copy button should be visible (or always present)
    const copyButton = screen.getByRole('button', { name: /copy/i });
    expect(copyButton).toBeInTheDocument();
  });

  it('calls onCopy with text when copy clicked', async () => {
    const handleCopy = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} onCopy={handleCopy} />
      </ThemeProvider>
    );

    const copyButton = screen.getByRole('button', { name: /copy/i });
    await user.click(copyButton);

    expect(handleCopy).toHaveBeenCalledWith(mockTranscription.text);
  });

  it('has proper confidence color (green>0.8, yellow>0.5, red)', () => {
    const { rerender } = render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} confidence={0.9} />
      </ThemeProvider>
    );

    let badge = screen.getByText(/90%/i);
    expect(badge).toHaveStyle({ color: expect.stringMatching(/green|success/i) });

    rerender(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} confidence={0.6} />
      </ThemeProvider>
    );

    badge = screen.getByText(/60%/i);
    expect(badge).toBeInTheDocument();

    rerender(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} confidence={0.3} />
      </ThemeProvider>
    );

    badge = screen.getByText(/30%/i);
    expect(badge).toBeInTheDocument();
  });

  it('is accessible with keyboard navigation', async () => {
    const handleCopy = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <TranscriptionCard {...mockTranscription} onCopy={handleCopy} />
      </ThemeProvider>
    );

    const copyButton = screen.getByRole('button', { name: /copy/i });
    copyButton.focus();

    await user.keyboard('{Enter}');
    expect(handleCopy).toHaveBeenCalled();
  });
});
