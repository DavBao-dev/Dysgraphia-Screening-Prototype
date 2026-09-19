"use client";

import { useRef, useState } from "react";

export interface DropzoneValue {
  name: string;
  size: number;
  duration?: number;
}

interface DropzoneProps {
  accept: string;
  onFile: (file: File) => void;
  value?: DropzoneValue;
  onRemove: () => void;
  title?: string;
}

function matchesAccept(file: File, accept: string): boolean {
  const accepted = accept
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const dot = file.name.lastIndexOf(".");
  const ext = dot >= 0 ? "." + file.name.slice(dot + 1).toLowerCase() : "";
  const type = file.type.toLowerCase();
  return accepted.some((a) => {
    if (a.startsWith(".")) return ext === a;
    if (a.endsWith("/*")) return type.startsWith(a.slice(0, -1));
    return type === a;
  });
}

function isVideoFile(name: string): boolean {
  return /\.(mp4|mov|avi|mpeg4)$/i.test(name);
}

const MAX_VIDEO_SIZE = 200 * 1024 * 1024;
const MAX_VIDEO_MSG = "Video quá lớn. Vui lòng chọn video nhỏ hơn 200 MB.";

export default function Dropzone({ accept, onFile, value, onRemove, title }: DropzoneProps) {
  const isVideoAccept = accept.includes("mp4") || accept.includes("video");
  const dropTitle = title ?? (isVideoAccept ? "Thả video vào đây" : "Thả ảnh vào đây");
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<File | null>(null);
  const urlRef = useRef<string | null>(null);
  const dragCounterRef = useRef(0);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);

  function acceptFile(next: File) {
    if (!matchesAccept(next, accept)) {
      setError("Định dạng tệp không hỗ trợ.");
      return;
    }
    if (isVideoFile(next.name) && next.size > MAX_VIDEO_SIZE) {
      setError(MAX_VIDEO_MSG);
      return;
    }
    setError(null);
    fileRef.current = next;
    setDuration(null);
    if (isVideoFile(next.name)) {
      const url = URL.createObjectURL(next);
      urlRef.current = url;
      const probe = document.createElement("video");
      probe.preload = "metadata";
      probe.muted = true;
      probe.onloadedmetadata = () => {
        URL.revokeObjectURL(url);
        if (urlRef.current === url) urlRef.current = null;
        if (Number.isFinite(probe.duration)) setDuration(probe.duration);
      };
      probe.onerror = () => {
        URL.revokeObjectURL(url);
        if (urlRef.current === url) urlRef.current = null;
      };
      probe.src = url;
    }
    onFile(next);
  }

  function handleRemove() {
    setDuration(null);
    fileRef.current = null;
    onRemove();
  }

  function openPicker() {
    inputRef.current?.click();
  }

  const info = value
    ? { name: value.name, size: value.size, duration: duration ?? value.duration ?? null }
    : null;

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const next = e.target.files?.[0];
          if (next) acceptFile(next);
          e.target.value = "";
        }}
      />

      {info ? (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-surface-2 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="h-5 w-5 shrink-0 text-accent"
              aria-hidden="true"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6M16 13H8M16 17H8" />
            </svg>
            <div className="min-w-0">
              <p className="truncate text-sm text-text">{info.name}</p>
              <p className="text-xs text-muted">
                {(info.size / (1024 * 1024)).toFixed(2)} MB
                {info.duration ? ` • ${info.duration.toFixed(1)}s` : ""}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="shrink-0 rounded-md px-2 py-1 text-xs text-red hover:bg-surface"
          >
            Xóa
          </button>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={0}
          onClick={openPicker}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPicker();
            }
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            dragCounterRef.current += 1;
            setDrag(true);
          }}
          onDragOver={(e) => e.preventDefault()}
          onDragLeave={() => {
            dragCounterRef.current -= 1;
            if (dragCounterRef.current <= 0) {
              dragCounterRef.current = 0;
              setDrag(false);
            }
          }}
          onDrop={(e) => {
            e.preventDefault();
            dragCounterRef.current = 0;
            setDrag(false);
            const next = e.dataTransfer.files?.[0];
            if (next) acceptFile(next);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed px-6 py-3 text-center ${
            drag ? "border-accent bg-surface-2" : "border-border bg-surface"
          }`}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`h-5 w-5 ${drag ? "text-accent" : "text-muted"}`}
            aria-hidden="true"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M17 8l-5-5-5 5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12 3v12" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="text-sm text-text">{dropTitle}</p>
          <p className="text-sm text-muted">hoặc chọn tệp từ thiết bị của bạn</p>
          <p className="text-xs text-muted">{isVideoAccept ? "MP4, MOV, AVI, MPEG4 • Tối đa 200 MB" : "PNG, JPG, JPEG"}</p>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-red">{error}</p>}
    </div>
  );
}