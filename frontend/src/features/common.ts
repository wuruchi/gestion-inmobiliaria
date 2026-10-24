export enum TipoProduct {
    Ventas = "Ventas",
    Habituales = "Habituales",
    Temporales = "Temporales",
    Todos = "Todos",
}

export const ATB_MAIN = "#893364";
export const ATB_RED = "#9b0c05";
export const ATB_YELLOW = "#eabd00";
export const ATB_ORANGE = "#f77500";

// create a mapping from tipoInmueble to string
export const tipoInmuebleToLongName = new Map<TipoProduct, string>([
    [TipoProduct.Ventas, "Ventas"],
    [TipoProduct.Habituales, "Alquiler Larga Estancia"],
    [TipoProduct.Temporales, "Alquiler Temporal"],
    [TipoProduct.Todos, "Todos"],
]);

export const tipoInmuebleToSubtitle = new Map<TipoProduct, string>([
    [TipoProduct.Ventas, "Comprar para uso propio o inversión."],
    [TipoProduct.Habituales, "Alquilar un piso por años."],
    [TipoProduct.Temporales, "Alquilar un piso por meses."],
    [TipoProduct.Todos, "Todos"],
]);

export const tipoInmuebleToColor = new Map<TipoProduct, string>([
    [TipoProduct.Ventas, ATB_RED],
    [TipoProduct.Habituales, ATB_YELLOW],
    [TipoProduct.Temporales, ATB_ORANGE],
    [TipoProduct.Todos, ATB_MAIN],
]);

export const lastPartToTipoProduct: Record<string, TipoProduct> = {
    "alquiler-temporal-barcelona": TipoProduct.Temporales,
    "alquiler-larga-estancia-barcelona": TipoProduct.Habituales,
    "venta-de-inmuebles": TipoProduct.Ventas,
    "": TipoProduct.Todos,
};

export const getTipoProductFromLastPart = (lastPart: string): TipoProduct => {
    return lastPartToTipoProduct[lastPart] || TipoProduct.Todos;
};

export type Status = "idle" | "loading" | "succeeded" | "failed";
