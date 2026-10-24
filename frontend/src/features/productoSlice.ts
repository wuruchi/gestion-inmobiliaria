import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { Status, TipoProduct } from "./common";
import {
    fetchDistritos,
    fetchMapCounters,
    fetchMunicipios,
    fetchProducto,
    fetchProvincias,
    fetchAllInmuebles,
    fetchTemporalInmuebles,
    fetchHabitualInmuebles,
    fetchVentaInmuebles,
    fetchNuevasPropiedades,
} from "./functions";
import {
    ListProducto,
    ListProductoResponse,
    Producto,
    Provincia,
    Municipio,
    Distrito,
} from "./interfaces";

const parseToInt = (value: string | number) => {
    if (typeof value === "string") {
        return parseInt(value);
    }
    return value;
};

export interface InmuebleState {
    currentProductoId: number | null;
    inmuebleInfo: Producto | null;
    inmuebles: ListProducto[] | null;
    nuevasPropiedades: ListProducto[] | null;
    provincias: Provincia[] | null;
    selectedProvincia: number | null;
    municipios: Municipio[] | null;
    selectedMunicipio: number | null;
    distritos: Distrito[] | null;
    selectedDistrito: number | null;
    currentInmuebleType: TipoProduct;
    status: Status;
    statusNuevas: Status;
    pageCounters: Record<TipoProduct, number>;
    pageTotals: Record<TipoProduct, number>;
    mapCounters: Record<string, number> | null;
    error: Error | null;
}

export const initialState: InmuebleState = {
    currentProductoId: null,
    inmuebleInfo: null,
    inmuebles: null,
    nuevasPropiedades: null,
    provincias: null,
    selectedProvincia: null,
    municipios: null,
    selectedMunicipio: null,
    distritos: null,
    selectedDistrito: null,
    currentInmuebleType: TipoProduct.Todos,
    status: "idle",
    statusNuevas: "idle",
    pageCounters: {
        [TipoProduct.Todos]: 0,
        [TipoProduct.Temporales]: 0,
        [TipoProduct.Habituales]: 0,
        [TipoProduct.Ventas]: 0,
    },
    pageTotals: {
        [TipoProduct.Todos]: 0,
        [TipoProduct.Temporales]: 0,
        [TipoProduct.Habituales]: 0,
        [TipoProduct.Ventas]: 0,
    },
    mapCounters: null,
    error: null,
};

