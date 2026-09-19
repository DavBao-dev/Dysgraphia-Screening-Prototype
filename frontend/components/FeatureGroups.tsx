const GROUPS: Record<string, string[]> = {
  "Cơ bản": [
    "num_frames", "fps",
  ],
  "Chuyển động": [
    "speed_mean", "speed_max", "speed_std",
    "acceleration_mean", "acceleration_max", "acceleration_std",
    "jerk_mean", "jerk_max", "jerk_std",
    "mean_speed", "std_speed",
    "mean_jerk", "max_jerk", "normalized_jerk",
    "nvc_per_second", "in_air_pause_ratio",
  ],
  "Run tay": [
    "tremor_peak_frequency_hz", "tremor_peak_amplitude",
    "spectral_entropy", "tremor_power_ratio",
  ],
  "Phối hợp": [
    "wrist_flexion_angle_mean", "wrist_flexion_angle_std",
    "pinch_distance_std", "pinch_distance_mean",
    "pincer_correlation", "wrist_drift_rate",
  ],
  "Chữ viết": [
    "ink_thickness_mean", "baseline_deviation",
  ],
};

const LABELS: Record<string, string> = {
  num_frames: "Số frame",
  fps: "Tần suất (FPS)",
  speed_mean: "Tốc độ trung bình",
  speed_max: "Tốc độ tối đa",
  speed_std: "Độ lệch chuẩn tốc độ",
  acceleration_mean: "Gia tốc trung bình",
  acceleration_max: "Gia tốc tối đa",
  acceleration_std: "Độ lệch chuẩn gia tốc",
  jerk_mean: "Jerk trung bình",
  jerk_max: "Jerk tối đa",
  jerk_std: "Độ lệch chuẩn jerk",
  mean_speed: "Tốc độ trung bình",
  std_speed: "Độ lệch chuẩn tốc độ",
  mean_jerk: "Jerk trung bình",
  max_jerk: "Jerk tối đa",
  normalized_jerk: "Jerk chuẩn hóa",
  nvc_per_second: "Số lần đổi vận tốc/giây",
  in_air_pause_ratio: "Tỷ lệ tạm dừng trên không",
  tremor_peak_frequency_hz: "Tần số đỉnh run (Hz)",
  tremor_peak_amplitude: "Biên độ đỉnh run",
  spectral_entropy: "Entropy phổ",
  tremor_power_ratio: "Tỷ lệ công suất run",
  wrist_flexion_angle_mean: "Góc gập cổ tay trung bình",
  wrist_flexion_angle_std: "Độ lệch chuẩn góc gập cổ tay",
  pinch_distance_std: "Độ lệch chuẩn khoảng cách pinch",
  pinch_distance_mean: "Khoảng cách pinch trung bình",
  pincer_correlation: "Tương quan pincer",
  wrist_drift_rate: "Tốc độ trôi cổ tay",
  ink_thickness_mean: "Độ dày mực trung bình",
  baseline_deviation: "Độ lệch đường cơ sở",
};

function formatValue(v: number | null | undefined): string {
  if (v == null) return "—";
  if (typeof v !== "number" || !Number.isFinite(v)) return "—";
  return v.toFixed(3);
}

interface FeatureGroupsProps {
  features: Record<string, number | null> | null;
  title?: string;
}

export default function FeatureGroups({ features, title }: FeatureGroupsProps) {
  if (!features || Object.keys(features).length === 0) {
    return (
      <p className="py-2 text-sm text-muted">Không có dữ liệu đặc trưng.</p>
    );
  }

  const unknownKeys: string[] = [];
  const groupedEntries = Object.entries(GROUPS).map(([group, keys]) => {
    const rows = keys
      .filter((k) => k in features)
      .map((k) => ({ key: k, label: LABELS[k] ?? k, value: features[k] }));
    return { group, rows };
  });

  for (const k of Object.keys(features)) {
    const inGroup = Object.values(GROUPS).some((keys) => keys.includes(k));
    if (!inGroup) unknownKeys.push(k);
  }

  if (unknownKeys.length > 0) {
    groupedEntries.push({
      group: "Khác",
      rows: unknownKeys.map((k) => ({
        key: k,
        label: LABELS[k] ?? k,
        value: features[k],
      })),
    });
  }

  return (
    <div className="space-y-4">
      {title && (
        <h4 className="text-sm font-semibold text-text">{title}</h4>
      )}
      {groupedEntries.map(({ group, rows }) =>
        rows.length === 0 ? null : (
          <div key={group}>
            <h5 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
              {group}
            </h5>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              {rows.map(({ key, label, value }) => (
                <div key={key} className="contents">
                  <dt className="text-muted" title={key}>
                    {label}
                  </dt>
                  <dd className="text-right font-mono text-text">
                    {formatValue(value)}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        )
      )}
    </div>
  );
}
