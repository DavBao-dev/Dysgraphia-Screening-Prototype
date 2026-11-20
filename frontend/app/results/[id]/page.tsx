"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import ModelCard from "@/components/ModelCard";
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  EyeIcon,
  ImageIcon,
  InfoIcon,
  PrinterIcon,
  VideoIcon,
} from "@/components/Icons";
import { getSession } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import type { SessionDetail } from "@/types/screening";

function formatDate(raw: string): string {
  try {
    return new Date(raw).toLocaleString("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return raw;
  }
}

interface Verdict {
  title: string;
  summary: string;
  steps: string[];
  tone: string;
  iconTone: string;
  icon: typeof CheckCircleIcon;
}

function verdictFor(prediction: number | null | undefined): Verdict {
  if (prediction === 1) {
    return {
      title: "Nên theo dõi thêm",
      summary:
        "Hệ thống thấy một vài dấu hiệu có thể liên quan đến khó viết. Điều này không có nghĩa là trẻ bị khó viết, nhưng trẻ nên được quan sát kỹ hơn.",
      steps: [
        "Trao đổi giữa giáo viên và phụ huynh về việc viết của trẻ ở lớp và ở nhà.",
        "Quan sát thêm trong 2–4 tuần: cách cầm bút, tốc độ viết, chữ có lệch dòng không, trẻ có hay kêu mỏi tay không.",
        "Nếu các dấu hiệu kéo dài, hãy đưa trẻ gặp chuyên gia để được đánh giá: chuyên viên tâm lý học đường, chuyên viên hoạt động trị liệu hoặc bác sĩ nhi khoa phát triển.",
        "Khó viết không liên quan đến trí thông minh. Phát hiện sớm giúp trẻ được hỗ trợ kịp thời.",
      ],
      tone: "border-accent/30 bg-accent-soft",
      iconTone: "bg-accent text-white",
      icon: EyeIcon,
    };
  }
  if (prediction === 0) {
    return {
      title: "Chưa thấy dấu hiệu đáng lo",
      summary:
        "Ở lần kiểm tra này, cách viết của trẻ chưa cho thấy dấu hiệu khó viết rõ rệt.",
      steps: [
        "Tiếp tục khuyến khích trẻ viết đều đặn mỗi ngày.",
        "Nếu trẻ vẫn gặp khó khăn kéo dài (viết rất chậm, chữ khó đọc, hay mỏi tay), hãy kiểm tra lại sau vài tuần hoặc trao đổi với giáo viên.",
        "Một lần kiểm tra không thể phát hiện mọi trường hợp. Sự quan sát của giáo viên và phụ huynh vẫn quan trọng nhất.",
      ],
      tone: "border-green/30 bg-green-soft",
      iconTone: "bg-green text-white",
      icon: CheckCircleIcon,
    };
  }
  return {
    title: "Chưa đủ thông tin",
    summary: "Hệ thống chưa có đủ dữ liệu để đưa ra kết quả. Hãy thử kiểm tra lại với một video rõ hơn.",
    steps: ["Xem lại phần “Cách quay video” và thực hiện kiểm tra mới."],
    tone: "border-border bg-surface-2",
    iconTone: "bg-muted text-white",
    icon: InfoIcon,
  };
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">{children}</div>;
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    getSession(id)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setLoading(false);
        }
      })
      .catch((e: ApiError) => {
        if (!cancelled) {
          setError(e.status === 404 ? "Không tìm thấy kết quả này." : "Không thể tải kết quả. Vui lòng thử lại.");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <Shell>
        <p className="text-base text-muted">Đang tải kết quả…</p>
      </Shell>
    );
  }

  if (error || !data) {
    return (
      <Shell>
        <p className="text-base text-red">{error ?? "Không thể tải kết quả."}</p>
        <Link href="/history" className="mt-4 inline-block text-[15px] font-medium text-accent-2 hover:underline">
          ← Về danh sách kết quả
        </Link>
      </Shell>
    );
  }

  const modelA = data.model_a;
  const modelB = data.model_b;
  const verdict = verdictFor(data.ensemble?.prediction);
  const VerdictIcon = verdict.icon;

  return (
    <Shell>
      <Link
        href="/history"
        className="inline-flex items-center gap-1.5 text-[15px] font-medium text-accent-2 hover:underline print:hidden"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Kết quả đã lưu
      </Link>

      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text">Kết quả kiểm tra</h1>
          <p className="mt-1.5 text-base text-muted">
            Mã học sinh: <span className="font-semibold text-text">{data.patient_id}</span>
            <span className="mx-2" aria-hidden="true">·</span>
            {formatDate(data.created_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 print:hidden">
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-[15px] font-semibold text-text hover:bg-surface-2"
          >
            <PrinterIcon className="h-4 w-4" />
            In kết quả
          </button>
          <Link
            href="/screening"
            className="inline-flex items-center rounded-xl bg-accent px-4 py-2.5 text-[15px] font-semibold text-white hover:bg-accent-2"
          >
            Kiểm tra lần mới
          </Link>
        </div>
      </div>

      {/* Main verdict */}
      <section className={`mt-6 rounded-2xl border p-6 ${verdict.tone}`} aria-labelledby="verdict-title">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-4">
          <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${verdict.iconTone}`}>
            <VerdictIcon className="h-6 w-6" />
          </span>
          <div>
            <h2 id="verdict-title" className="text-2xl font-bold text-text">
              {verdict.title}
            </h2>
            <p className="mt-2 text-lg leading-relaxed text-text">{verdict.summary}</p>
          </div>
        </div>
      </section>

      {/* Next steps */}
      <section className="mt-5 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text">Nên làm gì tiếp theo?</h2>
        <ol className="mt-4 space-y-3">
          {verdict.steps.map((step, i) => (
            <li key={step} className="flex items-start gap-3 text-base leading-relaxed text-text">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-2 text-sm font-semibold text-muted">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </section>

      {/* What was analysed */}
      <h2 className="mt-8 text-xl font-semibold text-text">Hệ thống đã xem những gì?</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ModelCard
          title="Chuyển động tay"
          icon={VideoIcon}
          lookedAt="Tốc độ và độ mượt khi viết, những lần dừng bút và độ run của bàn tay."
          available={modelA?.available ?? false}
          prediction={modelA?.prediction ?? null}
          score={modelA?.score ?? null}
          quality={modelA?.quality ?? null}
          features={modelA?.features ?? null}
          technicalName="MediaPipe Hands (21 điểm trên bàn tay) + Random Forest, 18 đặc trưng vận động"
          unavailableText="Không có dữ liệu chuyển động tay."
        />
        <ModelCard
          title="Chữ viết"
          icon={ImageIcon}
          lookedAt="Hình dạng chữ, độ đậm của nét và chữ có thẳng hàng theo dòng hay không."
          available={modelB?.available ?? false}
          prediction={modelB?.prediction ?? null}
          score={modelB?.score ?? null}
          handcrafted={
            modelB?.handcrafted
              ? {
                  ink_thickness_mean: modelB.handcrafted.ink_thickness_mean,
                  baseline_deviation: modelB.handcrafted.baseline_deviation,
                }
              : null
          }
          technicalName="ResNet50 + MLP (ONNX Runtime), 2 đặc trưng nét chữ"
          unavailableText="Lần kiểm tra này không có ảnh chữ viết. Thêm ảnh ở lần sau để kết quả đầy đủ hơn."
        />
      </div>

      <div className="mt-8 flex items-start gap-3 rounded-2xl border border-border bg-surface-2 p-5 text-[15px] leading-relaxed text-muted">
        <InfoIcon className="mt-0.5 h-5 w-5 shrink-0 text-muted" />
        <p>
          <span className="font-semibold text-text">Kết quả này chỉ là gợi ý sàng lọc, không phải chẩn đoán.</span>{" "}
          Chỉ chuyên gia mới có thể xác định trẻ có bị khó viết hay không. Hãy dùng kết quả này làm cơ sở để trao đổi
          giữa gia đình, nhà trường và chuyên gia.
        </p>
      </div>
    </Shell>
  );
}
