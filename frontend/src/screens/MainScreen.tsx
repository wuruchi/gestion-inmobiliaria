import React from "react";
import Contactanos from "../components/Contactanos";
import DeseaAlquilar from "../components/DeseaAlquilar";
import NuevasPropiedades from "../components/NuevasPropiedades";
import ServiciosPropietarios from "../components/ServiciosPropietarios";
import SobreNosotros from "../components/SobreNosotros";
import TipoHogar from "../components/TipoHogar";

type Props = {};

const MainScreen = (props: Props) => {
    return (
        <>
            <TipoHogar />
            <DeseaAlquilar />
            <NuevasPropiedades title='Nuevas Propiedades' />
            <ServiciosPropietarios />
            <SobreNosotros />
            <Contactanos />
        </>
    );
};

export default MainScreen;
