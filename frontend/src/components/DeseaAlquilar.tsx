import React from "react";

type Props = {};

const DeseaAlquilar = (props: Props) => {
  return (
    <section className='desea-alquilar'>
      <h1 className='section-title'>¿Desea alquilar su propiedad y cobrar sus rentas cada mes sin preocupaciones?</h1>
      <p className='section-content'>
        En ATB gestionamos su alquiler de principio a fin, garantizando el cobro seguro de sus renta mes a mes, además próximamente podrás adelantar los alquileres si lo consideras necesario. Quieres conocer todos los detalles de nuestro servicio que incluye: gestión integral avanzada y adaptada a tus necesidades, garantía de cobro y muy pronto adelanto de renta, por favor contáctenos, estaremos encantados de asesorarte paso a paso.
      </p>
      <button className='btn btn--big btn--outline'>
        Soy propietario y quiero saber más
      </button>
    </section>
  );
};

export default DeseaAlquilar;
