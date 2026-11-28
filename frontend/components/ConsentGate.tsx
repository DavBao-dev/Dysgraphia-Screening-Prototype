"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { loadPolicy, type DataPolicy, type ConsentReceipt } from "@/lib/consent";

export default function ConsentGate({ onConfirm }: { onConfirm: (receipt: ConsentReceipt) => void }) {
  const [policy, setPolicy] = useState<DataPolicy | null>(null);
  const [role, setRole] = useState("parent");
  const [reference, setReference] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [authority, setAuthority] = useState(false);
  const [assent, setAssent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; loadPolicy().then(p => { if (active) setPolicy(p); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, []);
  const canConfirm = policy?.ready && accepted && authority && assent && (role !== "teacher" || reference.trim().length > 0);
  async function confirm() {
    if (!canConfirm || busy || !policy) return;
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/consent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version: policy.version, policy_hash: policy.policy_hash, role, guardian_reference: role === "teacher" ? reference.trim() : "", accepted, authority_confirmed: authority, child_assent: assent }) });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Chưa ghi nhận được xác nhận. Vui lòng thử lại.");
      onConfirm(body as ConsentReceipt);
    } catch (e) { setError(e instanceof Error ? e.message : "Chưa kết nối được máy chủ."); setBusy(false); }
  }
  return <section className="mx-auto w-full max-w-2xl px-4 py-10 sm:px-6" aria-labelledby="consent-title">
    <p className="text-sm font-medium text-muted">Trước khi bắt đầu</p>
    <h1 id="consent-title" className="mt-2 font-serif text-3xl font-semibold">Xác nhận xử lý dữ liệu</h1>
    <p className="mt-4 leading-7">Chúng tôi phân tích video bàn tay hoặc điểm mốc bàn tay và ảnh chữ viết để hỗ trợ sàng lọc. Dữ liệu được gửi đến máy chủ; kết quả không thay thế chẩn đoán chuyên môn.</p>
    <p className="mt-3 leading-7">Nhóm thực hiện: Phan Xuân Khoa, Nguyễn Trần Gia Bảo, Cao Tùng Lâm. Liên hệ: <a className="underline" href="mailto:phanxuankhoa2010@gmail.com">phanxuankhoa2010@gmail.com</a>.</p>
    <p className="mt-4"><Link href="/terms" target="_blank" rel="noopener noreferrer" className="font-semibold text-accent underline underline-offset-4">Đọc điều khoản xử lý dữ liệu cá nhân (mở tab mới)</Link></p>
    {!policy && !error && <p role="status" className="mt-5">Đang tải thông tin xác nhận…</p>}
    {policy && !policy.ready && <p role="alert" className="mt-5 border border-border p-4 leading-7">Bản triển khai chưa sẵn sàng thu dữ liệu thật. Chưa thể xác nhận hoặc tải dữ liệu học sinh.</p>}
    <fieldset disabled={!policy?.ready || busy} className="mt-6 space-y-4 disabled:opacity-60">
      <legend className="font-semibold">Người xác nhận</legend>
      <label className="block">Tư cách của bạn<select value={role} onChange={e => { setRole(e.target.value); setAuthority(false); setReference(""); }} className="mt-2 block min-h-12 w-full rounded-md border border-field bg-surface px-3"><option value="parent">Cha hoặc mẹ của học sinh</option><option value="representative">Người đại diện hợp pháp khác</option><option value="teacher">Giáo viên đã có sự đồng ý được lưu riêng</option></select></label>
      {role === "teacher" && <label className="block">Mã hồ sơ đồng ý của người đại diện (không nhập họ tên)<input maxLength={120} value={reference} onChange={e => setReference(e.target.value)} className="mt-2 block min-h-12 w-full rounded-md border border-field bg-surface px-3" /></label>}
      <label className="flex cursor-pointer items-start gap-3 leading-7"><input type="checkbox" checked={authority} onChange={e => setAuthority(e.target.checked)} className="mt-1.5 size-5 shrink-0" />{role === "teacher" ? "Tôi đã có sự đồng ý hợp lệ, có thể kiểm chứng của người đại diện và chỉ thực hiện trong phạm vi được phép." : "Tôi xác nhận có quyền đại diện cho học sinh trong việc tham gia sàng lọc này."}</label>
      <label className="flex cursor-pointer items-start gap-3 leading-7"><input type="checkbox" checked={assent} onChange={e => setAssent(e.target.checked)} className="mt-1.5 size-5 shrink-0" />Tôi đã giải thích bằng lời dễ hiểu; học sinh muốn tham gia và biết có thể dừng bất cứ lúc nào.</label>
      <label className="flex cursor-pointer items-start gap-3 leading-7"><input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)} className="mt-1.5 size-5 shrink-0" />Tôi đã đọc điều khoản và đồng ý xử lý dữ liệu chỉ để sàng lọc, không bao gồm nghiên cứu hoặc huấn luyện mô hình.</label>
    </fieldset>
    {error && <p role="alert" className="mt-5 text-red">{error} {!policy && <button type="button" className="underline" onClick={() => window.location.reload()}>Tải lại</button>}</p>}
    <div className="mt-7 flex flex-wrap items-center gap-5"><button type="button" onClick={() => void confirm()} disabled={!canConfirm || busy} className="min-h-12 rounded-md bg-accent px-6 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{busy ? "Đang ghi nhận…" : "Xác nhận và tiếp tục"}</button><Link href="/" className="underline">Không tham gia</Link></div>
    <p className="mt-5 text-sm leading-6 text-muted">Không ô nào được chọn sẵn. Từ chối không ảnh hưởng kết quả học tập. Xác nhận được ghi theo phiên bản {policy?.version ?? "đang tải"} và cần thực hiện lại khi bắt đầu lần kiểm tra mới.</p>
  </section>;
}
