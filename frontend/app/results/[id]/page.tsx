"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import ModelCard from "@/components/ModelCard";
import DetailsSection from "@/components/DetailsSection";
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
          if (e.status === 404) {
            setError("Không tìm thấy phiên sàng lọc.");
          } else {
            setError("Không thể tải kết quả sàng lọc.");
          }
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
        <p className="text-sm text-muted">Đang tải kết quả…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
        <p className="text-sm text-red">{error}</p>
        <Link href="/history" className="mt-4 inline-block text-sm text-accent hover:underline">
          ← Về lịch sử
        </Link>
      </main>
    );
  }

  if (!data) return null;

  const ensemble = data.ensemble;
  const modelA = data.model_a;
  const modelB = data.model_b;

  const prediction = ensemble?.prediction;
  const verdict = (() => {
    if (prediction === 1) {
      return {
        primary: "Có dấu hiệu cần được xem xét thêm",
        detail:
          "Hệ thống phát hiện các mẫu có thể liên quan đến khó viết và khuyến nghị xem xét thêm.",
        descriptor: "Tín hiệu sàng lọc cao hơn",
        bg: "border-amber/30 bg-amber/10",
        textColor: "text-amber",
      };
    }
    if (prediction === 0) {
      return {
        primary: "Chưa phát hiện dấu hiệu đáng chú ý",
        detail: "Kết quả sàng lọc hiện chưa cho thấy tín hiệu nổi bật.",
        descriptor: "Tín hiệu sàng lọc thấp",
        bg: "border-green/30 bg-green/10",
        textColor: "text-green",
      };
    }
    return {
      primary: "Cần đánh giá thêm",
      detail: "Chưa đủ dữ liệu để tổng hợp kết quả.",
      descriptor: null,
      bg: "border-violet/30 bg-violet/10",
      textColor: "text-violet",
    };
  })();

  return (
    <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
      <Link href="/history" className="mb-4 inline-block text-sm text-accent hover:underline">
        ← Lịch sử sàng lọc
      </Link>

      <h1 className="text-3xl font-bold tracking-tight text-text">Kết quả sàng lọc</h1>
      <p className="mt-1 text-sm text-muted">Học sinh: {data.patient_id}</p>
      <p className="text-sm text-muted">Thời điểm: {formatDate(data.created_at)}</p>

      <div className={`mt-6 rounded-xl border p-5 ${verdict.bg}`}>
        <p className={`text-xl font-semibold ${verdict.textColor}`}>{verdict.primary}</p>
        <p className="mt-1.5 text-sm text-muted">{verdict.detail}</p>
        {verdict.descriptor && (
          <p className="mt-2 text-xs text-muted">{verdict.descriptor}</p>
        )}
        <p className="mt-3 border-t border-border/40 pt-3 text-xs text-muted">
          Đây là công cụ sàng lọc, không phải chẩn đoán.
        </p>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <ModelCard
          title="Chuyển động tay"
          badge="Bắt buộc"
          badgeVariant="accent"
          available={modelA?.available ?? false}
          prediction={modelA?.prediction ?? null}
          score={modelA?.score ?? null}
          quality={modelA?.quality ?? null}
          features={modelA?.features ?? null}
          technicalName="Random Forest (28 đặc trưng từ MediaPipe Hands)"
          unavailableText="Chưa có dữ liệu chuyển động tay."
        />
        <ModelCard
          title="Chữ viết tay"
          badge="Tùy chọn"
          badgeVariant="neutral"
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
          technicalName="ResNet50 + MLP (OpenVINO)"
          unavailableText="Chưa cung cấp mẫu chữ viết tay."
        />
      </div>

      <section className="mt-6 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-base font-semibold text-text">
          Chúng tôi đã phân tích điều gì?
        </h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-text">Chuyển động tay</h3>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-sm text-muted">
              <li>Tốc độ chuyển động của bàn tay</li>
              <li>Độ mượt và nhất quán của chuyển động</li>
              <li>Các quãng dừng hoặc khựng</li>
              <li>Các mẫu rung lắc nhẹ (run)</li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text">Chữ viết tay</h3>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-sm text-muted">
              <li>Độ dày của nét mực</li>
              <li>Mức độ thẳng hàng của dòng chữ</li>
            </ul>
          </div>
        </div>
      </section>

      {ensemble?.method && (
        <div className="mt-4">
          <DetailsSection title="Chi tiết kỹ thuật">
            <p className="text-sm text-muted">
              Kết quả chung được tổng hợp từ các tín hiệu phía trên (phương thức:{" "}
              {ensemble.method}).
            </p>
          </DetailsSection>
        </div>
      )}

      <div className="mt-6 rounded-xl border border-border bg-surface p-4">
        <p className="text-sm text-muted">{data.disclaimer}</p>
      </div>
    </main>
  );
}
