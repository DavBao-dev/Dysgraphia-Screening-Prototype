"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import StudentInput from "@/components/StudentInput";
import StepCard from "@/components/StepCard";
import TipList from "@/components/TipList";
import VideoPanel from "@/components/VideoPanel";
import HandwritingPanel from "@/components/HandwritingPanel";
import RunButton from "@/components/RunButton";
import { ArrowLeftIcon, ShieldIcon } from "@/components/Icons";
import type { DropzoneValue } from "@/components/Dropzone";
import type { LiveData } from "@/components/LiveCamera";
import { runScreening } from "@/lib/api";
import { MIN_LIVE_FRAMES } from "@/lib/constants";

const VIDEO_TIPS = [
  "Quay từ trên xuống, thấy rõ bàn tay cầm bút",
  "Trẻ viết bình thường khoảng 15–30 giây",
  "Đủ ánh sáng, không quay ngược sáng",
  "Giữ điện thoại cố định, không cần quay mặt trẻ",
];

const IMAGE_TIPS = [
  "Chụp thẳng trang vở, không nghiêng",
  "Chụp 2–3 dòng trẻ tự viết",
  "Đủ sáng, không bị bóng tay che",
  "Ảnh rõ nét, không bị mờ",
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
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <Link href="/" className="inline-flex items-center gap-1.5 text-[15px] font-medium text-accent-2 hover:underline">
        <ArrowLeftIcon className="h-4 w-4" />
        Trang chủ
      </Link>

      <h1 className="mt-3 text-3xl font-bold tracking-tight text-text">Kiểm tra dấu hiệu khó viết</h1>
      <p className="mt-2 text-lg leading-relaxed text-muted">
        Làm lần lượt các bước dưới đây. Chỉ có video bàn tay là bắt buộc.
      </p>

      <div className="mt-8 space-y-5">
        <StepCard number={1} title="Thông tin của trẻ" optional done={patientId.trim().length > 0}>
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
          title="Video bàn tay khi trẻ viết"
          done={hasModelA}
          description="Hệ thống xem cách bàn tay di chuyển: tốc độ, độ mượt, những lần dừng bút và độ run tay."
        >
          <div className="space-y-4">
            <TipList title="Cách quay video" tips={VIDEO_TIPS} />
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
          title="Ảnh chụp chữ viết"
          optional
          done={!!imageFile}
          description="Thêm ảnh giúp hệ thống xem cả hình dạng chữ: độ đậm nét và chữ có thẳng hàng hay không."
        >
          <div className="space-y-4">
            <TipList title="Cách chụp ảnh" tips={IMAGE_TIPS} />
            <HandwritingPanel
              onFile={handleImageFile}
              value={imageFile ? { name: imageFile.name, size: imageFile.size } : undefined}
            />
          </div>
        </StepCard>
      </div>

      <div className="mt-8 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <RunButton
          disabled={!hasModelA}
          loading={loading}
          error={error ?? undefined}
          hint={hasModelA ? "Kết quả sẽ hiện ngay sau khi phân tích xong." : "Hãy thêm video bàn tay ở Bước 2 để tiếp tục."}
          onClick={() => void handleRun()}
        />
      </div>

      <p className="mt-5 flex items-start justify-center gap-2 text-center text-sm text-muted">
        <ShieldIcon className="mt-0.5 h-4 w-4 shrink-0" />
        Video và ảnh không được lưu lại sau khi phân tích. Hệ thống chỉ lưu kết quả kèm mã học sinh.
      </p>
    </div>
  );
}
