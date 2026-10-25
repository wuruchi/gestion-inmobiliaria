# ADR 0007: Rent regulation data is declared per rental offer

- Status: Accepted (migration `0024`)
- Revises: ADR 0001 (rent-regulation columns on `Inmueble`) and ADR 0005 (`ultima_renta` derived from the price log).

## Context

Official Generalitat pages (Consum, Habitatge) say an ad, offer and contract for a habitual-residence lease in a
stressed zone must show the maximum price from the state reference index (SERPAVI, a lower and an upper value), the
rent of the last contract of the last five years, whether the owner is a large holder, the purpose of the lease and
(as a general contract term) the rent-update clause. The legal texts were not read; see the open item in `TODO.md`.

Deriving the last rent from `HistorialPrecio` (ADR 0005) was wrong: the log holds our own asking prices, a property
rented through another agency has no log here, and "no history" would read as "no previous rent".

## Decisions

- New model `RegulacionAlquiler`, one-to-one with a rental `InmuebleModalidad` (monthly price; a sale offer cannot
  have one): `indice_referencia_min/max`, `indice_referencia_fecha`, `renta_previa`, `ultima_renta`,
  `ultima_renta_fin`. Public in the detail as `modalidades[].regulacion` (`null` for sales; a rental without a
  record reads as `renta_previa: "desconocida"`).
- `renta_previa` has three states: `desconocida` (default), `con_renta`, `sin_renta`. The amount and end date exist
  exactly when it is `con_renta` (DB constraint + model). The end date is optional.
- It replaces `Inmueble.indice_referencia_min/max`, `Inmueble.situacion_5_anios` (free text) and the derived
  `ultima_renta`. `Inmueble.actualizacion_renta` becomes `Condiciones.actualizacion_renta`, a contract term; the
  seed's rent defaults include it.
- `HistorialPrecio` stays as a private log of our prices and no longer reaches the API.
- `python manage.py comprobar_regulacion_alquiler` lists published, open `habitual` offers in a stressed zone whose
  last-rent status is unconfirmed, whose contract has no end date or ended more than five years ago, or that lack
  the index maximum, and fails if there are any. Only the `habitual` modalidad is checked: a temporary lease whose
  purpose is not justified is treated as habitual by the law, which a script cannot tell.
- Migration `0024` copies the index range of a listing to its monthly offers, turns the last rent that migration
  `0022` had put in the log into `con_renta` (end date unknown) and removes that helper row, and does not migrate
  `situacion_5_anios` or `actualizacion_renta`. It is reversible for the index range.

## Consequences

- `ultima_renta` moved again: from a top-level field, to a field of each offer (ADR 0005), to
  `modalidades[].regulacion.ultima_renta`.
- Staff must enter the regulation data by hand (admin: the offer's own page); the command shows what is missing.
- Index values are as consulted on `indice_referencia_fecha`; they are not refreshed automatically.

## Legal scope: not verified, deliberately left as it is (added 2026-10-25)

The scope of `comprobar_regulacion_alquiler` was never checked against the legal texts (Llei 12/2023, Decret llei
1/2025 and the Catalan law on seasonal and room rentals approved by the Parlament on 18 December 2025). Press and
official summaries suggest it is probably too narrow:

- Seasonal (`de temporada`) and room rentals appear to fall under the same price limits when their purpose is not
  tourist, recreational or holiday use. The purpose of the contract, not its length, decides. The scan only looks at
  `habitual` offers, so a `temporal` offer that the law treats as habitual is not checked.
- The model has no field for the purpose of a temporary lease, so the system cannot tell which temporary offers are
  covered. Room rentals have no modalidad.
- Municipalities in stressed zones may ban seasonal lets; this is not modelled.
- What an advert exactly must show, and how the five-year window is counted, were taken from the Generalitat's
  summary pages and not from the texts. The sources found did not agree on how the three rules relate.

Decision: keep the scan as it is and do not extend it. Settling the scope needs a lawyer, and guessing would only
change one set of wrong alerts for another. For now the alerts are a work aid for the `habitual` offers, not proof of
compliance: a clean result does not mean an ad is compliant, and a flagged offer is not necessarily non-compliant.
Revisit in a later phase, with legal advice; the questions to ask are the list above, plus a purpose field for
temporary leases.
