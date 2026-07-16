// Ensure we have a consistent API base URL that falls back to localhost for local development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
