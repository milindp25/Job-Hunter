import { Suspense } from 'react';
import type { Metadata } from 'next';
import { AtsReportContent } from './ats-report-content';

export const metadata: Metadata = {
  title: 'ATS Compliance Report | Job Hunter',
  description: 'Detailed ATS compliance analysis for your resume',
};

export default function AtsReportPage() {
  return (
    <Suspense>
      <AtsReportContent />
    </Suspense>
  );
}
