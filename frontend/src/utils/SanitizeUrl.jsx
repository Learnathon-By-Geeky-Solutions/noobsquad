/**
 * 🔐 Securely sanitizes URLs by blocking potentially malicious schemes.
 * Blocks: javascript:, data:, vbscript:, and ensures proper URL format.
 */
export const sanitizeUrl = (url) => {
  // Return default if URL is invalid or not a string
  if (!url || typeof url !== 'string') return '/default-avatar.png';

  // Decode the URL fully, trim whitespace, and normalize to lowercase
  let decodedUrl = url;
  try {
    // Handle multiple layers of encoding by repeatedly decoding until no changes occur
    while (decodedUrl !== decodeURIComponent(decodedUrl)) {
      decodedUrl = decodeURIComponent(decodedUrl);
    }
  } catch (e) {
    // If decoding fails, return the default
    return '/default-avatar.png';
  }

  // Normalize the URL
  decodedUrl = decodedUrl.trim().toLowerCase();

  // Block malicious schemes (javascript:, data:, vbscript:)
  // Use a regex to catch variations and ensure we match the scheme properly
  if (
    decodedUrl.match(/^(javascript|data|vbscript):/i) || // Case-insensitive match for schemes
    decodedUrl.includes('javascript:') || // Catch any occurrence of javascript: in the string
    decodedUrl.includes('data:') || // Catch any occurrence of data: in the string
    decodedUrl.includes('vbscript:') // Catch any occurrence of vbscript: in the string
  ) {
    return '/default-avatar.png';
  }

  // Ensure valid http(s) URL format using a stricter regex
  const urlPattern = /^https?:\/\/([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
  if (!urlPattern.test(decodedUrl)) {
    return '/default-avatar.png';
  }

  // If all checks pass, return the original URL (not the decoded one, to preserve the original format)
  return url;
};