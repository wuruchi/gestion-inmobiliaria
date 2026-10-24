import React from "react";
import { convertToDateOnly, fomatNumberWithoutDecimalPart } from "../../utiles";

type Props = {
    esVenta: boolean;
    provincia?: string;
    municipio?: string;
    distrito?: string;
    referencia?: string;
    importeAlquiler: string;
    importeVenta: string;
    fechaDisponibilidad?: string;
};

const ProductoMetaCard = (props: Props) => {
    return (
        <div className='producto-meta__card'>
            <div className='producto-meta__card__header'>
                Disponible desde {convertToDateOnly(props.fechaDisponibilidad)}
            </div>
            <div className='producto-meta__card__body'>
                <h2 className='producto-meta__card__title'>
                    {props.municipio}
                </h2>
                <div className='producto-meta__card__ubicacion'>
                    <ion-icon name='location' />
                    <span>{props.distrito}</span>
                </div>
                <div className='producto-meta__card__referencia'>
                    Ref. {props.referencia}
                </div>
                <div className='producto-meta__card__precio'>
                    {fomatNumberWithoutDecimalPart(
                        props.esVenta
                            ? props.importeVenta
                            : props.importeAlquiler
                    )}{" "}
                    &euro;
                </div>
                <ul className='producto-meta__card__detalles'>
                    <li>
                        <span className='bold mr-small'>Precio Mensual:</span>
                        <span>{props.importeAlquiler}</span>
                    </li>
                    <li>
                        <span className='bold mr-small'>Fianza Mínima:</span>
                        <span>N/A</span>
                    </li>
                    <li>
                        <span className='bold mr-small'>
                            Honorarios de Agencia:
                        </span>
                        <span>N/A + IVA</span>
                    </li>
                    <li>
                        <span className='bold mr-small'>ITP:</span>
                        <span>N/A</span>
                    </li>
                </ul>
                <div className='producto-meta__card__buttons'>
                    <div>
                        <ion-icon name='document-text-outline'></ion-icon>
                        <span>Requisitos y Condiciones</span>
                    </div>
                    <div>
                        <ion-icon name='logo-whatsapp'></ion-icon>
                        <span>Contacto</span>
                    </div>
                    <div>
                        <ion-icon name='call-outline'></ion-icon>
                        <span>Llámenos</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductoMetaCard;
