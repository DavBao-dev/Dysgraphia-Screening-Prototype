import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Be_Vietnam_Pro, Lora } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

// Body: Be Vietnam Pro, drawn for Vietnamese diacritics, very readable at small sizes.
const bodyFont = Be_Vietnam_Pro({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin", "vietnamese"],
  display: "swap",
  variable: "--font-body",
});

// Headings: Lora, a book serif with full Vietnamese support; gives the "sách giáo khoa" tone of the direction.
const headingFont = Lora({
  subsets: ["latin", "vietnamese"],
  display: "swap",
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "DysScan · Sàng lọc sớm dấu hiệu khó viết",
  description:
    "Công cụ giúp giáo viên và phụ huynh nhận biết sớm dấu hiệu khó viết (dysgraphia) ở trẻ qua video bàn tay khi viết và ảnh chữ viết. Không thay thế chẩn đoán của chuyên gia.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={`${bodyFont.variable} ${headingFont.variable} h-full`}>
      <body className="flex min-h-full flex-col bg-background font-sans text-text antialiased">
        <Header />
        <main className="flex w-full flex-1 flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
