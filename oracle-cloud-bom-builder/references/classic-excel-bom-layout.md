# Classic Excel BOM Layout Reference

Use this reference when the user asks for the preferred classic Excel BOM style or provides a legacy/customer-facing workbook as the target layout.

Source inspected:

- `/Users/PWSTEPHE/Downloads/Sample-Excel-BOM.xlsx`
- Inspected on 2026-06-26.

This workbook is a layout and workflow reference, not a current pricing source. Its embedded price-list sheets and external links may be stale and must not be used as authoritative pricing without refreshing from current Oracle pricing sources.

## Workbook Role

The classic workbook supports the sales proposal workflow where enterprise architects:

- Gather current-state database, server, usage, storage, I/O, processor, and memory metrics.
- Model future-state OCI resource needs after accounting for newer hardware and cloud performance characteristics.
- Map future-state resources to Oracle SKUs and quantities.
- Organize the BOM by customer environment, such as production, non-production, disaster recovery, development, or other named environments.
- Apply sales discount assumptions.
- Present multi-year cost projections and TCO comparisons to customers.

## Observed Workbook Structure

The sample workbook is `.xlsx` and does not include an embedded VBA project. It does include external workbook links, so formulas may refer to historical local or SharePoint price-list sources.

Visible sheets:

- `BOM`: customer BOM entry and pricing sheet.
- `TCO`: multi-year current-state versus Oracle Cloud comparison.

Hidden support sheets in the sample include:

- `Cust Facing BOM`
- `Ramp Env`
- `Ramp OCPU`
- `Discount Compare`
- `Summary`
- `Usage Quantity`
- `Usage Cost`
- `Usage Chart`
- `TCO Labor`
- `TCO Software`
- `Industry Metrics`
- `License BOM`
- `Exadata BOM`
- `Rate Card`
- `Server Inventory`
- `TCO Metrics`
- `IaaS-PaaS Specs`
- `Exa Specs`
- `Discounts`
- `CAM`
- `CPL 200630`
- `Exchange`
- `Exadata Price List`
- `License Price List`
- `Cloud Price List`

These hidden sheets are useful as examples, but they are not required for the first version of the processor. Most are nice-to-have support sheets and are seldom used in normal customer-facing BOM work.

The main exception is the customer-facing BOM view. The processor should be able to produce a clean customer version of the BOM even when the internal helper sheets are omitted.

Structured tables observed:

- `Servers` on `Server Inventory`, with host, environment, tier, application, database, version, OS, CPU sockets, cores, memory, storage used, description, and physical/virtual fields.
- `UsageQty` on `Usage Quantity`, with data center, SKU, product name, total, and monthly quantity columns.
- `UsageCost` on `Usage Cost`, with user-defined/category/data-center/SKU/product columns and monthly cost columns.

## Preferred BOM Sheet Pattern

The `BOM` sheet uses environment blocks across the worksheet. The inspected sample includes environment headings for:

- `Prod`
- `Non-Prod`
- `DR`
- `Dev`
- `Other`

Each environment block includes quantity, hours, list price, and discounted price logic. The sheet also includes include/exclude flags and a total block.

The main SKU entry area starts with columns similar to:

- SKU or part number.
- Oracle Cloud service description populated from a price list.
- Metric.
- Discount type/category.
- List/unit price.
- Unit cost.
- Discount.
- Per-environment quantity, hours, list price, and discounted price.
- Total.
- Include/category flags.

The preferred multi-environment pattern is one row per unique SKU or priced line item, not one repeated row per environment. Each environment gets its own adjacent column block. When a SKU is not relevant to an environment, that environment's cells stay blank. The sample pattern uses blocks like:

- `Prod Qty`, `Prod Hrs`, `Prod List Price`, `Prod Discounted Price`.
- `Non-Prod Qty`, `Non-Prod Hrs`, `Non-Prod List Price`, `Non-Prod Discounted Price`.
- `DR Qty`, `DR Hrs`, `DR List Price`, `DR Discounted Price`.
- Final total columns for all environments.

Below the SKU rows, the workbook should include summary rows for each unique environment and a final all-environments total. This is the ideal customer-review format because it lets the reader scan each SKU once and see exactly which environments consume it.

## Required Customer-Facing BOM View

For proposal use, always provide or be able to generate a customer-facing BOM sheet. This view should be simple, visible, and safe to share with a customer.

