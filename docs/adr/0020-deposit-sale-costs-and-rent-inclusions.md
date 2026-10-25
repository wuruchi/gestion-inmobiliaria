# ADR 0020: Deposit months, sale costs and rent inclusions per offer

- Status: Accepted (migration `0045`)
- Source: step 3 of ADR 0019 (locb-01..03, atb-02, atb-03, idealista-03).
- Revises: ADR 0001 and ADR 0011 (the included-in-rent flags lived on `Inmueble`).

## Context

The pages show a deposit as a number of months (locb: 5.700 € for a 1.900 € rent, 2.327 € for 1.164 €), the sale costs
with an ITP rate and who pays the seller's agency fee (idealista-03), and what the rent includes (ATB: community fees,
insurance, IBI, wifi; locb: wifi, utilities excluded). `Condiciones` is shared text, and the two included-in-rent flags
sat on `Inmueble`, although a temporary and a habitual offer of one dwelling can include different things and a sale
includes none of it.

## Decisions

- **`InmuebleModalidad.fianza_meses`**: 1 to 12 months of rent, rental offers only (model `clean()` and `save()`, DB
  range check). The deposit is per offer, not per shared conditions record, because the same conditions serve
  listings with different deposits. The API returns `fianza_meses` and `fianza_total` (price x months, two decimals)
  in each entry of `modalidades[]` in the detail; both are `null` for a sale or when unset. With `tipo_iva` the amount is
  computed on the net `precio`. `Condiciones.fianza` stays as text for the details.
- **`Condiciones.itp_porcentaje`** (0-100, nullable) and **`honorarios_incluidos_en_precio`** (boolean, default
  `false`; the repository keeps booleans non-null): sale conditions only (model `clean()`/`save()`). A rental's ITP is
  a different tax with a different base (0.5% of the rent of the whole period), so it stays in the `itp` text. The
  reduced ITP rates (5%, 7%) also stay in the text; no total is computed.
- **`InclusionesAlquiler`**: one optional row per rental offer (one-to-one on `InmuebleModalidad`, CASCADE; sale
  rejected like `TerminosAlquiler`) with `gastos_comunidad`, `ibi`, `seguro`, `wifi` and `suministros`. A missing row means
  unknown. The detail returns `inclusiones` in each offer (`null` for a sale or without a row).
- **`Inmueble.gastos_comunidad_incluidos` and `ibi_incluido` are dropped.** The amounts `gtos_comunidad` and `ibi`
  stay on the listing. Migration `0045` copies a set flag to every rental offer of the listing; a listing with the flag
  but no rental offer loses it. The reverse sets the flag when any rental offer includes the item.
- **`Condiciones.incluido` / `no_incluido` stay as prose**; the flags are the structured version.
- **`RegulacionAlquiler.indice_referencia_min`** was already optional (the min <= max check skips an empty value), so a
  single index value (locb) needs no change; a test now covers it.

## Not done
VAT / AJD for new-build sales: no example page shows it. It waits for the agency to confirm the rule.

## Consequences
- The API breaks: `ibi_incluido` and `gastos_comunidad_incluidos` leave the top level; `modalidades[]` gains
  `fianza_meses`, `fianza_total` and `inclusiones`; the conditions gain `itp_porcentaje` and
  `honorarios_incluidos_en_precio`.
- The atb-02 and atb-03 fixtures now use `InclusionesAlquiler`.
- A deposit is not validated against the legal limits (for example the regional rules on deposits); that needs a lawyer.
