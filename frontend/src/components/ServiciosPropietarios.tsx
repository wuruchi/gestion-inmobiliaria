import React from "react";

type Props = {};

const ServiciosPropietarios = (props: Props) => {
  return (
    <section id='servicios-propietarios' className='servicios-propietarios'>
      <h1 className='section-title'>Servicios a los propietarios</h1>
      <p className='section-content'>
        Poseer un inmueble y ponerlo en alquiler o venta requiere tomar una serie de decisiones que conllevan relevantes consecuencias legales, 
        jurídicas y administrativas. En ATB servicios inmobiliarios contará con un asesor personal que lo acompañará y guiará en todo el proceso. 
        Y estas son las claves de nuestro servicio:
      </p>
      <div className='servicios-propietarios__cards'>
        <div className='card servicios-propietarios__card servicios-propietarios__card-gestion'>
          <div className='card__text servicios-propietarios__card-text bg--white'>
            Gestión Integral Personalizada
          </div>
        </div>
        <div className='card servicios-propietarios__card servicios-propietarios__card-alquileres'>
          <div className='card__text servicios-propietarios__card-text bg--white'>
            Gestión de Cobro en Alquileres
          </div>
        </div>
        <div className='card servicios-propietarios__card servicios-propietarios__card-incidencias'>
          <div className='card__text servicios-propietarios__card-text bg--white'>
            Resolución de Incidencias
          </div>
        </div>
      </div>
      <button className='btn btn--big btn--outline'>Ver más servicios</button>
    </section>
  );
};

export default ServiciosPropietarios;
