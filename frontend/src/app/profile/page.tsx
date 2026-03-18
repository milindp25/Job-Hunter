import { AuthGuard } from "@/components/layout/auth-guard";
import { ProfileContent } from "@/components/profile/profile-content";

export const metadata = {
  title: "Profile | Job Hunter",
  description: "Manage your professional profile",
};

export default function ProfilePage() {
  return (
    <AuthGuard>
      <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <ProfileContent />
      </main>
    </AuthGuard>
  );
}
