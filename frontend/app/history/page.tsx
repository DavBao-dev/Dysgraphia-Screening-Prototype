"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getHistory } from "@/lib/api";
import type { HistoryRow } from "@/types/screening";

function partLabel(p: number | null, missing: string): { text: string; cls: string } {
  if (p === 1) return { text: "Cần chú ý", cls: "text-accent-2 font-semibold" };
  if (p === 0) return { text: "Chưa thấy dấu hiệu", cls: "text-green" };
  return { text: missing, cls: "text-muted" };
}

function overall(p: number | null): { text: string; cls: string } {
  if (p === 1) return { text: "Nên theo dõi thêm", cls: "text-accent-2 font-semibold" };
  if (p === 0) return { text: "Chưa thấy dấu hiệu đáng lo", cls: "text-green font-semibold" };
  return { text: "Chưa đủ thông tin", cls: "text-muted font-semibold" };
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
    <div className="mx-auto w-full max-w-5xl px-4 pt-8 sm:px-6 sm:pt-12">
      <h1 className="font-serif text-[2rem] font-semibold leading-tight text-text sm:text-[2.4rem]">Kết quả đã lưu</h1>
      <p className="mt-3 max-w-2xl text-lg leading-8 text-muted">
        Các lần kiểm tra trước, mới nhất ở trên cùng. Chọn mã học sinh để mở lại phiếu kết quả.
      </p>
      {children}
    </div>
  );
}

export default function HistoryPage() {
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
          setError("Không tải được danh sách. Hãy kiểm tra kết nối mạng rồi tải lại trang.");
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
        <p className="mt-8 text-base text-muted" role="status">
          Đang tải danh sách kết quả...
        </p>
      </Shell>
    );
  }

  if (error) {
    return (
      <Shell>
        <p className="mt-8 text-base text-red" role="alert">
          {error}
        </p>
      </Shell>
    );
  }

  if (rows.length === 0) {
    return (
      <Shell>
        <div className="mt-8 border-y border-border py-10">
          <p className="font-serif text-xl font-semibold text-text">Chưa có lần kiểm tra nào</p>
          <p className="mt-2 text-base text-muted">
            Sau lần kiểm tra đầu tiên, phiếu kết quả sẽ được lưu ở đây kèm mã học sinh.
          </p>
          <Link
            href="/screening"
            className="mt-5 inline-flex min-h-12 items-center rounded-md bg-accent px-6 text-base font-semibold text-white hover:bg-accent-2 active:translate-y-px"
          >
            Kiểm tra cho một em
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      {/* Phones: one entry per child, the code is the link. */}
      <ul className="mt-8 border-t border-border md:hidden">
        {rows.map((row) => {
          const o = overall(row.final_output);
          const a = partLabel(row.model_a_output, "Không có");
          const b = partLabel(row.model_b_output, "Không có ảnh");
          return (
            <li key={row.session_id} className="border-b border-border py-4">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <Link
                  href={`/results/${row.session_id}`}
                  className="inline-flex min-h-11 items-center text-lg font-semibold text-accent-2 underline decoration-1 underline-offset-4"
                >
                  {row.patient_id}
                </Link>
                <span className="text-sm text-muted">{formatDate(row.predicted_at)}</span>
              </div>
              <p className={`mt-1 ${o.cls}`}>{o.text}</p>
              <p className="mt-1 text-sm text-muted">
                Bàn tay: <span className={a.cls}>{a.text}</span>. Trang vở: <span className={b.cls}>{b.text}</span>.
              </p>
            </li>
          );
        })}
      </ul>

      {/* Tablet and desktop: a table, the overall result right after the code because it is what people scan for. */}
      <table className="mt-8 hidden w-full border-collapse text-left text-[15px] md:table">
        <thead>
          <tr className="border-b-2 border-text/70 text-sm text-text">
            <th scope="col" className="py-3 pr-4 font-semibold">Mã học sinh</th>
            <th scope="col" className="py-3 pr-4 font-semibold">Kết quả chung</th>
            <th scope="col" className="py-3 pr-4 font-semibold">Bàn tay lúc viết</th>
            <th scope="col" className="py-3 pr-4 font-semibold">Trang vở</th>
            <th scope="col" className="py-3 font-semibold">Ngày kiểm tra</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const o = overall(row.final_output);
            const a = partLabel(row.model_a_output, "Không có");
            const b = partLabel(row.model_b_output, "Không có ảnh");
            return (
              <tr key={row.session_id} className="border-b border-border">
                <td className="py-4 pr-4">
                  <Link
                    href={`/results/${row.session_id}`}
                    className="inline-flex min-h-11 items-center font-semibold text-accent-2 underline decoration-1 underline-offset-4 hover:decoration-2"
                  >
                    {row.patient_id}
                  </Link>
                </td>
                <td className={`py-4 pr-4 ${o.cls}`}>{o.text}</td>
                <td className={`py-4 pr-4 ${a.cls}`}>{a.text}</td>
                <td className={`py-4 pr-4 ${b.cls}`}>{b.text}</td>
                <td className="whitespace-nowrap py-4 text-muted">{formatDate(row.predicted_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Shell>
  );
}
