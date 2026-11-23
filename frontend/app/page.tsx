import Link from "next/link";

const SIGNS = [
  "Chữ khó đọc, cỡ chữ to nhỏ không đều",
  "Khoảng cách giữa các chữ lúc rộng lúc hẹp",
  "Chữ không bám dòng kẻ, hay lệch lên lệch xuống",
  "Cầm bút rất chặt hoặc khó điều khiển bút",
  "Viết rất chậm, hay kêu mỏi tay",
  "Hay bỏ sót chữ cái khi viết",
];

const PREPARE = [
  "Điện thoại hoặc máy tính có camera",
  "Giấy, vở và cây bút em vẫn dùng hằng ngày",
  "Chỗ ngồi đủ sáng để quay rõ bàn tay",
];

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 sm:px-6">
      {/* Opening: the headline written on an exercise-book page (identity motif). */}
      <section className="grid gap-8 pt-8 sm:pt-12 lg:grid-cols-[1.5fr_1fr] lg:gap-12">
        <div>
          <div className="o-li rounded-sheet border border-border py-8 pl-14 pr-5 sm:py-10 sm:pl-16 sm:pr-8">
            <h1 className="font-serif text-[2rem] font-semibold leading-[1.15] text-text sm:text-[2.6rem]">
              Nhận biết sớm dấu hiệu khó viết ở trẻ
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-text">
              Quay một đoạn video bàn tay lúc em đang viết, chụp thêm trang vở nếu có. Hệ thống sẽ cho biết em có nên được
              quan sát thêm không, và gợi ý gia đình, nhà trường nên làm gì tiếp theo.
            </p>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
            <Link
              href="/screening"
              className="inline-flex min-h-12 items-center rounded-md bg-accent px-6 text-base font-semibold text-white hover:bg-accent-2 active:translate-y-px"
            >
              Bắt đầu kiểm tra
            </Link>
            <Link
              href="/about#cach-quay"
              className="inline-flex min-h-11 items-center text-base font-medium text-accent-2 underline decoration-1 underline-offset-4 hover:decoration-2"
            >
              Cách quay video cho đúng
            </Link>
          </div>
        </div>

        <aside aria-labelledby="prepare-title" className="lg:pt-4">
          <h2 id="prepare-title" className="font-serif text-xl font-semibold text-text">
            Trước khi bắt đầu
          </h2>
          <ul className="mt-3 divide-y divide-border border-y border-border">
            {PREPARE.map((item) => (
              <li key={item} className="py-3 text-base text-text">
                {item}
              </li>
            ))}
          </ul>
          <p className="mt-4 text-[15px] leading-relaxed text-muted">
            Không cần nhập họ tên. Mỗi em chỉ cần một mã ngắn, ví dụ HS01, để bạn tìm lại kết quả sau.
          </p>
        </aside>
      </section>

      {/* What the system looks at: two inputs with different weight, so they are not shown as equal cards. */}
      <section aria-labelledby="looks-title" className="mt-16 sm:mt-20">
        <h2 id="looks-title" className="font-serif text-2xl font-semibold text-text sm:text-[1.75rem]">
          Hệ thống xem những gì
        </h2>
        <div className="mt-6 grid gap-x-12 gap-y-8 md:grid-cols-[1.3fr_1fr]">
          <div>
            <p className="text-sm font-semibold text-accent-2">Bắt buộc</p>
            <h3 className="mt-1 text-xl font-semibold text-text">Bàn tay lúc đang viết</h3>
            <p className="mt-2 text-base leading-7 text-muted">
              Từ video, hệ thống theo dõi 21 điểm trên bàn tay qua từng khung hình để xem tốc độ và độ mượt của nét, số
              lần dừng bút giữa chừng và độ run của tay. Đây là những điều khó thấy bằng mắt khi chỉ nhìn trang vở đã
              viết xong.
            </p>
          </div>
          <div className="md:border-l md:border-border md:pl-10">
            <p className="text-sm font-semibold text-muted">Không bắt buộc</p>
            <h3 className="mt-1 text-xl font-semibold text-text">Trang vở em vừa viết</h3>
            <p className="mt-2 text-base leading-7 text-muted">
              Ảnh chụp giúp hệ thống xem thêm hình dạng chữ, độ đậm của nét và chữ có bám dòng hay không.
            </p>
          </div>
        </div>
        <p className="mt-8 max-w-3xl border-t border-border pt-6 text-base leading-7 text-text">
          Kết quả được viết thành một phiếu ngắn bằng lời thường, kèm những việc nên làm tiếp. Bạn có thể in phiếu để
          mang theo khi trao đổi giữa gia đình và nhà trường.
        </p>
      </section>

      {/* When to check: the signs written as lines on a notebook page. */}
      <section aria-labelledby="signs-title" className="mt-16 grid gap-8 sm:mt-20 lg:grid-cols-[1fr_1.2fr] lg:gap-12">
        <div>
          <h2 id="signs-title" className="font-serif text-2xl font-semibold text-text sm:text-[1.75rem]">
            Khi nào nên kiểm tra?
          </h2>
          <p className="mt-3 text-base leading-7 text-muted">
            Khó viết (dysgraphia) là khi trẻ gặp khó khăn kéo dài với việc viết tay, dù đã được hướng dẫn và luyện tập.
            Hãy thử kiểm tra nếu em thường xuyên có vài dấu hiệu trong danh sách sau.
          </p>
          <p className="mt-4 text-base leading-7 text-text">
            Khó viết không liên quan đến trí thông minh hay sự lười biếng. Phát hiện sớm giúp em được hỗ trợ kịp thời, và
            kỹ năng viết có thể tiến bộ khi được hỗ trợ đúng cách.
          </p>
        </div>
        <ol className="margin-line rounded-sheet border border-border bg-surface">
          {SIGNS.map((sign, i) => (
            <li
              key={sign}
              className="flex gap-4 border-b border-rule py-3.5 pl-11 pr-5 text-base text-text last:border-b-0"
            >
              <span className="w-4 shrink-0 font-serif text-muted" aria-hidden="true">
                {i + 1}.
              </span>
              {sign}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
