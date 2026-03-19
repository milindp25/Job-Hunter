import { AuthGuard } from '@/components/layout/auth-guard';
import { JobsContent } from './jobs-content';

export const metadata = {
  title: 'Browse Jobs | Job Hunter',
  description: 'Search and browse job listings matched to your profile',
};

export default function JobsPage() {
  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <JobsContent />
      </main>
    </AuthGuard>
  );
}
