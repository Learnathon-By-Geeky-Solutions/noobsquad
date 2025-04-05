/**
 * 🔐 Securely sanitizes URLs by blocking potentially malicious schemes.
 * Blocks: javascript:, data:, vbscript:
 */
export const sanitizeUrl = (url) => {
    if (!url || typeof url !== 'string') return '/default-avatar.png';
  
    const decodedUrl = decodeURIComponent(url).trim().toLowerCase();
  
    if (
      decodedUrl.startsWith('javascript:') ||
      decodedUrl.startsWith('data:') ||
      decodedUrl.startsWith('vbscript:')
    ) {
      return '/default-avatar.png'; // or "about:blank"
    }
  
    return url;
  };