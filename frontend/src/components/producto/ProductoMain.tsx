import React, { useEffect } from "react";
import ProductoEquipamiento from "./ProductoEquipamiento";
import Condiciones from "./Condiciones";
import NuevasPropiedades from "../NuevasPropiedades";
import Contactanos from "../Contactanos";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../hooks";
import { fetchProducto } from "../../features/functions";
import ProductoDetails from "./ProductoDetails";
import ProductoMetaCard from "./ProductoMetaCard";
import ImageGallery from "react-image-gallery";
import Map from "../common/Map";
import { scrollToTop, toIntOrNull, truncate } from "../../utiles";
import ProductoDescription from "./ProductoDescription";
import { TipoProduct } from "../../features/common";

type Props = {};

const ProductoMain = (props: Props) => {
    const productoId = toIntOrNull(useParams().id);
    const dispatch = useAppDispatch();
    const producto = useAppSelector((state) => state.inmueble.inmuebleInfo);
    const { currentProductoId, currentInmuebleType } = useAppSelector(
        (state) => state.inmueble
    );

    useEffect(() => {
        if (
            (productoId && producto === null) ||
            (productoId && productoId !== currentProductoId)
        ) {
            dispatch(fetchProducto(productoId));
        }
    }, [productoId, dispatch, producto, currentProductoId]);

    useEffect(() => {
        if (productoId) {
            scrollToTop();
        }
    }, [productoId]);

    const images = producto?.images.map((o) => ({ original: o.image })) || [];
    return (
        <>
            <section className='producto-section'>
                <div className='producto-intro'>
                    {truncate(producto?.descripcion_es, 240)}
                </div>
                <div className='producto-meta'>
                    <div className='producto-meta__left'>
                        <ImageGallery items={images} />
                    </div>
                    <div className='producto-meta__right'>
                        <ProductoMetaCard
                            provincia={producto?.provincia.nombre}
                            municipio={producto?.municipio.nombre}
                            distrito={producto?.distrito.nombre}
                            referencia={producto?.referencia}
                            esVenta={
                                currentInmuebleType === TipoProduct.Ventas
                                    ? true
                                    : false
                            }
                            importeVenta={producto?.importe_venta || "0.00"}
                            importeAlquiler={
                                producto?.importe_alquiler || "0.00"
                            }
                            fechaDisponibilidad={producto?.fecha_disponibilidad}
                        />
                    </div>
                    <div className='producto-meta__bottom'>
                        <ProductoDetails
                            superficieConstruida={producto?.sup_construida}
                            numberHabitaciones={
                                (producto?.dormitorios?.dobles || 0) +
                                (producto?.dormitorios?.individuales || 0)
                            }
                            numberBanyos={producto?.banios?.banios || 0}
                            terraza={
                                (producto?.terraza?.terraza || 0) > 0 ? "Terraza" : "Sin Terraza"
                            }
                            wifi={
                                producto?.instalaciones?.internet
                                    ? "Internet"
                                    : "Sin Internet"
                            }
                        />
                    </div>
                </div>
                <div className='matterport'>
                    {producto?.matterport_url && (
                        <iframe
                            title='Matterport'
                            width='100%'
                            height='800'
                            src={producto?.matterport_url}
                            frameBorder='0'
                            allowFullScreen
                            allow='xr-spatial-tracking'
                        ></iframe>
                    )}
                </div>
                <ProductoDescription
                    description_es={producto?.descripcion_es}
                />
                {producto?.geo_latitude && producto?.geo_longitude ? (
                    <Map
                        latitude={producto?.geo_latitude}
                        longitude={producto?.geo_longitude}
                        zoom={15}
                        height='56rem'
                    />
                ) : (
                    <div>No hay ubicación</div>
                )}
                {producto != null && (
                    <ProductoEquipamiento producto={producto} />
                )}
            </section>
            <Condiciones />
            <NuevasPropiedades title='Apartamentos que podrían interesarte' />
            <Contactanos />
        </>
    );
};

export default ProductoMain;
