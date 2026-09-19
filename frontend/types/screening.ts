export interface Quality { valid: boolean; fps?: number | null; frames?: number | null; duration?: number | null; }
export interface ModelAResult { available: boolean; prediction: number | null; score: number | null; status: string | null; quality: Quality | null; features: Record<string, number> | null; }
export interface ModelBResult { available: boolean; prediction: number | null; score: number | null; handcrafted?: { ink_thickness_mean: number; baseline_deviation: number }; }
export interface EnsembleResult { prediction: number; method: string; }
export interface ScreeningResponse { session_id: string | null; patient_id: string; model_a: ModelAResult; model_b: ModelBResult; ensemble: EnsembleResult; disclaimer: string; }
export interface SessionDetail extends ScreeningResponse { created_at: string; }
export interface HistoryRow { predicted_at: string; session_id: string; patient_id: string; model_a_output: number | null; model_b_output: number | null; final_output: number | null; ensemble_method: string; }
export interface HealthResponse { status: string; models: { model_a: boolean; model_b: boolean }; }