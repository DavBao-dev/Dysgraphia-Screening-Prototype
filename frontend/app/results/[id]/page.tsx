"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import ResultSlip from "@/components/ResultSlip";
import { getSession } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import type { SessionDetail } from "@/types/screening";

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-3xl px-4 pt-8 sm:px-6 sm:pt-12">{children}</div>;
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    getSession(id)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setLoading(false);
        }
      })
      .catch((e: ApiError) => {
        if (!cancelled) {
          setError(
            e.status === 404
              ? "Không tìm thấy phiếu kết quả này. Có thể máy chủ đã được khởi động lại và xoá dữ liệu cũ."
              : "Không tải được phiếu kết quả. Hãy kiểm tra kết nối mạng rồi tải lại trang."
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <Shell>
        <p className="text-base text-muted" role="status">
          Đang tải phiếu kết quả...
        </p>
      </Shell>
    );
  }

  if (error || !data) {
    return (
      <Shell>
        <h1 className="font-serif text-2xl font-semibold text-text">Không mở được phiếu kết quả</h1>
        <p className="mt-3 text-base text-text">{error ?? "Không tải được phiếu kết quả."}</p>
        <Link
          href="/history"
          className="mt-4 inline-flex min-h-11 items-center text-base font-medium text-accent-2 underline underline-offset-4"
        >
          Về danh sách kết quả đã lưu
        </Link>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link
          href="/history"
          className="inline-flex min-h-11 items-center text-[15px] font-medium text-accent-2 underline decoration-1 underline-offset-4 hover:decoration-2"
        >
          Kết quả đã lưu
        </Link>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => window.print()}
            className="min-h-11 rounded-md border border-border bg-surface px-4 text-[15px] font-semibold text-text hover:bg-surface-2 active:bg-border"
          >
            In phiếu
          </button>
          <Link
            href="/screening"
            className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 text-[15px] font-semibold text-white hover:bg-accent-2 active:translate-y-px"
          >
            Kiểm tra cho em khác
          </Link>
        </div>
      </div>

      <ResultSlip data={data} />
    </Shell>
  );
}
