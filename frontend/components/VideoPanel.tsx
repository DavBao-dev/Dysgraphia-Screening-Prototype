"use client";

import Dropzone, { type DropzoneValue } from "./Dropzone";
import LiveCamera, { type LiveData } from "./LiveCamera";

interface VideoPanelProps {
  mode: "video" | "live";
  onModeChange: (mode: "video" | "live") => void;
  videoValue?: DropzoneValue;
  onVideoFile: (file: File | null) => void;
  liveData: LiveData | null;
  onLiveData: (data: LiveData | null) => void;
  onRetake?: () => void;
}

const MIN_FRAMES = 15;

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
      <div className="inline-flex flex-wrap rounded-lg bg-surface-2 p-1">
        {(["video", "live"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => onModeChange(m)}
            className={`rounded-md px-4 py-2 text-sm font-medium ${
              mode === m ? "bg-surface text-text" : "text-muted hover:text-text"
            }`}
          >
            {m === "video" ? "Tải video lên" : "Camera trực tiếp"}
          </button>
        ))}
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
            {frameCount > 0 && frameCount < MIN_FRAMES && (
              <p className="mt-3 text-sm text-amber">
                Cần ít nhất 15 khung hình có bàn tay. Ghi thêm một chút nữa nhé.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}