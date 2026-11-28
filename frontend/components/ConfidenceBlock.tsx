import type { Confidence, ConfidenceLevel } from "@/lib/confidence";

// The word carries the meaning; colour only reinforces it.
const LEVELS: Record<ConfidenceLevel, { label: string; cls: string }> = {
  clear: { label: "Tín hiệu khá rõ", cls: "text-green" },
  uncertain: { label: "Chưa chắc chắn", cls: "text-accent-2" },
  insufficient: { label: "Không đủ căn cứ", cls: "text-text" },
};

// How sure the system is about this slip, with the reason, and a standing pointer to a specialist.
export default function ConfidenceBlock({ confidence }: { confidence: Confidence }) {
  const level = LEVELS[confidence.level];
  return (
    <section aria-labelledby="confidence-title" className="mt-6 border-t border-rule pt-5">
      <h3 id="confidence-title" className="text-sm font-semibold text-muted">
        Mức độ chắc chắn
      </h3>
      <p className={`mt-1 text-xl font-semibold ${level.cls}`}>{level.label}</p>
      <p className="mt-1 text-base leading-7 text-text">{confidence.reason}</p>
      {confidence.note && <p className="mt-1 text-[15px] leading-6 text-muted">{confidence.note}</p>}
      <p className="mt-2 text-base font-medium leading-7 text-text">
        Nên trao đổi với chuyên gia trước khi kết luận về em.
      </p>
    </section>
  );
}
