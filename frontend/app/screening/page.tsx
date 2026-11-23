"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import StudentInput from "@/components/StudentInput";
import StepCard from "@/components/StepCard";
import TipList from "@/components/TipList";
import VideoPanel from "@/components/VideoPanel";
import HandwritingPanel from "@/components/HandwritingPanel";
import RunButton from "@/components/RunButton";
import type { DropzoneValue } from "@/components/Dropzone";
import type { LiveData } from "@/components/LiveCamera";
import { runScreening } from "@/lib/api";
import { MIN_LIVE_FRAMES } from "@/lib/constants";

const VIDEO_TIPS = [
  "Đặt điện thoại phía trên bàn, quay từ trên xuống, thấy rõ bàn tay cầm bút",
  "Để em chép bài bình thường trong khoảng 15 đến 30 giây",
  "Ngồi chỗ đủ sáng, tránh quay ngược sáng",
  "Không cần quay khuôn mặt của em",
];

const IMAGE_TIPS = [
  "Chụp thẳng từ trên xuống, không nghiêng máy",
  "Chụp 2 hoặc 3 dòng em tự viết",
  "Không để bóng tay hay bóng điện thoại đè lên chữ",
];

export default function ScreeningPage() {
  const router = useRouter();
  const [patientId, setPatientId] = useState("");
  const [mode, setMode] = useState<"video" | "live">("video");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoDuration, setVideoDuration] = useState<number | undefined>(undefined);
  const [liveData, setLiveData] = useState<LiveData | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const videoValue: DropzoneValue | undefined = videoFile
    ? { name: videoFile.name, size: videoFile.size, duration: videoDuration }
    : undefined;

  const hasModelA =
    mode === "video" ? !!videoFile : !!liveData && liveData.landmarks.length >= MIN_LIVE_FRAMES;

  function handleVideoFile(file: File | null) {
    setVideoFile(file);
    setError(null);
    if (!file) {
      setVideoDuration(undefined);
      return;
    }
    const url = URL.createObjectURL(file);
    const probe = document.createElement("video");
    probe.preload = "metadata";
    probe.muted = true;
    probe.onloadedmetadata = () => {
      if (Number.isFinite(probe.duration)) setVideoDuration(probe.duration);
      URL.revokeObjectURL(url);
    };
    probe.onerror = () => URL.revokeObjectURL(url);
    probe.src = url;
  }

  function handleLiveData(data: LiveData | null) {
    setLiveData(data);
    setError(null);
  }

  function handleImageFile(file: File | null) {
    setImageFile(file);
    setError(null);
  }

  function handleModeChange(next: "video" | "live") {
    setMode(next);
    setLiveData(null);
    setError(null);
  }

  async function handleRun() {
    if (loading || !hasModelA) return;
    setLoading(true);
    setError(null);

    const form = new FormData();
    form.append("patient_id", patientId.trim() || "Chưa đặt mã");
    form.append("model_a_source", mode);
    if (mode === "video" && videoFile) {
      form.append("video", videoFile);
    } else if (liveData) {
      form.append(
        "landmarks_json",
        JSON.stringify({ landmarks: liveData.landmarks, fps: liveData.fps })
      );
    }
    if (imageFile) form.append("image", imageFile);

    try {
      const result = await runScreening(form);
      router.push(`/results/${result.session_id}`);
    } catch (e) {
      setLoading(false);
      setError(e instanceof Error ? e.message : "Đã có lỗi xảy ra. Vui lòng thử lại.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-4 pt-8 sm:px-6 sm:pt-12">
      <h1 className="font-serif text-[2rem] font-semibold leading-tight text-text sm:text-[2.4rem]">
        Kiểm tra cho một em
      </h1>
      <p className="mt-3 max-w-2xl text-lg leading-8 text-muted">
        Điền lần lượt ba bước dưới đây. Chỉ có video bàn tay là bắt buộc, phần còn lại có thể bỏ qua.
      </p>

      <div className="mt-8 border-b border-border">
        <StepCard number={1} title="Em nào đang được kiểm tra?" optional done={patientId.trim().length > 0}>
          <StudentInput
            value={patientId}
            onChange={(v) => {
              setPatientId(v);
              setError(null);
            }}
          />
        </StepCard>

        <StepCard
          number={2}
          title="Video bàn tay khi em viết"
          done={hasModelA}
          description="Hệ thống xem cách bàn tay di chuyển: tốc độ, độ mượt của nét, những lần dừng bút và độ run tay."
        >
          <div className="space-y-5">
            <TipList title="Cách quay" tips={VIDEO_TIPS} />
            <VideoPanel
              mode={mode}
              onModeChange={handleModeChange}
              videoValue={videoValue}
              onVideoFile={handleVideoFile}
              liveData={liveData}
              onLiveData={handleLiveData}
              onRetake={() => handleLiveData(null)}
            />
          </div>
        </StepCard>

        <StepCard
          number={3}
          title="Ảnh chụp trang vở"
          optional
          done={!!imageFile}
          description="Thêm ảnh để hệ thống xem cả hình dạng chữ: nét đậm hay nhạt, chữ có bám dòng hay không."
        >
          <div className="space-y-5">
            <TipList title="Cách chụp" tips={IMAGE_TIPS} />
            <HandwritingPanel
              onFile={handleImageFile}
              value={imageFile ? { name: imageFile.name, size: imageFile.size } : undefined}
            />
          </div>
        </StepCard>
      </div>

      <div className="py-8 md:pl-[252px]">
        <RunButton
          disabled={!hasModelA}
          loading={loading}
          error={error ?? undefined}
          hint={hasModelA ? "Kết quả hiện ngay sau khi phân tích xong." : "Cần có video bàn tay ở Bước 2 thì mới xem được kết quả."}
          onClick={() => void handleRun()}
        />
        <p className="mt-6 max-w-xl text-sm leading-relaxed text-muted">
          Video và ảnh không được lưu lại sau khi phân tích. Hệ thống chỉ lưu kết quả kèm mã học sinh bạn nhập.
        </p>
      </div>
    </div>
  );
}
