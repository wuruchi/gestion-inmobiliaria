import React, { ChangeEvent, useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../hooks";
import {
    tipoInmuebleToLongName,
    tipoInmuebleToSubtitle,
    TipoProduct,
    getTipoProductFromLastPart,
} from "../../features/common";
import {
    clearInmuebles,
    setInmuebleType,
    setCurrentProvincia,
    setCurrentMunicipio,
    setCurrentDistrito,
} from "../../features/productoSlice";
import {
    fetchHabitualInmuebles,
    fetchTemporalInmuebles,
    fetchVentaInmuebles,
    fetchAllInmuebles,
    SearchQueryParams,
    fetchProvincias,
    fetchMunicipios,
    fetchDistritos,
    fetchMapCounters,
} from "../../features/functions";
import { scrollToTop } from "../../utiles";
import Pagination from "../Pagination";

const getPathLastPart = () => {
    const path = window.location.href;
    const pathArray = path.split("/");
    return pathArray[pathArray.length - 1];
};

const CurrentTypeToFunction = {
    [TipoProduct.Habituales]: fetchHabitualInmuebles,
    [TipoProduct.Temporales]: fetchTemporalInmuebles,
    [TipoProduct.Ventas]: fetchVentaInmuebles,
    [TipoProduct.Todos]: fetchAllInmuebles,
};

const getFetchFunction = (currentType: TipoProduct) => {
    return CurrentTypeToFunction[currentType];
};

type Props = {};

const SearchControl = (props: Props) => {
    const producto = useAppSelector((state) => state.inmueble);
    const dispatch = useAppDispatch();
    const tipoProducto = getTipoProductFromLastPart(getPathLastPart());
    const fetchFunction = getFetchFunction(tipoProducto);

    const [precio, setPrecio] = useState<number | null>(null);
    const [fechaEntrada, setFechaEntrada] = useState<string>();
    const [nroHabitaciones, setNroHabitaciones] = useState<number | null>(null);
    const [referencia, setReferencia] = useState<string | null>(null);

    const onPriceChange = (e: ChangeEvent<HTMLInputElement>) => {
        setPrecio(parseInt(e.target.value));
    };

    const onFechaEntradaChange = (e: ChangeEvent<HTMLInputElement>) => {
        const newDate = e.target.value;
        setFechaEntrada(newDate);
    };

    const onHabitacionesChange = (e: ChangeEvent<HTMLInputElement>) => {
        const nroHabitaciones = parseInt(e.target.value);
        setNroHabitaciones(nroHabitaciones);
    };

    const getQueryParams = (page: number) => {
        const queryParams: SearchQueryParams = {
            page: page,
            nroHabitaciones: nroHabitaciones,
            maxPrecio: precio,
            provincia: producto.selectedProvincia,
            municipio: producto.selectedMunicipio,
            distrito: producto.selectedDistrito,
            referencia: referencia,
            fechaEntrada: fechaEntrada,
        };
        return queryParams;
    };

    const onSearch = () => {
        dispatch(fetchFunction(getQueryParams(1)));
    };

    const onClearFilters = () => {
        setPrecio(null);
        setFechaEntrada("");
        setNroHabitaciones(null);
        setReferencia(null);
        dispatch(clearInmuebles());
        dispatch(setCurrentMunicipio(null));
        dispatch(setCurrentDistrito(null));
    };

    useEffect(() => {
        if (producto.currentInmuebleType !== tipoProducto) {
            dispatch(clearInmuebles());
            dispatch(setInmuebleType(tipoProducto));
        }
    }, [tipoProducto, dispatch, producto.currentInmuebleType]);

    useEffect(() => {
        dispatch(fetchProvincias());
    }, [tipoProducto, dispatch]);

    useEffect(() => {
        if (producto.selectedProvincia) {
            dispatch(fetchMunicipios(producto.selectedProvincia));
        }
    }, [producto.selectedProvincia, dispatch]);

    useEffect(() => {
        if (producto.selectedMunicipio) {
            dispatch(fetchDistritos(producto.selectedMunicipio));
        }
    }, [producto.selectedMunicipio, dispatch]);

    useEffect(() => {
        if (tipoProducto) {
            scrollToTop();
        }
    }, [tipoProducto]);

    useEffect(() => {
        if (
            producto.currentInmuebleType &&
            producto.currentInmuebleType !== TipoProduct.Todos
        ) {
            dispatch(
                fetchMapCounters({
                    distritos: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    modalidad: producto.currentInmuebleType,
                })
            );
        }
    }, [producto.currentInmuebleType, dispatch]);

    useEffect(() => {
        if (producto.inmuebles === null && producto.status === "idle") {
            dispatch(fetchFunction(getQueryParams(1)));
        }
    }, [
        producto.currentInmuebleType,
        dispatch,
        fetchFunction,
        getQueryParams,
        producto.inmuebles,
        producto.status,
    ]);

    const getCounter = (
        name: string,
        classStyle: string,
        mapCounters: Record<string, number> | null
    ) => {
        if (mapCounters && mapCounters[name]) {
            return (
                <span className={`search-map__counter counter-${classStyle}`}>
                    {mapCounters[name]}
                </span>
            );
        }
        return null;
    };

    return (
        <>
            <section className='search-control'>
                <h1 className='section-title'>
                    {tipoInmuebleToLongName.get(producto.currentInmuebleType)}
                </h1>
                <p className='section-content'>
                    {tipoInmuebleToSubtitle.get(producto.currentInmuebleType)}
                </p>
                <div className='search-control__filters'>
                    <div className='search-control__filters__left'>
                        <label htmlFor='fecha-entrada'>
                            Fecha deseada de entrada
                        </label>
                        <input
                            type='date'
                            id='fecha-entrada'
                            name='fecha-entrada'
                            onChange={onFechaEntradaChange}
                            value={fechaEntrada}
                        />
                        <label htmlFor='provincia'>Provincia</label>
                        <select
                            name='provincia'
                            id='provincia'
                            onChange={(e) =>
                                dispatch(setCurrentProvincia(e.target?.value))
                            }
                        >
                            {(producto.provincias || []).map((provincia) => (
                                <option
                                    key={provincia._id}
                                    value={provincia._id}
                                >
                                    {provincia.nombre}
                                </option>
                            ))}
                        </select>
                        <label htmlFor='municipio'>Municipio</label>
                        <select
                            name='municipio'
                            id='municipio'
                            onChange={(e) =>
                                dispatch(setCurrentMunicipio(e.target?.value))
                            }
                        >
                            <option
                                value={-1}
                                selected={
                                    producto.selectedMunicipio === -1 ||
                                    producto.selectedMunicipio === null
                                }
                            >
                                -- --
                            </option>
                            {(producto.municipios || []).map((municipio) => (
                                <option
                                    key={municipio._id}
                                    value={municipio._id}
                                >
                                    {municipio.nombre}
                                </option>
                            ))}
                        </select>
                        <label htmlFor='distrito'>Distrito</label>
                        <select
                            name='distrito'
                            id='distrito'
                            onChange={(e) =>
                                dispatch(setCurrentDistrito(e.target.value))
                            }
                        >
                            <option
                                value={-1}
                                selected={
                                    producto.selectedDistrito === -1 ||
                                    producto.selectedDistrito === null
                                }
                            >
                                -- --
                            </option>
                            {(producto.distritos || []).map((distrito) => (
                                <option key={distrito._id} value={distrito._id}>
                                    {distrito.nombre}
                                </option>
                            ))}
                        </select>
                        <label htmlFor='nro-habitaciones'>
                            Nro de habitaciones
                        </label>
                        <input
                            type='number'
                            id='nro-habitaciones'
                            name='nro-habitaciones'
                            min={1}
                            max={6}
                            onChange={onHabitacionesChange}
                            value={nroHabitaciones || ""}
                        />
                        <label
                            className='search-control__filters__precio-mes'
                            htmlFor='precio-mes'
                        >
                            <span>Precio/mes hasta</span>
                            <span>&euro;</span>
                        </label>
                        <input
                            type='number'
                            min={1}
                            step={100}
                            value={precio || ""}
                            onChange={onPriceChange}
                        />
                        <label htmlFor='ref-apartamento'>
                            Ref. Apartamento
                        </label>
                        <input
                            type='text'
                            placeholder='Ej. 345726378'
                            onChange={(e) => setReferencia(e.target.value)}
                        />
                    </div>
                    <div className='search-control__filters__right'>
                        <div className='search-map__container'>
                            <img
                                className='search-map'
                                src='/img/atb/map.png'
                                alt='Barcelona Map'
                            ></img>
                            {getCounter(
                                "Gràcia",
                                "gracia",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Les Corts",
                                "les-corts",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Eixample",
                                "eixample",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Ciutat Vella",
                                "ciutat-vella",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Sants-Montjüic",
                                "sants-montjuic",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Sant Martí",
                                "sant-marti",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Sarrià-Sant Gervasi",
                                "sarria-sant-gervasi",
                                producto.mapCounters
                            )}
                            {getCounter(
                                "Horta-Guinardó",
                                "horta-guinardo",
                                producto.mapCounters
                            )}
                        </div>
                    </div>
                    <div className='search-control__filters__bottom'>
                        <div className='search-control__filters__busqueda-avanzada'>
                            <button
                                className='btn btn--main'
                                onClick={onSearch}
                            >
                                Buscar
                            </button>
                            <button
                                className='btn btn--outline'
                                onClick={() => onClearFilters()}
                            >
                                Borrar criterios
                            </button>
                        </div>
                    </div>
                </div>
            </section>
            <section
                style={{
                    display: "flex",
                    justifyContent: "center",
                }}
            >
                <Pagination
                    fnPrevious={() =>
                        dispatch(
                            fetchFunction(
                                getQueryParams(
                                    producto.pageCounters[
                                        producto.currentInmuebleType
                                    ] - 1
                                )
                            )
                        )
                    }
                    fnNext={() =>
                        dispatch(
                            fetchFunction(
                                getQueryParams(
                                    producto.pageCounters[
                                        producto.currentInmuebleType
                                    ] + 1
                                )
                            )
                        )
                    }
                    currentPage={
                        producto.pageCounters[producto.currentInmuebleType]
                    }
                    maxPage={producto.pageTotals[producto.currentInmuebleType]}
                />
            </section>
        </>
    );
};

export default SearchControl;
