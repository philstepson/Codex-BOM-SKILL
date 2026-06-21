# Oracle Estimator Workbook Reference

Use this reference when creating Oracle Cloud BOM Excel workbooks that should resemble an Oracle Cloud Cost Estimator export.

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

- `J`: `Discount %`
- `K`: `Discounted Monthly Cost`
- `L`: `Discounted Annual Cost`

Recommended behavior:

- Put one editable discount input above the table. The bundled builder uses `J3` for the `Discount %` label and `K3` for the editable discount value.
- Row-level `Discount %` cells should reference the single discount input, not require duplicate manual entries.
- `Discounted Monthly Cost` should equal the row's list `Monthly Cost` multiplied by `1 - discount`.
- `Discounted Annual Cost` should equal discounted monthly cost multiplied by `12`.
- Total rows should sum list monthly cost, discounted monthly cost, and discounted annual cost.

## Supplemental Pricing From Current PDF Sources

Use Oracle Cost Estimator pricing as the primary source. When an estimator row lacks needed SKU or price data, especially for Exadata Cloud@Customer database servers, storage servers, rack components, or related infrastructure, the BOM may use the current authenticated Oracle eSource PDF as a supplemental fallback.

Do not add persistent source-tracking columns for the supplemental PDF by default. Instead, keep the Oracle estimator columns unchanged and append a concise footnote to `Custom Note` for any row filled from the PDF. The note must identify Oracle eSource PDF pricing and include the document date from the PDF front page.

The supplemental PDF or extracted pricing table should not be committed into the skill repository. Use a temporary CSV during the build when script input is needed.

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

- Discount percent: `=$K$3`
- Discounted monthly cost: `=IF(G7="","",G7*(1-$K$3))`
- Discounted annual cost: `=IF(K7="","",K7*12)`

If calculating list monthly cost from quantities:

`=IF(OR(C7="",D7="",E7="",F7=""),"",C7*D7*E7*F7)`

## Formatting Guidance

- Currency cells should use USD currency formatting unless the user provides another currency.
- Discount cells should use percentage formatting.
- Freeze panes below the header row.
- Keep filters enabled on the BOM table.
- Use readable column widths; wrap long service descriptions and notes.
- Keep all user-entry fields unlocked/editable if workbook protection is used. By default, do not protect the workbook.

## Estimate Disclaimer

Include a concise note such as:

`Pricing is an estimate based on Oracle Cost Estimator or user-provided list-price inputs. It is not a formal Oracle quote. Validate pricing, terms, discounts, and availability with Oracle before procurement.`
