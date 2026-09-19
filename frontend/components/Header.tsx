import Link from "next/link";

const NAV_LINKS = [
  { href: "/screening", label: "Sàng lọc" },
  { href: "/history", label: "Lịch sử" },
  { href: "/about", label: "Giới thiệu" },
];

export default function Header() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex w-full max-w-[960px] items-center justify-between gap-4 px-6 py-4">
        <Link href="/screening" className="shrink-0">
          <p className="text-lg font-semibold text-text">Dysgraphia Screening</p>
          <p className="text-sm text-muted">Sàng lọc và đánh giá chữ viết cho học sinh</p>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm text-muted hover:bg-surface-2 hover:text-text"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/screening"
            className="ml-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-2"
          >
            Sàng lọc mới
          </Link>
        </nav>
      </div>
    </header>
  );
}