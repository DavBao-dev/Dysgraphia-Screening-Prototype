import Link from "next/link";
import DetailsSection from "@/components/DetailsSection";
import {
  ArrowRightIcon,
  CheckCircleIcon,
  EyeIcon,
  ImageIcon,
  InfoIcon,
  ShieldIcon,
  VideoIcon,
} from "@/components/Icons";

const VIDEO_STEPS = [
  "Cho trẻ ngồi viết như bình thường, với giấy và bút quen thuộc.",
  "Đặt điện thoại phía trên bàn (có thể kê lên chồng sách), camera hướng xuống tay và trang giấy.",
  "Bật quay, để trẻ chép một đoạn ngắn trong khoảng 15–30 giây.",
  "Tải video lên ở Bước 2 của trang Kiểm tra. Hoặc chọn “Quay bằng camera” để quay ngay trên máy tính.",
];

const VIDEO_DONT = [
  "Không quay ngược sáng hoặc nơi quá tối",
  "Không để tay người khác che mất bàn tay trẻ",
  "Không cần quay khuôn mặt của trẻ",
];

const PHOTO_STEPS = [
  "Chụp thẳng từ trên xuống trang vở trẻ vừa viết, không nghiêng.",
  "Chụp khoảng 2–3 dòng chữ trẻ tự viết.",
  "Chụp nơi đủ sáng, không có bóng tay hay bóng điện thoại đè lên chữ.",
];

function Section({ id, icon: Icon, title, children }: { id?: string; icon: typeof InfoIcon; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24 rounded-2xl border border-border bg-surface p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent-2">
          <Icon className="h-5 w-5" />
        </span>
        <h2 className="text-xl font-semibold text-text">{title}</h2>
      </div>
      <div className="mt-4 text-base leading-relaxed text-muted">{children}</div>
    </section>
  );
}

export default function AboutPage() {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-3xl font-bold tracking-tight text-text">Hướng dẫn sử dụng</h1>
      <p className="mt-2 text-lg leading-relaxed text-muted">
        Những điều cần biết để kiểm tra đúng cách và hiểu đúng kết quả.
      </p>

      <div className="mt-8 space-y-5">
        <Section icon={InfoIcon} title="Khó viết là gì?">
          <p>
            Khó viết (dysgraphia) là khi trẻ gặp khó khăn kéo dài trong việc viết tay: chữ khó đọc, viết rất chậm, cầm
            bút khó khăn hoặc nhanh mỏi tay, dù đã được hướng dẫn và luyện tập. Khó viết{" "}
            <strong className="text-text">không liên quan đến trí thông minh</strong>, và kỹ năng viết có thể cải thiện
            khi trẻ được hỗ trợ đúng cách.
          </p>
          <p className="mt-3">
            Công cụ này giúp giáo viên và phụ huynh nhận biết sớm những trẻ nên được quan sát thêm. Nó{" "}
            <strong className="text-text">không thay thế</strong> việc đánh giá của chuyên gia.
          </p>
        </Section>

        <Section id="cach-quay" icon={VideoIcon} title="Cách quay video bàn tay">
          <ol className="space-y-2.5">
            {VIDEO_STEPS.map((step, i) => (
              <li key={step} className="flex items-start gap-3 text-text">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-semibold text-white">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
          <div className="mt-5 rounded-xl bg-surface-2 p-4">
            <p className="text-sm font-semibold text-text">Nên tránh</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-[15px]">
              {VIDEO_DONT.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </Section>

        <Section icon={ImageIcon} title="Cách chụp ảnh chữ viết (không bắt buộc)">
          <ul className="list-disc space-y-1.5 pl-5">
            {PHOTO_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </Section>

        <Section icon={CheckCircleIcon} title="Hiểu kết quả">
          <div className="space-y-3">
            <div className="flex items-start gap-3 rounded-xl border border-green/30 bg-green-soft p-4">
              <CheckCircleIcon className="mt-0.5 h-5 w-5 shrink-0 text-green" />
              <p>
                <strong className="text-text">Chưa thấy dấu hiệu đáng lo:</strong> ở lần kiểm tra này, cách viết của trẻ
                chưa cho thấy dấu hiệu rõ rệt. Nếu bạn vẫn thấy trẻ gặp khó khăn kéo dài, hãy kiểm tra lại sau hoặc
                trao đổi với giáo viên.
              </p>
            </div>
            <div className="flex items-start gap-3 rounded-xl border border-accent/30 bg-accent-soft p-4">
              <EyeIcon className="mt-0.5 h-5 w-5 shrink-0 text-accent-2" />
              <p>
                <strong className="text-text">Nên theo dõi thêm:</strong> hệ thống thấy một vài dấu hiệu có thể liên quan
                đến khó viết. Điều này không có nghĩa là trẻ bị khó viết. Hãy quan sát thêm và, nếu cần, đưa trẻ gặp
                chuyên gia để được đánh giá.
              </p>
            </div>
          </div>
        </Section>

        <Section icon={ShieldIcon} title="Giới hạn và quyền riêng tư">
          <ul className="list-disc space-y-1.5 pl-5">
            <li>Kết quả là gợi ý sàng lọc, có thể bỏ sót hoặc báo nhầm. Chỉ chuyên gia mới có thể chẩn đoán.</li>
            <li>
              Mô hình chữ viết hiện được huấn luyện trên chữ viết của học sinh Malaysia; độ chính xác với chữ tiếng Việt
              đang được tiếp tục kiểm tra.
            </li>
            <li>Video và ảnh không được lưu lại sau khi phân tích. Hệ thống chỉ lưu kết quả kèm mã học sinh bạn nhập.</li>
            <li>Không nhập họ tên đầy đủ hay thông tin nhận dạng của trẻ.</li>
          </ul>

          <DetailsSection title="Thông tin kỹ thuật (dành cho chuyên môn)">
            <p>
              <strong className="text-text">Chuyển động tay:</strong> MediaPipe Hands nhận diện 21 điểm trên bàn tay ở
              mỗi khung hình; hệ thống tính 18 đặc trưng vận động (tốc độ, gia tốc, độ giật, tỉ lệ dừng bút, run tay
              3–8 Hz, khoảng cách ngón cái – ngón trỏ…) rồi đưa vào mô hình Random Forest. Tay đứng yên hoặc nắm chặt sẽ
              bị loại để tránh kết quả sai.
            </p>
            <p className="mt-2">
              <strong className="text-text">Chữ viết:</strong> ảnh được nhị phân hoá và đưa về dạng mực đen trên nền
              trắng, sau đó ResNet50 trích đặc trưng hình ảnh, ghép với độ dày nét mực và độ lệch dòng, rồi đưa vào mạng
              MLP (chạy bằng ONNX Runtime). Kiểm định chéo theo học sinh trên 83 học sinh (bộ dữ liệu Mendeley,
              Malaysia): độ chính xác khoảng 83%, ROC-AUC 0,90.
            </p>
            <p className="mt-2">
              <strong className="text-text">Kết hợp:</strong> hai kết quả được biểu quyết; nếu khác nhau thì lấy trung
              bình xác suất với ngưỡng 50%. Không có ảnh thì dùng kết quả chuyển động tay.
            </p>
          </DetailsSection>
        </Section>
      </div>

      <div className="mt-8 flex justify-center">
        <Link
          href="/screening"
          className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3.5 text-base font-semibold text-white hover:bg-accent-2"
        >
          Bắt đầu kiểm tra
          <ArrowRightIcon className="h-5 w-5" />
        </Link>
      </div>
    </div>
  );
}