export const moduloSlice = createSlice({
    name: "inmueble",
    initialState: initialState,
    reducers: {
        setInmuebleType: (state, action) => {
            state.currentInmuebleType = action.payload as TipoProduct;
        },
        clearInmuebles: (state) => {
            state.inmuebles = null;
            state.status = "idle";
        },
        clearInmuebleInfo: (state) => {
            state.inmuebleInfo = null;
        },
        setCurrentProvincia: (state, action) => {
            state.selectedProvincia = action.payload;
            state.selectedMunicipio = null;
            state.selectedDistrito = null;
        },
        setCurrentMunicipio: (state, action) => {
            console.log(action.payload);
            state.selectedMunicipio = action.payload;
            state.selectedDistrito = null;
        },
        setCurrentDistrito: (state, action) => {
            state.selectedDistrito = action.payload;
        },
    },
    extraReducers(builder) {
        builder
            .addCase(fetchMapCounters.pending, (state) => {
                // No need for now
            })
            .addCase(
                fetchMapCounters.fulfilled,
                (state, action: PayloadAction<Record<string, number>>) => {
                    state.status = "succeeded";
                    state.mapCounters = action.payload;
                }
            )
            .addCase(fetchMapCounters.rejected, (state, action) => {
                state.status = "failed";
                state.mapCounters = {};
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchProvincias.pending, (state) => {
                // No need for now
            })
            .addCase(
                fetchProvincias.fulfilled,
                (state, action: PayloadAction<Provincia[]>) => {
                    state.status = "succeeded";
                    state.provincias = action.payload;
                    state.selectedProvincia =
                        action.payload.length > 0
                            ? action.payload[0]._id
                            : null;
                }
            )
            .addCase(fetchProvincias.rejected, (state, action) => {
                state.status = "failed";
                state.provincias = [];
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchMunicipios.pending, (state) => {
                // No need for now
            })
            .addCase(
                fetchMunicipios.fulfilled,
                (state, action: PayloadAction<Municipio[]>) => {
                    state.status = "succeeded";
                    state.municipios = action.payload;
                    state.selectedMunicipio = null;
                }
            )
            .addCase(fetchMunicipios.rejected, (state, action) => {
                state.status = "failed";
                state.municipios = [];
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchDistritos.pending, (state) => {
                // No need for now
            })
            .addCase(fetchDistritos.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.distritos = action.payload;
                state.selectedDistrito = null;
            })
            .addCase(fetchDistritos.rejected, (state, action) => {
                state.status = "failed";
                state.distritos = [];
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchProducto.pending, (state) => {
                state.status = "loading";
            })
            .addCase(
                fetchProducto.fulfilled,
                (state, action: PayloadAction<Producto>) => {
                    state.status = "succeeded";
                    state.inmuebleInfo = action.payload;
                    state.currentProductoId = action.payload._id;
                }
            )
            .addCase(fetchProducto.rejected, (state, action) => {
                state.status = "failed";
                state.inmuebleInfo = null;
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchAllInmuebles.pending, (state) => {
                state.status = "loading";
            })
            .addCase(
                fetchAllInmuebles.fulfilled,
                (state, action: PayloadAction<ListProductoResponse>) => {
                    state.status = "succeeded";
                    state.inmuebles = action.payload.inmuebles;
                    state.currentInmuebleType = TipoProduct.Todos;
                }
            )
            .addCase(fetchAllInmuebles.rejected, (state, action) => {
                state.status = "failed";
                state.inmuebles = [];
                state.currentInmuebleType = TipoProduct.Todos;
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchTemporalInmuebles.pending, (state) => {
                state.status = "loading";
                state.currentInmuebleType = TipoProduct.Temporales;
            })
            .addCase(
                fetchTemporalInmuebles.fulfilled,
                (state, action: PayloadAction<ListProductoResponse>) => {
                    state.status = "succeeded";
                    state.inmuebles = action.payload.inmuebles;
                    state.pageCounters[TipoProduct.Temporales] = parseToInt(
                        action.payload.page
                    );
                    state.pageTotals[TipoProduct.Temporales] = parseToInt(
                        action.payload.pages
                    );
                }
            )
            .addCase(fetchTemporalInmuebles.rejected, (state, action) => {
                state.status = "failed";
                state.inmuebles = [];
                state.pageCounters[TipoProduct.Temporales] = 0;
                state.pageTotals[TipoProduct.Temporales] = 0;
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchHabitualInmuebles.pending, (state) => {
                state.status = "loading";
                state.currentInmuebleType = TipoProduct.Habituales;
            })
            .addCase(
                fetchHabitualInmuebles.fulfilled,
                (state, action: PayloadAction<ListProductoResponse>) => {
                    state.status = "succeeded";
                    state.inmuebles = action.payload.inmuebles;
                    state.pageCounters[TipoProduct.Habituales] = parseToInt(
                        action.payload.page
                    );
                    state.pageTotals[TipoProduct.Habituales] = parseToInt(
                        action.payload.pages
                    );
                }
            )
            .addCase(fetchHabitualInmuebles.rejected, (state, action) => {
                state.status = "failed";
                state.inmuebles = [];
                state.pageCounters[TipoProduct.Habituales] = 0;
                state.pageTotals[TipoProduct.Habituales] = 0;
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchVentaInmuebles.pending, (state) => {
                state.status = "loading";
                state.currentInmuebleType = TipoProduct.Ventas;
            })
            .addCase(
                fetchVentaInmuebles.fulfilled,
                (state, action: PayloadAction<ListProductoResponse>) => {
                    state.status = "succeeded";
                    state.inmuebles = action.payload.inmuebles;
                    state.pageCounters[TipoProduct.Ventas] = parseToInt(
                        action.payload.page
                    );
                    state.pageTotals[TipoProduct.Ventas] = parseToInt(
                        action.payload.pages
                    );
                }
            )
            .addCase(fetchVentaInmuebles.rejected, (state, action) => {
                state.status = "failed";
                state.inmuebles = [];
                state.pageCounters[TipoProduct.Ventas] = 0;
                state.pageTotals[TipoProduct.Ventas] = 0;
                state.error = action.error as Error;
            });
        builder
            .addCase(fetchNuevasPropiedades.pending, (state) => {
                state.statusNuevas = "loading";
            })
            .addCase(
                fetchNuevasPropiedades.fulfilled,
                (state, action: PayloadAction<ListProductoResponse>) => {
                    state.statusNuevas = "succeeded";
                    state.nuevasPropiedades = action.payload.inmuebles.slice(
                        0,
                        Math.min(action.payload.inmuebles.length, 3)
                    );
                }
            )
            .addCase(fetchNuevasPropiedades.rejected, (state, action) => {
                state.statusNuevas = "failed";
                state.nuevasPropiedades = [];
                state.error = action.error as Error;
            });
    },
});

export const {
    setInmuebleType,
    clearInmuebles,
    clearInmuebleInfo,
    setCurrentProvincia,
    setCurrentMunicipio,
    setCurrentDistrito,
} = moduloSlice.actions;
export default moduloSlice.reducer;
