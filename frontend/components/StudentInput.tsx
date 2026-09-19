"use client";

import { useState } from "react";

interface StudentInputProps {
  value: string;
  onChange: (value: string) => void;
}

export default function StudentInput({ value, onChange }: StudentInputProps) {
  // Optional display-only field (not persisted to the backend yet).
  const [grade, setGrade] = useState("");

  return (
    <div>
      <div className="flex flex-wrap items-end justify-center gap-x-6 gap-y-3">
        <div className="w-full sm:w-80">
          <label htmlFor="student-id" className="mb-1.5 block text-sm font-medium text-muted">
            Học sinh
          </label>
          <input
            id="student-id"
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Mã hoặc tên học sinh"
            className="w-full rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text outline-none placeholder:text-muted focus:border-accent"
          />
        </div>
        <div className="w-full sm:w-36">
          <label htmlFor="student-grade" className="mb-1.5 block text-sm font-medium text-muted">
            Lớp
          </label>
          <input
            id="student-grade"
            type="text"
            inputMode="numeric"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            placeholder="VD: 8"
            className="w-full rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text outline-none placeholder:text-muted focus:border-accent"
          />
        </div>
      </div>
      <p className="mt-2 text-center text-xs text-muted">Không cần cung cấp thông tin cá nhân nhạy cảm.</p>
    </div>
  );
}