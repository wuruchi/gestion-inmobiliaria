# ADR 0021: Additive fields from the Locabarcelona pages, and what was left out

- Status: Accepted (migration `0046`)
- Source: step 4 of ADR 0019, after checking each candidate field against the existing models.

## Context

The Locabarcelona pages list amenities and features that some tables lacked. Before adding anything, each item was
checked against every model, because several facts already have a home (the energy certificate has its own table, the
included wifi is in `InclusionesAlquiler`, tumble dryer, clothes line, fan, A/C and towels already exist).

## Added

| Field | Where | Evidence | Rule |
|---|---|---|---|
| `aseos` (half-baths) | `Distribucion` | locb "Half-bathroom"; ATB "Baños / Aseos" | A count like `banios`; empty is unknown; not added to the bathrooms |
| `patio`, `porche` | `OtrosEspacios` | locb "Patio"; idealista-01 "porche trasero" | Flags (ADR 0010: presence matters, not the number) |
| `internet_velocidad_mbps` | `Instalaciones` | locb-03 "Fiber 300MB" | Above 0 and only with `internet` (DB + `clean()`), like `Entorno.jardin_m2` |
| `cafetera`, `plancha`, `kit_limpieza`, `secador_pelo`, `papel_higienico`, `sofa_cama` | `Dotacion` | locb short-let list | Flags; `sofas` stays a count of sofas |
| `acepta_fumadores` | `TerminosAlquiler` | locb "Smoking accepted" | Yes/no like `acepta_animales` |
| `uso_temporada` | `TerminosAlquiler` | ATB "uso distinto de vivienda (vacaciones/ocio)" and the "justificante de temporalidad" | Closed list; accepted only on a `temporal` offer |
| `piscina`, `detalles` | `ImageInmueble.TIPOS` | idealista-01 photo tags | |
| `fr`, `it` | `DescripcionInmueble.IDIOMAS` | The Locabarcelona site languages | The evidence is the site's language switcher, not translated listing text |

## Checked and left out

- **`CertificadoEnergetico.estado`** (in process / exempt). The examples do not need it: locb-03 has a rating with no
  number, which the existing fields express, and the idealista pages show consumption with no letter. An "in process"
  certificate would collide with "a row with nothing in it". Revisit when a real listing needs it.
- **Photo tag `entrada`**: no example uses it.
- **A level above "buen estado" in `conservacion`** (locb "perfect condition"): it maps to `buen_estado` or `reformado`.
- **Internet type (fibre)**: only the speed is stored.
- **Wifi included in the rent**: already `InclusionesAlquiler.wifi` (ADR 0020), not an equipment flag.
- **"Cooktop"** (locb): no field; every listing with a kitchen has one.

## Consequences
- The API gains the keys above; no key is removed.
- The Locabarcelona fixtures (`Locb01Test` to `Locb03Test`) exercise all of them, plus the agency, the NRU in process,
  the deposit months and the single index value of the earlier steps.
- `uso_temporada` hard-codes the modalidad code `temporal`, as `comprobar_regulacion_alquiler` does for `habitual`.
