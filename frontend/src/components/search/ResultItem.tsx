import React from "react";
import { ListProducto } from "../../features/interfaces";
import {
    convertToDateOnly,
    firstImage,
    truncate,
    fomatNumberWithoutDecimalPart,
} from "../../utiles";

type Props = {
    producto: ListProducto;
    backgroundColor: string;
    tipoInmueble: string;
    esVenta: boolean;
};

const ResultItem = (props: Props) => {
    const { producto } = props;

    const handleShowDetails = () => {
        window.open(`#/producto/${producto._id}`, "_self");
    };

    const nroHabitaciones =
        (props.producto.dormitorios?.dobles || 0) +
        (props.producto.dormitorios?.dobles || 0);

    const nroBanyos = props.producto.banios?.banios || 0;

    const wifi = props.producto.instalaciones?.internet
        ? "Internet"
        : "Sin Internet";
    const terraza = (props.producto.terraza?.terraza || 0) > 0 ? "Terraza" : "Sin Terraza";

    return (
        <div className='result-item' role='button' onClick={handleShowDetails}>
            <div className='result-item__left'>
                <img
                    className='result-item__image'
                    src={firstImage(producto.images)?.image}
                    alt='Imagen Apartamento'
                />
            </div>
            <div className='result-item__right'>
                <div
                    className='result-item__tipo'
                    style={{ backgroundColor: props.backgroundColor }}
                >
                    {props.tipoInmueble}
                </div>
                <div className='result-item__content-wrapper'>
                    <span className='result-item__costo'>
                        {props.esVenta
                            ? fomatNumberWithoutDecimalPart(
                                  producto.importe_venta
                              )
                            : fomatNumberWithoutDecimalPart(
                                  producto.importe_alquiler
                              )}
                        &nbsp;€
                    </span>
                    <p className='result-item__descripcion'>
                        {truncate(producto.descripcion_es, 160)}
                    </p>
                    <div className='result-item__ubicacion-ref'>
                        <p>
                            {producto.provincia.nombre}/
                            {producto.municipio.nombre}/
                            {producto.distrito.nombre}
                        </p>
                        <span>Ref. {producto.referencia}</span>
                    </div>
                    <div className='result-item__details-wrapper'>
                        <div className='result-item__details'>
                            <div className='result-item__details__item'>
                                <ion-icon name='expand-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    {producto.sup_util} m2
                                </span>
                            </div>
                            <div className='result-item__details__item'>
                                <ion-icon name='bed-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    {nroHabitaciones}{" "}
                                    {nroHabitaciones > 1
                                        ? "habitaciones"
                                        : "habitación"}
                                </span>
                            </div>
                            <div className='result-item__details__item'>
                                <ion-icon name='water-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    {nroBanyos}&nbsp;
                                    {nroBanyos > 1 ? "baños" : "baño"}
                                </span>
                            </div>
                            <div className='result-item__details__item'>
                                <ion-icon name='storefront-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    {terraza}
                                </span>
                            </div>
                            <div className='result-item__details__item'>
                                <ion-icon name='business-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    N/A
                                </span>
                            </div>
                            <div className='result-item__details__item'>
                                <ion-icon name='wifi-outline'></ion-icon>
                                <span className='result-item__details__description'>
                                    {wifi}
                                </span>
                            </div>
                        </div>
                    </div>
                    {!props.esVenta ? (
                        <div className='result-item__disponible_desde'>
                            Disponible desde:{" "}
                            {convertToDateOnly(producto.fecha_disponibilidad)}
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
};

export default ResultItem;
