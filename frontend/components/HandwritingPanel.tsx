"use client";

import Dropzone, { type DropzoneValue } from "./Dropzone";

interface HandwritingPanelProps {
  onFile: (file: File | null) => void;
  value?: DropzoneValue;
}

export default function HandwritingPanel({ onFile, value }: HandwritingPanelProps) {
  return (
    <Dropzone
      accept=".png,.jpg,.jpeg"
      title="Chọn ảnh chụp trang viết"
      value={value}
      onFile={(f) => onFile(f)}
      onRemove={() => onFile(null)}
    />
  );
}
