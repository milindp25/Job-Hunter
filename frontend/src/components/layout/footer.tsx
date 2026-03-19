import Link from "next/link";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-foreground/10 bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center gap-4 px-4 py-6 sm:flex-row sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-6 text-sm text-foreground/50">
          <Link
            href="/about"
            className="transition-colors hover:text-foreground"
          >
            About
          </Link>
          <Link
            href="/privacy"
            className="transition-colors hover:text-foreground"
          >
            Privacy Policy
          </Link>
          <Link
            href="/terms"
            className="transition-colors hover:text-foreground"
          >
            Terms of Service
          </Link>
        </div>

        <div className="flex items-center gap-2 text-sm text-foreground/40">
          <span>&copy; {currentYear} Job Hunter. All rights reserved.</span>
          <span className="hidden sm:inline">&middot;</span>
          <span className="hidden sm:inline">Built with AI</span>
        </div>
      </div>
    </footer>
  );
}
