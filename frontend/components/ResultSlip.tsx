import PartRow from "@/components/PartRow";
import DetailsSection from "@/components/DetailsSection";
import StatusCard from "@/components/StatusCard";
import FeatureGroups from "@/components/FeatureGroups";
import ConfidenceBlock from "@/components/ConfidenceBlock";
import { assessConfidence } from "@/lib/confidence";
import type { SessionDetail } from "@/types/screening";

function formatDate(raw: string): string {
  try {
    return new Date(raw).toLocaleString("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return raw;
  }
}

interface Verdict {
  title: string;
  summary: string;
  steps: string[];
  titleCls: string;
}

function verdictFor(prediction: number | null | undefined): Verdict {
  if (prediction === 1) {
    return {
      title: "Nên theo dõi thêm",
      summary:
        "Hệ thống thấy một vài dấu hiệu có thể liên quan đến khó viết. Điều này không có nghĩa là em bị khó viết, nhưng em nên được quan sát kỹ hơn trong thời gian tới.",
      steps: [
        "Giáo viên và phụ huynh trao đổi với nhau về việc viết của em ở lớp và ở nhà.",
        "Quan sát thêm trong 2 đến 4 tuần: cách cầm bút, tốc độ viết, chữ có bám dòng không, em có hay kêu mỏi tay không.",
        "Nếu các dấu hiệu vẫn còn, đưa em gặp chuyên gia để được đánh giá, ví dụ chuyên viên tâm lý học đường, chuyên viên hoạt động trị liệu hoặc bác sĩ nhi khoa phát triển.",
      ],
      titleCls: "text-accent-2",
    };
  }
  if (prediction === 0) {
    return {
      title: "Chưa thấy dấu hiệu đáng lo",
      summary: "Ở lần kiểm tra này, cách viết của em chưa cho thấy dấu hiệu khó viết rõ rệt.",
      steps: [
        "Tiếp tục cho em viết đều đặn mỗi ngày.",
        "Nếu em vẫn gặp khó khăn kéo dài, như viết rất chậm, chữ khó đọc hay hay mỏi tay, hãy kiểm tra lại sau vài tuần hoặc trao đổi với giáo viên.",
        "Một lần kiểm tra không phát hiện được mọi trường hợp. Những gì thầy cô và gia đình quan sát hằng ngày vẫn quan trọng nhất.",
      ],
      titleCls: "text-green",
    };
  }
  return {
    title: "Chưa đủ căn cứ để đưa ra kết quả",
    summary:
      "Lần kiểm tra này chưa có đủ dữ liệu để nói điều gì về cách viết của em. Điều đó không cho thấy em tốt hay không tốt, chỉ là kết quả chưa dùng được.",
    steps: [
      "Quay lại video với bàn tay em hiện rõ trong khung hình, đủ sáng, dài khoảng 15 đến 30 giây.",
      "Xem lại phần cách quay video trong trang Hướng dẫn, rồi kiểm tra lại.",
      "Nếu vẫn lo lắng về việc viết của em, hãy trao đổi với giáo viên hoặc chuyên gia mà không cần chờ kết quả này.",
    ],
    titleCls: "text-text",
  };
}

// The printable result slip for one screening session.
export default function ResultSlip({ data }: { data: SessionDetail }) {
  const modelA = data.model_a;
  const modelB = data.model_b;
  const confidence = assessConfidence(data);
  const hasGrounds = confidence.level !== "insufficient";
  const verdict = verdictFor(hasGrounds ? data.ensemble?.prediction : null);

  // The result slip: the one raised element on the page, a sheet lying on the desk.
  return (
    <article className="mt-5 overflow-hidden rounded-sheet border border-border bg-surface shadow-[0_1px_2px_rgba(42,34,56,0.06),0_8px_24px_rgba(42,34,56,0.08)] print:shadow-none">
      <header className="o-li border-b border-border py-5 pl-14 pr-5 sm:pl-16">
        {/* Text on the ruled strip uses the main ink colour: muted grey drops below 4.5:1 where it crosses a strong rule. */}
        <p className="text-sm font-semibold text-text">Phiếu kết quả sàng lọc</p>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-text">Mã học sinh: {data.patient_id}</h1>
        <p className="mt-1 text-[15px] text-text">Ngày kiểm tra: {formatDate(data.created_at)}</p>
      </header>

      <div className="px-5 py-7 sm:px-8">
        <h2 className={`font-serif text-[1.9rem] font-semibold leading-tight ${verdict.titleCls}`}>{verdict.title}</h2>
        <p className="mt-3 text-lg leading-8 text-text">{verdict.summary}</p>

        <ConfidenceBlock confidence={confidence} />

        <h3 className="mt-8 text-lg font-semibold text-text">Nên làm gì tiếp theo</h3>
        <ol className="mt-3 list-decimal space-y-3 pl-6 text-base leading-7 text-text marker:font-semibold marker:text-accent">
          {verdict.steps.map((step) => (
            <li key={step} className="pl-1">
              {step}
            </li>
          ))}
        </ol>
        {hasGrounds && data.ensemble?.prediction === 1 && (
          <p className="mt-4 text-base leading-7 text-muted">
            Khó viết không liên quan đến trí thông minh. Phát hiện sớm giúp em được hỗ trợ kịp thời.
          </p>
        )}

        {hasGrounds && (
          <>
          <h3 className="mt-8 text-lg font-semibold text-text">Kết quả từng phần</h3>
          <dl className="mt-2 border-b border-rule">
            <PartRow
              title="Bàn tay lúc viết"
              lookedAt="Tốc độ và độ mượt của nét, những lần dừng bút và độ run của bàn tay."
              available={modelA?.available ?? false}
              prediction={modelA?.prediction ?? null}
              unavailableText="Không có dữ liệu chuyển động tay."
            />
            <PartRow
              title="Trang vở"
              lookedAt="Hình dạng chữ, độ đậm của nét và chữ có bám dòng hay không."
              available={modelB?.available ?? false}
              prediction={modelB?.prediction ?? null}
              unavailableText="Lần này không có ảnh trang vở. Lần sau thêm ảnh để kết quả đầy đủ hơn."
            />
          </dl>
          </>
        )}

        <p className="mt-8 text-[15px] leading-7 text-muted">
          Phiếu này chỉ là gợi ý sàng lọc, không phải chẩn đoán. Chỉ chuyên gia mới xác định được em có bị khó viết hay
          không. Hãy dùng phiếu làm cơ sở để gia đình, nhà trường và chuyên gia trao đổi với nhau.
        </p>

        <div className="print:hidden">
          <DetailsSection title="Chi tiết kỹ thuật">
            <p className="font-semibold text-text">Bàn tay lúc viết</p>
            <p className="mt-1">MediaPipe Hands (21 điểm trên bàn tay) và Random Forest, 18 đặc trưng vận động.</p>
            {modelA?.score != null && <p className="mt-1">Điểm của mô hình: {(modelA.score * 100).toFixed(1)}% (ngưỡng 50%)</p>}
            {modelA?.quality && (
              <div className="mt-2">
                <StatusCard quality={modelA.quality} />
              </div>
            )}
            {modelA?.features && Object.keys(modelA.features).length > 0 && (
              <div className="mt-3">
                <FeatureGroups features={modelA.features} />
              </div>
            )}
            <p className="mt-5 font-semibold text-text">Trang vở</p>
            {modelB?.available ? (
              <>
                <p className="mt-1">ResNet50 và MLP (ONNX Runtime), kèm 2 đặc trưng nét chữ.</p>
                {modelB.score != null && <p className="mt-1">Điểm của mô hình: {(modelB.score * 100).toFixed(1)}% (ngưỡng 50%)</p>}
                {modelB.handcrafted && (
                  <div className="mt-3">
                    <FeatureGroups
                      features={{
                        ink_thickness_mean: modelB.handcrafted.ink_thickness_mean,
                        baseline_deviation: modelB.handcrafted.baseline_deviation,
                      }}
                    />
                  </div>
                )}
              </>
            ) : (
              <p className="mt-1">Không có ảnh.</p>
            )}
            {data.ensemble?.method && <p className="mt-5">Cách kết hợp hai phần: {data.ensemble.method}</p>}
          </DetailsSection>
        </div>
      </div>
    </article>
  );
}
