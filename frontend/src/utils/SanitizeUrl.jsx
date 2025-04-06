/**
 * 🔐 Securely sanitizes URLs by blocking potentially malicious schemes.
 * Blocks: javascript:, data:, vbscript:, and ensures proper URL format.
 */
export const sanitizeUrl = (url) => {
  if (!url || typeof url !== 'string') return '/default-avatar.png';

  const decodedUrl = decodeURIComponent(url).trim().toLowerCase();

  // Block malicious schemes
  if (
    decodedUrl.startsWith('javascript:') ||
    decodedUrl.startsWith('data:') ||
    decodedUrl.startsWith('vbscript:') ||
    !/^https?:\/\/[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}/.test(decodedUrl) // Ensure valid http(s) URL format
  ) {
    return '/default-avatar.png'; // or "about:blank"
  }

  return url;
};
