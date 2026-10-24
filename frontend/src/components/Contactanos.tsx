import React from "react";

type Props = {};

const Contactanos = (props: Props) => {
  return (
    <section className='contactanos-wrapper'>
      <section className='contactanos'>
        <h1 className='section-title'>Contacta con nosotros</h1>
        <p className='section-content'>
          Contacta con nosotros si quieres una consulta o quieres hablar de tu
          proyecto inmobiliario.
        </p>
        <div className='contactanos__form-wrapper'>
          <div className='contactanos__form'>
            <div className='contactanos__form__left'>
              <input type='text' placeholder='Apellidos' />
              <input type='text' placeholder='Nombres' />
              <input type='text' placeholder='Email' />
              <input type='text' placeholder='Teléfono' />
            </div>
            <div className='contactanos__form__right'>
              <div>
                <input type='radio' id='buscando' name='tipo-contacto' />
                <label htmlFor='buscando'>Estoy buscando un apartamento</label>
              </div>
              <div>
                <input type='radio' id='tengo' name='tipo-contacto' />
                <label htmlFor='tengo'>
                  Tengo una propiedad en venta o alquiler
                </label>
              </div>
              <div>
                <input type='radio' id='otros' name='tipo-contacto' />
                <label htmlFor='otros'>Otros</label>
              </div>
              <textarea
                name=''
                id=''
                cols={30}
                placeholder='Mensaje'
              ></textarea>
            </div>
          </div>
          <div className='contactanos__form__footer'>
            <button className='btn btn--main btn--big' style={{ zIndex: 2 }}>Enviar</button>
          </div>
        </div>
      </section>
    </section>
  );
};

export default Contactanos;
