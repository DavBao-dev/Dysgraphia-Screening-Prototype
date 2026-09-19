"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import StudentInput from "@/components/StudentInput";
import ProgressSteps from "@/components/ProgressSteps";
import DetailsSection from "@/components/DetailsSection";
import VideoPanel from "@/components/VideoPanel";
import HandwritingPanel from "@/components/HandwritingPanel";
import RunButton from "@/components/RunButton";
import type { DropzoneValue } from "@/components/Dropzone";
import type { LiveData } from "@/components/LiveCamera";
import { runScreening } from "@/lib/api";

const MIN_LIVE_FRAMES = 15;

const PROGRESS_STEPS = ["1. Chuyển động tay", "2. Chữ viết tay", "3. Kết quả"];

export default function ScreeningPage() {
  const router = useRouter();
  const [patientId, setPatientId] = useState("student_001");
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

  const progressStep = !hasModelA ? 0 : imageFile ? 2 : 1;

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
    form.append("patient_id", patientId.trim() || "student_001");
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
    <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-8">
      <h1 className="text-3xl font-bold tracking-tight text-text">Sàng lọc chữ viết</h1>
      <p className="mt-2 text-sm text-muted">
        Đánh giá một vài đặc điểm trong cách bạn viết và chuyển động tay.
      </p>

      <div className="mt-4 flex justify-center">
        <ProgressSteps steps={PROGRESS_STEPS} current={progressStep} />
      </div>

      <div className="mt-4">
        <StudentInput value={patientId} onChange={(v) => { setPatientId(v); setError(null); }} />
      </div>

      <div className="mt-6 rounded-xl border border-border bg-surface p-4 sm:p-5">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-10">
          <section className="border-b border-border pb-6 lg:border-b-0 lg:border-r lg:pb-0 lg:pr-8">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-accent">01</span>
                <h2 className="text-lg font-semibold text-text">Chuyển động tay</h2>
              </div>
              <span className="rounded-full bg-accent px-2.5 py-0.5 text-xs font-medium text-white">
                Bắt buộc
              </span>
            </div>
            <div className="mt-3">
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
            <div className="mt-3">
              <DetailsSection>
                <ul className="list-disc space-y-1 pl-4">
                  <li>Một đoạn video ngắn (vài giây) với bàn tay trong khung hình là đủ.</li>
                  <li>Cần ít nhất 15 khung hình có bàn tay để phân tích chuyển động.</li>
                  <li>Đảm bảo đủ ánh sáng và bàn tay nằm gọn trong khung hình.</li>
                  <li>Video chỉ dùng trong phiên hiện tại, không lưu lại hình ảnh gốc.</li>
                </ul>
              </DetailsSection>
            </div>
          </section>

          <section className="lg:pl-8">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-accent">02</span>
                <h2 className="text-lg font-semibold text-text">Chữ viết tay</h2>
              </div>
              <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs font-medium text-teal">
                Tùy chọn
              </span>
            </div>
            <p className="mt-1 text-sm text-muted">
              Thêm ảnh chữ viết tay để có thêm một nguồn phân tích.
            </p>
            <div className="mt-3">
              <HandwritingPanel
                file={imageFile}
                onFile={handleImageFile}
                value={imageFile ? { name: imageFile.name, size: imageFile.size } : undefined}
              />
            </div>
          </section>
        </div>

        <div className="mt-5 flex flex-col items-center border-t border-border pt-4">
          <RunButton
            disabled={!hasModelA}
            loading={loading}
            error={error ?? undefined}
            onClick={() => void handleRun()}
          />
        </div>
      </div>

      <p className="mt-5 text-center text-xs text-muted">
        Đây là công cụ sàng lọc, không phải chẩn đoán. Kết quả chỉ mang tính tham khảo.
      </p>
    </main>
  );
}