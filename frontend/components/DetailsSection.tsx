"use client";

import { useState } from "react";

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
        className="flex items-center gap-1.5 text-sm text-muted hover:text-text"
        aria-expanded={open}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
          aria-hidden="true"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
        {title}
      </button>
      {open && <div className="mt-2 rounded-lg bg-surface-2/60 p-3 text-sm text-muted">{children}</div>}
    </div>
  );
}