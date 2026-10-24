import { configureStore } from "@reduxjs/toolkit";
// import headerReducer from "./features/header/headerSlice";
// import moduloReducer from "./features/modulo/moduloSlice";
import moduloReducer from "./features/productoSlice";

// export default configureStore({
//   reducer: {
//     inmueble: moduloReducer,
//     // header: headerReducer,
//   },
// });

// create the types for useSelector
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export const store = configureStore({
  reducer: {
    inmueble: moduloReducer,
    // header: headerReducer,
  },
});
