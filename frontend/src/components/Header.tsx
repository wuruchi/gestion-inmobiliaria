import React from "react";
import { useNavigate } from "react-router-dom";
import { scrollToSection } from "../utiles";
import Dropdown from "./dropdown/dropdown";

type Props = {};

const Header = (props: Props) => {
    const navigate = useNavigate();
    const gotoPlace = (place: string) => {
        navigate(`/${place}`);
    };

    const navigateToSection = (section: string) => {
        const sectionComponent = document.getElementById(section);
        if (sectionComponent) {
            scrollToSection(section);
        } else {
            navigate(`/`);
        }
    };

    return (
        <header className='header'>
            <a href='/'>
                <img
                    className='main__logo'
                    src='/img/atb/logo-atb-no-fondo.png'
                    alt='business logo'
                ></img>
            </a>
            <div className='header__menu'>
                <div className='header__menu-top'>
                    <div className='header__menu__complements'>
                    <div>
                        <span className='web-propietarios'>
                            Visitar la web de propietarios
                        </span>
                    </div>
                        <button className='btn btn--main'>
                            Acceso a usuario
                        </button>
                        <span className='header__menu__complements__idioma'>
                            Español
                        </span>
                        <img src='/img/languages/spanish.png' alt='language selector' />
                    </div>
                </div>
                <nav className='header__menu-bottom'>
                    <Dropdown trigger={<button className="header__menu-bottom__controller">Alquiler</button>} menu={[
                        <button className="header__menu-bottom__sub-item" onClick={() => gotoPlace("pisos-de-alquiler-y-venta/alquiler-larga-estancia-barcelona")}>Alquiler Temporal</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => gotoPlace("pisos-de-alquiler-y-venta/alquiler-temporal-barcelona")}>Alquiler de Vivienda Habitual</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("glamour")}>Alquiler de Habitaciones con Glamour</button>
                    ]} />
                    <Dropdown trigger={<button className="header__menu-bottom__controller">Venta</button>} menu={[
                        <button className="header__menu-bottom__sub-item" onClick={() => gotoPlace("pisos-de-alquiler-y-venta/venta-de-inmuebles")}>Pisos en Venta</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("glamour")}>Quiero Invertir</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("glamour")}>Personal Shopper Inmobiliario</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("glamour")}>Vender y Comprar en Criptomonedas</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("glamour")}>Golden Visa</button>,
                    ]} />
                    <button className="header__menu-bottom__controller">Novedades</button>
                    <button className="header__menu-bottom__controller">Mundo Inmobiliario</button>
                    <Dropdown trigger={<button className="header__menu-bottom__controller">Sobre Nostros</button>} menu={[
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Alquiler Temporal de Apartamentos</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Alquiler de Vivienda Habitual y Larga Estancia</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Alquiler de Habitaciones con Glamour</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Compra y Venta de Apartaments</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Asesoramiento a Inversores</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>El Equipo</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Quiéres Trabajar con Nosotros?</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Preguntas Frecuentes</button>,
                        <button className="header__menu-bottom__sub-item" onClick={() => navigateToSection("blog")}>Contacta con Nosotros</button>,
                    ]} />
                </nav>
            </div>
        </header>
    );
};

export default Header;
