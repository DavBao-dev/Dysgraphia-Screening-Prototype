import { CheckIcon } from "./Icons";

interface TipListProps {
  title?: string;
  tips: string[];
}

export default function TipList({ title = "Mẹo để có kết quả tốt", tips }: TipListProps) {
  return (
    <div className="rounded-xl bg-surface-2 p-4">
      <p className="text-sm font-semibold text-text">{title}</p>
      <ul className="mt-2 grid gap-2 sm:grid-cols-2">
        {tips.map((tip) => (
          <li key={tip} className="flex items-start gap-2 text-[15px] leading-snug text-muted">
            <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-green" />
            {tip}
          </li>
        ))}
      </ul>
    </div>
  );
}
