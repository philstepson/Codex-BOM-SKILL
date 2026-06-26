# Oracle Estimator Workbook Reference

Use this reference when creating Oracle Cloud BOM Excel workbooks that should resemble an Oracle Cloud Cost Estimator export.

For the preferred classic multi-environment proposal format, also read `references/classic-excel-bom-layout.md`. The Oracle estimator-style layout remains useful for deterministic starter BOMs and calculator/export transposition; the classic workbook layout is the better target when the user needs multiple environments, current-state inventory, usage history, ramping, discount comparison, or TCO presentation in one workbook.

The required customer-delivery view for proposal workbooks is a visible customer-facing BOM that lists all SKUs, quantities, and list prices. Hidden support sheets from a legacy workbook are optional unless the user asks for them.

## Observed Source Template

Sample asset: `assets/oracle-cost-estimator-sample.xlsx`

Observed workbook:

- One visible worksheet named `PAAS`.
- Used range: `A1:I16`.
- Header and metadata rows:
  - `A1`: `Oracle Investment Proposal (as of MM/DD/YYYY)`
  - `A2`: `Reference label: My Estimate`
  - `A3`: `Currency: USD`
  - `A4`: `Realm: PUBLIC`
  - `A5`: `Service Type: PAAS`
- Table header row at row 6:
  - `A`: `Part`
  - `B`: `Description`
  - `C`: `Part Qty`
  - `D`: `Instance Qty`
  - `E`: `Usage Qty`
  - `F`: `Unit Price`
  - `G`: `Monthly Cost`
  - `H`: `Custom Label`
  - `I`: `Custom Note`
- Service grouping rows may have a blank part number and a description only.
- Monthly total row appears below the line items with `Monthly Total` in column `B` and total monthly list cost in column `G`.
- Disclaimer text appears below the table.

## Required BOM Enhancements

Add discount support without removing the Oracle estimator columns.

Recommended columns:

- `I`: `Discount %`
- `J`: `Discounted Monthly Cost`
- `K`: `Discounted Annual Cost`
- `L`: `Custom Note`

Recommended behavior:

- Put one editable discount input above the table. The bundled builder uses `J3` for the `Discount %` label and `K3` for the editable discount value.
- Row-level `Discount %` cells should reference the single discount input, not require duplicate manual entries.
- The discount input should accept both whole-number percentages and decimal percentages. Treat values greater than `1` as whole-number percentages, so `15` and `0.15` both mean 15%.
- `Discounted Monthly Cost` should equal the row's list `Monthly Cost` multiplied by `1 - discount`.
- `Discounted Annual Cost` should equal discounted monthly cost multiplied by `12`.
- Total rows should sum list monthly cost, discounted monthly cost, and discounted annual cost.
- Keep `Custom Note` as the rightmost table column so long source notes do not interrupt the numeric estimate columns.
- Generated formula cells should include cached values for the default discount, and `xl/workbook.xml` should force automatic recalculation on open with `calcMode="auto"`, `fullCalcOnLoad="1"`, and `forceFullCalc="1"`.

## Supplemental Pricing From Current PDF Sources

Use Oracle Cost Estimator or Oracle pricing calculator output as the primary source. Check calculator coverage before using eSource for any BOM that is not clearly Exadata Cloud@Customer. For standard Exadata Dedicated Infrastructure and Database@Azure, Database@Google Cloud, or Database@AWS, the calculator output is the source of truth for SKU rows, quantities, unit prices, and monthly costs. Transpose those rows into the BOM and add discount/formula columns without changing the calculator price fields.

Database@Azure, Database@Google Cloud, and Database@AWS use Exadata Dedicated Cloud pricing, not Exadata Cloud@Customer pricing. The default calculator configuration is a quarter rack with 2 database servers and 3 storage servers unless the user or calculator configuration says otherwise.

When an estimator row lacks needed SKU or price data, especially for Exadata Cloud@Customer database servers, storage servers, rack components, or related infrastructure, the BOM may use the current authenticated Oracle eSource PDF as a supplemental fallback. Ask the user to authenticate to eSource only after the calculator path is unavailable or incomplete, or when the request is Exadata Cloud@Customer.

When the user explicitly asks to add a SKU, treat that SKU as an intentional workbook row even if it is not a normal calculator-generated product row. Search the verified current eSource price-list PDF by exact SKU before attempting description matching. Use the exact price-list description and price fields for the row, and include the billing basis and document date in `Custom Note`. For example, `B91390` may be requested as `Gen 2 Exadata Cloud at Customer Installation and Activation Service`; if that SKU is not present in the calculator output, it should be resolved from the current or date-verified cached price-list PDF rather than inferred from the service description.

For one-time or non-metered service SKUs, keep the billing basis visible in `Custom Note`. If the user wants the service included in the annual estimate but not recurring monthly cost, leave `Monthly Cost` blank and calculate `Discounted Annual Cost` once from quantity and unit price. This is the current behavior for `B91390` in the Standard C@C output.

Do not add persistent source-tracking columns for the supplemental PDF by default. Instead, keep the Oracle estimator columns unchanged and append a concise footnote to `Custom Note` for any row filled from the PDF. The note must identify Oracle eSource PDF pricing and include the document date from the PDF front page.

