import React from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

interface Props {
  latitude: number;
  longitude: number;
  zoom: number;
  height: string;
}

const API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "";

const Map: React.FC<Props> = ({ latitude, longitude, zoom, height }) => {
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: API_KEY,
  });

  const containerStyle = {
    height: height,
    width: "100%",
  };

  const center = {
    lat: latitude,
    lng: longitude,
  };

  const [map, setMap] = React.useState<google.maps.Map | null>(null);

  const onLoad = React.useCallback(function callback(map: google.maps.Map) {
    // const center = {
    //   lat: latitude,
    //   lng: longitude,
    // };
    // const bounds = new window.google.maps.LatLngBounds(center);
    // const bounds = new window.google.maps.LatLngBounds();
    // map.fitBounds(bounds);
    setMap(map);
  }, []);

  const onUnmount = React.useCallback(function callback(map: google.maps.Map) {
    setMap(null);
  }, []);

  return (
    <div style={containerStyle}>
      {isLoaded ? (
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={center}
          zoom={zoom}
          onLoad={onLoad}
          onUnmount={onUnmount}
        >
          <Marker position={center} />
        </GoogleMap>
      ) : null}
    </div>
  );
};

export default React.memo(Map);
