"use client";

import { useEffect, useState } from "react";
import Dropzone, { type DropzoneValue } from "./Dropzone";

interface HandwritingPanelProps {
  file: File | null;
  onFile: (file: File | null) => void;
  value?: DropzoneValue;
}

export default function HandwritingPanel({ file, onFile, value }: HandwritingPanelProps) {
  const [previewFile, setPreviewFile] = useState<File | null>(file);
  const [preview, setPreview] = useState<string | null>(file ? URL.createObjectURL(file) : null);

  // Adjust derived state during render (documented React pattern), then revoke the
  // replaced object URL in the effect cleanup.
  if (file !== previewFile) {
    setPreviewFile(file);
    setPreview(file ? URL.createObjectURL(file) : null);
  }

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  return (
    <div>
      {preview && (
        <div className="mb-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Ảnh chữ viết tay"
            className="h-32 w-auto rounded-lg border border-border object-cover"
          />
        </div>
      )}
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