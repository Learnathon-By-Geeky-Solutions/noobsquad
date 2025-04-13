/**
 * 🔐 Securely sanitizes URLs by allowing only trusted schemes (http, https).
 * Rejects all other schemes to prevent execution of untrusted code.
 */
export const sanitizeUrl = (url) => {
  // Return default if URL is invalid or not a string
  if (!url || typeof url !== 'string') return '/default-avatar.png';

  // Trim whitespace from the URL
  const trimmedUrl = url.trim();

  // Use the URL API to parse the URL and extract the scheme (protocol)
  let parsedUrl;
  try {
    parsedUrl = new URL(trimmedUrl);
  } catch (e) {
    console.error('Malformed URL:', e);
    // If the URL is malformed, return the default
    return '/default-avatar.png';
  }

  // Whitelist: Allow only http and https schemes
  const allowedSchemes = ['http:', 'https:'];
  if (!allowedSchemes.includes(parsedUrl.protocol)) {
    return '/default-avatar.png';
  }

  // Ensure the URL has a valid hostname (not empty, not just localhost)
  const hostname = parsedUrl.hostname;
  if (!hostname || hostname === 'localhost' || !hostname.includes('.')) {
    return '/default-avatar.png';
  }

  // If all checks pass, return the original URL
  return trimmedUrl;
};