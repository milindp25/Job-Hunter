import { Suspense } from 'react';
import type { Metadata } from 'next';
import { AtsReportContent } from './ats-report-content';

export const metadata: Metadata = {
  title: 'ATS Compliance Report | Job Hunter',
  description: 'Detailed ATS compliance analysis for your resume',
};

export default function AtsReportPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>}>
      <AtsReportContent />
    </Suspense>
  );
}
