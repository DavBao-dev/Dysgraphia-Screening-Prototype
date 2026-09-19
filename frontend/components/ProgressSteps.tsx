interface ProgressStepsProps {
  steps: string[];
  current: number;
}

export default function ProgressSteps({ steps, current }: ProgressStepsProps) {
  return (
    <ol className="flex flex-wrap items-center gap-y-1 text-sm">
      {steps.map((step, i) => {
        const done = i < current;
        const active = i === current;
        const dotClass = active
          ? "bg-accent"
          : done
            ? "bg-green"
            : "bg-border/70";
        const labelClass = active
          ? "font-semibold text-text"
          : done
            ? "text-green"
            : "text-muted/70";
        return (
          <li key={step} className="flex items-center">
            {i > 0 && <span className="mx-2 h-px w-5 bg-border" aria-hidden="true" />}
            <span className={`flex items-center gap-1.5 ${labelClass}`}>
              <span className={`h-2 w-2 rounded-full ${dotClass}`} aria-hidden="true" />
              {step}
            </span>
          </li>
        );
      })}
    </ol>
  );
}