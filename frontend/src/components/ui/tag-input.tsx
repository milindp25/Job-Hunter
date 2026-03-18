"use client";

import { useState, useCallback, type KeyboardEvent } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface TagInputProps {
  id?: string;
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  error?: boolean;
  disabled?: boolean;
}

export function TagInput({
  id,
  value,
  onChange,
  placeholder = "Type and press Enter to add...",
  error,
  disabled,
}: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addTag = useCallback(
    (tag: string) => {
      const trimmed = tag.trim();
      if (trimmed && !value.includes(trimmed)) {
        onChange([...value, trimmed]);
      }
      setInputValue("");
    },
    [value, onChange],
  );

  const removeTag = useCallback(
    (index: number) => {
      onChange(value.filter((_, i) => i !== index));
    },
    [value, onChange],
  );

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === "Backspace" && !inputValue && value.length > 0) {
      removeTag(value.length - 1);
    }
  }

  return (
    <div
      className={cn(
        "flex min-h-[40px] flex-wrap items-center gap-1.5 rounded-lg border bg-background px-3 py-1.5 transition-colors focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2",
        error
          ? "border-red-500 focus-within:ring-red-500"
          : "border-foreground/20",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {value.map((tag, index) => (
        <span
          key={`${tag}-${index}`}
          className="inline-flex items-center gap-1 rounded-md bg-blue-100 px-2 py-0.5 text-sm text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(index)}
            disabled={disabled}
            className="rounded-sm p-0.5 hover:bg-blue-200 dark:hover:bg-blue-800"
            aria-label={`Remove ${tag}`}
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        id={id}
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={value.length === 0 ? placeholder : ""}
        disabled={disabled}
        className="min-w-[120px] flex-1 border-none bg-transparent py-1 text-sm text-foreground outline-none placeholder:text-foreground/40"
      />
    </div>
  );
}
