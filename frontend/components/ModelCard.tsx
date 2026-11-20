import type { ComponentType, SVGProps } from "react";
import type { Quality } from "@/types/screening";
import StatusCard from "./StatusCard";
import FeatureGroups from "./FeatureGroups";
import DetailsSection from "./DetailsSection";

function signal(p: number | null): { label: string; cls: string; dot: string } {
  if (p === 1) return { label: "Có dấu hiệu cần chú ý", cls: "bg-accent-soft text-accent-2", dot: "bg-accent" };
  if (p === 0) return { label: "Chưa thấy dấu hiệu", cls: "bg-green-soft text-green", dot: "bg-green" };
  return { label: "Chưa phân tích được", cls: "bg-surface-2 text-muted", dot: "bg-muted" };
}

interface ModelCardProps {
  title: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  lookedAt: string;
  available: boolean;
  prediction: number | null;
  score?: number | null;
  quality?: Quality | null;
  features?: Record<string, number | null> | null;
  handcrafted?: Record<string, number | null> | null;
  technicalName?: string;
  unavailableText?: string;
}

export default function ModelCard({
  title,
  icon: Icon,
  lookedAt,
  available,
  prediction,
  score,
  quality,
  features,
  handcrafted,
  technicalName,
  unavailableText,
}: ModelCardProps) {
  const s = available ? signal(prediction) : { label: "Không có dữ liệu", cls: "bg-surface-2 text-muted", dot: "bg-muted" };
  const hasDetails =
    available &&
    Boolean(
      technicalName ||
        score != null ||
        quality != null ||
        (features && Object.keys(features).length > 0) ||
        (handcrafted && Object.keys(handcrafted).length > 0)
    );

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface-2 text-accent">
          <Icon className="h-5 w-5" />
        </span>
        <h3 className="text-lg font-semibold text-text">{title}</h3>
      </div>

      <p className={`mt-4 inline-flex items-center gap-2 rounded-full px-3 py-1 text-[15px] font-medium ${s.cls}`}>
        <span className={`h-2 w-2 rounded-full ${s.dot}`} aria-hidden="true" />
        {s.label}
      </p>

      <p className="mt-3 text-[15px] leading-relaxed text-muted">{available ? lookedAt : unavailableText}</p>

      {hasDetails && (
        <div className="print:hidden">
          <DetailsSection title="Chi tiết kỹ thuật">
            {technicalName && <p>Mô hình: {technicalName}</p>}
            {score != null && <p className="mt-1">Điểm của mô hình: {(score * 100).toFixed(1)}% (ngưỡng 50%)</p>}
            {quality != null && (
              <div className="mt-2">
                <StatusCard quality={quality} />
              </div>
            )}
            {features && Object.keys(features).length > 0 && (
              <div className="mt-3">
                <FeatureGroups features={features} />
              </div>
            )}
            {handcrafted && Object.keys(handcrafted).length > 0 && (
              <div className="mt-3">
                <FeatureGroups features={handcrafted} />
              </div>
            )}
          </DetailsSection>
        </div>
      )}
    </div>
  );
}
