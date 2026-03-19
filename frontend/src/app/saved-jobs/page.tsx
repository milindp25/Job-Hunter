import { AuthGuard } from '@/components/layout/auth-guard';
import { SavedJobsContent } from './saved-jobs-content';

export const metadata = {
  title: 'Saved Jobs | Job Hunter',
  description: 'View and manage your saved job listings',
};

export default function SavedJobsPage() {
  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <SavedJobsContent />
      </main>
    </AuthGuard>
  );
}
