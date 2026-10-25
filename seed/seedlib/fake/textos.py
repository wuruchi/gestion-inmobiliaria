"""Titles and descriptions of the fake offers, in Spanish, English and Catalan.

Each example has its own wording because the text has to agree with its photos and equipment (a pool, a
terrace, a garden...). `{zona}` is the barrio (or the municipio outside Barcelona), `{municipio}` the
municipio, `{sup}` the built surface in m2 and `{planta}` the floor.
"""

TITULOS = {
    'atb-01': 'Piso de diseño con terraza y piscina en {zona}',
    'atb-02': 'Oficina con patio en {zona}',
    'atb-03': 'Piso reformado de 4 habitaciones en {zona}',
    'idealista-01': 'Chalet adosado con jardín en {zona}',
    'idealista-02': 'Casa independiente con dos dúplex en {zona}',
    'idealista-03': 'Piso de 1 habitación en {zona}',
    'locb-01': 'Piso de obra nueva con piscina, trastero y parking en {zona}',
    'locb-02': 'Piso luminoso de 3 habitaciones en {zona}',
    'locb-03': 'Piso amplio de 4 habitaciones en {zona}',
}

TEXTOS = {
    'atb-01': {
        'es': 'Fantástico piso de diseño de {sup} m² en {zona}, con terraza privada, solárium y piscina comunitaria '
              'en una finca con ascensor. Salón comedor con acceso directo a una de las terrazas, cocina americana '
              'totalmente equipada, habitación doble en suite con acceso al balcón y segunda habitación doble con '
              'baño completo con ducha. Aire acondicionado y calefacción, wifi y alarma incluidos.',
        'en': 'Fantastic {sup} m² designer flat in {zona}, with a private terrace, a solarium and a communal '
              'swimming pool, in a building with a lift. Living-dining room opening onto one of the terraces, fully '
              'equipped open-plan kitchen, double bedroom with en-suite shower and access to the balcony, and a '
              'second double bedroom with a full bathroom. Air conditioning, heating, wifi and alarm included.',
        'ca': 'Fantàstic pis de disseny de {sup} m² a {zona}, amb terrassa privada, solàrium i piscina comunitària en '
              'una finca amb ascensor. Menjador amb sortida directa a una de les terrasses, cuina americana '
              'totalment equipada, habitació doble en suite amb accés al balcó i una segona habitació doble amb '
              'bany complet. Aire condicionat, calefacció, wifi i alarma inclosos.',
    },
    'atb-02': {
        'es': 'Oficina de {sup} m² en {zona}, a escasos metros de la zona comercial. Dispone de dos espacios '
              'diáfanos, uno de ellos con baño con ducha, y un patio privado. Persianas eléctricas. Plazas de '
              'parking opcionales. En el precio están incluidos los gastos de comunidad, el seguro y el IBI.',
        'en': '{sup} m² office in {zona}, a few metres from the shopping area. Two open-plan spaces, one with a '
              'bathroom with shower, and a private patio. Electric shutters. Optional parking spaces. Community '
              'fees, insurance and property tax are included in the rent.',
        'ca': 'Oficina de {sup} m² a {zona}, a pocs metres de la zona comercial. Disposa de dos espais diàfans, un '
              'amb bany amb dutxa, i un pati privat. Persianes elèctriques. Places de pàrquing opcionals. Al preu '
              'hi estan inclosos les despeses de comunitat, l\'assegurança i l\'IBI.',
    },
    'atb-03': {
        'es': 'Piso reformado de {sup} m² en {zona}, con 4 habitaciones dobles, 2 baños y balcón. Salón comedor '
              'luminoso, cocina office con lavadero y suelo de terrazo en toda la vivienda. Calefacción central y '
              'finca con ascensor. Wifi de cortesía incluido. Ideal para estancias de temporada.',
        'en': 'Refurbished {sup} m² flat in {zona} with 4 double bedrooms, 2 bathrooms and a balcony. Bright '
              'living-dining room, kitchen with dining area and utility room, terrazzo floors throughout. Central '
              'heating and a building with a lift. Complimentary wifi included. Ideal for seasonal stays.',
        'ca': 'Pis reformat de {sup} m² a {zona}, amb 4 habitacions dobles, 2 banys i balcó. Menjador lluminós, cuina '
              'office amb safareig i terra de terratzo a tot l\'habitatge. Calefacció central i finca amb ascensor. '
              'Wifi de cortesia inclòs. Ideal per a estades de temporada.',
    },
    'idealista-01': {
        'es': 'Chalet adosado de dos plantas en {zona}, con {sup} m² construidos, 3 amplios dormitorios con armarios '
              'empotrados, salón con chimenea, cocina independiente y un baño. Jardín, porche con acceso directo y '
              'dos trasteros. Zona residencial tranquila, bien comunicada y con todos los servicios cerca.',
        'en': 'Two-storey terraced house in {zona}, {sup} m² built, with 3 spacious bedrooms with built-in wardrobes, '
              'a living room with a fireplace, a separate kitchen and one bathroom. Garden, porch with direct access '
              'and two storage rooms. Quiet residential area, well connected, with all services nearby.',
        'ca': 'Xalet adossat de dues plantes a {zona}, amb {sup} m² construïts, 3 dormitoris amplis amb armaris '
              'encastats, menjador amb xemeneia, cuina independent i un bany. Jardí, porxo amb accés directe i dos '
              'trasters. Zona residencial tranquil·la, ben comunicada i amb tots els serveis a prop.',
    },
    'idealista-02': {
        'es': 'Edificio moderno con dos dúplex reformados en {zona}, {sup} m² construidos en total. Cada dúplex tiene '
              'salón comedor, cocina, tres habitaciones y tres baños completos; cuentan con división horizontal y '
              'pueden destinarse a vivienda o a alquiler vacacional. Gas ciudad, ventanas climalit y varios trasteros.',
        'en': 'Modern building with two refurbished duplexes in {zona}, {sup} m² built in total. Each duplex has a '
              'living-dining room, a kitchen, three bedrooms and three full bathrooms; they have horizontal '
              'division and can be used as homes or holiday lets. Mains gas, double-glazed windows and several '
              'storage rooms.',
        'ca': 'Edifici modern amb dos dúplex reformats a {zona}, {sup} m² construïts en total. Cada dúplex té menjador, '
              'cuina, tres habitacions i tres banys complets; tenen divisió horitzontal i es poden destinar a '
              'habitatge o a lloguer vacacional. Gas ciutat, finestres climalit i diversos trasters.',
    },
    'idealista-03': {
        'es': 'Piso de {sup} m² en {zona}, en finca seminueva y en perfecto estado. Recibidor, salón comedor con cocina '
              'abierta, una habitación doble, baño completo y zona de lavandería. Exterior, con ascensor y aire '
              'acondicionado. Una excelente opción para vivir todo el año o como segunda residencia.',
        'en': '{sup} m² flat in {zona}, in a nearly new building in perfect condition. Hallway, living-dining room '
              'with open kitchen, one double bedroom, a full bathroom and a laundry area. Exterior, with a lift and '
              'air conditioning. An excellent choice to live in all year or as a second home.',
        'ca': 'Pis de {sup} m² a {zona}, en finca seminova i en perfecte estat. Rebedor, menjador amb cuina oberta, '
              'una habitació doble, bany complet i zona de bugaderia. Exterior, amb ascensor i aire condicionat. '
              'Una excel·lent opció per viure-hi tot l\'any o com a segona residència.',
    },
    'locb-01': {
        'es': 'Piso de obra nueva de {sup} m² en {zona}, planta {planta} con ascensor, 2 habitaciones, 2 baños y un '
              'aseo. Amueblado y equipado, con aire acondicionado, calefacción, wifi, balcón y terraza. La finca '
              'cuenta con piscina, conserje e interfono. Incluye trastero y plaza de aparcamiento.',
        'en': 'New-build {sup} m² flat in {zona}, floor {planta} with a lift, 2 bedrooms, 2 bathrooms and a half '
              'bathroom. Furnished and equipped, with air conditioning, heating, wifi, a balcony and a terrace. The '
              'building has a swimming pool, a concierge and an intercom. Storage room and parking space included.',
        'ca': 'Pis d\'obra nova de {sup} m² a {zona}, planta {planta} amb ascensor, 2 habitacions, 2 banys i un lavabo. '
              'Moblat i equipat, amb aire condicionat, calefacció, wifi, balcó i terrassa. La finca disposa de piscina, '
              'consergeria i interfon. Inclou traster i plaça d\'aparcament.',
    },
    'locb-02': {
        'es': 'Piso de {sup} m² en {zona}, con 3 habitaciones, baño y aseo. Amueblado y totalmente equipado, con aire '
              'acondicionado, calefacción, wifi y balcón. Finca con ascensor e interfono. Alquiler de corta estancia '
              'de hasta 11 meses, con ropa de cama y toallas.',
        'en': '{sup} m² flat in {zona}, with 3 bedrooms, a bathroom and a half bathroom. Furnished and fully '
              'equipped, with air conditioning, heating, wifi and a balcony. Building with a lift and an '
              'intercom. Short-term rental of up to 11 months, with bed linen and towels.',
        'ca': 'Pis de {sup} m² a {zona}, amb 3 habitacions, bany i lavabo. Moblat i totalment equipat, amb aire '
              'condicionat, calefacció, wifi i balcó. Finca amb ascensor i interfon. Lloguer de curta estada de fins '
              'a 11 mesos, amb roba de llit i tovalloles.',
    },
    'locb-03': {
        'es': 'Piso amplio de {sup} m² en {zona}, en planta {planta} con ascensor, 4 habitaciones y un baño. Cocina '
              'equipada, aire acondicionado, calefacción y wifi de fibra. Balcón, vestidor y trastero. La finca tiene '
              'piscina, conserje e interfono.',
        'en': 'Spacious {sup} m² flat in {zona}, on floor {planta} with a lift, 4 bedrooms and one bathroom. '
              'Equipped kitchen, air conditioning, heating and fibre wifi. Balcony, dressing room and storage room. '
              'The building has a swimming pool, a concierge and an intercom.',
        'ca': 'Pis ampli de {sup} m² a {zona}, a la planta {planta} amb ascensor, 4 habitacions i un bany. Cuina '
              'equipada, aire condicionat, calefacció i wifi de fibra. Balcó, vestidor i traster. La finca disposa de '
              'piscina, consergeria i interfon.',
    },
}


def titulo(clave, **ctx):
    return TITULOS[clave].format(**ctx)


def descripciones(clave, rng, **ctx):
    """Spanish always; English with 70 % and Catalan with 40 % probability, like a real agency's partial translations."""
    textos = {'es': TEXTOS[clave]['es'].format(**ctx)}
    if rng.random() < 0.7:
        textos['en'] = TEXTOS[clave]['en'].format(**ctx)
    if rng.random() < 0.4:
        textos['ca'] = TEXTOS[clave]['ca'].format(**ctx)
    return textos
