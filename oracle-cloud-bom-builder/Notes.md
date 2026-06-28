# Session Notes

Use this file to resume the Oracle Cloud BOM Builder work quickly in a future session.

## Current State

- Repository: `/Users/PWSTEPHE/codex/Codex-BOM-SKILL/oracle-cloud-bom-builder`
- Previous pushed commit before the monthly/annual totals and Autonomous test updates: `e7b6109 Align PAAS and customer environment layouts`

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
  - `Monthly Disc`
  - `Annual Disc`
  - `One-Time Disc`
- Recurring list-price columns show both monthly and annual totals. One-time service rows remain separate.
- Every environment should show a monthly recurring total and annual recurring total. Multi-environment workbooks should also show combined all-environment monthly and annual recurring totals.
- Generated colored headers and summary cells use bold white text, thin borders, whole-dollar currency formats, and emphasized subtotal rows for readability.
- Generated workbooks include a visible `System Summary` worksheet. It uses a vertical layout: each environment has its own heading, followed by `Description` and `Value` rows for configured-system characteristics.
- `scripts/build_bom_template.py` can optionally emit a Draw.io-compatible `.drawio` block diagram with `--diagram-output`.

## Current Generated Outputs

- `outputs/multi-env-standard-cc-prod-dr-oci-nonprod.xlsx`
  - Production: Standard C@C, 64 BYOL ECPUs.
  - Disaster Recovery: Standard C@C with 20% ECPU reduction, rounded from 51.2 to 52 BYOL ECPUs.
  - Non-Prod: OCI Dedicated Exadata X11M 64 BYOL ECPU BOM.
  - Optional paired diagram: `outputs/multi-env-standard-cc-prod-dr-oci-nonprod.drawio`.
- `outputs/StandardC@C.xlsx`
- `outputs/StandardC@C.drawio`
- `outputs/oci-dedicated-exadata-x11m-64-byol-ecpus.xlsx`
- `outputs/oci-dedicated-exadata-x11m-64-byol-ecpus.drawio`
- `outputs/prod-autonomous-dedicated-exadata-x11m-64-li-ecpus.xlsx`
- `outputs/prod-autonomous-dedicated-exadata-x11m-64-li-ecpus.drawio`
- `outputs/sample-oracle-cloud-bom.xlsx`
- `outputs/sample-oracle-cloud-bom.drawio`

## Source Inputs

- `inputs/multi-env-standard-cc-prod-dr-oci-nonprod.csv`
- `inputs/oci-dedicated-exadata-x11m-64-byol-ecpus.csv`
- `inputs/prod-autonomous-dedicated-exadata-x11m-64-li-ecpus.csv`
- `tmp/StandardC@C-b91390.csv`

## Pricing Rules Captured

- Treat the current authenticated/date-verified eSource PDF as the definitive price list when exact rows are available.
- Oracle pricing calculator / Cost Estimator exports are also authoritative for calculator-covered resources and are usually the fastest complete workflow source.
- Do not treat public pricing pages, old workbook price tabs, or prior extracted files as pricing authority.
- Explicit SKU additions, such as `B91390`, must be looked up by exact SKU in the verified price source.
- One-time service SKUs should not contribute to recurring monthly cost but should appear in one-time list/discount totals.
- Run `scripts/check_pricing_refresh.py` before finalizing BOMs that depend on calculator exports or eSource PDF rows. Provide `--current-esource-date` from the authenticated eSource PDF so the script can compare the live document date with cache metadata.

## Validation Commands

```bash
.venv/bin/python -m compileall scripts
.venv/bin/python scripts/check_pricing_refresh.py --input-csv inputs/multi-env-standard-cc-prod-dr-oci-nonprod.csv --current-esource-date "June 11, 2026"
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
- `scripts/validate_bom_workbook.py` now also checks the `System Summary` sheet, its vertical environment sections, and workbook registration for sheet 3.
- `scripts/check_pricing_refresh.py` is a preflight, not a live downloader. Human eSource authentication and live document-date reading still happen in the browser session.

## Completed Enhancements

- Improved workbook visual polish: borders, number formats, high-contrast headers, and subtotal emphasis.
- Added configured-system summary sheet for processor, memory, storage, and performance capacity.
- Added optional Draw.io-compatible block diagram output.
- Added pricing refresh preflight around calculator export and eSource date verification.

## Follow-Up Items

- Add BOM coverage tests/examples for Base Database Service.
- Add BOM coverage tests/examples for Exadata Database Service on Exascale Infrastructure.
- Review and correct any remaining workbook/source-policy issues after those service paths are added.
