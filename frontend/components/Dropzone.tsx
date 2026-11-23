"use client";

import { useRef, useState } from "react";

import { MAX_VIDEO_BYTES, MAX_VIDEO_MB, MAX_VIDEO_MSG } from "@/lib/constants";
import { UploadIcon } from "./Icons";

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

export default function Dropzone({ accept, onFile, value, onRemove, title }: DropzoneProps) {
  const isVideoAccept = accept.includes("mp4") || accept.includes("video");
  const dropTitle = title ?? (isVideoAccept ? "Chọn video từ máy" : "Chọn ảnh từ máy");
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<File | null>(null);
  const urlRef = useRef<string | null>(null);
  const dragCounterRef = useRef(0);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);

  function acceptFile(next: File) {
    if (!matchesAccept(next, accept)) {
      setError(isVideoAccept ? "Tệp này không phải video được hỗ trợ (MP4, MOV, AVI)." : "Tệp này không phải ảnh PNG hoặc JPG.");
      return;
    }
    if (isVideoFile(next.name) && next.size > MAX_VIDEO_BYTES) {
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
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-sheet border border-green/40 bg-green-soft px-4 py-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-green">✓ Đã chọn tệp</p>
            <p className="truncate text-base font-medium text-text">{info.name}</p>
            <p className="text-sm text-muted">
              {(info.size / (1024 * 1024)).toFixed(1)} MB
              {info.duration ? ` · ${Math.round(info.duration)} giây` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="min-h-11 shrink-0 rounded-md border border-border bg-surface px-4 text-sm font-medium text-text hover:bg-surface-2 active:bg-border"
          >
            Chọn tệp khác
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
          className={`flex flex-col items-center justify-center gap-1 rounded-sheet border-2 border-dashed px-6 py-7 text-center ${
            drag ? "border-accent bg-accent-soft" : "border-field-accent bg-surface hover:border-accent active:bg-accent-soft"
          }`}
        >
          {/* Upload glyph: says "this box takes a file", the only icon on the form. */}
          <UploadIcon className="h-6 w-6 text-accent" />
          <p className="mt-1 text-base font-semibold text-accent-2 underline decoration-1 underline-offset-4">{dropTitle}</p>
          <p className="text-[15px] text-muted">hoặc kéo thả tệp vào đây</p>
          <p className="text-sm text-muted">
            {isVideoAccept ? `Video MP4, MOV, AVI · tối đa ${MAX_VIDEO_MB} MB` : "Ảnh PNG hoặc JPG"}
          </p>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-2 text-[15px] text-red">
          {error}
        </p>
      )}
    </div>
  );
}