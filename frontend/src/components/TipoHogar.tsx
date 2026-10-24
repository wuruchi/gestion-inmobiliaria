import React from "react";
import { useNavigate } from "react-router-dom";

type Props = {};

const TipoHogar = (props: Props) => {
  const navigate = useNavigate();

  return (
    <section className='tipo-hogar-wrapper'>
      <section className='tipo-hogar'>
        <section className='tipo-hogar__text'>
          <h1 className='section-title'>¿Qué tipo de hogar buscas?</h1>
          <p className='section-content'>
            Encuentra el alojamiento perfecto para ti en Barcelona
          </p>
        </section>
        <section className='tipo-hogar__cards'>
          <div
            className='card tipo-hogar__card tipo-hogar__card-temporal'
            onClick={() => navigate("/pisos-de-alquiler-y-venta/alquiler-temporal-barcelona")}
          >
            <div className='card__text tipo-hogar__card-text bg--main'>
              <header>Alquiler temporal</header>
              <p>De 2 a 11 meses.</p>
            </div>
            <div className='card--ribbon bg--orange'></div>
          </div>
          <div
            className='card tipo-hogar__card tipo-hogar__card-larga'
            onClick={() => navigate("/pisos-de-alquiler-y-venta/alquiler-larga-estancia-barcelona")}
          >
            <div className='card__text tipo-hogar__card-text bg--main'>
              <header>Alquiler de larga estancia</header>
              <p>De 1 a 5 años.</p>
            </div>
            <div className='card--ribbon bg--yellow'></div>
          </div>
          <div
            className='card tipo-hogar__card tipo-hogar__card-ventas'
            onClick={() => navigate("/pisos-de-alquiler-y-venta/venta-de-inmuebles")}
          >
            <div className='card__text tipo-hogar__card-text bg--main'>
              <header>Venta</header>
              <p>Para uso propio o inversión.</p>
            </div>
            <div className='card--ribbon bg--red'></div>
          </div>
        </section>
        <section className="tipo-hogar__text">
          <h1 className="section-title">¿Quiénes somos y qué podemos hacer por ti?</h1>
          <p className="section-content">
            <b>ATBarcelona</b> es una empresa inmobiliaria conformada por un equipo multicultural y experimentado que busca atender las necesidades de vivienda con la finalidad de alquiler temporal (meses), alquiler vivienda habitual (años),  venta y compra de apartamentos en Barcelona, contamos con dos oficinas físicas ubicadas en enclaves estratégicos de Barcelona como son la <i>Calle Aragón 189</i> y la <i>Avenida Diagonal 327</i>. Nos caracterizamos por el trato ágil, profesional y de calidad, se sentirá acompañado durante todo el proceso. 
          </p>
          <p className="section-content">
            Contamos con una oferta en su mayoría de alquiler temporal (alquiler por meses) para estudiantes, profesionales, expatriados, nómadas digitales  y empresas, sin embargo nuestra cartera de alquiler también incluye otros dos productos: Alquiler Larga estancia o vivienda habitual para personas residentes en Barcelona que buscan un nuevo hogar y finalmente ofrecemos la opción de habitaciones con glamour para estudiantes que necesiten acomodación temporal en Barcelona. 
          </p>
          <p className="section-content">
            Además ofrecemos inmuebles en venta para primera vivienda, segunda residencia o para invertir, cubriendo diferentes necesidades y presupuestos, también estamos incursionando en la mano de expertos en la comercialización de inmuebles en criptomonedas.
          </p>
        </section>
      </section>
    </section>
  );
};

export default TipoHogar;
