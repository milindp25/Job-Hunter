"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { FileDown, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useResumeGenerator } from "@/hooks/useResumeGenerator";
import { cn } from "@/lib/utils";

const ACCENT_PRESETS = [
  { label: "Navy", value: "#1a1a2e" },
  { label: "Blue", value: "#2563EB" },
  { label: "Teal", value: "#0D9488" },
  { label: "Purple", value: "#7C3AED" },
  { label: "Rose", value: "#E11D48" },
  { label: "Gray", value: "#374151" },
] as const;

interface TemplatPickerProps {
  resumeId: string;
  trigger?: React.ReactNode;
}

export function TemplatePicker({ resumeId, trigger }: TemplatPickerProps) {
  const { templates, isLoadingTemplates, isGenerating, generate } =
    useResumeGenerator();

  const [selectedTemplate, setSelectedTemplate] = useState("classic");
  const [selectedColor, setSelectedColor] = useState<string>(ACCENT_PRESETS[0].value);
  const [open, setOpen] = useState(false);

  async function handleGenerate() {
    await generate(resumeId, selectedTemplate, selectedColor);
    toast.success("Resume PDF downloaded!");
    setOpen(false);
  }

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        {trigger ?? (
          <Button variant="outline" size="sm">
            <FileDown className="mr-1.5 h-4 w-4" />
            Generate PDF
          </Button>
        )}
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border border-foreground/10 bg-background p-6 shadow-lg focus:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]"
          aria-describedby="template-picker-desc"
        >
          <Dialog.Title className="text-lg font-semibold text-foreground">
            Generate Resume PDF
          </Dialog.Title>
          <Dialog.Description id="template-picker-desc" className="mt-1 text-sm text-foreground/60">
            Choose a template and accent colour, then generate your resume.
          </Dialog.Description>

          {/* Template grid */}
          <div className="mt-5">
            <p className="mb-2 text-sm font-medium text-foreground/80">
              Template
            </p>
            {isLoadingTemplates ? (
              <div className="grid grid-cols-3 gap-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-24 animate-pulse rounded-lg bg-foreground/10"
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-3">
                {templates.map((tpl) => (
                  <button
                    key={tpl.id}
                    type="button"
                    onClick={() => setSelectedTemplate(tpl.id)}
                    className={cn(
                      "rounded-lg border-2 p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                      selectedTemplate === tpl.id
                        ? "border-blue-600 bg-blue-50 dark:bg-blue-950/30"
                        : "border-foreground/10 hover:border-foreground/20",
                    )}
                  >
                    <p className="text-sm font-semibold text-foreground">
                      {tpl.name}
                    </p>
                    <p className="mt-1 text-xs text-foreground/60 line-clamp-2">
                      {tpl.description}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Accent colour */}
          <div className="mt-5">
            <p className="mb-2 text-sm font-medium text-foreground/80">
              Accent Colour
            </p>
            <div className="flex gap-2">
              {ACCENT_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  title={preset.label}
                  onClick={() => setSelectedColor(preset.value)}
                  className={cn(
                    "h-8 w-8 rounded-full border-2 transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                    selectedColor === preset.value
                      ? "scale-110 border-foreground"
                      : "border-transparent hover:scale-105",
                  )}
                  style={{ backgroundColor: preset.value }}
                  aria-label={`Select ${preset.label} accent colour`}
                />
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 flex justify-end gap-3">
            <Dialog.Close asChild>
              <Button variant="ghost" size="sm">
                Cancel
              </Button>
            </Dialog.Close>
            <Button
              size="sm"
              loading={isGenerating}
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              <FileDown className="mr-1.5 h-4 w-4" />
              Generate PDF
            </Button>
          </div>

          <Dialog.Close asChild>
            <button
              type="button"
              className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
