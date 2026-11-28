import { test } from "node:test";
import assert from "node:assert/strict";

import { assessConfidence } from "./confidence.ts";
import type { SessionDetail } from "@/types/screening";

type Overrides = {
  a?: Partial<NonNullable<SessionDetail["model_a"]>> | null;
  b?: Partial<NonNullable<SessionDetail["model_b"]>> | null;
  ensemble?: Partial<SessionDetail["ensemble"]>;
};

// A fully populated, clearly positive session; each test overrides what it needs.
function session({ a, b, ensemble }: Overrides = {}): SessionDetail {
  return {
    session_id: "s",
    patient_id: "HS01",
    created_at: "2026-11-28T08:00:00+07:00",
    disclaimer: "x",
    model_a:
      a === null
        ? (null as unknown as SessionDetail["model_a"])
        : { available: true, prediction: 1, score: 0.82, status: "OK", quality: { valid: true }, features: null, ...a },
    model_b:
      b === null
        ? (null as unknown as SessionDetail["model_b"])
        : { available: true, prediction: 1, score: 0.74, ...b },
    ensemble: { prediction: 1, method: "majority_vote (majority)", ...ensemble } as SessionDetail["ensemble"],
  };
}

test("clear positive when both models are far from the threshold and agree", () => {
  const c = assessConfidence(session());
  assert.equal(c.level, "clear");
  assert.equal(c.note, null);
  assert.ok(c.reason.length > 0);
});

test("clear negative when both models are low and agree", () => {
  const c = assessConfidence(
    session({ a: { prediction: 0, score: 0.18 }, b: { prediction: 0, score: 0.21 }, ensemble: { prediction: 0 } })
  );
  assert.equal(c.level, "clear");
});

test("uncertain when Model A is near the threshold", () => {
  assert.equal(assessConfidence(session({ a: { score: 0.52 } })).level, "uncertain");
});

test("uncertain when a score is exactly 0.5", () => {
  assert.equal(assessConfidence(session({ a: { score: 0.5 } })).level, "uncertain");
});

test("0.65 and 0.35 sit on the boundary and count as clear", () => {
  assert.equal(assessConfidence(session({ a: { score: 0.65 } })).level, "clear");
  const low = session({
    a: { prediction: 0, score: 0.35 },
    b: { prediction: 0, score: 0.21 },
    ensemble: { prediction: 0 },
  });
  assert.equal(assessConfidence(low).level, "clear");
});

test("uncertain when the two models disagree", () => {
  const c = assessConfidence(session({ a: { prediction: 1, score: 0.8 }, b: { prediction: 0, score: 0.2 } }));
  assert.equal(c.level, "uncertain");
});

test("no photo keeps the level but adds a note", () => {
  const c = assessConfidence(session({ b: { available: false, prediction: null, score: null } }));
  assert.equal(c.level, "clear");
  assert.ok(c.note && c.note.length > 0);
});

test("Model B available with a null score does not throw and is ignored", () => {
  assert.equal(assessConfidence(session({ b: { score: null } })).level, "clear");
});

test("old session with null quality is treated as valid", () => {
  assert.equal(assessConfidence(session({ a: { quality: null } })).level, "clear");
});

test("insufficient when the video is invalid", () => {
  assert.equal(assessConfidence(session({ a: { quality: { valid: false } } })).level, "insufficient");
});

test("insufficient when Model A is unavailable", () => {
  assert.equal(assessConfidence(session({ a: { available: false } })).level, "insufficient");
});

test("insufficient when the ensemble has no prediction", () => {
  assert.equal(
    assessConfidence(session({ ensemble: { prediction: null as unknown as number } })).level,
    "insufficient"
  );
});
