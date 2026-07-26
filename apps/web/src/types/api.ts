import { Place } from "./place";
import { ChatRequest, ChatResponse } from "./chat";

export type { ChatRequest, ChatResponse };

export interface PlaceSearchResponse {
  query: string;
  count: number;
  places: Place[];
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
  detail?: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}
