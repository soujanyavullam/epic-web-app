/**
 * Unicode-safe base64 encoding and decoding utilities
 * These functions properly handle UTF-8 characters that btoa/atob don't support
 */

/**
 * Encode a string to base64, safely handling Unicode characters
 * @param str - The string to encode
 * @returns Base64 encoded string
 */
export const encodeBase64 = (str: string): string => {
  try {
    // First encode to UTF-8, then to base64
    return btoa(unescape(encodeURIComponent(str)));
  } catch (error) {
    console.error('Error encoding to base64:', error);
    throw new Error('Failed to encode string to base64');
  }
};

/**
 * Decode a base64 string back to the original string, safely handling Unicode characters
 * @param base64 - The base64 encoded string
 * @returns Decoded string
 */
export const decodeBase64 = (base64: string): string => {
  try {
    // First decode from base64, then decode from UTF-8
    return decodeURIComponent(escape(atob(base64)));
  } catch (error) {
    console.error('Error decoding from base64:', error);
    throw new Error('Failed to decode string from base64');
  }
};

/**
 * Check if a string contains only ASCII characters
 * @param str - The string to check
 * @returns True if the string contains only ASCII characters
 */
export const isAsciiOnly = (str: string): boolean => {
  return /^[\x00-\x7F]*$/.test(str);
};

/**
 * Safely encode a string to base64, using the most appropriate method
 * @param str - The string to encode
 * @returns Base64 encoded string
 */
export const safeBase64Encode = (str: string): string => {
  if (isAsciiOnly(str)) {
    // If it's ASCII only, use the faster btoa
    return btoa(str);
  } else {
    // If it contains Unicode, use the safe encoding
    return encodeBase64(str);
  }
}; 