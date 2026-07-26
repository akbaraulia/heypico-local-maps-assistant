export interface Place {
  place_id: string;
  name: string;
  address: string | null;
  rating: number | null;
  user_rating_count: number | null;
  open_now: boolean | null;
  primary_type: string | null;
  price_level?: string | null;
  lat: number;
  lng: number;
  google_maps_url: string;
  directions_url: string;
}
