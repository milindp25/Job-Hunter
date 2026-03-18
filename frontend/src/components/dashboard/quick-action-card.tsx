import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuickActionCardProps {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  variant?: "default" | "primary";
}

export function QuickActionCard({
  title,
  description,
  href,
  icon: Icon,
  variant = "default",
}: QuickActionCardProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group flex flex-col rounded-xl border p-6 transition-all hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
        variant === "primary"
          ? "border-blue-200 bg-blue-50 hover:border-blue-300 dark:border-blue-900 dark:bg-blue-950 dark:hover:border-blue-800"
          : "border-foreground/10 bg-background hover:border-foreground/20",
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-lg",
          variant === "primary"
            ? "bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400"
            : "bg-foreground/5 text-foreground/70",
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-sm text-foreground/60">{description}</p>
    </Link>
  );
}
