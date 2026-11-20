"use client";

import { useState } from "react";
import { ChevronDownIcon } from "./Icons";

interface DetailsSectionProps {
  title?: string;
  children: React.ReactNode;
}

export default function DetailsSection({ title = "Xem chi tiết", children }: DetailsSectionProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-md text-left text-[15px] font-medium text-accent-2 hover:underline"
        aria-expanded={open}
      >
        <ChevronDownIcon className={`h-4 w-4 shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
        {title}
      </button>
      {open && (
        <div className="mt-2 rounded-xl border border-border bg-surface-2 p-4 text-sm leading-relaxed text-muted">
          {children}
        </div>
      )}
    </div>
  );
}
