// One line of the result sheet: which part was analysed, what it found, and what it looked at.
interface PartRowProps {
  title: string;
  lookedAt: string;
  available: boolean;
  prediction: number | null;
  unavailableText: string;
}

function finding(available: boolean, p: number | null): { label: string; cls: string } {
  if (!available) return { label: "Không có dữ liệu", cls: "text-muted" };
  if (p === 1) return { label: "Có dấu hiệu cần chú ý", cls: "text-accent-2" };
  if (p === 0) return { label: "Chưa thấy dấu hiệu", cls: "text-green" };
  return { label: "Chưa phân tích được", cls: "text-muted" };
}

export default function PartRow({ title, lookedAt, available, prediction, unavailableText }: PartRowProps) {
  const f = finding(available, prediction);
  return (
    <div className="grid gap-1 border-t border-rule py-4 sm:grid-cols-[200px_1fr] sm:gap-6">
      <dt className="font-semibold text-text">{title}</dt>
      <dd>
        <p className={`font-semibold ${f.cls}`}>{f.label}</p>
        <p className="mt-1 text-[15px] leading-6 text-muted">{available ? lookedAt : unavailableText}</p>
      </dd>
    </div>
  );
}
