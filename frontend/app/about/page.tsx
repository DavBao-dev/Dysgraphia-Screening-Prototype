import Link from "next/link";
import DetailsSection from "@/components/DetailsSection";

export default function AboutPage() {
  return (
    <main className="mx-auto w-full max-w-[960px] flex-1 px-6 py-10">
      <h1 className="text-3xl font-bold tracking-tight text-text">Giới thiệu</h1>
      <p className="mt-2 text-sm text-muted">
        Nguyên mẫu này khám phá cách AI có thể giúp nhận diện các mẫu chữ viết
        và chuyển động tay có thể hữu ích cho việc sàng lọc chứng khó viết
        (dysgraphia).
      </p>
      <p className="mt-3 text-sm text-muted">
        Công cụ này chỉ dành cho mục đích <strong>sàng lọc và nghiên cứu</strong>,
        không thay thế việc đánh giá của các chuyên gia có trình độ.
      </p>

      <section className="mt-6 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-base font-semibold text-text">Nguyên tắc hoạt động</h2>
        <p className="mt-1 text-sm text-muted">
          Một bài sàng lọc gồm phân tích chuyển động tay (bắt buộc) và phân tích
          chữ viết tay (tùy chọn). Hệ thống tổng hợp các tín hiệu và đưa ra kết
          quả sàng lọc mang tính tham khảo.
        </p>
      </section>

      <div className="mt-4 space-y-4">
        <DetailsSection title="Chi tiết kỹ thuật — Chuyển động tay">
          <p className="text-sm text-muted">
            Phân tích chuyển động tay từ video hoặc camera trực tiếp sử dụng{" "}
            <strong>MediaPipe Hands</strong> để phát hiện 21 điểm mốc bàn tay
            trên mỗi frame, trích xuất <strong>28 đặc trưng vận động học</strong>,
            sau đó đưa vào bộ phân loại <strong>Random Forest</strong> để đưa ra
            dự đoán. Đầu ra là tín hiệu nhị phân: cao hơn / thấp.
          </p>
          <ul className="mt-3 space-y-1 text-sm text-text">
            <li>
              <span className="text-muted">Nguồn dữ liệu:</span> Video (mp4, mov,
              avi) hoặc landmarks từ camera trực tiếp
            </li>
            <li>
              <span className="text-muted">Đặc trưng:</span> MediaPipe Hands
              landmarks + 28 đặc trưng vận động học
            </li>
            <li>
              <span className="text-muted">Mô hình phân loại:</span> Random
              Forest
            </li>
          </ul>
        </DetailsSection>

        <DetailsSection title="Chi tiết kỹ thuật — Chữ viết tay">
          <p className="text-sm text-muted">
            Phân tích ảnh chữ viết tay sử dụng backbone ResNet50 để trích xuất
            đặc trưng hình ảnh, kết hợp hai đặc trưng thủ công (độ dày mực và
            độ lệch đường cơ sở) đưa vào mạng MLP classifier chạy trên OpenVINO.
          </p>
          <ul className="mt-3 space-y-1 text-sm text-text">
            <li>
              <span className="text-muted">Nguồn dữ liệu:</span> Ảnh PNG/JPG chữ
              viết tay
            </li>
            <li>
              <span className="text-muted">Đặc trưng:</span> ResNet50 embedding +
              ink_thickness_mean + baseline_deviation
            </li>
            <li>
              <span className="text-muted">Mô hình phân loại:</span> MLP
              (OpenVINO)
            </li>
          </ul>
        </DetailsSection>

        <DetailsSection title="Chi tiết kỹ thuật — Kết hợp kết quả">
          <p className="text-sm text-muted">
            Kết quả bỏ phiếu đa số giữa phân tích chuyển động tay và phân tích
            chữ viết tay. Nếu chỉ có một nguồn hoạt động, kết quả trực tiếp từ
            nguồn đó được sử dụng.
          </p>
        </DetailsSection>
      </div>

      <div className="mt-6 rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-text">Lưu ý</h2>
        <p className="mt-1 text-sm text-muted">
          Kết quả sàng lọc, không phải chẩn đoán y tế.
        </p>
      </div>

      <div className="mt-6">
        <Link href="/screening" className="text-sm text-accent hover:underline">
          ← Bắt đầu sàng lọc mới
        </Link>
      </div>
    </main>
  );
}
