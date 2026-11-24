import Link from "next/link";
import DetailsSection from "@/components/DetailsSection";

const VIDEO_STEPS = [
  "Cho em ngồi viết như bình thường, với giấy, vở và cây bút quen thuộc.",
  "Đặt điện thoại phía trên bàn (có thể kê lên chồng sách), camera hướng xuống bàn tay và trang giấy.",
  "Bật quay, để em chép một đoạn ngắn trong khoảng 15 đến 30 giây.",
  "Mở trang Kiểm tra, tải video lên ở Bước 2. Hoặc chọn quay bằng camera để quay ngay trên máy tính.",
];

const VIDEO_AVOID = [
  "Quay ngược sáng hoặc ở chỗ quá tối",
  "Để tay người khác che mất bàn tay em",
  "Quay khuôn mặt em: hệ thống không cần đến",
];

const PHOTO_STEPS = [
  "Chụp thẳng từ trên xuống trang vở em vừa viết, không nghiêng máy.",
  "Chụp khoảng 2 hoặc 3 dòng em tự viết.",
  "Chụp ở chỗ đủ sáng, không có bóng tay hay bóng điện thoại đè lên chữ.",
];

const TOC = [
  { href: "#kho-viet", label: "Khó viết là gì" },
  { href: "#cach-quay", label: "Cách quay video" },
  { href: "#cach-chup", label: "Cách chụp ảnh" },
  { href: "#hieu-ket-qua", label: "Hiểu phiếu kết quả" },
  { href: "#gioi-han", label: "Giới hạn và quyền riêng tư" },
];

