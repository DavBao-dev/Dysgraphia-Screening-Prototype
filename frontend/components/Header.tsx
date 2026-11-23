"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/history", label: "Kết quả đã lưu" },
  { href: "/about", label: "Hướng dẫn" },
];

function isActive(pathname: string, href: string): boolean {
  // A single result belongs to the saved-results section.
  if (href === "/history" && pathname.startsWith("/results/")) return true;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Header() {
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close the phone menu when the route changes.
  const [lastPath, setLastPath] = useState(pathname);
  if (lastPath !== pathname) {
    setLastPath(pathname);
    setOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const linkClass = (active: boolean) =>
    `inline-flex min-h-11 items-center rounded-md px-3 text-[15px] font-medium underline-offset-4 ${
      active ? "text-accent-2 underline decoration-2" : "text-muted hover:text-text hover:underline active:text-accent-2"
    }`;

  return (
    <header className="border-b border-border bg-surface print:hidden">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        {/* Wordmark: the product name chosen by the team, set in the heading serif (no logo has been supplied). */}
        <Link href="/" className="inline-flex min-h-11 items-center font-serif text-[1.4rem] font-semibold text-text hover:text-accent-2">
          DysScan
        </Link>

        <nav aria-label="Điều hướng chính" className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => {
            const active = isActive(pathname, link.href);
            return (
              <Link key={link.href} href={link.href} aria-current={active ? "page" : undefined} className={linkClass(active)}>
                {link.label}
              </Link>
            );
          })}
          <Link
            href="/screening"
            className="ml-2 inline-flex min-h-11 items-center rounded-md bg-accent px-4 text-[15px] font-semibold text-white hover:bg-accent-2 active:translate-y-px"
          >
            Kiểm tra cho một em
          </Link>
        </nav>

        <button
          ref={buttonRef}
          type="button"
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
          className="min-h-11 rounded-md border border-border px-4 text-[15px] font-medium text-text hover:bg-surface-2 active:bg-border md:hidden"
        >
          {open ? "Đóng" : "Menu"}
        </button>
      </div>

      {open && (
        <nav id="mobile-menu" aria-label="Điều hướng chính" className="border-t border-border px-4 pb-4 pt-2 md:hidden">
          <ul className="flex flex-col">
            {NAV_LINKS.map((link) => {
              const active = isActive(pathname, link.href);
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    aria-current={active ? "page" : undefined}
                    className={`block min-h-11 py-3 text-base font-medium ${active ? "text-accent-2 underline decoration-2 underline-offset-4" : "text-text"}`}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
          <Link
            href="/screening"
            className="mt-2 flex min-h-12 items-center justify-center rounded-md bg-accent px-4 text-base font-semibold text-white hover:bg-accent-2"
          >
            Kiểm tra cho một em
          </Link>
        </nav>
      )}
    </header>
  );
}
