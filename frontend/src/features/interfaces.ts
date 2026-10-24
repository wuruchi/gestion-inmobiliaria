export interface Otros {
    id: number;
    capacidad_personas: number;
    suelo_piso: string;
    exterior: string;
    altura_real_m: string | null;
    anio_ultima_reforma: number;
    gastos_comunidad_incluidos: boolean;
    orientacion: string;
    chimenea: boolean;
    vistas_al_mar: boolean;
    vistas_montania: boolean;
    tipo_fachada: string;
    office: string;
    acepta_animales: boolean;
    estancia_minima_meses: number | null;
    estancia_maxima_meses: number | null;
    inmueble: number;
}

export interface Banios {
    id: number;
    banios: number;
    suelo: string;
    inmueble: number;
}

export interface Dormitorios {
    id: number;
    dobles: number;
    individuales: number;
    exteriores: number;
    suites: number;
    inmueble: number;
}

export interface Instalaciones {
    id: number;
    contador_agua: boolean;
    compania_agua: string;
    contador_electricidad: boolean;
    compania_electricidad: string;
    gas: boolean;
    tipo_gas: string;
    contador_gas: boolean;
    compania_gas: string;
    calefaccion: boolean;
    tipo_calefaccion: string;
    subtipo_calefaccion: string;
    tvs: number;
    tv_internacional: boolean;
    antena_parabolica: boolean;
    aire_acondicionado: boolean;
    ascensor: number;
    internet: boolean;
    telefono: boolean;
    instalacion_telefono: boolean;
    dvd: boolean;
    hilo_musical: boolean;
    acceso_silla_ruedas: boolean;
    inmueble: number;
}

export interface Dotacion {
    id: number;
    amueblado: boolean;
    armarios_empotrados: number;
    jacuzzi_hidromasaje: number;
    secadora: number;
    lavadora: number;
    lavavajillas: number;
    microondas: number;
    nevera: number;
    radio: number;
    ropero: number;
    toldo: number;
    horno: number;
    utensilios_cocina: boolean;
    estufa: number;
    ventilador: number;
    camas: number;
    sofas: number;
    tendedero: number;
    inmueble: number;
}

export interface AreaRecreo {
    id: number;
    zona_deportiva: boolean;
    gimnasio: boolean;
    piscina: boolean;
    solarium: boolean;
    jardin_infantil: boolean;
    local_social: boolean;
    inmueble: number;
}

export interface PlazaAparcamiento {
    id: number;
    numero: string;
    tipo: "coche" | "moto";
    superficie: string | null;
    notas: string;
}

export interface Terraza {
    id: number;
    terraza: number;
    balcones: number;
    descripcion: string;
    inmueble: number;
}

export interface Cocina {
    id: number;
    cocina: boolean;
    cocina_amueblada: boolean;
    tipo_cocina: string | null;
    suelo_cocina: string | null;
    inmueble: number;
}

export interface Salon {
    id: number;
    salon: number;
    descripcion: string | null;
    inmueble: number;
}

export interface Carpinteria {
    id: number;
    carpinteria_interior: boolean;
    carpinteria_exterior: boolean;
    inmueble: number;
}

export interface OtrosEspacios {
    id: number;
    despachos: number;
    vestidores: number;
    altillo: number;
    galeria: number;
    trastero: number;
    buhardilla: number;
    bodega: number;
    lavadero: number;
    estudios: number;
    bibliotecas: number;
    inmueble: number;
}

export interface Seguridad {
    id: number;
    portero_conserje: boolean;
    vigilancia_privada: boolean;
    camaras_seguridad: boolean;
    puerta_blindada: boolean;
    caja_seguridad: boolean;
    cristales_blindados: boolean;
    sistema_alarma: boolean;
    instalacion_antirrobo: boolean;
    instalacion_contra_incendio: boolean;
    video_portero: boolean;
    portero_automatico: boolean;
    inmueble: number;
}

export interface Entorno {
    id: number;
    zona_comunitaria: boolean;
    otras_areas_comunitarias: boolean;
    jardin: boolean;
    cerca_colegios: boolean;
    cerca_farmacia: boolean;
    cerca_guarderias: boolean;
    cerca_medico: boolean;
    cerca_centro_comercial: boolean;
    distancia_playa_m: number | null;
    distancia_poblacion_m: number | null;
    distancia_ciudad_m: number | null;
    cerca_supermercado: boolean;
    cerca_restaurantes: boolean;
    cerca_discotecas: boolean;
    inmueble: number;
}

export interface Transporte {
    inmueble: number;
    cerca_bus: boolean;
    descripcion_bus: string | null;
    cerca_metro: boolean;
    descripcion_metro: string | null;
    cerca_tranvia: boolean;
    descripcion_tranvia: string | null;
    cerca_tren: boolean;
    descripcion_tren: string | null;
    cerca_ferrocarril: boolean;
    descripcion_ferrocarril: string | null;
}

