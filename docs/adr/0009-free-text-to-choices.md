# ADR 0009: free-text columns with a closed vocabulary become choices

- Status: Accepted (migration `0028`)

## Context

Several columns were `CharField(max_length=150)` although the answer comes from a short list. Staff could type
"Sur", "sur" and "south", filters and counts failed, nothing was validated, and the label and the stored value were
the same string, so they could not be translated.

## Decisions

- Choices on the model (same approach as `Inmueble.conservacion`), lowercase `snake_case` values, `blank=True`, and
  `max_length=20`. No lookup tables: the lists change rarely, and a new value is one line plus a no-op migration.
- Lists (drafted from the example listings, to be reviewed with the agency):
  - Floor material, shared by `Otros.suelo_piso`, `Banios.suelo` and `Estancias.suelo_cocina`: parquet, tarima, gres,
    baldosa, terrazo, marmol, microcemento, hidraulico, otro (`models/opciones.py`).
  - Carpentry material, shared by `carpinteria_interior` and `carpinteria_exterior`: madera, aluminio, pvc, hierro, otro.
  - `Otros.tipo_fachada`: ladrillo, piedra, hormigon, revoco, cristal, otro.
  - `Estancias.tipo_cocina`: independiente, americana, abierta, office, otro.
  - `Inmueble.situacion_actual`: libre, ocupado, alquilado, alquiler_vacacional, otro.
- `Otros.orientacion` is replaced by `orientacion_norte`, `_sur`, `_este` and `_oeste` (booleans). The examples hold
  several directions ("norte, sur"), so a single choice would lose data. This is a fixed set of four, not an open
  repeating group.
- `Otros.office` is dropped (migration `0029`). The examples use "office" only as a kitchen type, which is the
  `office` value of `tipo_cocina`, so the column duplicated it. Migration `0028` had first turned it into a boolean.
- `usos` stays free text: it is prose, not a category.
- The migration maps known text (ignoring case, accents and spaces) to the value. Other text becomes `otro`
  (so detail such as "Pizarra" is lost), and a corner such as "SE" sets both of its flags. It is reversible, and
  the reverse writes the labels back.

## Consequences

- The API returns lowercase values (`terrazo`, `alquiler_vacacional`) instead of the typed text, and
  `otros.orientacion` is gone in favour of the four flags. This is a breaking change, accepted while the contract
  is being redesigned.
- The admin shows dropdowns, and `full_clean` rejects values outside the list.

## Addendum: lists widened (migration `0042`)

The lists above came from six example listings. Without the agency's own terms yet, they were widened with common
market values (not confirmed by the agency; review them before relying on them):

- `Inmueble.tipo`: terreno, trastero, edificio, nave (before `otro`).
- `Inmueble.subtipo`: loft, planta_baja, chalet_pareado, casa_pueblo, masia.
- `Inmueble.conservacion`: reformado.
- Floor material: laminado, vinilico, ceramica, moqueta, cemento_pulido.
- `Caracteristicas.tipo_fachada`: madera, metalica.
- `Instalaciones.subtipo_calefaccion`: butano_propano, solar.

Adding a value is one line plus a migration that changes no data. Renaming or removing one needs a data migration.
`subtipo` still applies only to `vivienda`.