A local supplemental PDF cache may be maintained, but it must be date-checked against the eSource URL before each pricing run. Replace the cached PDF when the eSource document date is newer. The extracted pricing table should remain a temporary runtime CSV and should not be treated as authoritative across runs.

## Exadata Cloud@Customer X11M Sample Baseline

The bundled sample BOM should model an Exadata Database Service on Cloud@Customer X11M single-rack baseline unless the user supplies another configuration:

- 1 rack.
- 2 database servers, because each rack should be modeled as prepopulated with 2 database servers.
- 3 storage servers, because that is the minimum for High redundancy.
- High redundancy by default unless Normal redundancy is explicitly specified.
- License model marked as TBD when the user has not chosen License Included or Bring Your Own License.

Leave SKU and price fields blank when current pricing has not been supplied or extracted from an approved source. The sample should preserve editable Oracle estimator fields and use `Custom Note` to make the rack, redundancy, and licensing assumptions visible.

## Current Generated BOM Patterns

The repo currently contains two generated BOM patterns:

- `outputs/StandardC@C.xlsx`: Cloud@Customer X11M Base rack output generated from `tmp/StandardC@C-b91390.csv`. It includes `B110634` Base System Rack, `B110647` High Capacity storage servers, `B110663` BYOL ECPU runtime, and `B91390` one-time installation and activation. The installation row is excluded from recurring monthly totals and included once in discounted annual cost.
- `outputs/oci-dedicated-exadata-x11m-64-byol-ecpus.xlsx`: OCI Dedicated Exadata X11M output generated from `inputs/oci-dedicated-exadata-x11m-64-byol-ecpus.csv`. It preserves calculator-backed rows for 2 database servers, 3 storage servers, and 64 BYOL ECPUs.

## Default Sheet Design

Prefer one of these layouts:

1. Single-sheet layout:
   - Keep metadata rows at the top.
   - Add `Discount %` input near the top right, preferably `J3:K3`.
   - Extend the table to columns `J:L`.
   - Add totals for list monthly, discounted monthly, and discounted annual.

2. Two-sheet layout:
   - `Summary`: discount input, list monthly total, discount amount, net monthly total, net annual total, assumptions.
   - `PAAS`: Oracle estimator-style detail table with discount formulas.

Use the single-sheet layout when the user asks to stay close to the Oracle estimator export. Use the two-sheet layout when the BOM contains multiple services, multiple categories, or architecture assumptions.

## Formula Guidance

Use formulas rather than hardcoded discounted outputs.

Assuming:

- Monthly cost is in `G`.
- Discount input is in `K3` on the primary service sheet.
- First data row is row `7`.

Example formulas:

- Discount percent: `=IF($K$3>1,$K$3/100,$K$3)`
- Discounted monthly cost: `=IF(G7="","",G7*(1-IF($K$3>1,$K$3/100,$K$3)))`
- Discounted annual cost: `=IF(J7="","",J7*12)`

If calculating list monthly cost from quantities:

`=IF(OR(C7="",D7="",E7="",F7=""),"",C7*D7*E7*F7)`

For one-time service SKUs that should be added to the annual estimate but not recurring monthly cost, leave `Monthly Cost` blank and calculate `Discounted Annual Cost` once from quantity and unit price:

`=IF(OR(C7="",D7="",F7=""),"",C7*D7*F7*(1-IF($K$3>1,$K$3/100,$K$3)))`

## Calculation Cache

The workbook builder should write cached values into formula cells for row-level discounted monthly cost, row-level discounted annual cost, monthly total, discounted monthly total, and discounted annual total. These cached values are based on the initial discount supplied to the builder.

The workbook should also force recalculation on open. In `xl/workbook.xml`, `calcPr` should be:

```xml
<calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/>
```

Do not include a stale `xl/calcChain.xml` from the template after replacing worksheet formulas.

## Legacy Workbook Pricing Warning

When a user supplies a sample or classic Excel BOM, treat the workbook's embedded price-list sheets as potentially stale. Use the workbook to learn preferred layout, formulas, environment organization, and proposal workflow. For current pricing, refresh from the Oracle pricing calculator, Cost Estimator export, or verified current eSource PDF according to the pricing rules above.

## Formatting Guidance

- `Monthly Cost`, `Discounted Monthly Cost`, and `Discounted Annual Cost` should use whole-dollar currency formatting with comma separators, such as `$19,858`.
- Keep `Unit Price` unrounded unless the source already supplies a rounded value, because hourly rates may need precision such as `0.0807`.
- Discount cells should use percentage formatting.
- Freeze panes below the header row.
- Keep filters enabled on the BOM table.
- Use readable column widths; wrap long service descriptions and notes.
- Keep all user-entry fields unlocked/editable if workbook protection is used. By default, do not protect the workbook.

## Estimate Disclaimer

Include a concise note such as:

`Pricing is an estimate based on Oracle Cost Estimator or user-provided list-price inputs. It is not a formal Oracle quote. Validate pricing, terms, discounts, and availability with Oracle before procurement.`
