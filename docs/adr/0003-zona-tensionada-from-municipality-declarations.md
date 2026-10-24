# ADR 0003: `zona_tensionada` comes from municipal declarations

- Status: Accepted (migration `0020`)
- Revises: ADR 0001 (`zona_tensionada` as a default-`False` column on `Inmueble`).

## Context

A stressed residential market ("zona de mercado residencial tensionado") is declared by the housing
administration for a territory under Llei 12/2023 (art. 18), after a public consultation. Declarations start,
end and are amended. A flag on each listing is manual, can go stale and can disagree between listings of the
same municipality.

## Decisions

- New private model `DeclaracionZonaTensionada`: `municipio`, `desde`, `hasta` (empty = in force),
  `referencia`. The scope is the municipality; declarations of part of a municipality are not modelled.
- `Inmueble.zona_tensionada` is no longer a column. It is a property: the municipality has a declaration in
  force today (`Municipio.es_zona_tensionada`). The detail response keeps the `zona_tensionada` key.
- Overlapping declarations of one municipality are allowed; only the pair (`municipio`, `desde`) is unique.
- The detail view prefetches the declarations, so the field costs one query.
- Migration `0020` creates an open declaration, dated on the migration day, for every municipality that had a
  flagged listing. The real start dates are unknown and must be corrected in the admin. The migration is
  reversible.
- No declarations are seeded: the lists found (131, 140, 271 municipalities) disagree and must be verified
  against the Generalitat housing portal and the DOGC first.

## Consequences

- Staff maintain declarations in one place instead of flagging each listing.
- The list endpoint still does not return `zona_tensionada`, as before.
