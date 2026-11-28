import { test } from "node:test";
import assert from "node:assert/strict";

import { listedRow } from "./historyRow.ts";
import type { HistoryRow } from "@/types/screening";

const row = (valid: boolean | null | undefined): HistoryRow => ({
  predicted_at: "2026-11-28T08:00:00",
  session_id: "s",
  patient_id: "HS01",
  model_a_output: 0,
  model_b_output: 1,
  final_output: 0,
  ensemble_method: "majority_vote (majority)",
  model_a_valid: valid,
});

test("a session whose video was unusable is listed with no result, like its slip", () => {
  const r = listedRow(row(false));
  assert.deepEqual([r.model_a_output, r.model_b_output, r.final_output], [null, null, null]);
});

test("a usable video keeps its result", () => {
  const r = listedRow(row(true));
  assert.deepEqual([r.model_a_output, r.model_b_output, r.final_output], [0, 1, 0]);
});

test("an old session with unknown video quality keeps its result", () => {
  assert.equal(listedRow(row(null)).final_output, 0);
  assert.equal(listedRow(row(undefined)).final_output, 0);
});
