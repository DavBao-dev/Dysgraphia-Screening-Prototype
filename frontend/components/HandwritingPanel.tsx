"use client";

import { useState } from "react";
import Dropzone, { type DropzoneValue } from "./Dropzone";
import LivePhoto from "./LivePhoto";

interface HandwritingPanelProps {
  onFile: (file: File | null) => void;
  value?: DropzoneValue;
}

export default function HandwritingPanel({ onFile, value }: HandwritingPanelProps) {
  const [mode, setMode] = useState<"upload" | "camera">("upload");
  return (
    <div>
      <div role="group" aria-label="Cách đưa ảnh vào" className="flex flex-wrap gap-2">
        {([{ id: "upload", label: "Tải ảnh đã chụp" }, { id: "camera", label: "Chụp bằng camera máy này" }] as const).map(({ id, label }) => (
          <button key={id} type="button" aria-pressed={mode === id}
            onClick={() => { if (mode !== id) { onFile(null); setMode(id); } }}
            className={`min-h-11 rounded-md border px-4 text-[15px] font-medium ${mode === id ? "border-accent bg-accent-soft text-accent-2" : "border-field bg-surface text-muted hover:border-accent hover:text-text"}`}>
            {label}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {mode === "camera" ? <LivePhoto onFile={onFile} /> : <Dropzone
          accept=".png,.jpg,.jpeg"
          title="Chọn ảnh chụp trang viết"
          value={value}
          onFile={onFile}
          onRemove={() => onFile(null)}
        />}
      </div>
    </div>
  );
}
