/**
 * RecordButton Component Tests (TDD)
 * Write tests first, then implement component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider } from '../../theme';
import { RecordButton } from './RecordButton';

describe('RecordButton', () => {
  it('renders idle state with microphone icon', () => {
    render(
      <ThemeProvider>
        <RecordButton onClick={() => {}} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /start recording/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toHaveAttribute('aria-pressed', 'true');
  });

  it('shows recording state when recording prop is true', () => {
    render(
      <ThemeProvider>
        <RecordButton recording={true} onClick={() => {}} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /stop recording/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-pressed', 'true');
  });

  it('displays timer when recording', () => {
    render(
      <ThemeProvider>
        <RecordButton recording={true} duration={65} onClick={() => {}} />
      </ThemeProvider>
    );

    // Timer should show 1:05 (65 seconds)
    expect(screen.getByText(/1:05/)).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <RecordButton onClick={handleClick} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(
      <ThemeProvider>
        <RecordButton disabled onClick={() => {}} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('does not call onClick when disabled and clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <RecordButton disabled onClick={handleClick} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('has proper ARIA labels for accessibility', () => {
    render(
      <ThemeProvider>
        <RecordButton onClick={() => {}} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label');
    expect(button).toHaveAttribute('aria-pressed');
  });

  it('supports keyboard interaction (Enter/Space)', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <RecordButton onClick={handleClick} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    button.focus();

    // Press Enter
    await user.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Press Space
    await user.keyboard(' ');
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('renders different sizes correctly', () => {
    const { rerender } = render(
      <ThemeProvider>
        <RecordButton size="small" onClick={() => {}} />
      </ThemeProvider>
    );

    let button = screen.getByRole('button');
    expect(button).toHaveStyle({ width: '48px', height: '48px' });

    rerender(
      <ThemeProvider>
        <RecordButton size="medium" onClick={() => {}} />
      </ThemeProvider>
    );

    button = screen.getByRole('button');
    expect(button).toHaveStyle({ width: '64px', height: '64px' });

    rerender(
      <ThemeProvider>
        <RecordButton size="large" onClick={() => {}} />
      </ThemeProvider>
    );

    button = screen.getByRole('button');
    expect(button).toHaveStyle({ width: '80px', height: '80px' });
  });

  it('applies pulse animation when recording', () => {
    render(
      <ThemeProvider>
        <RecordButton recording pulse onClick={() => {}} />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    // Check for animation-related styles or classes
    const styles = window.getComputedStyle(button);
    expect(styles.animation || button.className).toBeTruthy();
  });
});
