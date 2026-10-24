import React from "react";
import { useAppSelector } from "../../hooks";
import ResultItem from "./ResultItem";
import {
    tipoInmuebleToColor,
    tipoInmuebleToLongName,
    ATB_MAIN,
    TipoProduct,
} from "../../features/common";

type Props = {};

const SearchResults = (props: Props) => {
    const productoState = useAppSelector((state) => state.inmueble);
    const { inmuebles, currentInmuebleType, status } = productoState;

    const backgroundColor =
        tipoInmuebleToColor.get(currentInmuebleType) || ATB_MAIN;
    const tipoInmueble =
        tipoInmuebleToLongName.get(currentInmuebleType) || "Loading...";

    return (
        <section className='search-results'>
            {status === "loading" && <p>Loading...</p>}
            {inmuebles &&
                status !== "loading" &&
                inmuebles.length > 0 &&
                inmuebles.map((producto) => (
                    <ResultItem
                        producto={producto}
                        key={producto._id}
                        backgroundColor={backgroundColor}
                        tipoInmueble={tipoInmueble}
                        esVenta={currentInmuebleType === TipoProduct.Ventas}
                    />
                ))}
        </section>
    );
};

export default SearchResults;
