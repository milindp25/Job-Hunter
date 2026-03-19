import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy | Job Hunter",
  description: "How Job Hunter collects, uses, and protects your data",
};

export default function PrivacyPolicyPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-foreground">Privacy Policy</h1>
      <p className="mt-2 text-sm text-foreground/50">
        Last updated: March 2026
      </p>

      <div className="mt-8 space-y-8 text-foreground/80 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-foreground">
            1. Information We Collect
          </h2>
          <p className="mt-2">
            When you create an account and use Job Hunter, we collect the
            following information:
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Account details (name, email address, authentication provider)</li>
            <li>Profile information (skills, work experience, education, certifications)</li>
            <li>Job preferences (desired roles, locations, salary expectations)</li>
            <li>Uploaded resumes and parsed resume content</li>
            <li>Saved jobs and match history</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            2. How We Use AI
          </h2>
          <p className="mt-2">
            Job Hunter uses Google Gemini to power job matching and resume
            analysis. When processing your data with AI:
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Profile and resume data is sent to Gemini for analysis in an anonymized form</li>
            <li>Google does not store your data beyond the API request lifecycle</li>
            <li>AI-generated recommendations are stored in our database for your review</li>
            <li>You can delete all AI-generated data by deleting your account</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            3. Third-Party Job Sources
          </h2>
          <p className="mt-2">
            We aggregate job listings from publicly available APIs including
            RemoteOK, The Muse, Adzuna, Indeed, and USAJobs. Job data is
            fetched and cached on our servers; we do not share your personal
            information with these job sources.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            4. Data Storage and Security
          </h2>
          <p className="mt-2">
            Your data is stored securely in a PostgreSQL database hosted on
            Neon with encryption at rest and in transit. Passwords are hashed
            using bcrypt. Access tokens use JWT with short expiration windows.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            5. Your Rights
          </h2>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Access and export all your personal data at any time</li>
            <li>Request correction of inaccurate information</li>
            <li>Delete your account and all associated data</li>
            <li>Opt out of AI-powered features</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            6. Contact
          </h2>
          <p className="mt-2">
            For privacy-related inquiries, please contact us at{" "}
            <span className="font-medium text-foreground">privacy@jobhunter.app</span>.
          </p>
        </section>
      </div>

      <div className="mt-12 border-t border-foreground/10 pt-6">
        <Link
          href="/"
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          Back to Home
        </Link>
      </div>
    </main>
  );
}
