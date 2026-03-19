import type { TailoredResume } from "@/lib/types";

interface TailorDiffViewProps {
  tailored: TailoredResume;
  originalSummary?: string;
  originalSkills?: string[];
}

function ExperienceEntry({ entry }: { entry: Record<string, unknown> }) {
  const title = (entry.title as string) ?? "Untitled";
  const company = (entry.company as string) ?? "";
  const duration = (entry.duration as string) ?? "";
  const highlights = (entry.highlights as string[]) ?? [];

  return (
    <div className="rounded-lg border border-foreground/10 p-4">
      <div className="mb-2">
        <h4 className="font-semibold text-foreground">{title}</h4>
        {company && (
          <p className="text-sm text-foreground/70">
            {company}
            {duration ? ` | ${duration}` : ""}
          </p>
        )}
      </div>
      {highlights.length > 0 && (
        <ul className="ml-4 list-disc space-y-1">
          {highlights.map((highlight, idx) => (
            <li key={idx} className="text-sm text-foreground/80">
              {highlight}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function TailorDiffView({
  tailored,
  originalSummary,
  originalSkills,
}: TailorDiffViewProps) {
  return (
    <div className="space-y-8">
      {/* Summary Section */}
      <section>
        <h2 className="mb-4 text-lg font-bold text-foreground">
          Professional Summary
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium text-foreground/60">
              Original
            </h3>
            <div className="rounded-lg border border-foreground/10 bg-foreground/[0.02] p-4">
              <p className="text-sm text-foreground/70">
                {originalSummary || "No summary provided"}
              </p>
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-green-700 dark:text-green-300">
              Tailored
            </h3>
            <div className="rounded-lg border border-green-200 bg-green-50/50 p-4 dark:border-green-800 dark:bg-green-950/50">
              <p className="text-sm text-foreground">
                {tailored.tailored_summary || "No tailored summary"}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Experience Section */}
      {tailored.tailored_experience.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-bold text-foreground">
            Experience
          </h2>
          <div className="space-y-3">
            {tailored.tailored_experience.map((entry, idx) => (
              <ExperienceEntry key={idx} entry={entry} />
            ))}
          </div>
        </section>
      )}

      {/* Skills Section */}
      <section>
        <h2 className="mb-4 text-lg font-bold text-foreground">Skills</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium text-foreground/60">
              Original Order
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {(originalSkills ?? []).map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center rounded-full bg-foreground/5 px-2.5 py-0.5 text-xs font-medium text-foreground/70"
                >
                  {skill}
                </span>
              ))}
              {(!originalSkills || originalSkills.length === 0) && (
                <p className="text-sm text-foreground/50">No skills listed</p>
              )}
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-medium text-green-700 dark:text-green-300">
              Tailored &amp; Reordered
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {tailored.tailored_skills.map((skill, idx) => (
                <span
                  key={skill}
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    idx < 3
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : "bg-foreground/5 text-foreground/70"
                  }`}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
