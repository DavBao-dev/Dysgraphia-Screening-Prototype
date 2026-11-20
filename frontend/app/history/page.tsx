"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { ArrowRightIcon } from "@/components/Icons";
import { getHistory } from "@/lib/api";
import type { HistoryRow } from "@/types/screening";

function partLabel(p: number | null, missing = "—"): { text: string; cls: string } {
  if (p === 1) return { text: "Cần chú ý", cls: "text-accent-2" };
  if (p === 0) return { text: "Bình thường", cls: "text-green" };
  return { text: missing, cls: "text-muted" };
}

function finalPill(p: number | null): { text: string; cls: string } {
  if (p === 1) return { text: "Nên theo dõi thêm", cls: "bg-accent-soft text-accent-2" };
  if (p === 0) return { text: "Chưa thấy dấu hiệu", cls: "bg-green-soft text-green" };
  return { text: "Chưa đủ thông tin", cls: "bg-surface-2 text-muted" };
}

function formatDate(raw: string): string {
  try {
    return new Date(raw).toLocaleString("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return raw;
  }
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-3xl font-bold tracking-tight text-text">Kết quả đã lưu</h1>
      <p className="mt-2 text-lg text-muted">Các lần kiểm tra trước, mới nhất ở trên cùng. Bấm vào một dòng để xem lại.</p>
      {children}
    </div>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHistory()
      .then((d) => {
        if (!cancelled) {
          setRows(d);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Không thể tải danh sách kết quả. Vui lòng thử lại.");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <Shell>
        <p className="mt-6 text-base text-muted">Đang tải…</p>
      </Shell>
    );
  }

  if (error) {
    return (
      <Shell>
        <p className="mt-6 text-base text-red">{error}</p>
      </Shell>
    );
  }

  if (rows.length === 0) {
    return (
      <Shell>
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-surface p-10 text-center">
          <p className="text-lg font-semibold text-text">Chưa có lần kiểm tra nào</p>
          <p className="mt-1 text-base text-muted">Kết quả sẽ hiện ở đây sau lần kiểm tra đầu tiên.</p>
          <Link
            href="/screening"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-3 text-base font-semibold text-white hover:bg-accent-2"
          >
            Bắt đầu kiểm tra
            <ArrowRightIcon className="h-5 w-5" />
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      {/* Phone: cards */}
      <ul className="mt-6 space-y-3 md:hidden">
        {rows.map((row) => {
          const pill = finalPill(row.final_output);
          return (
            <li key={row.session_id}>
              <Link
                href={`/results/${row.session_id}`}
                className="block rounded-2xl border border-border bg-surface p-4 shadow-sm hover:border-accent/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-text">{row.patient_id}</p>
                    <p className="text-sm text-muted">{formatDate(row.predicted_at)}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-3 py-1 text-sm font-medium ${pill.cls}`}>{pill.text}</span>
                </div>
                <p className="mt-3 text-sm text-muted">
                  Chuyển động tay:{" "}
                  <span className={partLabel(row.model_a_output).cls}>{partLabel(row.model_a_output).text}</span>
                  <span className="mx-2" aria-hidden="true">·</span>
                  Chữ viết:{" "}
                  <span className={partLabel(row.model_b_output, "Không có ảnh").cls}>
                    {partLabel(row.model_b_output, "Không có ảnh").text}
                  </span>
                </p>
              </Link>
            </li>
          );
        })}
      </ul>

      {/* Tablet and desktop: table */}
      <div className="mt-6 hidden overflow-hidden rounded-2xl border border-border bg-surface shadow-sm md:block">
        <table className="w-full text-left text-[15px]">
          <thead>
            <tr className="border-b border-border bg-surface-2 text-sm text-muted">
              <th scope="col" className="px-5 py-3 font-semibold">Mã học sinh</th>
              <th scope="col" className="px-5 py-3 font-semibold">Ngày kiểm tra</th>
              <th scope="col" className="px-5 py-3 font-semibold">Kết quả chung</th>
              <th scope="col" className="px-5 py-3 font-semibold">Chuyển động tay</th>
              <th scope="col" className="px-5 py-3 font-semibold">Chữ viết</th>
              <th scope="col" className="px-5 py-3"><span className="sr-only">Xem</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const pill = finalPill(row.final_output);
              const a = partLabel(row.model_a_output);
              const b = partLabel(row.model_b_output, "Không có ảnh");
              return (
                <tr
                  key={row.session_id}
                  onClick={() => router.push(`/results/${row.session_id}`)}
                  className="cursor-pointer border-b border-border last:border-b-0 hover:bg-accent-soft/40"
                >
                  <td className="px-5 py-4 font-semibold text-text">{row.patient_id}</td>
                  <td className="whitespace-nowrap px-5 py-4 text-muted">{formatDate(row.predicted_at)}</td>
                  <td className="px-5 py-4">
                    <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${pill.cls}`}>
                      {pill.text}
                    </span>
                  </td>
                  <td className={`px-5 py-4 ${a.cls}`}>{a.text}</td>
                  <td className={`px-5 py-4 ${b.cls}`}>{b.text}</td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      href={`/results/${row.session_id}`}
                      className="font-semibold text-accent-2 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Xem
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
