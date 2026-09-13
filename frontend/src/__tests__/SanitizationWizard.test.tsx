import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TypedConfirmationModal } from '../components/common/TypedConfirmationModal';
import { SafetyGateBanner } from '../components/common/SafetyGateBanner';
import { StatusBadge } from '../components/common/StatusBadge';

describe('Safety-Critical Frontend Components & Workflows', () => {
  it('TypedConfirmationModal blocks execution button until typed token matches exactly', () => {
    const onConfirmMock = vi.fn();
    const onCloseMock = vi.fn();

    const expectedToken = 'CONFIRM DESTROY /dev/sdb';

    render(
      <TypedConfirmationModal
        isOpen={true}
        onClose={onCloseMock}
        onConfirm={onConfirmMock}
        title="Test Drive Sanitization"
        targetDescription="Target /dev/sdb"
        expectedToken={expectedToken}
        isSubmitting={false}
      />
    );

    const submitBtn = screen.getByRole('button', { name: /Confirm Execution/i });
    expect(submitBtn).toBeDisabled();

    const input = screen.getByPlaceholderText(expectedToken);

    // Partial match -> still disabled
    fireEvent.change(input, { target: { value: 'CONFIRM DESTROY' } });
    expect(submitBtn).toBeDisabled();

    // Exact match -> enabled
    fireEvent.change(input, { target: { value: expectedToken } });
    expect(submitBtn).not.toBeDisabled();

    fireEvent.click(submitBtn);
    expect(onConfirmMock).toHaveBeenCalledTimes(1);
  });

  it('SafetyGateBanner displays system disk violation notice prominently', () => {
    render(
      <SafetyGateBanner
        devicePath="/dev/sda"
        isSystemDisk={true}
        safeMode={true}
        realDeviceOps={false}
      />
    );

    expect(screen.getByText(/CRITICAL SAFETY GATE VIOLATION: SYSTEM DISK DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText(/\/dev\/sda/i)).toBeInTheDocument();
  });

  it('StatusBadge correctly renders 5-point classification status pills', () => {
    const { rerender } = render(<StatusBadge status="Verified" />);
    expect(screen.getByText('Verified')).toBeInTheDocument();

    rerender(<StatusBadge status="Inconclusive" />);
    expect(screen.getByText('Inconclusive')).toBeInTheDocument();

    rerender(<StatusBadge status="Failed" />);
    expect(screen.getByText('Failed')).toBeInTheDocument();

    rerender(<StatusBadge status="Unsupported" />);
    expect(screen.getByText('Unsupported')).toBeInTheDocument();

    rerender(<StatusBadge status="Manual Review" />);
    expect(screen.getByText('Manual Review')).toBeInTheDocument();
  });
});
