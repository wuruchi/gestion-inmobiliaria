# ADR 0010: an equipment item is a count only when the number matters

- Status: Accepted (migration `0030`)

## Context

`Dotacion` and `OtrosEspacios` mixed `PositiveIntegerField` counts and `BooleanField` flags with no rule. Items that
can only be 0 or 1 in practice (a jacuzzi, a wine cellar) were counts, which allowed "3 jacuzzis", made "has it"
a different test per column (`lavadora > 0` vs `vajilla = true`), and gave clients 1 next to true.

## Decision

An item is a **count** only if two are plausible and the quantity matters to a tenant or buyer. Otherwise it is a
**flag** (`BooleanField`). The equipment catalogue (a row per item) was considered and left out: the item list is
stable and the wide tables keep their per-column types.

- `Dotacion` flags: `jacuzzi_hidromasaje`, `secadora`, `lavadora`, `lavavajillas`, `microondas`, `nevera`, `radio`,
  `toldo`, `horno`, `tendedero` (plus the existing `amueblado`, `utensilios_cocina`, `vajilla`, `cuberteria`,
  `cristaleria`, `ropa_cama`, `toallas`).
- `Dotacion` counts: `armarios_empotrados`, `ropero`, `estufa`, `ventilador`, `camas`, `sofas`.
- `OtrosEspacios` flags: `altillo`, `galeria`, `buhardilla`, `bodega`, `lavadero`.
- `OtrosEspacios` counts: `despachos`, `vestidores`, `trastero`, `estudios`, `bibliotecas`.
- `Instalaciones` (`tvs`, `ascensor`) and `Estancias` (`n_terrazas`, `n_balcones`, renamed in ADR 0014) already follow the rule.
- The lists were drafted without the agency's input; moving an item between the groups is a one-line change plus
  a conversion in a migration.

## Consequences

- Migration `0030` clamps any count above 1 to 1 and then converts the column to a boolean (so a 3 becomes true).
  Reversing gives 0 and 1 back; the original numbers above 1 are not recoverable.
- The API returns `true`/`false` for the flag items instead of 0/1.
- A test classifies every count and flag column of the two tables, so a new column fails until it is placed.
