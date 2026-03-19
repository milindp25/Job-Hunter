import { AuthGuard } from '@/components/layout/auth-guard';
import { JobDetailContent } from './job-detail-content';

export const metadata = {
  title: 'Job Details | Job Hunter',
  description: 'View full job details and take action',
};

interface JobDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function JobDetailPage({ params }: JobDetailPageProps) {
  const { id } = await params;

  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <JobDetailContent jobId={id} />
      </main>
    </AuthGuard>
  );
}
