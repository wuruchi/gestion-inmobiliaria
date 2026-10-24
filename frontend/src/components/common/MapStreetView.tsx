import React from "react";
import { GoogleMap, useJsApiLoader, Marker } from "@react-google-maps/api";

interface Props {
  latitude: number;
  longitude: number;
}

const API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "";

const MapStreetView: React.FC<Props> = ({ latitude, longitude }) => {
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: API_KEY,
  });

  const containerStyle = {
    height: "100%",
    width: "100%",
  };

  const center = {
    lat: latitude,
    lng: longitude,
  };

  const [map, setMap] = React.useState<google.maps.Map | null>(null);

  const onLoad = React.useCallback(
    function callback(map: google.maps.Map) {
      // const center = {
      //   lat: latitude,
      //   lng: longitude,
      // };
      // const bounds = new window.google.maps.LatLngBounds(center);
      // const bounds = new window.google.maps.LatLngBounds();
      // map.fitBounds(bounds);
      setMap(map);
    },
    [latitude, longitude]
  );

  const onUnmount = React.useCallback(function callback(map: google.maps.Map) {
    setMap(null);
  }, []);

  return (
    <div style={containerStyle}>
      {isLoaded ? (
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={center}
          zoom={19}
          onLoad={onLoad}
          onUnmount={onUnmount}
        >
          <Marker position={center} />
          {/* <StreetViewPanorama options={{ visible: true }} /> */}
        </GoogleMap>
      ) : null}
    </div>
  );
};

export default React.memo(MapStreetView);
