"use client";

interface RunButtonProps {
  disabled: boolean;
  loading: boolean;
  error?: string;
  hint?: string;
  onClick: () => void;
}

export default function RunButton({ disabled, loading, error, hint, onClick }: RunButtonProps) {
  return (
    <div className="flex flex-col items-start gap-3">
      {error && (
        <p role="alert" className="w-full max-w-xl rounded-sheet border border-red/30 bg-surface px-4 py-3 text-[15px] text-red">
          <strong>Chưa phân tích được.</strong> {error}
        </p>
      )}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        aria-describedby="run-hint"
        className={`inline-flex min-h-12 w-full items-center justify-center gap-3 rounded-md px-8 text-lg font-semibold sm:w-auto ${
          disabled && !loading
            ? "border border-border bg-surface-2 text-muted"
            : loading
              ? "bg-accent-2 text-white"
              : "bg-accent text-white hover:bg-accent-2 active:translate-y-px"
        }`}
      >
        {loading && (
          <span
            className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white"
            aria-hidden="true"
          />
        )}
        {loading ? "Đang phân tích..." : "Xem kết quả"}
      </button>
      <p id="run-hint" className="text-[15px] text-muted" aria-live="polite">
        {loading ? "Video càng dài thì càng phải chờ lâu, có thể vài phút. Vui lòng giữ nguyên trang này." : hint}
      </p>
    </div>
  );
}
