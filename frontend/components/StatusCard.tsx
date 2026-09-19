import type { Quality } from "@/types/screening";

const LABELS: Array<[string, (q: Quality) => string]> = [
  ["Hợp lệ", (q) => (q.valid ? "Có" : "Không")],
  ["Số frame", (q) => (q.frames != null ? String(q.frames) : "—")],
  ["FPS", (q) => (q.fps != null ? q.fps.toFixed(2) : "—")],
  ["Thời lượng (s)", (q) => (q.duration != null ? q.duration.toFixed(2) : "—")],
];

export default function StatusCard({ quality }: { quality: Quality | null }) {
  if (!quality) {
    return (
      <div className="mt-2 rounded-lg border border-border bg-surface-2 p-3 text-sm text-muted">
        Không có dữ liệu chất lượng.
      </div>
    );
  }

  return (
    <div className="mt-2 rounded-lg border border-border bg-surface-2 p-3">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
        Chất lượng dữ liệu
      </h4>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
        {LABELS.map(([label, fmt]) => (
          <div key={label} className="contents">
            <dt className="text-muted">{label}</dt>
            <dd className="text-right text-text">{fmt(quality)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