export default function AboutPage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 pt-8 sm:px-6 sm:pt-12">
      <h1 className="font-serif text-[2rem] font-semibold leading-tight text-text sm:text-[2.4rem]">Hướng dẫn</h1>
      <p className="mt-3 max-w-2xl text-lg leading-8 text-muted">
        Những điều cần biết để kiểm tra đúng cách và đọc đúng phiếu kết quả.
      </p>

      <div className="mt-10 grid gap-10 lg:grid-cols-[200px_1fr]">
        <nav aria-label="Mục lục" className="lg:sticky lg:top-6 lg:self-start">
          <p className="text-sm font-semibold text-muted">Trong trang này</p>
          <ul className="mt-1">
            {TOC.map((t) => (
              <li key={t.href}>
                <a
                  href={t.href}
                  className="inline-flex min-h-11 items-center text-[15px] text-accent-2 underline decoration-1 underline-offset-4 hover:decoration-2"
                >
                  {t.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="max-w-2xl space-y-12 text-base leading-7 text-text">
          <section id="kho-viet" className="scroll-mt-6">
            <h2 className="font-serif text-2xl font-semibold">Khó viết là gì?</h2>
            <p className="mt-3">
              Khó viết (dysgraphia) là khi trẻ gặp khó khăn kéo dài với việc viết tay: chữ khó đọc, viết rất chậm, cầm bút
              khó khăn hoặc nhanh mỏi tay, dù đã được hướng dẫn và luyện tập. Khó viết không liên quan đến trí thông minh,
              và kỹ năng viết có thể tiến bộ khi trẻ được hỗ trợ đúng cách.
            </p>
            <p className="mt-3 text-muted">
              Công cụ này giúp giáo viên và phụ huynh nhận ra sớm những em nên được quan sát thêm. Nó không thay thế việc
              đánh giá của chuyên gia.
            </p>
          </section>

          <section id="cach-quay" className="scroll-mt-6">
            <h2 className="font-serif text-2xl font-semibold">Cách quay video bàn tay</h2>
            <ol className="margin-line mt-4 rounded-sheet border border-border bg-surface">
              {VIDEO_STEPS.map((step, i) => (
                <li key={step} className="flex gap-4 border-b border-rule py-3.5 pl-11 pr-5 last:border-b-0">
                  <span className="w-4 shrink-0 font-serif text-muted" aria-hidden="true">
                    {i + 1}.
                  </span>
                  {step}
                </li>
              ))}
            </ol>
            <p className="mt-5 font-semibold">Nên tránh</p>
            <ul className="mt-1 list-disc space-y-1 pl-6 text-muted marker:text-accent">
              {VIDEO_AVOID.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section id="cach-chup" className="scroll-mt-6">
            <h2 className="font-serif text-2xl font-semibold">Cách chụp ảnh trang vở</h2>
            <p className="mt-2 text-muted">Ảnh không bắt buộc, nhưng giúp kết quả đầy đủ hơn.</p>
            <ul className="mt-3 list-disc space-y-1.5 pl-6 marker:text-accent">
              {PHOTO_STEPS.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </section>

          <section id="hieu-ket-qua" className="scroll-mt-6">
            <h2 className="font-serif text-2xl font-semibold">Hiểu phiếu kết quả</h2>
            <dl className="mt-4 space-y-5">
              <div>
                <dt className="font-semibold text-green">Chưa thấy dấu hiệu đáng lo</dt>
                <dd className="mt-1 text-muted">
                  Ở lần kiểm tra này, cách viết của em chưa cho thấy dấu hiệu rõ rệt. Nếu bạn vẫn thấy em gặp khó khăn kéo
                  dài, hãy kiểm tra lại sau hoặc trao đổi với giáo viên.
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-accent-2">Nên theo dõi thêm</dt>
                <dd className="mt-1 text-muted">
                  Hệ thống thấy một vài dấu hiệu có thể liên quan đến khó viết. Điều này không có nghĩa là em bị khó viết.
                  Hãy quan sát thêm, và nếu dấu hiệu vẫn còn, đưa em gặp chuyên gia để được đánh giá.
                </dd>
              </div>
            </dl>
          </section>

          <section id="gioi-han" className="scroll-mt-6">
            <h2 className="font-serif text-2xl font-semibold">Giới hạn và quyền riêng tư</h2>
            <ul className="mt-3 list-disc space-y-2 pl-6 marker:text-accent">
              <li>Kết quả là gợi ý sàng lọc, có thể bỏ sót hoặc báo nhầm. Chỉ chuyên gia mới chẩn đoán được.</li>
              <li>
                Phần đọc chữ viết hiện được huấn luyện trên chữ của học sinh Malaysia. Độ chính xác với chữ tiếng Việt đang
                được tiếp tục kiểm tra.
              </li>
              <li>Video và ảnh không được lưu lại sau khi phân tích. Hệ thống chỉ lưu kết quả kèm mã học sinh bạn nhập.</li>
              <li>Không nhập họ tên đầy đủ hay thông tin giúp nhận ra em.</li>
            </ul>

            <DetailsSection title="Chi tiết kỹ thuật">
              <p>
                <strong className="text-text">Bàn tay lúc viết:</strong> MediaPipe Hands nhận diện 21 điểm trên bàn tay ở
                mỗi khung hình. Hệ thống tính 18 đặc trưng vận động (tốc độ, gia tốc, độ giật, tỉ lệ dừng bút, run tay trong
                dải 3 đến 8 Hz, khoảng cách giữa ngón cái và ngón trỏ...) rồi đưa vào mô hình Random Forest. Tay đứng yên
                hoặc nắm chặt bị loại để tránh kết quả sai.
              </p>
              <p className="mt-2">
                <strong className="text-text">Trang vở:</strong> ảnh được nhị phân hoá và đưa về dạng mực đen trên nền
                trắng, sau đó ResNet50 trích đặc trưng hình ảnh, ghép với độ dày nét mực và độ lệch dòng, rồi đưa vào mạng
                MLP chạy bằng ONNX Runtime. Kiểm định chéo theo từng học sinh trên 83 học sinh (bộ dữ liệu Mendeley,
                Malaysia): độ chính xác khoảng 83%, ROC-AUC 0,90.
              </p>
              <p className="mt-2">
                <strong className="text-text">Kết hợp:</strong> hai kết quả được biểu quyết. Nếu khác nhau thì lấy trung
                bình xác suất với ngưỡng 50%. Không có ảnh thì dùng kết quả của bàn tay.
              </p>
            </DetailsSection>
          </section>

          <p className="border-t border-border pt-8">
            <Link
              href="/screening"
              className="inline-flex min-h-12 items-center rounded-md bg-accent px-6 text-base font-semibold text-white hover:bg-accent-2 active:translate-y-px"
            >
              Bắt đầu kiểm tra
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
