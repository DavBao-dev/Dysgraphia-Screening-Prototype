import type { HealthResponse, HistoryRow, ScreeningResponse, SessionDetail } from "@/types/screening";
import { MAX_VIDEO_MSG } from "@/lib/constants";

export type ApiError = Error & { status?: number };

const NETWORK_MSG = "Không thể kết nối tới máy chủ. Hãy kiểm tra backend đang chạy.";

async function j<T>(res: Promise<Response>): Promise<T> {
  let r: Response;
  try {
    r = await res;
  } catch {
    throw new Error(NETWORK_MSG);
  }
  if (!r.ok) {
    const body = await r.json().catch(() => null);
    if (body && typeof body.detail === "string") {
      const err: ApiError = new Error(body.detail);
      err.status = r.status;
      throw err;
    }
    if (r.status === 413) {
      const err: ApiError = new Error(MAX_VIDEO_MSG);
      err.status = r.status;
      throw err;
    }
    throw new Error(NETWORK_MSG);
  }
  return r.json() as Promise<T>;
}

export function runScreening(form: FormData): Promise<ScreeningResponse> {
  return j(fetch("/api/screening", { method: "POST", body: form }));
}
export function getHistory(): Promise<HistoryRow[]> {
  return j(fetch("/api/history"));
}
export function getSession(id: string): Promise<SessionDetail> {
  return j(fetch(`/api/history/${id}`));
}
export function getHealth(): Promise<HealthResponse> {
  return j(fetch("/api/health"));
}