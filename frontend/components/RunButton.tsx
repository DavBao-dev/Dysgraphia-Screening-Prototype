"use client";

interface RunButtonProps {
  disabled: boolean;
  loading: boolean;
  error?: string;
  onClick: () => void;
}

export default function RunButton({ disabled, loading, error, onClick }: RunButtonProps) {
  return (
    <div className="flex flex-col items-center gap-3">
      {error && (
        <p
          role="alert"
          className="w-full max-w-sm rounded-lg border border-red/30 bg-surface-2 px-4 py-3 text-sm text-red"
        >
          {error}
        </p>
      )}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        className={`w-full max-w-xs rounded-lg border px-6 py-3 text-base font-semibold transition-colors ${
          disabled || loading
            ? "cursor-not-allowed border-accent/40 bg-accent/20 text-accent/90"
            : "border-accent bg-accent text-white hover:bg-accent-2"
        }`}
      >
        {loading ? "Đang phân tích..." : "Bắt đầu sàng lọc →"}
      </button>
      <p className="text-sm text-muted">Ảnh chữ viết tay là tùy chọn.</p>
    </div>
  );
}