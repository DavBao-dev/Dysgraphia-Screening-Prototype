/**
 * Minimum number of hand-detected frames accepted by the Model A API.
 * Keep in sync with MIN_MODEL_A_FRAMES in backend/config.py.
 */
export const MIN_LIVE_FRAMES = 5;

/**
 * Gioi han dung luong video. Giu dong bo voi MAX_VIDEO_SIZE_MB trong
 * backend/config.py; next.config.ts dat gioi han proxy cao hon mot chut de
 * backend tra ve 413 JSON ro rang thay vi proxy cat body giua duong.
 */
export const MAX_VIDEO_MB = 4096;
export const MAX_VIDEO_BYTES = MAX_VIDEO_MB * 1024 * 1024;
export const MAX_VIDEO_MSG = `Video quá lớn. Vui lòng chọn video nhỏ hơn ${MAX_VIDEO_MB} MB.`;
