import type { SessionDetail } from "@/types/screening";

export type ConfidenceLevel = "clear" | "uncertain" | "insufficient";

export interface Confidence {
  level: ConfidenceLevel;
  /** One sentence saying why the level is what it is. */
  reason: string;
  /** Extra caveat (for example a missing photo), or null. */
  note: string | null;
}

/**
 * A score closer than this to the 0.5 threshold counts as "not sure". The value is a rule of thumb, not
 * calibrated: the models' scores are not probabilities, so this is deliberately expressed in words, not numbers.
 */
export const UNCERTAIN_MARGIN = 0.15;

const NO_PHOTO_NOTE = "Chưa có ảnh trang vở nên mức độ chắc chắn bị giới hạn.";

/** How sure the system is about one screening session, from fields the API already returns. */
export function assessConfidence(session: SessionDetail): Confidence {
  const a = session.model_a;
  const b = session.model_b;
  const note = b?.available ? null : NO_PHOTO_NOTE;

  if (!a?.available || a.quality?.valid === false || session.ensemble?.prediction == null) {
    return {
      level: "insufficient",
      reason: "Video chưa đủ rõ hoặc thiếu dữ liệu bàn tay nên hệ thống chưa có đủ căn cứ để đưa ra kết quả.",
      note,
    };
  }

  const scores = [a, b]
    .filter((m) => m?.available && m.score != null)
    .map((m) => m!.score as number);
  if (scores.some((s) => Math.abs(s - 0.5) < UNCERTAIN_MARGIN)) {
    return {
      level: "uncertain",
      reason: "Kết quả nằm sát ranh giới giữa hai khả năng, nên hệ thống chưa chắc chắn.",
      note,
    };
  }

  if (a.available && b?.available && a.prediction !== b.prediction) {
    return {
      level: "uncertain",
      reason: "Hai phần phân tích (bàn tay và trang vở) cho hướng khác nhau, nên hệ thống chưa chắc chắn.",
      note,
    };
  }

  return {
    level: "clear",
    reason: b?.available
      ? "Hai phần phân tích cùng chỉ về một hướng và cách xa ranh giới."
      : "Phần phân tích bàn tay chỉ về một hướng rõ ràng, cách xa ranh giới.",
    note,
  };
}
