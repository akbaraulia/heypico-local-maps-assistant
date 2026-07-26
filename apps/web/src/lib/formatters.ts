export function formatRating(rating: number | null): string {
  if (rating === null || rating === undefined || Number.isNaN(rating)) {
    return "N/A";
  }
  return rating.toFixed(1);
}

export function formatReviewCount(count: number | null): string {
  if (count === null || count === undefined || count < 0) {
    return "No reviews";
  }
  const formatted = new Intl.NumberFormat("en-US").format(count);
  return `${formatted} ${count === 1 ? "review" : "reviews"}`;
}

export interface OpenStatusInfo {
  text: string;
  variant: "open" | "closed" | "unknown";
}

export function formatOpenStatus(openNow: boolean | null): OpenStatusInfo {
  if (openNow === true) {
    return { text: "Open now", variant: "open" };
  }
  if (openNow === false) {
    return { text: "Closed", variant: "closed" };
  }
  return { text: "Hours unavailable", variant: "unknown" };
}

export function formatPrimaryType(type: string | null): string {
  if (!type || !type.trim()) {
    return "Place";
  }
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}
