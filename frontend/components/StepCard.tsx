import type { ReactNode } from "react";
import { CheckIcon } from "./Icons";

interface StepCardProps {
  number: number;
  title: string;
  optional?: boolean;
  done?: boolean;
  description?: ReactNode;
  children: ReactNode;
}

export default function StepCard({ number, title, optional, done, description, children }: StepCardProps) {
  return (
    <section
      aria-labelledby={`step-${number}-title`}
      className={`rounded-2xl border bg-surface p-5 shadow-sm sm:p-6 ${done ? "border-green/40" : "border-border"}`}
    >
      <div className="flex items-start gap-4">
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-base font-bold ${
            done ? "bg-green text-white" : "bg-accent-soft text-accent-2"
          }`}
          aria-hidden="true"
        >
          {done ? <CheckIcon className="h-5 w-5" /> : number}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h2 id={`step-${number}-title`} className="text-xl font-semibold text-text">
              <span className="sr-only">Bước {number}: </span>
              {title}
            </h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${
                optional ? "bg-surface-2 text-muted" : "bg-accent-soft text-accent-2"
              }`}
            >
              {optional ? "Không bắt buộc" : "Bắt buộc"}
            </span>
            {done && <span className="text-sm font-medium text-green">Đã xong</span>}
          </div>
          {description && <div className="mt-1.5 text-base leading-relaxed text-muted">{description}</div>}
        </div>
      </div>
      <div className="mt-5 sm:pl-[52px]">{children}</div>
    </section>
  );
}
