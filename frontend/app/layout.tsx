import type { Metadata } from "next";
import type { ReactNode } from "react";
import Header from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sàng lọc rối loạn chữ viết",
  description: "Ứng dụng sàng lọc rối loạn chữ viết (dysgraphia) cho trẻ em.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className="dark h-full">
      <body className="bg-background text-text antialiased flex min-h-full flex-col">
        <Header />
        <main className="flex w-full flex-1 flex-col">{children}</main>
      </body>
    </html>
  );
}