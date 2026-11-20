"use client";

import { useState } from "react";

interface StudentInputProps {
  value: string;
  onChange: (value: string) => void;
}

const INPUT_CLASS =
  "w-full rounded-xl border border-border bg-surface px-4 py-3 text-base text-text outline-none transition-colors placeholder:text-muted/70 focus:border-accent focus:ring-2 focus:ring-accent/20";

export default function StudentInput({ value, onChange }: StudentInputProps) {
  // Optional display-only field (not persisted to the backend yet).
  const [grade, setGrade] = useState("");

  return (
    <div className="grid gap-4 sm:grid-cols-[1fr_200px]">
      <div>
        <label htmlFor="student-id" className="mb-1.5 block text-base font-medium text-text">
          Mã học sinh
        </label>
        <input
          id="student-id"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ví dụ: HS01"
          autoComplete="off"
          aria-describedby="student-id-hint"
          className={INPUT_CLASS}
        />
        <p id="student-id-hint" className="mt-1.5 text-sm text-muted">
          Dùng mã hoặc biệt danh để tìm lại kết quả. Không cần nhập họ tên đầy đủ của trẻ.
        </p>
      </div>
      <div>
        <label htmlFor="student-grade" className="mb-1.5 block text-base font-medium text-text">
          Lớp <span className="font-normal text-muted">(không bắt buộc)</span>
        </label>
        <input
          id="student-grade"
          type="text"
          inputMode="numeric"
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
          placeholder="Ví dụ: 3"
          className={INPUT_CLASS}
        />
      </div>
    </div>
  );
}
