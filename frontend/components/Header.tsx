"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PenIcon } from "./Icons";

const NAV_LINKS = [
  { href: "/", label: "Trang chủ" },
  { href: "/history", label: "Kết quả đã lưu" },
  { href: "/about", label: "Hướng dẫn" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  // A single result belongs to the saved-results section.
  if (href === "/history" && pathname.startsWith("/results/")) return true;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Header() {
  const pathname = usePathname() ?? "/";

  return (
    <header className="border-b border-border bg-surface print:hidden">
      <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-white">
            <PenIcon className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-base font-bold leading-tight text-text">Sàng lọc khó viết</span>
            <span className="block text-sm leading-tight text-muted">Dành cho giáo viên và phụ huynh</span>
          </span>
        </Link>

        <nav aria-label="Điều hướng chính" className="flex flex-wrap items-center gap-1">
          {NAV_LINKS.map((link) => {
            const active = isActive(pathname, link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-lg px-3 py-2 text-[15px] font-medium transition-colors ${
                  active ? "bg-accent-soft text-accent-2" : "text-muted hover:bg-surface-2 hover:text-text"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <Link
            href="/screening"
            className="ml-1 rounded-lg bg-accent px-4 py-2 text-[15px] font-semibold text-white transition-colors hover:bg-accent-2"
          >
            Kiểm tra mới
          </Link>
        </nav>
      </div>
    </header>
  );
}
