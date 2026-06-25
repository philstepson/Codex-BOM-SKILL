---
name: oracle-cloud-bom-builder
description: Use this skill when a user asks for an Oracle Cloud BOM, Oracle Cloud Bill of Material, Oracle pricing workbook, Oracle cost-estimator output, OCI bill of materials, or an Excel spreadsheet for Oracle Cloud architecture configuration. Trigger on mentions of BOM, Bill of Material, Oracle pricing, Oracle Cloud pricing, Oracle Cost Estimator, OCI pricing, or named OCI services when the requested output is a spreadsheet or bill of material.
---

# Oracle Cloud BOM Builder

Use this skill to create a new Excel BOM workbook for Oracle Cloud architecture configurations from Oracle Cost Estimator-style product SKUs, quantities, usage quantities, and list-price outputs.

## Core Workflow

1. Gather inputs from the user or source file:
   - Oracle part/SKU numbers when available.
   - Service descriptions.
   - Part quantity, instance quantity, usage quantity, unit price, and monthly cost.
   - Service type, usually `PAAS`, unless the user provides another Oracle service category.
   - Any named OCI services, custom labels, notes, architecture assumptions, and region/currency details.
   - Supplemental pricing source details when calculator data is incomplete, especially the current Oracle eSource PDF URL and the document date shown on the PDF front page.
2. Decide pricing source before extracting rows. Try Oracle pricing calculator or Oracle Cost Estimator coverage first for any BOM that is not clearly Exadata Cloud@Customer. For standard Exadata Dedicated Infrastructure, Database@Azure, Database@Google Cloud, Database@AWS, and most OCI services, use calculator output as the source of truth for SKU rows, quantities, unit prices, and monthly costs. Transpose those rows into the BOM format without changing the calculator price fields.
3. If the architecture is described but estimator inputs are missing, read `references/requirements-gathering.md` and ask the smallest useful set of sizing questions for the named services.
4. Prompt for any parameter required for a valid configuration when it is missing. For Exadata requests this includes platform, license model, Exadata generation/model when not defaulting to latest, ECPU quantity, database server count, storage server count, and any additional database or storage servers beyond the calculator default.
5. Create a new `.xlsx` workbook using the Oracle Cost Estimator format as the base layout.
6. Keep the original Oracle list-price fields intact and editable.
7. Add a single editable discount percentage input that applies to all final list-price values. The input must tolerate whole-number percentages such as `15` and decimal percentages such as `0.15`.
8. Add formula-driven discounted totals; do not hardcode values that should update when the discount changes.
9. Preserve source assumptions and add clear notes that prices are estimates unless the user provides formal quote data.
10. Use eSource only after the calculator path is unavailable or incomplete, or when the request is Exadata Cloud@Customer. Ask the user to authenticate to eSource when needed, then verify the managed Oracle eSource price-list PDF cache before extracting supplemental prices. Read `references/esource-price-list-cache.md` before using cached PDF pricing.
11. Verify the workbook formulas and formatting before delivering the final `.xlsx`.

## Workbook Format

Read `references/oracle-estimator-workbook.md` before building or modifying a BOM workbook.

Use `assets/oracle-cost-estimator-sample.xlsx` as a format reference when a user asks to match the Oracle online pricing estimator export.

Use `scripts/build_bom_template.py` when a deterministic starter workbook is appropriate. It can build from its embedded sample data or from a CSV with Oracle estimator headers.

After generating a workbook with the script, run `scripts/validate_bom_workbook.py` against the output before delivering it.

The default workbook should include:

- A primary `PAAS` sheet unless the user specifies another service type.
- Oracle estimator columns plus discount columns in this order: `Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Custom Label`, `Discount %`, `Discounted Monthly Cost`, `Discounted Annual Cost`, `Custom Note`.
- A visible discount input near the top of the primary sheet or on an `Inputs`/`Summary` sheet.
- Additional columns for discounted monthly and annual cost.
- A monthly and annual total section showing list price, discount percentage, discounted monthly cost, and discounted annual cost.
- Whole-dollar currency formatting with comma separators for monthly and annual amount columns. Preserve unit-rate precision in `Unit Price`.

## Service Scope

Prioritize Oracle Platform Services. Also include any OCI service the user names explicitly. Examples include Exadata Database Service, Autonomous Database, Base Database Service, Compute, Block Volume, Object Storage, Load Balancer, VCN, DRG, FastConnect, OKE, Logging, Monitoring, WAF, IAM, and Security Zones.

If the user provides a service name without SKU details, include it as a line item with blank editable SKU/pricing fields and add a note that pricing requires Oracle Cost Estimator or formal quote input.

For standard Exadata Dedicated Infrastructure and Database@Azure, Database@Google Cloud, or Database@AWS, use the Oracle pricing calculator as the go-to pricing and SKU source. Database@Azure, Database@Google Cloud, and Database@AWS use Exadata Dedicated Cloud pricing, not Exadata Cloud@Customer pricing. The calculator default is a quarter rack with 2 database servers and 3 storage servers; additional database or storage servers should be reflected by the calculator-generated SKU quantities before the rows are transposed into the BOM.

For Exadata Cloud@Customer, explicitly gather model-level resource details because Oracle Cost Estimator may not cover the C@C infrastructure pricing path. Ask for database server model/count, storage server model/count, rack configuration, and any other Cloud@Customer infrastructure components the user expects in the BOM.

