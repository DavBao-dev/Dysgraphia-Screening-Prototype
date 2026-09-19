"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface LiveData {
  landmarks: number[][][];
  fps: number;
}

interface LiveCameraProps {
  onResult: (data: LiveData) => void;
  onRetake?: () => void;
}

type Status = "idle" | "loading" | "recording" | "processing" | "done";

type HandLandmark = { x: number; y: number; z: number };

interface MediaPipeResults {
  image: CanvasImageSource;
  multiHandLandmarks?: HandLandmark[][];
}

interface HandsInstance {
  setOptions: (options: object) => void;
  onResults: (callback: (results: MediaPipeResults) => void) => void;
  send: (input: { image: HTMLVideoElement }) => Promise<void>;
  close: () => void;
}

const HANDS_CDN = "https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4";
const SCRIPTS: Array<{ src: string; global: string }> = [
  { src: "https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils@0.3/camera_utils.js", global: "Camera" },
  { src: `${HANDS_CDN}/hands.js`, global: "Hands" },
];

const HAND_CONNECTIONS: Array<[number, number]> = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const el = document.createElement("script");
    el.src = src;
    el.crossOrigin = "anonymous";
    el.async = true;
    el.onload = () => resolve();
    el.onerror = () => reject(new Error(`Không tải được script: ${src}`));
    document.head.appendChild(el);
  });
}

function computeMedianFps(timestamps: number[]): number {
  if (timestamps.length >= 2) {
    const intervals: number[] = [];
    for (let i = 1; i < timestamps.length; i++) intervals.push(timestamps[i] - timestamps[i - 1]);
    intervals.sort((a, b) => a - b);
    const median = intervals[Math.floor(intervals.length / 2)];
    if (median > 0) return Math.round(1000 / median);
  }
  return 30;
}

