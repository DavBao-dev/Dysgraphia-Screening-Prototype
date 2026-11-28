export interface DataPolicy {
  version: string;
  title: string;
  policy_hash: string;
  ready: boolean;
  notice: string;
  sections: { title: string; text: string }[];
}
export interface ConsentReceipt { token: string; receipt_id: string; accepted_at: string }
export async function loadPolicy(): Promise<DataPolicy> {
  const response = await fetch("/api/consent/policy", { cache: "no-store" });
  if (!response.ok) throw new Error("Chưa tải được điều khoản. Vui lòng thử lại.");
  return response.json();
}
