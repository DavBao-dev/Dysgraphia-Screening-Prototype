"use client";

import Dropzone, { type DropzoneValue } from "./Dropzone";

interface HandwritingPanelProps {
  onFile: (file: File | null) => void;
  value?: DropzoneValue;
}

export default function HandwritingPanel({ onFile, value }: HandwritingPanelProps) {
  return (
    <div>
      <Dropzone
        accept=".png,.jpg,.jpeg"
        title="Thả ảnh chữ viết vào đây"
        value={value}
        onFile={(f) => onFile(f)}
        onRemove={() => onFile(null)}
      />
    </div>
  );
}
