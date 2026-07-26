"use client";

import { useCallback, useState } from "react";

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface UseBrowserLocationReturn {
  isLoading: boolean;
  error: string | null;
  coords: Coordinates | null;
  requestLocation: () => Promise<Coordinates>;
  clearLocationError: () => void;
}

export function useBrowserLocation(): UseBrowserLocationReturn {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [coords, setCoords] = useState<Coordinates | null>(null);

  const clearLocationError = useCallback(() => {
    setError(null);
  }, []);

  const requestLocation = useCallback((): Promise<Coordinates> => {
    setIsLoading(true);
    setError(null);

    return new Promise<Coordinates>((resolve, reject) => {
      if (typeof window === "undefined" || !("geolocation" in navigator)) {
        const errMessage = "Current location is unavailable in this browser.";
        setError(errMessage);
        setIsLoading(false);
        return reject(new Error(errMessage));
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location: Coordinates = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          setCoords(location);
          setIsLoading(false);
          setError(null);
          resolve(location);
        },
        (geolocationError) => {
          setIsLoading(false);
          let errMessage = "Current location is unavailable in this browser.";

          if (geolocationError.code === geolocationError.PERMISSION_DENIED) {
            errMessage =
              "Location access was not granted. Enter a city, area, or landmark instead.";
          }

          setError(errMessage);
          reject(new Error(errMessage));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000,
        }
      );
    });
  }, []);

  return {
    isLoading,
    error,
    coords,
    requestLocation,
    clearLocationError,
  };
}
