/* eslint-disable @typescript-eslint/no-explicit-any */
// Global declarations for the MediaPipe Hands 0.4 CDN scripts loaded by LiveCamera.
// camera_utils.js exposes `window.Camera`, hands.js exposes `window.Hands`.
interface Window {
  Hands: any;
  Camera: any;
}