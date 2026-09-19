"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getHistory } from "@/lib/api";
import type { HistoryRow } from "@/types/screening";

function signalSimple(p: number | null): string {
  if (p === 1) return "Cao";
  if (p === 0) return "Thấp";
  return "—";
}

function finalPill(p: number | null): { text: string; cls: string } {
  if (p === 1) return { text: "Tín hiệu cao", cls: "bg-amber/15 text-amber" };
  if (p === 0) return { text: "Tín hiệu thấp", cls: "bg-green/15 text-green" };
  return { text: "Cần xem xét", cls: "bg-violet/15 text-violet" };
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
          setError("Không thể tải lịch sử.");
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
        <p className="text-sm text-muted">Đang tải lịch sử…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
        <p className="text-sm text-red">{error}</p>
      </main>
    );
  }

  if (rows.length === 0) {
    return (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
        <h1 className="text-3xl font-bold tracking-tight text-text">Lịch sử sàng lọc</h1>
        <p className="mt-4 text-sm text-muted">Chưa có phiên sàng lọc nào.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
      <h1 className="text-3xl font-bold tracking-tight text-text">Lịch sử sàng lọc</h1>

      <div className="mt-4 overflow-x-auto rounded-xl border border-border bg-surface">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2 text-xs uppercase tracking-wide text-muted">
              <th className="px-4 py-3">Học sinh</th>
              <th className="px-4 py-3">Thời điểm</th>
              <th className="px-4 py-3">Chuyển động tay</th>
              <th className="px-4 py-3">Chữ viết tay</th>
              <th className="px-4 py-3">Kết quả sàng lọc</th>
              <th className="px-4 py-3 text-right">Chi tiết</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.session_id}
                onClick={() => router.push(`/results/${row.session_id}`)}
                className="cursor-pointer border-b border-border last:border-b-0 hover:bg-surface-2"
              >
                <td className="px-4 py-3 text-text">{row.patient_id}</td>
                <td className="px-4 py-3 whitespace-nowrap text-text">
                  {formatDate(row.predicted_at)}
                </td>
                <td
                  className={`px-4 py-3 ${
                    row.model_a_output === 1
                      ? "text-amber"
                      : row.model_a_output === 0
                        ? "text-green"
                        : "text-muted"
                  }`}
                >
                  {signalSimple(row.model_a_output)}
                </td>
                <td
                  className={`px-4 py-3 ${
                    row.model_b_output == null
                      ? "text-muted"
                      : row.model_b_output === 1
                        ? "text-amber"
                        : "text-green"
                  }`}
                >
                  {row.model_b_output == null ? "Không có" : signalSimple(row.model_b_output)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${finalPill(row.final_output).cls}`}
                  >
                    {finalPill(row.final_output).text}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/results/${row.session_id}`}
                    className="text-accent hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Xem
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
