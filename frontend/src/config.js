// ============================================================
//  CHANGE THIS ONE URL when you get a new Cloudflare tunnel
// ============================================================
export const BACKEND_URL = 'https://YOUR-TUNNEL-URL.trycloudflare.com';
// ============================================================

export const API_BASE_URL = BACKEND_URL;
export const WS_BASE_URL = BACKEND_URL.replace('https://', 'wss://');
