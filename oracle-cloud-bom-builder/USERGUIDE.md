# Oracle Cloud BOM Builder User Guide

## Purpose

Use this skill to create Oracle Cloud bill of material workbooks in an Oracle Cost Estimator-style Excel format. The workbook keeps the original list-price fields editable, adds a single discount input, and calculates discounted monthly and annual totals.

The skill is intended for architecture estimates, not formal quotes. Validate final pricing, terms, availability, and discounts with Oracle before procurement.

## When To Use It

Use the skill when you need:

- An Oracle Cloud BOM spreadsheet.
- A discount-enabled Oracle Cost Estimator-style workbook.
- A workbook from Oracle Cost Estimator rows or an architecture description.
- Exadata Cloud@Customer BOM rows that include infrastructure resources not fully covered by the calculator.

## Inputs The Skill Needs

For the cleanest result, provide Oracle Cost Estimator-style rows with these columns:

`Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Custom Label`, `Custom Note`

If you do not have estimator rows, describe the architecture and include the quantities you know. The skill should ask only for the missing sizing details needed for the named services.

Common inputs include:

- Project or reference label.
- Currency and realm, usually `USD` and `PUBLIC`.
- Discount percentage.
- Service names and descriptions.
- Part/SKU numbers, when known.
- Part quantity, instance quantity, usage quantity, unit price, and monthly cost.
- Custom labels or notes for architecture assumptions.

## Exadata Cloud@Customer Inputs

For Exadata Cloud@Customer, provide as much model-level detail as possible because Oracle Cost Estimator may expose ECPU pricing without all required infrastructure SKUs.

Useful details include:

- Exadata generation, such as `X11M`.
- Base System or elastic configuration.
- Single-rack or multi-rack design.
- Database server type: Base, Standard, Large, or Extra Large.
- Storage server type: Base, High Capacity, or Extreme Flash.
- Database server count and storage server count.
- Expansion rack count and expansion rack server counts, when applicable.
- Storage redundancy, defaulting to High unless Normal is explicitly specified.
- License model: License Included or Bring Your Own License.
- ECPU quantity.
- Hours per month, usually `744` for always-on resources.
- Default memory and storage assumptions, if applicable.

For Exadata Database Service on Cloud@Customer X11M, the default test baseline is a single rack with 2 database servers and 3 storage servers. Model each rack as prepopulated with 2 database servers. Additional database servers increase usable memory and database cores/ECPUs.

High redundancy is the default storage assumption. It keeps two mirrored copies of the original data and can survive two HDA failures. Normal redundancy provides more usable storage because it keeps one mirrored copy, but it only survives one HDA failure.

Example request:

```text
Create a BOM for an Exadata Cloud@Customer X11M single-rack baseline with 3 High Capacity storage servers, High redundancy, and License Included software. Name it Test-BOM.
```

## Pricing Source Order

The skill uses this pricing order:

1. Oracle Cost Estimator values supplied by the user or source file.
2. Supplemental pricing extracted at runtime from the current authenticated Oracle eSource PDF, only when calculator pricing is missing.
3. Blank editable price fields with notes when neither source is available.

The skill must not invent Oracle SKU pricing.

## Supplemental Oracle eSource PDF Pricing

Some resources, especially Exadata Cloud@Customer database servers, storage servers, and rack infrastructure, may require pricing from the current Oracle eSource PDF.

Current supplemental source:

`https://esource.oraclecorp.com/sites/eSource/ContentAsset_1530207473152`

Use browser authentication to open the current PDF. Do not save or commit the PDF into the skill repository. Extract only the rows needed for the active BOM into a temporary CSV.

The supplemental CSV can use these headers:

`Part`, `Description`, `Part Qty`, `Instance Qty`, `Usage Qty`, `Unit Price`, `Monthly Cost`, `Source Document Date`, `Source Note`

When supplemental PDF pricing is used, the skill adds a footnote in `Custom Note` that identifies Oracle eSource PDF pricing and includes the document date from the PDF front page.

## Building A Workbook

From the skill directory:

```bash
python3 scripts/build_bom_template.py \
  --input-csv /tmp/estimator.csv \
  --discount 0.15 \
  --reference-label "My Oracle Cloud BOM" \
  --output outputs/my-oracle-cloud-bom.xlsx
```

With supplemental PDF pricing:

```bash
python3 scripts/build_bom_template.py \
  --input-csv /tmp/estimator.csv \
  --supplemental-pricing-csv /tmp/esource-exacc-pricing.csv \
  --supplemental-source-date "MM/DD/YYYY" \
  --discount 0.15 \
  --reference-label "My Exadata Cloud@Customer BOM" \
  --output outputs/my-exacc-bom.xlsx
```

## Workbook Output

The generated workbook includes:

- A primary `PAAS` worksheet by default.
- Oracle estimator columns from `Part` through `Custom Note`.
- A single editable discount input.
- Discounted monthly and annual cost columns.
- Monthly and annual totals.
- Estimate disclaimer text.

If a row has quantity and unit price but no monthly cost, the workbook calculates monthly list cost as:

```text
Part Qty * Instance Qty * Usage Qty * Unit Price
```

## Validation

Always validate generated workbooks before delivery:

```bash
python3 scripts/validate_bom_workbook.py outputs/my-oracle-cloud-bom.xlsx
```

Expected success output:

```text
PASS: outputs/my-oracle-cloud-bom.xlsx
```

## Practical Workflow

1. Gather architecture details or estimator rows.
2. Ask for only the missing sizing details.
3. Build an estimator-style input CSV when needed.
4. Open the current eSource PDF through browser authentication only if calculator pricing is incomplete.
5. Extract only required supplemental pricing rows into a temporary CSV.
6. Generate the workbook.
7. Validate the workbook.
8. Review rows with blank prices or PDF-sourced notes.
9. Deliver the `.xlsx` file and state any assumptions.

## Common Follow-Up Questions

The skill may ask:

- Do you have Oracle Cost Estimator export rows?
- What discount percentage should apply?
- What Exadata generation, rack count, and server counts should be used?
- Should the software license model be License Included or BYOL?
- Should storage use the default High redundancy assumption or Normal redundancy?
- Should blank rows be left editable when pricing is unavailable?
- What is the document date on the supplemental PDF front page?

## Limitations

- The workbook is an estimate, not an Oracle quote.
- The skill cannot price private or authenticated sources unless access is available during the session.
- The current PDF should be used live at runtime; stale extracted pricing files should not be reused as authoritative sources.
- If a calculator row already has pricing, supplemental PDF pricing does not overwrite it.
