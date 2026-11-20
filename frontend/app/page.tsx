import Link from "next/link";
import {
  ArrowRightIcon,
  ChartIcon,
  CheckIcon,
  ImageIcon,
  InfoIcon,
  ShieldIcon,
  UsersIcon,
  VideoIcon,
} from "@/components/Icons";

const STEPS = [
  {
    icon: VideoIcon,
    title: "Quay video bàn tay khi trẻ viết",
    text: "Đặt điện thoại phía trên, quay khoảng 15–30 giây lúc trẻ chép bài. Hoặc quay trực tiếp bằng camera máy tính.",
  },
  {
    icon: ImageIcon,
    title: "Chụp ảnh chữ viết (không bắt buộc)",
    text: "Chụp thẳng trang vở trẻ vừa viết để hệ thống xem thêm hình dạng chữ.",
  },
  {
    icon: ChartIcon,
    title: "Xem kết quả và gợi ý",
    text: "Kết quả viết bằng lời dễ hiểu, kèm những việc nên làm tiếp theo. Có thể in ra để trao đổi với giáo viên.",
  },
];

const SIGNS = [
  "Chữ khó đọc, cỡ chữ to nhỏ không đều",
  "Khoảng cách giữa các chữ lúc rộng lúc hẹp",
  "Chữ không thẳng hàng, hay lệch khỏi dòng kẻ",
  "Cầm bút rất chặt hoặc khó điều khiển bút",
  "Viết rất chậm, nhanh mỏi tay",
  "Hay bỏ sót chữ cái khi viết",
];

const PREPARE = [
  "Điện thoại hoặc máy tính có camera",
  "Giấy, vở và cây bút quen thuộc của trẻ",
  "Khoảng 5 phút ở nơi đủ ánh sáng",
];

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
      {/* Hero */}
      <section className="grid items-start gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-sm font-medium text-accent-2">
            <UsersIcon className="h-4 w-4" />
            Dành cho giáo viên và phụ huynh
          </p>
          <h1 className="mt-4 text-3xl font-bold leading-tight tracking-tight text-text sm:text-4xl">
            Nhận biết sớm dấu hiệu khó viết ở trẻ
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-muted">
            Chỉ cần một đoạn video quay bàn tay lúc trẻ viết, và ảnh chụp chữ viết nếu có. Hệ thống sẽ cho biết trẻ
            có nên được theo dõi thêm hay không, kèm gợi ý nên làm gì tiếp theo.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link
              href="/screening"
              className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-accent-2"
            >
              Bắt đầu kiểm tra
              <ArrowRightIcon className="h-5 w-5" />
            </Link>
            <Link
              href="/about#cach-quay"
              className="inline-flex items-center rounded-xl border border-border bg-surface px-6 py-3.5 text-base font-semibold text-text transition-colors hover:bg-surface-2"
            >
              Xem cách quay video
            </Link>
          </div>
          <p className="mt-4 text-sm text-muted">Miễn phí · Khoảng 5 phút · Không cần đăng ký</p>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Bạn cần chuẩn bị</h2>
          <ul className="mt-4 space-y-3">
            {PREPARE.map((item) => (
              <li key={item} className="flex items-start gap-3 text-base text-text">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-soft text-green">
                  <CheckIcon className="h-4 w-4" />
                </span>
                {item}
              </li>
            ))}
          </ul>
          <div className="mt-5 flex items-start gap-3 rounded-xl bg-surface-2 p-4 text-sm text-muted">
            <ShieldIcon className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
            <p>Không cần nhập họ tên trẻ. Chỉ cần một mã ngắn, ví dụ “HS01”.</p>
          </div>
        </div>
      </section>

      {/* Steps */}
      <section className="mt-14">
        <h2 className="text-2xl font-bold tracking-tight text-text">3 bước đơn giản</h2>
        <ol className="mt-5 grid gap-4 md:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-base font-bold text-white">
                  {i + 1}
                </span>
                <Icon className="h-6 w-6 text-accent" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-text">{title}</h3>
              <p className="mt-2 text-base leading-relaxed text-muted">{text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Signs */}
      <section className="mt-14 grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-text">Khi nào nên kiểm tra?</h2>
          <p className="mt-3 text-base leading-relaxed text-muted">
            Khó viết (dysgraphia) là khi trẻ gặp khó khăn kéo dài trong việc viết tay, dù đã được hướng dẫn và luyện
            tập. Bạn có thể dùng công cụ này nếu thấy trẻ thường xuyên có một vài dấu hiệu sau:
          </p>
          <div className="mt-5 flex items-start gap-3 rounded-2xl border border-accent/20 bg-accent-soft p-5">
            <InfoIcon className="mt-0.5 h-5 w-5 shrink-0 text-accent-2" />
            <p className="text-base leading-relaxed text-text">
              Khó viết <strong>không liên quan đến trí thông minh</strong> hay sự lười biếng. Kỹ năng viết có thể cải
              thiện khi trẻ được phát hiện sớm và hỗ trợ đúng cách.
            </p>
          </div>
        </div>
        <ul className="grid gap-3 sm:grid-cols-2">
          {SIGNS.map((sign) => (
            <li
              key={sign}
              className="flex items-start gap-3 rounded-xl border border-border bg-surface p-4 text-base text-text"
            >
              <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-accent" aria-hidden="true" />
              {sign}
            </li>
          ))}
        </ul>
      </section>

      {/* Final call to action */}
      <section className="mt-14 flex flex-col items-start justify-between gap-4 rounded-2xl bg-accent px-6 py-8 text-white sm:flex-row sm:items-center sm:px-8">
        <div>
          <h2 className="text-xl font-bold">Sẵn sàng thử?</h2>
          <p className="mt-1 text-base text-white/85">Kết quả chỉ mang tính tham khảo, không phải chẩn đoán y khoa.</p>
        </div>
        <Link
          href="/screening"
          className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-semibold text-accent-2 transition-colors hover:bg-accent-soft"
        >
          Bắt đầu kiểm tra
          <ArrowRightIcon className="h-5 w-5" />
        </Link>
      </section>
    </div>
  );
}
