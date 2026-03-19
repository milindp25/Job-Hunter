import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service | Job Hunter",
  description: "Terms and conditions for using Job Hunter",
};

export default function TermsOfServicePage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-foreground">Terms of Service</h1>
      <p className="mt-2 text-sm text-foreground/50">
        Last updated: March 2026
      </p>

      <div className="mt-8 space-y-8 text-foreground/80 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-foreground">
            1. Service Description
          </h2>
          <p className="mt-2">
            Job Hunter is an AI-powered platform that helps job seekers find
            relevant opportunities by analyzing their profiles, matching them
            with job listings from multiple sources, and providing resume
            optimization tools.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            2. User Responsibilities
          </h2>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Provide accurate and truthful information in your profile</li>
            <li>Keep your login credentials secure and confidential</li>
            <li>Use the platform for legitimate job-seeking purposes only</li>
            <li>Respect the intellectual property of job listings and content</li>
            <li>Do not attempt to scrape, reverse-engineer, or abuse the service</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            3. AI-Generated Content Disclaimer
          </h2>
          <p className="mt-2">
            Job Hunter uses artificial intelligence to generate match scores,
            resume suggestions, and other recommendations. This content is
            provided as guidance only and may contain inaccuracies. You are
            responsible for reviewing and verifying all AI-generated suggestions
            before acting on them.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            4. No Guarantee of Employment
          </h2>
          <p className="mt-2">
            Job Hunter is a tool to assist your job search. We do not guarantee
            employment, interviews, or any specific outcomes. Job listings are
            sourced from third parties and may be outdated or inaccurate.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            5. Limitation of Liability
          </h2>
          <p className="mt-2">
            To the maximum extent permitted by law, Job Hunter and its
            operators shall not be liable for any indirect, incidental, or
            consequential damages arising from the use of this service. The
            platform is provided &ldquo;as is&rdquo; without warranties of any
            kind.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            6. Account Termination
          </h2>
          <p className="mt-2">
            We reserve the right to suspend or terminate accounts that violate
            these terms. You may delete your account at any time, which will
            permanently remove all your data from our systems.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-foreground">
            7. Changes to Terms
          </h2>
          <p className="mt-2">
            We may update these terms from time to time. Continued use of the
            platform after changes constitutes acceptance of the updated terms.
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
