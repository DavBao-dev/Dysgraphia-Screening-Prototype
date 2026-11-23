import type { Quality } from "@/types/screening";

const LABELS: Array<[string, (q: Quality) => string]> = [
  ["Đủ dữ liệu để phân tích", (q) => (q.valid ? "Có" : "Không")],
  ["Số khung hình có bàn tay", (q) => (q.frames != null ? String(q.frames) : "Không có")],
  ["Khung hình/giây", (q) => (q.fps != null ? q.fps.toFixed(0) : "Không có")],
  ["Thời lượng (giây)", (q) => (q.duration != null ? q.duration.toFixed(1) : "Không có")],
];

export default function StatusCard({ quality }: { quality: Quality | null }) {
  if (!quality) {
    return (
      <div className="rounded-lg border border-border bg-surface p-3 text-sm text-muted">
        Không có dữ liệu chất lượng video.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      <h4 className="mb-2 text-sm font-semibold text-text">Chất lượng video</h4>
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
