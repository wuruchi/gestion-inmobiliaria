# ADR 0016: Consistency scans run by hand for now

- Status: Accepted (deferred; revisit before the first real deployment)

## Context

The backend has read-only scan commands. Each lists the offenders and exits with an error if it finds any:

- `comprobar_ubicaciones`: municipio, distrito and barrio that do not nest (ADR 0006).
- `comprobar_condiciones`: conditions of another modalidad on an offer (ADR 0012).
- `comprobar_regulacion_alquiler`: published, open habitual-rent offers in a stressed zone without the reference index
  or the last-rent data (ADR 0007).

`purgar_solicitudes` is a retention task, not a scan, and also needs a schedule.

The first two only catch rows written outside the model (bulk imports, `update()`, SQL). The third depends on the
date: a listing can become non-compliant with no edit when a declaration starts or ends or when the last contract
passes five years.

## Decision

Nothing runs the scans automatically yet, and publishing is not blocked or warned about. They are run by hand: after a
bulk import, after loading or changing stressed-zone declarations, and before relying on the rent-regulation data.
`python seed.py locations` already runs the location scan. The project is at an early stage, there is no deployment
to schedule on, and the rent-regulation scope is itself still to be verified against the law.

## Options considered for later

- A. Run all the scans, and `purgar_solicitudes`, from a scheduler (cron or the platform's jobs), daily, alerting on a
  non-zero exit. A single `comprobar_todo` command would make this simpler.
- B. Check at publication: the admin warns, or blocks, when `publicar_web` is set on an out-of-compliance offer.
- C. Both. Recommended: A as a safety net, and B as a warning only, because the agency may need to publish while it
  gathers the data.

## Consequences

- Until then, a listing in a stressed zone can stay published without the legally required rent data and nothing
  reports it.
- `purgar_solicitudes` does not run either, so personal data in reservation requests is not blanked after 12 months
  unless someone runs it. This matters for data-protection compliance once real requests arrive.