The customer-facing BOM should show:

- SKU or part number.
- Oracle product or service description.
- Metric or billing basis.
- Unit list price.
- One column block for each environment, with quantity, usage quantity or hours, monthly list price, annual list price, and one-time list price.
- Final total columns for all environments.
- Summary rows for each environment and one final all-environments total.
- Optional notes that are appropriate for customer review.

The customer-facing BOM should hide or omit:

- Internal discount comparison formulas unless the user asks to show discounted pricing.
- Internal price-list tabs.
- Source extraction scratch data.
- Complex helper columns used only to populate formulas.

When the user asks for a customer version that shows only list price, include all SKUs and quantities in the wide environment-block format and do not show discounted totals. Keep discounts in the internal/proposal working view only unless the user explicitly asks to expose them.

## Future Configured-System Summary

A useful future enhancement is a configured-system summary sheet that translates BOM rows and datasheet sizing rules into an easy-to-read description of the configured platform.

For Exadata and similar engineered systems, the summary should show:

- Processor resources requested, configured, and available.
- Memory configured and available to VM clusters or database workloads.
- Storage raw/configured/usable capacity, with the redundancy assumption visible.
- Local VM or database-server storage constraints when relevant.
- IOPS, bandwidth, XRMEM, flash cache, and data load-rate limits when the datasheet provides them and the user supplied workload requirements.
- Server counts and server types used to derive the totals.
- Any capacity that is included with infrastructure but not separately metered.

The summary should distinguish between:

- Resources requested by the architecture, such as 64 ECPUs.
- Physical or infrastructure resources included in the configured system.
- Resources available for database workloads after redundancy, VM, or platform limits.
- Resources actually allocated to an environment or VM cluster.

This summary should be generated from current datasheet references and BOM inputs, not inferred from price alone.

## Future Draw.io Diagram

Another useful future enhancement is an optional simple block diagram, preferably in Draw.io-compatible `.drawio` XML, that depicts the configured system at proposal level.

The diagram should be intentionally simple:

- One block for the Exadata or OCI platform.
- Child blocks for database servers, storage servers, VM clusters, and environments.
- Labels for configured ECPUs/cores, memory, usable storage, and key performance limits.
- Environment labels such as Production, Test/Dev, DR, and Shared/Common when present.
- Source note identifying that sizing values come from the active datasheet reference and BOM inputs.

The diagram should be an optional artifact. Do not make it a prerequisite for producing the BOM.

## Environment Requirement

For this layout, every modeled resource or SKU row should have an environment assignment. Do not assume a row belongs to production just because no environment is specified.

When a user describes resources without identifying the environment, ask which environment is being described before generating a multi-environment workbook. The minimum environment fields are:

- Environment name, such as `Production`, `Test/Dev`, `DR`, `Non-Prod`, or a customer-specific name.
- Resource rows or SKU quantities that belong to that environment.
- Whether shared resources should be allocated to one environment, duplicated across environments, or placed in a shared/common environment.
- Environment-specific hours, ramp timing, and inclusion flag when they differ from the workbook default.

## Pricing Freshness Rule

The sample workbook's embedded pricing is historical. Treat it as a schema example only.

For current BOM generation:

- Use the Oracle pricing calculator or Cost Estimator export as the source of truth when it can produce the requested SKU rows and prices.
- Use current authenticated Oracle eSource PDF pricing only for Exadata Cloud@Customer gaps or explicit SKUs that are unavailable from the calculator.
- Refresh or date-check any persisted eSource PDF before extracting prices.
- Do not reuse the sample workbook's `Cloud Price List`, `Exadata Price List`, `License Price List`, or external links as authoritative current pricing.
- Preserve source date, pricing source, and billing basis in row notes for any price-list-sourced rows.

## Target Processor Direction

The current deterministic builder can produce simple estimator-style BOMs. The preferred processor should evolve toward this classic workbook model by adding:

- Multi-environment row modeling.
- A visible customer-facing list-price BOM view with all SKUs and quantities.
- Optional current-state input tables for server inventory and usage.
- Future-state resource mapping by environment.
- Optional configured-system summary with processor, memory, storage, and performance capacity.
- Optional Draw.io block diagram for customer-friendly system specification views.
- Current pricing refresh from calculator/export or verified eSource.
- Optional discount comparison and multi-year TCO output.
- Clear separation between layout templates, sizing assumptions, and current pricing data.
