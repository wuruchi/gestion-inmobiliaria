import React, { useEffect } from "react";
import { fetchNuevasPropiedades } from "../features/functions";
import { useAppDispatch, useAppSelector } from "../hooks";
import {
    truncate,
    fomatNumberWithoutDecimalPart,
    toIntOrZero,
} from "../utiles";

type Props = { title: string };

const NuevasPropiedades = (props: Props) => {
    const dispatch = useAppDispatch();
    const nuevasPropiedades = useAppSelector(
        (state) => state.inmueble.nuevasPropiedades
    );

    useEffect(() => {
        if (nuevasPropiedades === null) {
            dispatch(fetchNuevasPropiedades());
        }
    }, [nuevasPropiedades, dispatch]);

    const openProduct = (_id: number) => {
        window.open(`#/producto/${_id}`, "_self");
    };

    return (
        <section className='nuevas-propiedades'>
            <h1 className='section-title'>{props.title}</h1>
            <p className='section-content'>
                Descubre junto a ATB
            </p>
            <div className='nuevas-propiedades__cards'>
                {nuevasPropiedades?.map((propiedad) => (
                    <div
                        key={propiedad._id}
                        className='card nuevas-propiedades__card nuevas-propiedades__card-piso'
                        style={{
                            backgroundImage: `url(${propiedad.images[0]?.image})`,
                        }}
                        onClick={() => openProduct(propiedad._id)}
                    >
                        <div className='card__text nuevas-propiedades__card-text bg--main'>
                            <header>
                                {truncate(propiedad.descripcion_es, 40)}
                            </header>
                            <p>
                                {propiedad.municipio.nombre}/
                                {propiedad.distrito.nombre}
                            </p>
                            <p>
                                {(propiedad.dormitorios?.dobles || 0) +
                                    (propiedad.dormitorios?.individuales ||
                                        0)}{" "}
                                habitaciones - {propiedad.sup_util} m2
                            </p>
                            <footer>
                                {fomatNumberWithoutDecimalPart(
                                    propiedad.es_venta
                                        ? toIntOrZero(propiedad.importe_venta) >
                                          0
                                            ? propiedad.importe_venta
                                            : propiedad.importe_alquiler
                                        : propiedad.importe_alquiler
                                )}
                                &nbsp;&euro;
                            </footer>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default NuevasPropiedades;
