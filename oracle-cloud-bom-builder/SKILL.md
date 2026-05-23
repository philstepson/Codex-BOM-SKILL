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
2. If the architecture is described but estimator inputs are missing, read `references/requirements-gathering.md` and ask the smallest useful set of sizing questions for the named services.
3. Create a new `.xlsx` workbook using the Oracle Cost Estimator format as the base layout.
4. Keep the original Oracle list-price fields intact and editable.
5. Add a single editable discount percentage input that applies to all final list-price values.
6. Add formula-driven discounted totals; do not hardcode values that should update when the discount changes.
7. Preserve source assumptions and add clear notes that prices are estimates unless the user provides formal quote data.
8. Verify the workbook formulas and formatting before delivering the final `.xlsx`.

## Workbook Format

Read `references/oracle-estimator-workbook.md` before building or modifying a BOM workbook.

Use `assets/oracle-cost-estimator-sample.xlsx` as a format reference when a user asks to match the Oracle online pricing estimator export.

Use `scripts/build_bom_template.py` when a deterministic starter workbook is appropriate. It can build from its embedded sample data or from a CSV with Oracle estimator headers.

After generating a workbook with the script, run `scripts/validate_bom_workbook.py` against the output before delivering it.

The default workbook should include:

- A primary `PAAS` sheet unless the user specifies another service type.
- Oracle estimator columns: `Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Custom Label`, `Custom Note`.
- A visible discount input near the top of the primary sheet or on an `Inputs`/`Summary` sheet.
- Additional columns for discounted monthly and annual cost.
- A monthly and annual total section showing list price, discount percentage, discounted monthly cost, and discounted annual cost.

## Service Scope

Prioritize Oracle Platform Services. Also include any OCI service the user names explicitly. Examples include Exadata Database Service, Autonomous Database, Base Database Service, Compute, Block Volume, Object Storage, Load Balancer, VCN, DRG, FastConnect, OKE, Logging, Monitoring, WAF, IAM, and Security Zones.

If the user provides a service name without SKU details, include it as a line item with blank editable SKU/pricing fields and add a note that pricing requires Oracle Cost Estimator or formal quote input.

## Requirements Gathering

Use `references/requirements-gathering.md` when the user is designing a cloud architecture, system configuration, or migration target and has not provided complete Oracle Cost Estimator rows.

Prompt for quantities and service parameters required to build estimator-ready BOM rows, such as ECPUs/OCPUs, instance counts, storage quantities, usage hours, deployment model, license model, HA/DR assumptions, backup retention, and environment counts.

Ask targeted questions only for services that are in scope. Do not run a full questionnaire when the user already supplied estimator export rows.

## Pricing Rules

- Treat Oracle Cost Estimator values as list-price estimates.
- Preserve `Unit Price` and `Monthly Cost` as list-price fields.
- Discount input should be a percentage, for example `15%`.
- Discounted monthly cost formula: `Monthly Cost * (1 - Discount %)`.
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
python3 scripts/build_bom_template.py --discount 0.15 --output outputs/sample-oracle-cloud-bom.xlsx
```

Optional CSV input must use these headers:

`Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Custom Label`, `Custom Note`

`scripts/validate_bom_workbook.py` checks the generated workbook for the expected Oracle estimator headers, discount input, discount formulas, totals, and disclaimer.

## User Follow-Up Questions

Ask only for information required to proceed. Good follow-up questions are:

- "Do you have Oracle Cost Estimator export rows or should I create blank editable rows from the architecture description?"
- "What discount percentage should be applied?"
- "Should the workbook include only PAAS services, or also named OCI services?"
- "Do you want a separate summary sheet or should the discount and totals stay on the PAAS sheet?"
