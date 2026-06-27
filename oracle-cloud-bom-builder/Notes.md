# Session Notes

Use this file to resume the Oracle Cloud BOM Builder work quickly in a future session.

## Current State

- Repository: `/Users/PWSTEPHE/codex/Codex-BOM-SKILL/oracle-cloud-bom-builder`
- Latest pushed commit at the time of this note: `e7b6109 Align PAAS and customer environment layouts`
- `resume.txt` is untracked and has been intentionally left untouched.

## Current Workbook Direction

- The preferred customer-facing format is the classic multi-environment BOM style:
  - One row per unique SKU or priced line item.
  - Separate grouped column blocks per environment.
  - Blank cells when a SKU does not apply to an environment.
  - Environment summary rows below the SKU rows.
  - Final all-environment total columns.
- `Customer BOM` is the default active sheet when generated workbooks open.
- `Customer BOM` is list-price-only and intentionally omits verbose source notes and discount columns.
- `PAAS` is the internal working sheet using the same wide environment-block layout, with discount columns:
  - `Disc Price`
  - `One-Time Disc`
- Recurring list-price columns are annualized. One-time service rows remain separate.

## Current Generated Outputs

- `outputs/multi-env-standard-cc-prod-dr-oci-nonprod.xlsx`
  - Production: Standard C@C, 64 BYOL ECPUs.
  - Disaster Recovery: Standard C@C with 20% ECPU reduction, rounded from 51.2 to 52 BYOL ECPUs.
  - Non-Prod: OCI Dedicated Exadata X11M 64 BYOL ECPU BOM.
- `outputs/StandardC@C.xlsx`
- `outputs/oci-dedicated-exadata-x11m-64-byol-ecpus.xlsx`
- `outputs/sample-oracle-cloud-bom.xlsx`

## Source Inputs

- `inputs/multi-env-standard-cc-prod-dr-oci-nonprod.csv`
- `inputs/oci-dedicated-exadata-x11m-64-byol-ecpus.csv`
- `tmp/StandardC@C-b91390.csv`

## Pricing Rules Captured

- Use Oracle pricing calculator / Cost Estimator rows first for standard OCI Dedicated Exadata and Database@ platforms.
- Use current/date-verified eSource PDF only for Cloud@Customer gaps or explicit price-list-only SKUs.
- Explicit SKU additions, such as `B91390`, must be looked up by exact SKU in the verified price source.
- One-time service SKUs should not contribute to recurring monthly cost but should appear in one-time list/discount totals.

## Validation Commands

```bash
.venv/bin/python -m compileall scripts
.venv/bin/python scripts/validate_bom_workbook.py outputs/multi-env-standard-cc-prod-dr-oci-nonprod.xlsx
.venv/bin/python scripts/validate_bom_workbook.py outputs/sample-oracle-cloud-bom.xlsx
.venv/bin/python scripts/validate_bom_workbook.py outputs/StandardC@C.xlsx
.venv/bin/python scripts/validate_bom_workbook.py outputs/oci-dedicated-exadata-x11m-64-byol-ecpus.xlsx
```

## Important Implementation Notes

- `scripts/build_bom_template.py` is still standard-library-only and writes workbook XML directly.
- Excel is strict about worksheet XML order. Keep `<autoFilter>` before `<mergeCells>` and before `<pageMargins>`.
- `scripts/validate_bom_workbook.py` checks this ordering because Excel previously repaired `sheet2.xml` when the order was wrong.
- `workbook.xml` sets `Customer BOM` as the active tab.
- The generated styles include custom fills for environment block headers.

## Possible Next Enhancements

- Improve workbook visual polish further: borders, number formats, and subtotal emphasis.
- Add a configured-system summary sheet for processor, memory, storage, and performance capacity.
- Add optional Draw.io-compatible block diagram output.
- Add current pricing refresh automation around calculator export and eSource date verification.
