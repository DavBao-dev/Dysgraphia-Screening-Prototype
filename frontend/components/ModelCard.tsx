import type { Quality } from "@/types/screening";
import StatusCard from "./StatusCard";
import FeatureGroups from "./FeatureGroups";
import DetailsSection from "./DetailsSection";

function signalLabel(p: number | null): string {
  if (p === 1) return "Có dấu hiệu";
  if (p === 0) return "Chưa phát hiện dấu hiệu";
  return "Chưa phân tích";
}

function signalColor(p: number | null): string {
  if (p === 1) return "text-amber";
  if (p === 0) return "text-green";
  return "text-muted";
}

function signalDot(p: number | null): string {
  if (p === 1) return "bg-amber";
  if (p === 0) return "bg-green";
  return "bg-border";
}

interface ModelCardProps {
  title: string;
  badge?: string;
  badgeVariant?: "accent" | "neutral";
  available: boolean;
  prediction: number | null;
  score?: number | null;
  quality?: Quality | null;
  features?: Record<string, number | null> | null;
  handcrafted?: Record<string, number | null> | null;
  featuresLabel?: string;
  technicalName?: string;
  unavailableText?: string;
}

export default function ModelCard({
  title,
  badge,
  badgeVariant = "accent",
  available,
  prediction,
  score,
  quality,
  features,
  handcrafted,
  featuresLabel,
  technicalName,
  unavailableText,
}: ModelCardProps) {
  const hasDetails = Boolean(
    technicalName || quality != null || (features && Object.keys(features).length > 0) || (handcrafted && Object.keys(handcrafted).length > 0)
  );

  if (!available) {
    return (
      <div className="rounded-xl border border-border bg-surface p-5">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-text">{title}</h3>
          {badge && (
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                badgeVariant === "accent"
                  ? "bg-accent text-white"
                  : "bg-surface-2 text-green"
              }`}
            >
              {badge}
            </span>
          )}
        </div>
        <p className="mt-3 flex items-center gap-1.5 text-sm text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-border" aria-hidden="true" />
          Chưa phân tích
        </p>
        <p className="mt-1 text-sm text-muted">{unavailableText ?? "Không khả dụng"}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-semibold text-text">{title}</h3>
        {badge && (
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              badgeVariant === "accent"
                ? "bg-accent text-white"
                : "bg-surface-2 text-green"
            }`}
          >
            {badge}
          </span>
        )}
      </div>

      <dl className="mt-4 rounded-lg border border-border bg-surface-2 p-3 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-muted">Tín hiệu sàng lọc</dt>
          <dd className={`flex items-center gap-1.5 font-medium ${signalColor(prediction)}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${signalDot(prediction)}`} aria-hidden="true" />
            {signalLabel(prediction)}
          </dd>
        </div>
        {score != null && (
          <div className="mt-1 flex items-center justify-between">
            <dt className="text-muted">Điểm mô hình</dt>
            <dd className="font-mono text-text">{(score * 100).toFixed(1)}%</dd>
          </div>
        )}
      </dl>

      {hasDetails && (
        <div className="mt-3">
          <DetailsSection title="Chi tiết kỹ thuật">
            {technicalName && <p className="text-sm text-muted">Mô hình: {technicalName}</p>}
            {quality != null && (
              <div className="mt-2">
                <StatusCard quality={quality} />
              </div>
            )}
            {features && Object.keys(features).length > 0 && (
              <div className="mt-3">
                <FeatureGroups features={features} title={featuresLabel} />
              </div>
            )}
            {handcrafted && Object.keys(handcrafted).length > 0 && (
              <div className="mt-3">
                <FeatureGroups features={handcrafted} title={featuresLabel} />
              </div>
            )}
          </DetailsSection>
        </div>
      )}
    </div>
  );
}