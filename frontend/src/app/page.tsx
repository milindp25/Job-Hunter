import Link from "next/link";
import {
  Brain,
  ShieldCheck,
  FileText,
  UserPlus,
  Search,
  ScanSearch,
  Rocket,
  ArrowRight,
  Globe,
  Monitor,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Brain,
    title: "Smart Job Matching",
    description:
      "Our AI analyzes your skills, experience, and preferences to rank jobs by your likelihood of getting hired.",
  },
  {
    icon: ShieldCheck,
    title: "ATS Resume Checker",
    description:
      "Check your resume against the same systems Fortune 500 companies use — Workday, Greenhouse, Lever, and more.",
  },
  {
    icon: FileText,
    title: "Tailored Resumes",
    description:
      "Generate beautiful LaTeX resumes customized for each job application. One-click PDF export.",
  },
] as const;

const steps = [
  {
    icon: UserPlus,
    title: "Create Your Profile",
    description:
      "Upload your resume or connect LinkedIn. Our AI extracts your skills and experience automatically.",
  },
  {
    icon: Search,
    title: "Get Matched",
    description:
      "We search thousands of jobs from top job boards and rank them by your fit.",
  },
  {
    icon: ScanSearch,
    title: "Check ATS Compatibility",
    description:
      "See exactly how ATS systems will parse your resume. Fix issues before you apply.",
  },
  {
    icon: Rocket,
    title: "Apply with Confidence",
    description:
      "Generate a tailored resume for each job. Maximize your chances with AI-powered optimization.",
  },
] as const;

const stats = [
  {
    icon: Globe,
    value: "5+",
    label: "Job Boards",
    description: "Aggregated sources",
  },
  {
    icon: Monitor,
    value: "Top 6",
    label: "ATS Systems",
    description: "Checked against",
  },
  {
    icon: Sparkles,
    value: "Free",
    label: "To Use",
    description: "No credit card required",
  },
] as const;


export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-50 via-white to-slate-50 dark:from-blue-950/20 dark:via-background dark:to-slate-950/20" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(37,99,235,0.12),transparent)] dark:bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(37,99,235,0.08),transparent)]" />

        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8 lg:py-40">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Land Your Dream Job with{" "}
              <span className="text-blue-600">AI-Powered Matching</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-foreground/70 sm:text-xl">
              Upload your resume, get matched with the best opportunities, and
              generate ATS-optimized resumes that get past the filters.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button size="lg" asChild>
                <Link href="/register">
                  Get Started Free
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link href="#how-it-works">See How It Works</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="border-t border-foreground/5 bg-white dark:bg-background">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Everything you need to land your next role
            </h2>
            <p className="mt-4 text-lg text-foreground/60">
              Powerful tools designed to give you an unfair advantage in your job
              search.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group relative rounded-2xl border border-foreground/10 bg-background p-8 transition-colors hover:border-blue-600/30 hover:bg-blue-50/50 dark:hover:bg-blue-950/20"
              >
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/50">
                  <feature.icon className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-base leading-7 text-foreground/60">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section
        id="how-it-works"
        className="border-t border-foreground/5 bg-slate-50 dark:bg-foreground/[0.02]"
      >
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              How It Works
            </h2>
            <p className="mt-4 text-lg text-foreground/60">
              From profile to offer in four simple steps.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-4xl">
            <div className="grid gap-0 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map((step, index) => (
                <div key={step.title} className="relative flex flex-col items-center px-4 py-8 text-center">
                  {/* Connecting line (hidden on last item and on mobile) */}
                  {index < steps.length - 1 && (
                    <div className="absolute right-0 top-[4.5rem] hidden h-px w-8 bg-blue-300 dark:bg-blue-800 lg:block" />
                  )}

                  {/* Step number circle */}
                  <div className="relative mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-600/25">
                    <span className="text-xl font-bold">{index + 1}</span>
                    <div className="absolute -bottom-1.5 -right-1.5 flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm dark:bg-slate-800">
                      <step.icon className="h-4 w-4 text-blue-600" strokeWidth={2} />
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

      {/* Stats / Social Proof Section */}
      <section className="border-t border-foreground/5 bg-white dark:bg-background">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
          <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-3">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="flex flex-col items-center rounded-2xl border border-foreground/10 bg-background p-8 text-center"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/50">
                  <stat.icon className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <p className="text-3xl font-bold text-foreground sm:text-4xl">
                  {stat.value}
                </p>
                <p className="mt-1 text-lg font-semibold text-foreground">
                  {stat.label}
                </p>
                <p className="mt-1 text-sm text-foreground/50">
                  {stat.description}
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
              Ready to Find Your Perfect Job?
            </h2>
            <p className="mt-4 text-lg text-blue-100">
              Join thousands of job seekers who are landing more interviews with
              Job Hunter.
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
