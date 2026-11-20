"use client";

import { ArrowRightIcon } from "./Icons";

interface RunButtonProps {
  disabled: boolean;
  loading: boolean;
  error?: string;
  hint?: string;
  onClick: () => void;
}

export default function RunButton({ disabled, loading, error, hint, onClick }: RunButtonProps) {
  return (
    <div className="flex flex-col items-center gap-3 text-center">
      {error && (
        <p
          role="alert"
          className="w-full max-w-md rounded-xl border border-red/25 bg-red/5 px-4 py-3 text-[15px] text-red"
        >
          {error}
        </p>
      )}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        className={`inline-flex w-full max-w-sm items-center justify-center gap-2 rounded-xl px-6 py-4 text-lg font-semibold transition-colors ${
          disabled && !loading
            ? "cursor-not-allowed bg-surface-2 text-muted"
            : loading
              ? "cursor-wait bg-accent/80 text-white"
              : "bg-accent text-white shadow-sm hover:bg-accent-2"
        }`}
      >
        {loading ? (
          <>
            <span
              className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white"
              aria-hidden="true"
            />
            Đang phân tích...
          </>
        ) : (
          <>
            Xem kết quả
            <ArrowRightIcon className="h-5 w-5" />
          </>
        )}
      </button>
      <p className="text-[15px] text-muted" aria-live="polite">
        {loading
          ? "Việc phân tích có thể mất 1–2 phút với video dài. Vui lòng giữ nguyên trang này."
          : hint}
      </p>
    </div>
  );
}
