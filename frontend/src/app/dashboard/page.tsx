import { AuthGuard } from "@/components/layout/auth-guard";
import { DashboardContent } from "@/components/dashboard/dashboard-content";

export const metadata = {
  title: "Dashboard | Job Hunter",
  description: "Your job hunting dashboard",
};

export default function DashboardPage() {
  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <DashboardContent />
      </main>
    </AuthGuard>
  );
}
