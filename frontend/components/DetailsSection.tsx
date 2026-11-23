"use client";

import { useState } from "react";

interface DetailsSectionProps {
  title?: string;
  children: React.ReactNode;
}

export default function DetailsSection({ title = "Xem chi tiết", children }: DetailsSectionProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="min-h-11 text-left text-[15px] font-medium text-accent-2 underline decoration-1 underline-offset-4 hover:decoration-2"
        aria-expanded={open}
      >
        {open ? `Ẩn ${title.toLowerCase()}` : title}
      </button>
      {open && <div className="mt-2 rounded-sheet bg-surface-2 p-4 text-sm leading-relaxed text-muted">{children}</div>}
    </div>
  );
}
