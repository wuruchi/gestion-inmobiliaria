import React from "react";

type Props = {};

const SobreNosotros = (props: Props) => {
  return (
    <section id='sobre-nosotros' className='sobre-nosotros'>
      <h1 className='section-title'>Sobre ATBarcelona</h1>
      <p className='section-content'>
        Nacimos como ALQUILER TEMPORAL BARCELONA empresa especializada en alquileres por meses a expatriados, estudiantes, nómadas digitales y personas con necesidades específicas para vivir en Barcelona.
      </p>
      <p className='section-content'>
        Y crecimos y evolucionamos en ATB Servicios Inmobiliarios. Esta nueva marca busca ir más allá y convertirse en la primera inmobiliaria que involucra toda la cadena de valor en el mercado inmobiliario de Catalunya; fusionando la gestión avanzada, tecnología, seguridad, diseño y productos alternativos para dar respuesta a las necesidades de propietarios particulares y grandes patrimonios y conseguir exponenciar su rentabilidad y ofrecer inmuebles de calidad para nuestros inquilinos y compradores. 
        Somos un equipo multicultural con un objetivo incansable de introducir la innovación y con ganas de hacerlo todo más y mejor.
      </p>
      <div className='sobre-nosotros__cards'>
        <div className='sobre-nosotros__card'>
          <ion-icon name='people-outline'></ion-icon>
          <h2 className='sobre-nosotros__card__title'>Transparencia</h2>
          <p>Ponemos a nuestros clientes en el centro de todo lo que hacemos</p>
        </div>
        <div className='sobre-nosotros__card'>
          <ion-icon name='heart-outline'></ion-icon>
          <h2 className='sobre-nosotros__card__title'>Compromiso</h2>
          <p>Tomamos los retos y proyectos inmobiliarios como propios</p>
        </div>
        <div className='sobre-nosotros__card'>
          <ion-icon name='trophy-outline'></ion-icon>
          <h2 className='sobre-nosotros__card__title'>Innovación</h2>
          <p>
            Trabajamos con dedicación y eficiencia para ofrecer la mejor
            experiencia
          </p>
        </div>
      </div>
    </section>
  );
};

export default SobreNosotros;
