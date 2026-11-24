"use client";

import Dropzone, { type DropzoneValue } from "./Dropzone";
import LiveCamera, { type LiveData } from "./LiveCamera";
import { MIN_LIVE_FRAMES } from "@/lib/constants";

interface VideoPanelProps {
  mode: "video" | "live";
  onModeChange: (mode: "video" | "live") => void;
  videoValue?: DropzoneValue;
  onVideoFile: (file: File | null) => void;
  liveData: LiveData | null;
  onLiveData: (data: LiveData | null) => void;
  onRetake?: () => void;
}

const MODES = [
  { id: "video" as const, label: "Tải video đã quay" },
  { id: "live" as const, label: "Quay bằng camera máy này" },
];

export default function VideoPanel({
  mode,
  onModeChange,
  videoValue,
  onVideoFile,
  liveData,
  onLiveData,
  onRetake,
}: VideoPanelProps) {
  const frameCount = liveData?.landmarks.length ?? 0;

  return (
    <div>
      {/* Two-way switch built from pressed buttons (no tab semantics, so no arrow-key contract to break). */}
      <div role="group" aria-label="Cách đưa video vào" className="flex flex-wrap gap-2">
        {MODES.map(({ id, label }) => {
          const active = mode === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => onModeChange(id)}
              className={`min-h-11 rounded-md border px-4 text-[15px] font-medium ${
                active
                  ? "border-accent bg-accent-soft text-accent-2"
                  : "border-field bg-surface text-muted hover:border-accent hover:text-text active:bg-surface-2"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      <div className="mt-4">
        {mode === "video" ? (
          <Dropzone
            accept=".mp4,.mov,.avi,.mpeg4"
            value={videoValue}
            onFile={(f) => onVideoFile(f)}
            onRemove={() => onVideoFile(null)}
          />
        ) : (
          <div>
            <LiveCamera onResult={(data) => onLiveData(data)} onRetake={onRetake} />
            {frameCount > 0 && frameCount < MIN_LIVE_FRAMES && (
              <p className="mt-3 text-[15px] text-amber">Chưa đủ hình ảnh bàn tay. Hãy quay thêm một chút nữa.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
