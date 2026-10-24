export {};
declare global {
  namespace JSX {
    interface IntrinsicElements {
      "ion-icon": { name: string };
    }
  }

  interface Window {
    google: typeof google;
    initMap?: () => void;
  }
}
