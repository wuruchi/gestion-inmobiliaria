import React from "react";

type Props = {};

const Footer = (props: Props) => {
    return (
        <footer className='footer'>
            <div className='footer__first-row'>
                <div className='footer__column'>
                    <img
                        className='main__logo'
                        src='/img/atb/logo-atb-no-fondo.png'
                        alt='business logo'
                    ></img>
                    <div className='footer__content__icons'>
                        <div className='social-icons'>
                            <ion-icon name='logo-instagram'></ion-icon>
                            <ion-icon name='logo-facebook'></ion-icon>
                            <ion-icon name='logo-linkedin'></ion-icon>
                            <ion-icon name='logo-whatsapp'></ion-icon>
                        </div>
                    </div>
                </div>
                <div className='footer__column'>
                    <div className='footer__item'>Calle Aragó 189 Local 2</div>
                    <div className='footer__item'>
                        Avda. Diagonal 327 Local 2
                    </div>
                    <div className='footer__item mb-large'>Barcelona</div>
                    <div className='footer__content__telemail'>
                        <a href='tel:+34 93 307 09 12'>+34 93 307 09 12</a>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <a href='mailto:info@atbarcelona.es'>
                            info@atbarcelona.es
                        </a>
                    </div>
                </div>
                <div className='footer__column'>
                    <div className='footer__item'>Requisitos</div>
                    <div className='footer__item'>Proceso de Reserva</div>
                    <div className='footer__item'>Contacto</div>
                    <div className='footer__item'>Pagos a Efectuar</div>
                </div>
            </div>
            <div className='footer__second-row'>
                <div>Protección de datos LOPD</div>
                <div>Política de cookies</div>
                <div>Aviso legal</div>
            </div>
        </footer>
    );
};

export default Footer;