When the requested BOM includes Exadata Database Service on Cloud@Customer X11M, read `references/exadata-cloud-at-customer-x11m.md` before asking questions or preparing rows. Use it to validate allowable database server types, storage server types, server counts, VM/cluster limits, rack limits, storage capacity assumptions, and networking/facility assumptions.

## Requirements Gathering

Use `references/requirements-gathering.md` when the user is designing a cloud architecture, system configuration, or migration target and has not provided complete Oracle Cost Estimator rows.

Prompt for quantities and service parameters required to build estimator-ready BOM rows, such as ECPUs/OCPUs, instance counts, storage quantities, usage hours, deployment model, license model, HA/DR assumptions, backup retention, and environment counts.

Ask targeted questions only for services that are in scope. Do not run a full questionnaire when the user already supplied estimator export rows.

## Pricing Rules

- Treat Oracle Cost Estimator values as list-price estimates.
- Preserve `Unit Price` and `Monthly Cost` as list-price fields.
- Prefer Oracle Cost Estimator or Oracle pricing calculator output whenever it provides a complete price for a row. This is the default for nearly all non-Cloud@Customer BOMs.
- For standard Exadata Dedicated Infrastructure and Database@Azure, Database@Google Cloud, or Database@AWS, use the calculator output as authoritative for SKUs, row quantities, unit prices, and monthly costs. Do not replace those rows with hand-derived eSource pricing when calculator output is available.
- When a user asks for a Database@Azure, Database@Google Cloud, or Database@AWS Exadata BOM and omits the license model, ask whether the configuration is BYOL or License Included before pricing. When the Exadata generation/model is omitted, default to the latest model only after stating that assumption, unless the user asks for a prior generation.
- If Oracle Cost Estimator or the pricing calculator cannot provide the needed SKU or price for a row, use the current Oracle eSource PDF supplied by the user as a supplemental fallback source.
- The current supplemental PDF URL is `https://esource.oraclecorp.com/sites/eSource/ContentAsset_1530207473152`; open it through browser authentication when needed.
- A local PDF cache is allowed for repeatability, but it must be refreshed from eSource before each pricing run when the eSource document date is newer than the cached document date. Follow `references/esource-price-list-cache.md`.
- Extract only the rows needed for the BOM from the authenticated PDF into a temporary runtime CSV, then pass that CSV to `scripts/build_bom_template.py` with `--supplemental-pricing-csv`.
- Capture the document date from the PDF front page and pass it with `--supplemental-source-date`; when supplemental PDF pricing is used, add a footnote in `Custom Note` identifying Oracle eSource PDF pricing and that document date.
- Discount input should be a percentage. Accept either `15` or `0.15` as 15%.
- Discounted monthly cost formula: `Monthly Cost * (1 - normalized Discount %)`, where values greater than `1` are divided by `100`.
- Discounted annual cost formula: `Discounted Monthly Cost * 12`.
- If row-level monthly cost is missing but quantity and unit price are present, calculate monthly list cost as `Part Qty * Instance Qty * Usage Qty * Unit Price`.
- Do not invent Oracle SKU pricing. Ask for pricing input or leave fields blank when pricing is unavailable.
- If the user asks for current Oracle pricing and does not provide it, use only current Oracle sources or the Oracle Cost Estimator, and cite the source used.

## Validation Checklist

Before finalizing the workbook, confirm:

- All BOM rows have service descriptions.
- SKU/part numbers are included when provided.
- Quantity, usage, and price fields are numeric where applicable.
- Discount percentage is editable and visibly labeled.
- Discounted monthly and annual totals update from formulas.
- Original list-price values remain visible.
- Workbook is not protected or locked unless the user asks for protection.
- Notes identify assumptions, missing prices, and non-binding estimate status.

## Bundled Scripts

`scripts/build_bom_template.py` creates a discount-enabled Oracle Cloud BOM workbook using the bundled Oracle Cost Estimator sample workbook as the package template.

Example:

```bash
python3 scripts/build_bom_template.py --discount 15 --output outputs/sample-oracle-cloud-bom.xlsx
```

Optional CSV input must use these headers:

`Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Custom Label`, `Custom Note`

Optional supplemental pricing CSV input is intended for temporary rows extracted from the current authenticated Oracle eSource PDF. Supported headers are:

`Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Source Document Date`, `Source Note`

Supplemental pricing is used only when the primary input row has neither `Unit Price` nor `Monthly Cost`. Matching prefers exact `Part`, then exact normalized `Description`, then containment-based normalized `Description`.

Example with supplemental PDF pricing:

```bash
python3 scripts/build_bom_template.py \
  --input-csv /tmp/estimator.csv \
  --supplemental-pricing-csv /tmp/esource-exadata-customer-pricing.csv \
  --supplemental-source-date "MM/DD/YYYY" \
  --discount 15 \
  --output outputs/sample-oracle-cloud-bom.xlsx
```

`scripts/validate_bom_workbook.py` checks the generated workbook for the expected Oracle estimator headers, discount input, discount formulas, totals, and disclaimer.

## User Follow-Up Questions

Ask only for information required to proceed. Good follow-up questions are:

- "Do you have Oracle Cost Estimator export rows or should I create blank editable rows from the architecture description?"
- "What discount percentage should be applied?"
- "Should the workbook include only PAAS services, or also named OCI services?"
- "Do you want a separate summary sheet or should the discount and totals stay on the PAAS sheet?"
