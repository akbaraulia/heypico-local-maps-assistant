"use client";

import React, { useEffect, useRef, useState } from "react";
import { importLibrary, setOptions } from "@googlemaps/js-api-loader";
import { Place } from "@/types/place";
import {
  DEFAULT_MAP_CENTER,
  DEFAULT_MAP_ZOOM,
  FOCUSED_MAP_ZOOM,
  GOOGLE_MAPS_API_KEY,
} from "@/lib/constants";
import { MapFallback } from "./MapFallback";
import { SelectedPlaceOverlay } from "./SelectedPlaceOverlay";

interface PlacesMapProps {
  places: Place[];
  selectedPlaceId: string | null;
  onSelectPlace: (placeId: string | null) => void;
}

export function PlacesMap({
  places,
  selectedPlaceId,
  onSelectPlace,
}: PlacesMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<Map<string, google.maps.Marker>>(new Map());

  const [loadError, setLoadError] = useState<string | null>(
    !GOOGLE_MAPS_API_KEY
      ? "Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to display the interactive map."
      : null
  );
  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  // Initialize Map API
  useEffect(() => {
    if (!GOOGLE_MAPS_API_KEY) return;

    setOptions({
      key: GOOGLE_MAPS_API_KEY,
      v: "weekly",
    });

    Promise.all([importLibrary("maps"), importLibrary("places")])
      .then(() => {
        if (!mapRef.current || googleMapRef.current) return;

        const map = new google.maps.Map(mapRef.current, {
          center: DEFAULT_MAP_CENTER,
          zoom: DEFAULT_MAP_ZOOM,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
          zoomControl: true,
          styles: [
            {
              featureType: "poi",
              elementType: "labels",
              stylers: [{ visibility: "off" }],
            },
          ],
        });

        googleMapRef.current = map;
        setIsLoaded(true);
      })
      .catch((err) => {
        console.error("Failed to load Google Maps API", err);
        setLoadError(
          "Failed to load Google Maps JavaScript API. Please check your API key and network."
        );
      });
  }, []);

  // Sync Markers with Places
  useEffect(() => {
    const map = googleMapRef.current;
    if (!isLoaded || !map) return;

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current.clear();

    const validPlaces = places.filter(
      (p) =>
        typeof p.lat === "number" &&
        typeof p.lng === "number" &&
        !Number.isNaN(p.lat) &&
        !Number.isNaN(p.lng)
    );

    if (validPlaces.length === 0) {
      map.setCenter(DEFAULT_MAP_CENTER);
      map.setZoom(DEFAULT_MAP_ZOOM);
      return;
    }

    const bounds = new google.maps.LatLngBounds();

    validPlaces.forEach((place, index) => {
      const position = { lat: place.lat, lng: place.lng };
      bounds.extend(position);

      const isSelected = place.place_id === selectedPlaceId;

      const marker = new google.maps.Marker({
        position,
        map,
        title: `Select ${place.name}`,
        label: {
          text: String(index + 1),
          color: "#ffffff",
          fontWeight: "bold",
          fontSize: "12px",
        },
        icon: isSelected
          ? {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 16,
              fillColor: "#2563eb",
              fillOpacity: 1,
              strokeColor: "#ffffff",
              strokeWeight: 3,
            }
          : {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 13,
              fillColor: "#4b5563",
              fillOpacity: 0.9,
              strokeColor: "#ffffff",
              strokeWeight: 2,
            },
        zIndex: isSelected ? 1000 : index + 1,
      });

      marker.addListener("click", () => {
        onSelectPlace(place.place_id);
      });

      markersRef.current.set(place.place_id, marker);
    });

    if (validPlaces.length === 1) {
      map.setCenter({ lat: validPlaces[0].lat, lng: validPlaces[0].lng });
      map.setZoom(FOCUSED_MAP_ZOOM);
    } else {
      map.fitBounds(bounds);

      const listener = google.maps.event.addListenerOnce(map, "idle", () => {
        if (map.getZoom() && (map.getZoom() as number) > 16) {
          map.setZoom(16);
        }
      });

      return () => {
        google.maps.event.removeListener(listener);
      };
    }
  }, [isLoaded, places, selectedPlaceId, onSelectPlace]);

  // Handle Selected Place marker highlight & pan
  useEffect(() => {
    const map = googleMapRef.current;
    if (!isLoaded || !map) return;

    markersRef.current.forEach((marker, placeId) => {
      const isSelected = placeId === selectedPlaceId;
      marker.setIcon(
        isSelected
          ? {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 16,
              fillColor: "#2563eb",
              fillOpacity: 1,
              strokeColor: "#ffffff",
              strokeWeight: 3,
            }
          : {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 13,
              fillColor: "#4b5563",
              fillOpacity: 0.9,
              strokeColor: "#ffffff",
              strokeWeight: 2,
            }
      );
      marker.setZIndex(isSelected ? 1000 : 1);
    });

    if (selectedPlaceId) {
      const place = places.find((p) => p.place_id === selectedPlaceId);
      if (place) {
        map.panTo({ lat: place.lat, lng: place.lng });
        if ((map.getZoom() as number) < 14) {
          map.setZoom(FOCUSED_MAP_ZOOM);
        }
      }
    }
  }, [isLoaded, selectedPlaceId, places]);

  if (!GOOGLE_MAPS_API_KEY || loadError) {
    return <MapFallback message={loadError || undefined} />;
  }

  const selectedPlace = places.find((p) => p.place_id === selectedPlaceId);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-100 shadow-2xs dark:border-zinc-800 dark:bg-zinc-900">
      <div ref={mapRef} className="h-full w-full min-h-[350px]" />
      {selectedPlace && (
        <SelectedPlaceOverlay
          place={selectedPlace}
          onClose={() => onSelectPlace(null)}
        />
      )}
    </div>
  );
}
