import React from "react";

type Props = {
    superficieConstruida?: string;
    numberHabitaciones: number;
    numberBanyos: number;
    terraza: string;
    wifi: string;
};

const ProductoDetails = (props: Props) => {
    return (
        <div className='producto-meta__details'>
            <div className='producto-meta__details__item'>
                <ion-icon name='expand-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    {props.superficieConstruida} m2
                </span>
            </div>
            <div className='producto-meta__details__item'>
                <ion-icon name='bed-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    {props.numberHabitaciones}{" "}
                    {props.numberHabitaciones > 1
                        ? "habitaciones"
                        : "habitación"}
                </span>
            </div>
            <div className='producto-meta__details__item'>
                <ion-icon name='water-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    {props.numberBanyos}{" "}
                    {props.numberBanyos > 1 ? "baños" : "baño"}
                </span>
            </div>
            <div className='producto-meta__details__item'>
                <ion-icon name='storefront-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    {props.terraza}
                </span>
            </div>
            <div className='producto-meta__details__item'>
                <ion-icon name='business-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    Planta N/A
                </span>
            </div>
            <div className='producto-meta__details__item'>
                <ion-icon name='wifi-outline'></ion-icon>
                <span className='producto-meta__detail__description'>
                    {props.wifi}
                </span>
            </div>
        </div>
    );
};

export default ProductoDetails;