export default function LiveCamera({ onResult, onRetake }: LiveCameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const bufferRef = useRef<number[][][]>([]);
  const timestampsRef = useRef<number[]>([]);
  const runningRef = useRef(false);
  const startingRef = useRef(false);
  const rafRef = useRef(0);
  const streamRef = useRef<MediaStream | null>(null);
  const handsRef = useRef<HandsInstance | null>(null);
  const hasResultsRef = useRef(false);
  const scriptsLoadedRef = useRef(false);
  const procTimerRef = useRef(0);

  const [status, setStatus] = useState<Status>("idle");
  const [frameCount, setFrameCount] = useState(0);
  const [fps, setFps] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scriptsReady, setScriptsReady] = useState(false);

  // Load the MediaPipe Hands 0.4 CDN scripts once on mount.
  useEffect(() => {
    let disposed = false;
    (async () => {
      if (typeof window === "undefined") return;
      if (scriptsLoadedRef.current || "Hands" in window) {
        scriptsLoadedRef.current = true;
        if (!disposed) setScriptsReady(true);
        return;
      }
      for (const script of SCRIPTS) {
        if (!(script.global in window)) await loadScript(script.src);
      }
      scriptsLoadedRef.current = true;
      if (!disposed) setScriptsReady(true);
    })().catch((e: unknown) => {
      if (!disposed) {
        setError(e instanceof Error ? e.message : "Lỗi khi tải mô hình nhận dạng bàn tay.");
      }
    });
    return () => {
      disposed = true;
    };
  }, []);

  // Full teardown on unmount.
  useEffect(
    () => () => {
      window.clearTimeout(procTimerRef.current);
      runningRef.current = false;
      cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (handsRef.current) {
        try {
          handsRef.current.close();
        } catch {
          // ignore close errors
        }
        handsRef.current = null;
      }
    },
    []
  );

  const onResults = useCallback((results: MediaPipeResults) => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;
    hasResultsRef.current = true;
    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Mirror the preview horizontally (selfie view). Landmarks are drawn under
    // the same transform so the overlay stays aligned; the buffered landmark
    // values remain unmirrored (unchanged Model A input).
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
    const landmarks = results.multiHandLandmarks?.[0];
    if (landmarks && landmarks.length === 21) {
      bufferRef.current.push(landmarks.map((lm) => [lm.x, lm.y, lm.z]));
      timestampsRef.current.push(performance.now());
      setFrameCount(bufferRef.current.length);
      for (const [a, b] of HAND_CONNECTIONS) {
        ctx.beginPath();
        ctx.moveTo(landmarks[a].x * canvas.width, landmarks[a].y * canvas.height);
        ctx.lineTo(landmarks[b].x * canvas.width, landmarks[b].y * canvas.height);
        ctx.strokeStyle = "#34D399";
        ctx.lineWidth = 3;
        ctx.stroke();
      }
      for (const lm of landmarks) {
        ctx.beginPath();
        ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 4, 0, 2 * Math.PI);
        ctx.fillStyle = "#FF0000";
        ctx.fill();
      }
    }
    ctx.restore();
  }, []);

  function loop() {
    if (!runningRef.current) return;
    void (async () => {
      try {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = ctxRef.current;
        if (!hasResultsRef.current && video && canvas && ctx && video.readyState >= 2) {
          // Keep the pre-detection preview mirrored too, so it does not flip
          // once the first MediaPipe result arrives.
          ctx.save();
          ctx.translate(canvas.width, 0);
          ctx.scale(-1, 1);
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          ctx.restore();
        }
        if (handsRef.current && video && video.readyState >= 2) {
          await handsRef.current.send({ image: video });
        }
      } catch {
        // ignore per-frame errors
      }
      if (runningRef.current) {
        rafRef.current = requestAnimationFrame(loop);
      }
    })();
  }

  async function start() {
    if (startingRef.current || status === "recording" || status === "loading") return;
    startingRef.current = true;
    setError(null);
    setFrameCount(0);
    setFps(null);
    bufferRef.current = [];
    timestampsRef.current = [];
    hasResultsRef.current = false;

    try {
      if (!scriptsReady) {
        setStatus("loading");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) {
        stream.getTracks().forEach((t) => t.stop());
        setStatus("idle");
        return;
      }
      video.srcObject = stream;
      await video.play();

      ctxRef.current = canvasRef.current?.getContext("2d") ?? null;
      const hands = new window.Hands({ locateFile: (file: string) => `${HANDS_CDN}/${file}` });
      handsRef.current = hands as HandsInstance;
      hands.setOptions({
        maxNumHands: 1,
        modelComplexity: 1,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });
      hands.onResults(onResults);

      runningRef.current = true;
      setStatus("recording");
      rafRef.current = requestAnimationFrame(loop);
    } catch (e: unknown) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      runningRef.current = false;
      setError(e instanceof Error ? e.message : "Không thể truy cập camera. Kiểm tra quyền webcam.");
      setStatus("idle");
    } finally {
      startingRef.current = false;
    }
  }

  function stop() {
    runningRef.current = false;
    cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    if (handsRef.current) {
      try {
        handsRef.current.close();
      } catch {
        // ignore close errors
      }
      handsRef.current = null;
    }
    const medianFps = computeMedianFps(timestampsRef.current);
    setFps(medianFps);
    onResult({ landmarks: bufferRef.current, fps: medianFps });
    setStatus("processing");
    window.clearTimeout(procTimerRef.current);
    procTimerRef.current = window.setTimeout(() => setStatus("done"), 600);
  }

  function retake() {
    window.clearTimeout(procTimerRef.current);
    runningRef.current = false;
    cancelAnimationFrame(rafRef.current);
    setFrameCount(0);
    setFps(null);
    setError(null);
    onRetake?.();
    setStatus("idle");
    bufferRef.current = [];
    timestampsRef.current = [];
    hasResultsRef.current = false;
  }

  const stateMeta: Record<Status, { label: string; dot: string }> = {
    idle: { label: "Chuẩn bị", dot: "bg-muted" },
    loading: { label: "Đang chuẩn bị", dot: "bg-muted" },
    recording: { label: "Đang ghi", dot: "bg-accent" },
    processing: { label: "Đang xử lý", dot: "bg-amber" },
    done: { label: "Hoàn tất", dot: "bg-green" },
  };

  return (
    <div>
      <div
        className={`relative overflow-hidden rounded-lg ${
          status === "recording" && frameCount > 0
            ? "ring-2 ring-green/70"
            : "ring-1 ring-border"
        }`}
      >
        <video
          ref={videoRef}
          className="absolute -left-[9999px] top-0"
          playsInline
          muted
          width={640}
          height={480}
        />
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          className="aspect-video w-full bg-black"
        />
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="flex items-center gap-1.5 rounded-full bg-surface-2 px-3 py-1 text-xs text-muted">
          <span className={`h-2 w-2 rounded-full ${stateMeta[status].dot}`} aria-hidden="true" />
          {stateMeta[status].label}
        </span>
        {!scriptsReady && !error && (
          <p className="text-sm text-muted">Đang chuẩn bị camera và nhận diện bàn tay...</p>
        )}
      </div>

      {status === "idle" && (
        <div className="mt-3">
          <p className="text-sm font-medium text-text">Sẵn sàng nhé!</p>
          <ul className="mt-1.5 space-y-1 text-sm text-muted">
            <li>Giữ bàn tay trong khung hình, đủ ánh sáng.</li>
            <li>Tránh đứng ngược sáng để dễ nhận diện.</li>
            <li>Bấm Bắt đầu ghi rồi vẫy nhẹ bàn tay vài giây.</li>
          </ul>
        </div>
      )}

      {status === "loading" && (
        <p className="mt-3 text-sm text-muted">Đang mở camera, một chút nữa thôi...</p>
      )}

      {status === "recording" && (
        <p className="mt-3 text-sm text-muted">
          {frameCount > 0 ? (
            <span className="flex items-center gap-1.5 font-medium text-green">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green" aria-hidden="true" />
              Đã nhận diện bàn tay — đã ghi {frameCount} khung hình.
            </span>
          ) : (
            "Chưa thấy bàn tay. Đưa bàn tay vào khung hình nhé."
          )}
        </p>
      )}

      {status === "processing" && (
        <p className="mt-3 text-sm text-amber">Đang xử lý dữ liệu chuyển động...</p>
      )}

      {status === "done" && (
        <p className="mt-3 text-sm text-green">
          Hoàn tất! Đã ghi nhận {frameCount} khung hình có bàn tay (FPS ~{fps ?? 30}).
        </p>
      )}

      {error && <p className="mt-3 text-sm text-red">{error}</p>}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void start()}
          disabled={status === "recording" || status === "loading" || status === "processing" || !scriptsReady}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            status === "recording" || status === "loading" || status === "processing" || !scriptsReady
              ? "cursor-not-allowed bg-surface-2 text-muted"
              : "bg-accent text-white hover:bg-accent-2"
          }`}
        >
          Bắt đầu ghi
        </button>
        <button
          type="button"
          onClick={stop}
          disabled={status !== "recording"}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            status === "recording"
              ? "border border-border bg-surface text-text hover:bg-surface-2"
              : "cursor-not-allowed bg-surface-2 text-muted"
          }`}
        >
          Dừng ghi
        </button>
        {status === "done" && (
          <button
            type="button"
            onClick={retake}
            className="rounded-lg border border-border bg-surface-2 px-4 py-2 text-sm font-medium text-text hover:bg-surface"
          >
            Ghi lại
          </button>
        )}
      </div>
    </div>
  );
}