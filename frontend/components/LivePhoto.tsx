"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Status = "idle" | "starting" | "live" | "captured" | "saving" | "done";
const BUTTON = "min-h-11 rounded-md border border-field bg-surface px-4 text-[15px] font-medium text-text hover:border-accent disabled:cursor-not-allowed disabled:opacity-50";

export default function LivePhoto({ onFile }: { onFile: (file: File | null) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewRef = useRef<HTMLCanvasElement>(null);
  const sourceRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  // Cancels late camera grants or JPEG callbacks after closing, retaking or leaving the panel.
  const requestRef = useRef(0);
  const [status, setStatus] = useState<Status>("idle");
  const [rotation, setRotation] = useState(0);
  const [error, setError] = useState("");

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(() => () => {
    requestRef.current += 1;
    stopStream();
    sourceRef.current = null;
  }, [stopStream]);

  useEffect(() => {
    const source = sourceRef.current;
    const preview = previewRef.current;
    if (!source || !preview) return;
    const quarterTurn = rotation % 180 !== 0;
    preview.width = quarterTurn ? source.height : source.width;
    preview.height = quarterTurn ? source.width : source.height;
    const ctx = preview.getContext("2d");
    if (!ctx) return;
    ctx.translate(preview.width / 2, preview.height / 2);
    ctx.rotate(rotation * Math.PI / 180);
    ctx.drawImage(source, -source.width / 2, -source.height / 2);
  }, [rotation, status]);

  async function start() {
    if (status === "starting" || status === "live" || status === "saving") return;
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError("Camera cần HTTPS hoặc localhost và trình duyệt hỗ trợ. Bạn vẫn có thể tải ảnh từ máy.");
      return;
    }
    const request = ++requestRef.current;
    setError("");
    setStatus("starting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
      });
      if (request !== requestRef.current) {
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) { stopStream(); return; }
      video.srcObject = stream;
      await video.play();
      if (request !== requestRef.current) return;
      setStatus("live");
    } catch (cause) {
      if (request !== requestRef.current) return;
      stopStream();
      setStatus("idle");
      const name = cause instanceof DOMException ? cause.name : "";
      setError(name === "NotAllowedError"
        ? "Chưa được cấp quyền camera. Hãy cho phép camera trong trình duyệt hoặc tải ảnh từ máy."
        : name === "NotFoundError"
          ? "Không tìm thấy camera. Bạn có thể tải ảnh từ máy."
          : "Không mở được camera. Hãy đóng ứng dụng đang dùng camera và thử lại, hoặc tải ảnh từ máy.");
    }
  }

  function close() {
    requestRef.current += 1;
    stopStream();
    setStatus("idle");
    setError("");
  }

  function capture() {
    const video = videoRef.current;
    if (status !== "live" || !video?.videoWidth || !video.videoHeight) {
      setError("Camera chưa có hình. Hãy đợi hình ảnh xuất hiện rồi chụp lại.");
      return;
    }
    const source = document.createElement("canvas");
    source.width = video.videoWidth;
    source.height = video.videoHeight;
    const ctx = source.getContext("2d");
    if (!ctx) { setError("Không tạo được ảnh. Hãy thử lại hoặc tải ảnh từ máy."); return; }
    // Do not mirror handwriting: the captured text must remain readable.
    ctx.drawImage(video, 0, 0);
    sourceRef.current = source;
    stopStream();
    setRotation(0);
    setError("");
    setStatus("captured");
  }

  function retake() {
    requestRef.current += 1;
    stopStream();
    sourceRef.current = null;
    onFile(null);
    setRotation(0);
    setStatus("idle");
    setError("");
  }

  function usePhoto() {
    const preview = previewRef.current;
    if (!preview || status !== "captured") return;
    const request = ++requestRef.current;
    setStatus("saving");
    try {
      preview.toBlob(blob => {
        if (request !== requestRef.current) return;
        if (!blob) {
          setStatus("captured");
          setError("Không tạo được tệp ảnh. Vui lòng thử lại.");
          return;
        }
        onFile(new File([blob], `handwriting-camera-${Date.now()}.jpg`, { type: "image/jpeg" }));
        setStatus("done");
      }, "image/jpeg", 0.95);
    } catch {
      setStatus("captured");
      setError("Không tạo được tệp ảnh. Vui lòng thử lại.");
    }
  }

  const hasPhoto = status === "captured" || status === "saving" || status === "done";
  return <div>
    <p className="mb-3 text-[15px] leading-7 text-muted">Đặt trang viết trong khung hình, đủ sáng, không có họ tên hoặc khuôn mặt. Ảnh chỉ được gửi khi bạn bấm “Xem kết quả”.</p>
    <video ref={videoRef} autoPlay muted playsInline aria-label="Camera chụp trang viết" className={status === "live" || status === "starting" ? "aspect-video max-h-[480px] w-full rounded-sheet border border-border bg-black object-contain" : "hidden"} />
    <canvas ref={previewRef} role="img" aria-label={`Ảnh chụp trang viết, xoay ${rotation} độ`} className={hasPhoto ? "max-h-[520px] w-full rounded-sheet border border-border bg-surface object-contain" : "hidden"} />
    <p role="status" className="mt-3 text-[15px] leading-7 text-muted">
      {status === "idle" ? "Bấm mở camera để chuẩn bị chụp." : status === "starting" ? "Đang mở camera…" : status === "live" ? "Camera đã sẵn sàng. Giữ máy ổn định rồi bấm chụp." : status === "done" ? "Đã chọn ảnh này. Bạn có thể bấm “Xem kết quả” ở cuối trang." : "Kiểm tra chiều chữ, xoay ảnh nếu cần rồi bấm “Dùng ảnh này”."}
    </p>
    {error && <p role="alert" className="mt-3 text-[15px] text-red">{error}</p>}
    <div className="mt-4 flex flex-wrap gap-2">
      {status === "idle" && <button type="button" className={BUTTON} onClick={() => void start()}>Mở camera chụp ảnh</button>}
      {(status === "live" || status === "starting") && <>
        <button type="button" className={BUTTON} disabled={status !== "live"} onClick={capture}>Chụp ảnh</button>
        <button type="button" className={BUTTON} onClick={close}>Tắt camera</button>
      </>}
      {hasPhoto && <>
        <button type="button" className={BUTTON} disabled={status !== "captured"} onClick={() => setRotation(r => (r + 270) % 360)}>Xoay trái 90°</button>
        <button type="button" className={BUTTON} disabled={status !== "captured"} onClick={() => setRotation(r => (r + 90) % 360)}>Xoay phải 90°</button>
        <button type="button" className={BUTTON} disabled={status === "saving"} onClick={retake}>Chụp lại</button>
        {status !== "done" && <button type="button" className="min-h-11 rounded-md bg-accent px-5 text-[15px] font-semibold text-white disabled:opacity-50" disabled={status === "saving"} onClick={usePhoto}>{status === "saving" ? "Đang tạo ảnh…" : "Dùng ảnh này"}</button>}
      </>}
    </div>
  </div>;
}
