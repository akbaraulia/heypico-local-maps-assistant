export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const GOOGLE_MAPS_EMBED_API_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_MAPS_EMBED_API_KEY ||
  process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ||
  "";

export const GOOGLE_MAPS_API_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ||
  process.env.NEXT_PUBLIC_GOOGLE_MAPS_EMBED_API_KEY ||
  "";

export const EXAMPLE_QUERIES = [
  "Sundanese restaurants in Bogor",
  "Coffee shops near Sudirman Jakarta",
  "Hospitals near Bandung Station",
  "Hotels in Sentul",
  "ATM BCA near Grand Indonesia",
] as const;

export const DEFAULT_MAP_CENTER = {
  lat: -6.200000,
  lng: 106.816666,
};

export const DEFAULT_MAP_ZOOM = 6;
export const FOCUSED_MAP_ZOOM = 15;
