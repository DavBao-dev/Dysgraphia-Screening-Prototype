interface TipListProps {
  title: string;
  tips: string[];
}

export default function TipList({ title, tips }: TipListProps) {
  return (
    <div className="rounded-sheet bg-surface-2 px-5 py-4">
      <p className="text-[15px] font-semibold text-text">{title}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-[15px] leading-6 text-muted marker:text-accent">
        {tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </div>
  );
}
