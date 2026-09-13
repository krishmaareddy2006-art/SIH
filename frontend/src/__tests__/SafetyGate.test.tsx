import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PermissionDeniedState, OfflineBanner } from '../components/common/StateViews';
import { TechnicalLimitationsBox } from '../components/common/TechnicalLimitationsBox';

describe('Safety Gate & State View Components', () => {
  it('PermissionDeniedState displays required roles badge', () => {
    render(<PermissionDeniedState requiredRoles={['Administrator', 'Investigator']} />);

    expect(screen.getByText(/ACCESS DENIED: INSUFFICIENT PERMISSIONS/i)).toBeInTheDocument();
    expect(screen.getByText(/Administrator OR Investigator/i)).toBeInTheDocument();
  });

  it('OfflineBanner renders network connection alert', () => {
    render(<OfflineBanner />);

    expect(screen.getByText(/OFFLINE MODE DETECTED/i)).toBeInTheDocument();
  });

  it('TechnicalLimitationsBox renders collapsible SSD/NVMe disclaimers', () => {
    render(<TechnicalLimitationsBox defaultExpanded={true} />);

    expect(screen.getByText(/HDD vs. SSD\/Flash Media/i)).toBeInTheDocument();
    expect(screen.getByText(/Non-Contiguous File Fragmentation/i)).toBeInTheDocument();
  });
});
