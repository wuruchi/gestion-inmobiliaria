# ADR 0019: Gaps found in the platform examples (agency, NRUA, unknown, deposit, sale costs)

- Status: Accepted. Steps 1 (agency, NRUA; migration `0043`) 2 (unknown is not "no", hidden coordinates; migration `0044`) and 3 (money fields; ADR 0020, migration `0045`) are implemented; the rest is planned in `TODO.md`, section 8.
- Source: a second pass over the saved pages in `../gestion-inmobiliaria-examples` (atb-01..03, idealista-01..03,
  locb-01..03). The Locabarcelona pages had not been compared before.
- Revises: ADR 0001 (registry numbers, agency out of scope), ADR 0003 (`zona_tensionada` is a plain boolean) and
  ADR 0002 (`gran_tenedor` is a plain boolean) once step 2 lands.

## Context

The same agency number appears on every listing of an agency: AICAT 5205 on all three ATBarcelona pages, 11525 on all
three Locabarcelona pages, 3366 on the GrupLiving page; the API number (A13529, A10580) is also the agency's.
`RegistroLegal` stored the AICAT per listing, so one agency fact was repeated on every row. The pages also show an
NRA/NRUA number (atb-03), an NRU that is "in process" (locb-02), and statements ("the owner is not a large owner")
for which the model has no evidence.

## Decisions

### Step 1: implemented
- **`Agencia`** holds `nombre`, `aicat`, `numero_api` and contact data. `Inmueble.agencia` is optional and `PROTECT`:
  an agency in use cannot be deleted. Filled registry numbers are unique; empty means not recorded. The public detail
  returns `agencia: {nombre, aicat, numero_api}` (`null` without one); address, phone and e-mail stay private until
  the frontend needs them.
- **`aicat` is no longer a `RegistroLegal` type.** Migration `0043` turns each AICAT row into an `Agencia` (named
  `AICAT <number>` until staff rename it) linked to the listing, then deletes the row. It is reversible.
- **`RegistroLegal` gains the type `nrua`** and an `estado`: `vigente` (default), `en_tramite` (applied for, no number
  yet) or `no_aplica` (exempt). A registry that is not `vigente` cannot carry a number (DB). An empty number with
  `vigente` still means "has it, the advert does not publish it" (ADR 0001, idealista-03 tourist licence).

### Step 2: implemented
- **Unknown is not "no"**: `gran_tenedor` is `null` when the listing has no owner rows (with owners it is `true` if any
  is a large holder, else `false`). `zona_tensionada` is `true` with a declaration in force, `false` when the
  municipality's declarations are loaded and none applies, and `null` otherwise. A declaration in force wins over a
  missing flag.
- **`Municipio.declaraciones_cargadas`** (default `false`) records that the declarations are loaded. The seed command
  sets it for every loaded municipio of Catalonia, because its list covers all of Catalonia; municipios elsewhere stay
  unknown until staff mark them. Migration `0044` marks the municipios that already have a declaration. The caveat of
  ADR 0015 holds: the 2026 changes are not loaded, so "false" means "not stressed in the loaded data".
- **`comprobar_regulacion_alquiler`** also reports `zona_tensionada_desconocida`: a published, open `habitual` offer
  whose municipality has no declarations loaded cannot be checked.
- **Hidden address hides the point too**: with `ocultar_direccion` the detail snaps `geo_latitude` and `geo_longitude`
  to the centre of a 0.005° grid cell (about 550 m); the exact point is never sent. Stored coordinates are untouched,
  and the postal code is still returned.

### Planned (see TODO section 8)
- (Step 3 is done, see ADR 0020: deposit months, ITP rate and seller's fee, per-offer inclusions. VAT/AJD for new builds
  waits for confirmation.)
- **Small additive fields**: half-baths, patio, porch, internet speed, short-let amenities, smoking policy, purpose of
  a seasonal lease, energy-certificate status, three photo tags, `fr` and `it` descriptions.
- **Scans, after legal review**: NRUA on temporal offers, stay limits per modalidad, rent above the index maximum,
  sale-cost completeness, surface per bedroom.

## Decided out of scope
Nightly price unit and a vacation modalidad, rooms, renaming modalidades (`habitual` is the long-term modalidad),
urbanización as a location level, building/unit links between listings, price tiers by duration or season,
availability wording (computed from the date), and price-drop alerts. Site features (favourites, sharing, PDF sheet,
mortgage calculators, statistics, machine translations) stay out as in ADR 0001.

## Consequences
- The API breaks once more: `aicat` is gone from `registros_legales`; `agencia` and `registros_legales[].estado` are new;
  `gran_tenedor` and `zona_tensionada` can be `null`; hidden listings return snapped coordinates.
- Staff must create the agencies and link each listing; a listing without agency shows no AICAT.
- The fixtures for atb-01 and idealista-03 now use `Agencia`; atb-03 carries its NRUA.
