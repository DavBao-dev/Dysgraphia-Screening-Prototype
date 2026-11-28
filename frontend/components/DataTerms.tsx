"use client";
import { useEffect, useState } from "react";
import { loadPolicy, type DataPolicy } from "@/lib/consent";

export default function DataTerms() {
  const [policy, setPolicy] = useState<DataPolicy | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; loadPolicy().then(p => { if (active) setPolicy(p); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, []);
  return <article className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
    <h1 className="font-serif text-3xl font-semibold">Điều khoản xử lý dữ liệu cá nhân</h1>
    <p className="mt-3 text-muted">Thông tin để xác nhận trước khi tham gia sàng lọc.</p>
    {error && <p role="alert" className="mt-6">{error} <button type="button" className="underline" onClick={() => window.location.reload()}>Tải lại</button></p>}
    {!policy && !error && <p role="status" className="mt-6">Đang tải điều khoản…</p>}
    {policy && <><p className="mt-4 text-sm text-muted">Phiên bản {policy.version}</p>
      {policy.sections.map(section => <section key={section.title} className="mt-7"><h2 className="text-lg font-semibold">{section.title}</h2><p className="mt-2 leading-8">{section.text}</p></section>)}
      <p className="mt-8 text-sm leading-7 text-muted">Căn cứ tham chiếu: <a className="underline" href="https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm" target="_blank" rel="noopener noreferrer">Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15</a>, đặc biệt Điều 3, 4, 9, 10, 14 và 24; các văn bản hướng dẫn có liên quan. Việc bấm xác nhận không thay thế trách nhiệm bảo vệ dữ liệu của bên vận hành.</p>
      <button type="button" className="mt-6 min-h-12 border border-border px-5" onClick={() => window.print()}>In hoặc lưu điều khoản</button>
    </>}
  </article>;
}
