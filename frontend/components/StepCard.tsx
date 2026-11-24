import type { ReactNode } from "react";

interface StepCardProps {
  number: number;
  title: string;
  optional?: boolean;
  done?: boolean;
  description?: ReactNode;
  children: ReactNode;
}

// One step of the form, laid out like a numbered exercise: label column on the left, the work on the right.
export default function StepCard({ number, title, optional, done, description, children }: StepCardProps) {
  return (
    <section
      aria-labelledby={`step-${number}-title`}
      className="grid gap-x-8 gap-y-4 border-t border-border py-8 md:grid-cols-[220px_1fr]"
    >
      <div>
        <p className="text-sm font-semibold text-muted">
          Bước {number}
          <span className="font-normal"> · {optional ? "không bắt buộc" : "bắt buộc"}</span>
        </p>
        <h2 id={`step-${number}-title`} className="mt-1 font-serif text-xl font-semibold leading-snug text-text">
          {title}
        </h2>
        {done && (
          <p className="mt-2 text-sm font-semibold text-green" role="status">
            ✓ Đã xong
          </p>
        )}
      </div>
      <div className="min-w-0">
        {description && <p className="mb-4 text-base leading-7 text-muted">{description}</p>}
        {children}
      </div>
    </section>
  );
}
