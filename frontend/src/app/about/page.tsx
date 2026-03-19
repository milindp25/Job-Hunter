import type { Metadata } from "next";
import Link from "next/link";
import {
  Brain,
  ShieldCheck,
  FileText,
  Wand2,
  UserPlus,
  Search,
  ScanSearch,
  Rocket,
  ArrowRight,
  Cpu,
  Layers,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "About - Job Hunter",
  description:
    "Learn about Job Hunter, the AI-powered job matching platform that helps you land your dream job.",
};

const capabilities = [
  {
    icon: Brain,
    title: "AI-Powered Job Matching",
    description:
      "Advanced natural language processing analyzes your skills, experience, and career goals to surface the most relevant opportunities from thousands of listings across multiple job boards.",
  },
  {
    icon: FileText,
    title: "Resume Tailoring",
    description:
      "Generate professionally formatted resumes customized for each application. Our AI rewrites and optimizes content to highlight the skills and experience each employer is looking for.",
  },
  {
    icon: ShieldCheck,
    title: "ATS Compliance Checking",
    description:
      "Test your resume against the same Applicant Tracking Systems used by Fortune 500 companies. Get actionable feedback to ensure your resume passes automated screening.",
  },
  {
    icon: Wand2,
    title: "Smart Resume Generation",
    description:
      "Create polished, professional resumes from scratch using beautiful LaTeX templates. One-click PDF export with formatting that stands out to both humans and machines.",
  },
] as const;

const steps = [
  {
    icon: UserPlus,
    title: "Build Your Profile",
    description:
      "Upload your existing resume or connect your LinkedIn profile. Our AI extracts your skills, experience, education, and career preferences automatically — no manual data entry required.",
  },
  {
    icon: Search,
    title: "Discover Opportunities",
    description:
      "We aggregate jobs from RemoteOK, The Muse, Adzuna, Indeed, USAJobs, and more. Each listing is scored and ranked based on how well it matches your unique profile.",
  },
  {
    icon: ScanSearch,
    title: "Optimize Your Resume",
    description:
      "Run your resume through real ATS parsers to see exactly how automated systems read it. Identify formatting issues, missing keywords, and structural problems before you apply.",
  },
  {
    icon: Rocket,
    title: "Apply with Confidence",
    description:
      "Generate a tailored resume for each job with a single click. Every version is optimized for ATS compatibility and highlights the experience most relevant to the role.",
  },
] as const;

const techHighlights = [
  {
    icon: Cpu,
    title: "AI at the Core",
    description:
      "Powered by state-of-the-art language models for intelligent matching, resume analysis, and content generation.",
  },
  {
    icon: Layers,
    title: "Modern Architecture",
    description:
      "Built with a modern web stack designed for speed, reliability, and a seamless user experience across all devices.",
  },
  {
    icon: Zap,
    title: "Real-Time Processing",
    description:
      "Instant job matching and resume analysis with results delivered in seconds, not minutes.",
  },
] as const;

export default function AboutPage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-50 via-white to-slate-50 dark:from-blue-950/20 dark:via-background dark:to-slate-950/20" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(37,99,235,0.12),transparent)] dark:bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(37,99,235,0.08),transparent)]" />

        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              About <span className="text-blue-600">Job Hunter</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-foreground/70 sm:text-xl">
              Job Hunter is an AI-powered platform that transforms how you
              search for jobs. We combine intelligent matching, automated resume
              optimization, and real ATS compliance checking to help you land
              more interviews and find the right role faster.
            </p>
          </div>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="border-t border-foreground/5 bg-white dark:bg-background">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              What We Do
            </h2>
            <p className="mt-4 text-lg text-foreground/60">
              Four powerful capabilities working together to accelerate your job
              search.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl gap-8 sm:grid-cols-2">
            {capabilities.map((capability) => (
              <div
                key={capability.title}
                className="group relative rounded-2xl border border-foreground/10 bg-background p-8 transition-colors hover:border-blue-600/30 hover:bg-blue-50/50 dark:hover:bg-blue-950/20"
              >
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/50">
                  <capability.icon
                    className="h-6 w-6"
                    strokeWidth={1.5}
                  />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-foreground">
                  {capability.title}
                </h3>
                <p className="text-base leading-7 text-foreground/60">
                  {capability.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="border-t border-foreground/5 bg-slate-50 dark:bg-foreground/[0.02]">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              How It Works
            </h2>
            <p className="mt-4 text-lg text-foreground/60">
              From profile to offer — a streamlined process designed to maximize
              your success.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-4xl">
            <div className="grid gap-0 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map((step, index) => (
                <div
                  key={step.title}
                  className="relative flex flex-col items-center px-4 py-8 text-center"
                >
                  {index < steps.length - 1 && (
                    <div className="absolute right-0 top-[4.5rem] hidden h-px w-8 bg-blue-300 dark:bg-blue-800 lg:block" />
                  )}

                  <div className="relative mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-600/25">
                    <span className="text-xl font-bold">{index + 1}</span>
                    <div className="absolute -bottom-1.5 -right-1.5 flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm dark:bg-slate-800">
                      <step.icon
                        className="h-4 w-4 text-blue-600"
                        strokeWidth={2}
                      />
                    </div>
                  </div>

                  <h3 className="mb-2 text-lg font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="text-sm leading-6 text-foreground/60">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="border-t border-foreground/5 bg-white dark:bg-background">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Built with Modern Technology
            </h2>
            <p className="mt-4 text-lg text-foreground/60">
              Powered by AI and built on a modern web stack for speed and
              reliability.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-4xl gap-8 sm:grid-cols-3">
            {techHighlights.map((tech) => (
              <div
                key={tech.title}
                className="flex flex-col items-center rounded-2xl border border-foreground/10 bg-background p-8 text-center"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/50">
                  <tech.icon className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  {tech.title}
                </h3>
                <p className="text-sm leading-6 text-foreground/60">
                  {tech.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t border-foreground/5 bg-gradient-to-br from-blue-600 to-blue-700">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to Transform Your Job Search?
            </h2>
            <p className="mt-4 text-lg text-blue-100">
              Create your free account and let AI do the heavy lifting.
            </p>
            <div className="mt-10">
              <Button
                size="lg"
                className="bg-white text-blue-600 shadow-lg hover:bg-blue-50"
                asChild
              >
                <Link href="/register">
                  Get Started Free
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
