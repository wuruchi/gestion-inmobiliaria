import React from "react";

type Props = {};

const Condiciones = (props: Props) => {
  return (
    <section className='condiciones-wrapper'>
      <section className='condiciones'>
        <div className='condiciones__header'>
          <h2>Condiciones</h2>
          <button className='btn btn--yellow bold'>Descargar PDF</button>
        </div>
        <div className='condiciones__row'>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Documentación</span>
          </div>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Condiciones Económicas</span>
          </div>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Reserva</span>
          </div>
        </div>
        <div className='condiciones__row'>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Consumos</span>
          </div>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Fianza</span>
          </div>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Limpieza</span>
          </div>
          <div className='condiciones__card'>
            <ion-icon name='checkmark-sharp' />
            <span>Proceso de Solicitud</span>
          </div>
        </div>
      </section>
    </section>
  );
};

export default Condiciones;