export interface CondicionesAlquiler {
    id: number;
    nombre: string;
    fianza: string;
    honorarios: string;
    pago_adelantado: string;
    itp: string;
    suministros: string;
    limpieza_final: string;
    incluido: string;
    no_incluido: string;
}

export interface SolicitudReserva {
    nombre: string;
    email: string;
    telefono: string;
    fecha_desde: string | null;
    acepta_aviso_legal: boolean;
}

export interface Modalidad {
    codigo: string;
    nombre: string;
}

export interface ProductoImage {
    _id: number; // A numeric identifier for the image
    image: string; // A URL to the image file
    default: boolean; // A flag indicating if the image is the default one
}

export interface Producto {
    _id: number;
    images: ProductoImage[];
    provincia: { _id: number; nombre: string };
    municipio: { _id: number; nombre: string };
    distrito: { _id: number; nombre: string };
    barrio: { _id: number; nombre: string } | null;
    otros: Otros | null;
    banios: Banios | null;
    dormitorios: Dormitorios | null;
    instalaciones: Instalaciones | null;
    dotacion: Dotacion | null;
    arearecreo: AreaRecreo | null;
    cocina: Cocina | null;
    terraza: Terraza | null;
    salon: Salon | null;
    carpinteria: Carpinteria | null;
    otros_espacios: OtrosEspacios | null;
    seguridad: Seguridad | null;
    entorno: Entorno | null;
    transporte: Transporte | null;
    condiciones: CondicionesAlquiler | null;
    consumo_energetico: string | null;
    ultima_renta: string | null;
    indice_referencia_min: string | null;
    indice_referencia_max: string | null;
    actualizacion_renta: string | null;
    situacion_5_anios: string | null;
    gran_tenedor: boolean;
    zona_tensionada: boolean;
    original_id: number;
    referencia: string;
    fecha_disponibilidad: string;
    titulo: string;
    tipo: string;
    modalidades: Modalidad[];
    es_venta: boolean;
    codigo_postal: string;
    zona: string | null;
    zona_ref: string | null;
    direccion: string;
    direccion_short: string;
    geo_latitude: number | null;
    geo_longitude: number | null;
    fecha_alta: string;
    fecha_baja: string | null;
    estado: string;
    sup_construida: string;
    sup_cont_comun: string;
    sup_util: string;
    n_plz_garaje: number;
    plazas: PlazaAparcamiento[];
    registros_legales: RegistroLegal[];
    ocultar_direccion: boolean;
    emisiones_co2: string | null;
    importe_alquiler: string;
    importe_venta: string;
    publicar_web: boolean;
    eficiencia: string;
    nombre_eficiencia: string;
    descripcion_es: string;
    descripcion_en: string;
    descripcion_cat: string | null;
    usos: string;
    notas_internas: string;
    otros_datos: string;
    gtos_comunidad: string;
    ibi_incluido: boolean;
    ibi: string;
    situacion_actual: string;
    n_habitaciones: number;
    n_banios: number;
    notas_web: string | null;
    fecha_firma: string | null;
    fecha_entrega: string | null;
    propietario: string;
    matterport_url: string | null;
    created_at: string;
    updated_at: string;
}

export interface ListProducto {
    _id: number;
    es_venta: boolean;
    modalidades: Modalidad[];
    referencia: string;
    tipo: string;
    estado: string;
    sup_util: string;
    importe_alquiler: string;
    importe_venta: string;
    n_habitaciones: number;
    n_banios: number;
    descripcion_es: string;
    descripcion_en: string | null;
    description_cat: string | null;
    situacion_actual: string;
    fecha_disponibilidad: string;
    cocina: Cocina | null;
    terraza: Terraza | null;
    images: ProductoImage[];
    provincia: { _id: number; nombre: string };
    municipio: { _id: number; nombre: string };
    distrito: { _id: number; nombre: string };
    barrio: { _id: number; nombre: string } | null;
    otros: Otros | null;
    banios: Banios | null;
    dormitorios: Dormitorios | null;
    instalaciones: Instalaciones | null;
    dotacion: Dotacion | null;
    arearecreo: AreaRecreo | null;
}

export interface ListProductoResponse {
    inmuebles: ListProducto[];
    page: number;
    pages: number;
}

export interface Provincia {
    _id: number;
    nombre: string;
}

export interface Municipio {
    _id: number;
    nombre: string;
    provincia: number;
}

export interface Distrito {
    _id: number;
    codigo: string;
    nombre: string;
    slug: string;
    municipio: number;
}

export interface Barrio {
    _id: number;
    codigo: string;
    nombre: string;
    slug: string;
    distrito: number;
}

export interface DistritoCounter {
    distrito_id: number;
    distrito: string;
    modalidad: string;
    count: number;
}

export interface RegistroLegal {
    tipo: 'aicat' | 'cedula_habitabilidad' | 'certificado_energetico' | 'licencia_turistica' | 'otro';
    numero: string;
    organismo: string;
}
