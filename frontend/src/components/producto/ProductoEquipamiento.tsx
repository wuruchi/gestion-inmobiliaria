import React from "react";
import { Producto } from "../../features/interfaces";

type Props = { producto: Producto };

const ProductoEquipamiento = (props: Props) => {
    const { producto } = props;
    const { dotacion, instalaciones, arearecreo } = producto;
    return (
        <div className='producto-equipamiento'>
            <h2>Equipamiento</h2>
            <div className='producto-equipamiento__grid'>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='home-outline'></ion-icon>
                    <span>Instalaciones</span>
                    <ul>
                        {!!instalaciones?.contador_agua && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Contador de agua</span>
                            </li>
                        )}
                        {!!instalaciones?.compania_agua && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Compañía agua: {instalaciones.compania_agua}
                                </span>
                            </li>
                        )}
                        {!!instalaciones?.contador_electricidad && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Contador de electricidad</span>
                            </li>
                        )}
                        {!!instalaciones?.compania_electricidad && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Compañía electricidad:{" "}
                                    {instalaciones.compania_electricidad}
                                </span>
                            </li>
                        )}
                        {!!instalaciones?.gas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Gas</span>
                            </li>
                        )}
                        {!!instalaciones?.tipo_gas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Tipo Gas: {instalaciones.tipo_gas}</span>
                            </li>
                        )}
                        {!!instalaciones?.contador_gas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Contador de gas</span>
                            </li>
                        )}
                        {!!instalaciones?.compania_gas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Compañía gas: {instalaciones.compania_gas}
                                </span>
                            </li>
                        )}
                        {!!instalaciones?.calefaccion && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Calefacción</span>
                            </li>
                        )}
                        {!!instalaciones?.tipo_calefaccion && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Tipo Calefacción:{" "}
                                    {instalaciones.tipo_calefaccion}
                                </span>
                            </li>
                        )}
                        {!!instalaciones?.subtipo_calefaccion && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Subtipo Calefacción:{" "}
                                    {instalaciones.subtipo_calefaccion}
                                </span>
                            </li>
                        )}
                        {!!instalaciones?.tvs && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>TVs: {instalaciones.tvs}</span>
                            </li>
                        )}
                        {!!instalaciones?.tv_internacional && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>TV Internacional</span>
                            </li>
                        )}
                        {!!instalaciones?.antena_parabolica && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Antena Parabólica</span>
                            </li>
                        )}
                        {!!instalaciones?.aire_acondicionado && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Aire Acondicionado</span>
                            </li>
                        )}
                        {!!instalaciones?.ascensor && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Ascensor: {instalaciones.ascensor}</span>
                            </li>
                        )}
                        {!!instalaciones?.internet && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Internet</span>
                            </li>
                        )}
                        {!!instalaciones?.telefono && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Teléfono</span>
                            </li>
                        )}
                        {!!instalaciones?.instalacion_telefono && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Instalación Teléfono</span>
                            </li>
                        )}
                        {!!instalaciones?.dvd && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>DVD</span>
                            </li>
                        )}
                        {!!instalaciones?.hilo_musical && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Hilo musical</span>
                            </li>
                        )}
                        {!!instalaciones?.acceso_silla_ruedas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Acceso Silla de Ruedas</span>
                            </li>
                        )}
                    </ul>
                </div>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='water-outline'></ion-icon>
                    <span>Baños</span>
                    <ul>
                        <li>
                            <ion-icon name='checkmark-sharp'></ion-icon>
                            <span>
                                Número: {props.producto.banios?.banios || 0}
                            </span>
                        </li>
                        {props.producto.banios?.suelo != null && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Suelo: {props.producto.banios.suelo}
                                </span>
                            </li>
                        )}
                    </ul>
                </div>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='bed-outline'></ion-icon>
                    <span>Dormitorios</span>
                    <ul>
                        {producto.dormitorios?.dobles != null && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Habitación con cama doble:{" "}
                                    {producto.dormitorios.dobles}
                                </span>
                            </li>
                        )}
                        {producto.dormitorios?.individuales != null && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Habitación con cama simple:{" "}
                                    {producto.dormitorios.individuales}
                                </span>
                            </li>
                        )}
                        {!!producto.dormitorios?.exteriores && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Exteriores:{" "}
                                    {producto.dormitorios.exteriores}
                                </span>
                            </li>
                        )}
                        {!!producto.dormitorios?.suites && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Suites: {producto.dormitorios.suites}
                                </span>
                            </li>
                        )}
                    </ul>
                </div>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='fast-food-outline'></ion-icon>
                    <span>Área Recreo</span>
                    <ul>
                        {!!arearecreo?.zona_deportiva && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Zona deportiva</span>
                            </li>
                        )}
                        {!!arearecreo?.gimnasio && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Gimnasio</span>
                            </li>
                        )}
                        {!!arearecreo?.piscina && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Piscina</span>
                            </li>
                        )}
                        {!!arearecreo?.solarium && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Solarium</span>
                            </li>
                        )}
                        {!!arearecreo?.jardin_infantil && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Jardín Infantil</span>
                            </li>
                        )}
                        {!!arearecreo?.local_social && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Local Social</span>
                            </li>
                        )}
                    </ul>
                </div>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='wifi-outline'></ion-icon>
                    <span>Dotación</span>
                    <ul>
                        {!!dotacion?.amueblado && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Amueblado</span>
                            </li>
                        )}
                        {!!dotacion?.armarios_empotrados && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Armarios Empotrados:{" "}
                                    {dotacion.armarios_empotrados}
                                </span>
                            </li>
                        )}
                        {!!dotacion?.jacuzzi_hidromasaje && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Jacuzzi Hidromasaje:{" "}
                                    {dotacion.jacuzzi_hidromasaje}
                                </span>
                            </li>
                        )}
                        {!!dotacion?.secadora && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Secadora: {dotacion.secadora}</span>
                            </li>
                        )}
                        {!!dotacion?.lavadora && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Lavadora: {dotacion.lavadora}</span>
                            </li>
                        )}
                        {!!dotacion?.lavavajillas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>
                                    Lavavajilla: {dotacion.lavavajillas}
                                </span>
                            </li>
                        )}
                        {!!dotacion?.microondas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Microondas: {dotacion.microondas}</span>
                            </li>
                        )}
                        {!!dotacion?.nevera && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Nevera: {dotacion.nevera}</span>
                            </li>
                        )}
                        {!!dotacion?.radio && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Radio: {dotacion.radio}</span>
                            </li>
                        )}
                        {!!dotacion?.ropero && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Ropero: {dotacion.ropero}</span>
                            </li>
                        )}
                        {!!dotacion?.toldo && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Toldo: {dotacion.toldo}</span>
                            </li>
                        )}
                        {!!dotacion?.horno && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Horno: {dotacion.horno}</span>
                            </li>
                        )}
                        {!!dotacion?.utensilios_cocina && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Utensilios de Cocina</span>
                            </li>
                        )}
                        {!!dotacion?.estufa && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Estufa: {dotacion.estufa}</span>
                            </li>
                        )}
                        {!!dotacion?.ventilador && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Ventilador: {dotacion.ventilador}</span>
                            </li>
                        )}
                        {!!dotacion?.camas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Camas: {dotacion.camas}</span>
                            </li>
                        )}
                        {!!dotacion?.sofas && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Sofas: {dotacion.sofas}</span>
                            </li>
                        )}
                        {!!dotacion?.tendedero && (
                            <li>
                                <ion-icon name='checkmark-sharp'></ion-icon>
                                <span>Tendedero: {dotacion.tendedero}</span>
                            </li>
                        )}
                    </ul>
                </div>
                <div className='producto-equipamiento__item'>
                    <ion-icon name='leaf-outline'></ion-icon>
                    <span>Etiqueta Energética</span>
                </div>
            </div>
        </div>
    );
};

export default ProductoEquipamiento;
