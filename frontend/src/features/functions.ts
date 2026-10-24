import { createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";
import {
    ListProductoResponse,
    Producto,
    Provincia,
    Municipio,
    Distrito,
    DistritoCounter,
} from "./interfaces";

export interface SearchQueryParams {
    page?: number;
    maxPrecio?: number | null;
    nroHabitaciones?: number | null;
    provincia?: number | null;
    municipio?: number | null;
    distrito?: number | null;
    referencia?: string | null;
    fechaEntrada?: string | null;
}

// Set REACT_APP_API_URL at build time; "/api" works when the backend serves the build.
const getURL = () => process.env.REACT_APP_API_URL || `http://localhost:8000/api`;

export const fetchMapCounters = createAsyncThunk(
    `inmuebles/fetchMapCounters`,
    async (args: { distritos: number[]; modalidad: string }) => {
        const promises = args.distritos.map((distritoId) => {
            return axios.get<DistritoCounter>(
                `${getURL()}/inmuebles/modalidad/${args.modalidad.toLowerCase()}/distrito/${distritoId}/count/`
            );
        });
        const results = await Promise.all(promises);
        const counters: Record<string, number> = {};
        results.forEach((result) => {
            counters[result.data.distrito] = result.data.count;
        });
        return counters;
    }
);

export const fetchProvincias = createAsyncThunk(
    `inmuebles/fetchProvincias`,
    async () => {
        const { data } = await axios.get<Provincia[]>(`${getURL()}/provincias`);
        return data;
    }
);

export const fetchMunicipios = createAsyncThunk(
    `inmuebles/fetchMunicipios`,
    async (provinciaId: number) => {
        const { data } = await axios.get<Municipio[]>(
            `${getURL()}/provincias/${provinciaId}/municipios`
        );
        return data;
    }
);

export const fetchDistritos = createAsyncThunk(
    `inmuebles/fetchDistritos`,
    async (municipioId: number) => {
        const { data } = await axios.get<Distrito[]>(
            `${getURL()}/municipios/${municipioId}/distritos`
        );
        return data;
    }
);

const buildParams = (queryParams?: SearchQueryParams): URLSearchParams => {
    let params = new URLSearchParams();
    params.append("page", queryParams?.page?.toString() || "1");
    queryParams?.fechaEntrada &&
        params.append("fecha_entrada", queryParams.fechaEntrada.toString());
    queryParams?.nroHabitaciones &&
        params.append("habitaciones", queryParams.nroHabitaciones.toString());
    queryParams?.maxPrecio &&
        params.append("max_precio", queryParams.maxPrecio.toString());
    queryParams?.provincia &&
        params.append("provincia", queryParams.provincia.toString());
    queryParams?.municipio &&
        params.append("municipio", queryParams.municipio.toString());
    queryParams?.distrito &&
        params.append("distrito", queryParams.distrito.toString());
    queryParams?.referencia &&
        params.append("referencia", queryParams.referencia.toString());
    return params;
};

export const fetchProducto = createAsyncThunk(
    `inmuebles/fetchProducto`,
    async (productoId: number) => {
        const { data } = await axios.get<Producto>(
            `${getURL()}/inmuebles/${productoId}`
        );
        return data;
    }
);

export const fetchAllInmuebles = createAsyncThunk(
    `inmuebles/fetchAllInmuebles`,
    async (queryParams?: SearchQueryParams) => {
        const { data } = await axios.get<ListProductoResponse>(
            `${getURL()}/inmuebles`,
            {
                params: buildParams(queryParams),
            }
        );
        return data;
    }
);

export const fetchTemporalInmuebles = createAsyncThunk(
    `inmuebles/fetchTemporalInmuebles`,
    async (queryParams?: SearchQueryParams) => {
        const { data } = await axios.get<ListProductoResponse>(
            `${getURL()}/inmuebles/modalidad/temporales`,
            {
                params: buildParams(queryParams),
            }
        );
        return data;
    }
);

export const fetchHabitualInmuebles = createAsyncThunk(
    `inmuebles/fetchHabitualInmuebles`,
    async (queryParams?: SearchQueryParams) => {
        const { data } = await axios.get<ListProductoResponse>(
            `${getURL()}/inmuebles/modalidad/habituales`,
            {
                params: buildParams(queryParams),
            }
        );
        return data;
    }
);

export const fetchVentaInmuebles = createAsyncThunk(
    `inmuebles/fetchVentaInmuebles`,
    async (queryParams?: SearchQueryParams) => {
        const { data } = await axios.get<ListProductoResponse>(
            `${getURL()}/inmuebles/modalidad/ventas`,
            {
                params: buildParams(queryParams),
            }
        );
        return data;
    }
);

export const fetchNuevasPropiedades = createAsyncThunk(
    `productos/fetchNuevasPropiedades`,
    async (queryParams?: SearchQueryParams) => {
        const { data } = await axios.get<ListProductoResponse>(
            `${getURL()}/inmuebles/modalidad/ventas`,
            {
                params: buildParams(queryParams),
            }
        );
        return data;
    }
);
