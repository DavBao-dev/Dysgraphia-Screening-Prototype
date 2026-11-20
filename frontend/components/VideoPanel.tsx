"use client";

import Dropzone, { type DropzoneValue } from "./Dropzone";
import LiveCamera, { type LiveData } from "./LiveCamera";
import { UploadIcon, VideoIcon } from "./Icons";
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
  { id: "video" as const, label: "Tải video có sẵn", icon: UploadIcon },
  { id: "live" as const, label: "Quay bằng camera", icon: VideoIcon },
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
      <div role="tablist" aria-label="Cách cung cấp video" className="grid grid-cols-2 gap-1 rounded-xl bg-surface-2 p-1 sm:inline-grid">
        {MODES.map(({ id, label, icon: Icon }) => {
          const active = mode === id;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onModeChange(id)}
              className={`flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-[15px] font-medium transition-colors ${
                active ? "bg-surface text-accent-2 shadow-sm" : "text-muted hover:text-text"
              }`}
            >
              <Icon className="h-4 w-4" />
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
              <p className="mt-3 text-[15px] text-amber">
                Chưa đủ hình ảnh bàn tay. Hãy quay thêm một chút nữa nhé.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
