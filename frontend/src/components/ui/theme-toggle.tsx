"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

const subscribe = () => () => {};
function useIsMounted() {
  return useSyncExternalStore(subscribe, () => true, () => false);
}

export function ThemeToggle() {
  const mounted = useIsMounted();
  const { resolvedTheme, setTheme } = useTheme();

  if (!mounted) {
    return (
      <button
        type="button"
        className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-foreground/70 transition-colors hover:bg-foreground/5 hover:text-foreground"
        aria-label="Toggle theme"
      >
        <span className="h-5 w-5" />
      </button>
    );
  }

  return (
    <button
      type="button"
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-foreground/70 transition-colors hover:bg-foreground/5 hover:text-foreground"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
    >
      {resolvedTheme === "dark" ? (
        <Sun className="h-5 w-5" />
      ) : (
        <Moon className="h-5 w-5" />
      )}
    </button>
  );
}
