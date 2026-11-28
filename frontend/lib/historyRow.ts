import type { HistoryRow } from "@/types/screening";

/**
 * A history row as it is listed. A session whose hand video was unusable has no result on its slip
 * ("Không đủ căn cứ"), so the list shows no result for it either. Old sessions (video quality unknown) are unchanged.
 */
export function listedRow(row: HistoryRow): HistoryRow {
  return row.model_a_valid === false
    ? { ...row, model_a_output: null, model_b_output: null, final_output: null }
    : row;
}
