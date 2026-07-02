# Oracle eSource Price List Cache

Use this protocol before using Oracle eSource PDF pricing as a supplemental source for BOM rows. For calculator-covered resources, current Oracle customer-facing pricing calculator/export rows may be used directly even when eSource lags the public calculator.

## Source

- Current eSource URL: `https://esource.oraclecorp.com/sites/eSource/ContentAsset_1530207473152`
- Current known document title: `ORACLE PAAS AND IAAS PUBLIC CLOUD GLOBAL PRICE LIST.pdf`
- The document date is the date printed in the PDF, such as `Last updated: June 11, 2026`.
- New Exadata X11 storage-server and Zero Data Loss Recovery Appliance RA26/RA26-Z-related rows announced June 30, 2026 require either current Oracle pricing calculator/export rows or the Oracle eSource price list dated July 1, 2026 or newer.

## Cache Rule

A local PDF cache may be persisted for repeatability, but eSource remains authoritative.

Before each pricing run:

1. Open the eSource URL in Chrome with the user's authenticated Oracle session.
2. Download the current eSource PDF from Chrome instead of relying on browser/PDF-viewer automation.
3. Run the repository preflight against the downloaded PDF so the script extracts the printed document date.
4. If the downloaded PDF date is newer than the cached metadata, refresh the managed cache from the downloaded PDF.
5. Update the cache metadata with the eSource URL, document date, retrieval date, and cached filename.
6. Extract pricing rows only from the verified current cached PDF.

Do not depend on Chrome extension access to Oracle's PDF viewer as the normal workflow. The supported path is manual download from the authenticated browser session followed by local PDF validation. If the current eSource PDF cannot be downloaded or its date cannot be extracted, do not silently reuse the cached PDF. Ask the user whether to proceed from the cached PDF and label the output as using an unverified cached source.

For new Exadata X11 storage-server rows, Exadata X11M XT rows, Exadata Database Server-Z rows, and RA26/RA26-Z-related rows, prefer current Oracle pricing calculator/export rows when they expose the SKU and pricing. If the current customer-facing calculator/site exposes a SKU before eSource reflects it, use the calculator/site row and preserve that source in the BOM note. If using eSource, do not use the June 11, 2026 cache. Refresh to the July 1, 2026 eSource PDF or newer before extracting SKU, billing-basis, or price values. The July 1, 2026 PaaS/IaaS price list did not expose RA26/RA26-Z hardware SKU rows by exact text search.

Use the repository preflight script to enforce this check when preparing a BOM:

```bash
.venv/bin/python scripts/check_pricing_refresh.py \
  --input-csv inputs/multi-env-standard-cc-prod-dr-oci-nonprod.csv \
  --downloaded-esource-pdf ~/Downloads/ORACLE+PAAS+AND+IAAS+PUBLIC+CLOUD+GLOBAL+PRICE+LIST.pdf
```

When the downloaded PDF is newer than the managed cache, refresh the cache from the same validated download:

```bash
.venv/bin/python scripts/check_pricing_refresh.py \
  --downloaded-esource-pdf ~/Downloads/ORACLE+PAAS+AND+IAAS+PUBLIC+CLOUD+GLOBAL+PRICE+LIST.pdf \
  --refresh-cache-from-download
```

For eSource-priced rows that depend on the June 30, 2026 Exadata announcement, require the July 1, 2026 price list:

```bash
.venv/bin/python scripts/check_pricing_refresh.py \
  --input-csv /tmp/exadata-x11-or-ra26-rows.csv \
  --downloaded-esource-pdf ~/Downloads/ORACLE+PAAS+AND+IAAS+PUBLIC+CLOUD+GLOBAL+PRICE+LIST.pdf \
  --minimum-esource-date "July 1, 2026"
```

`--downloaded-esource-pdf` should point to the current PDF downloaded from the authenticated eSource page. The script extracts the document date from the PDF front page. `--current-esource-date` remains available as a manual fallback when the date is known but PDF extraction is not possible. If the downloaded/current date is newer than the cache metadata, refresh the PDF cache before extracting or reusing any supplemental rows.

## Recommended Local Layout

Store cached source files outside committed skill source. Paths below are relative to the `oracle-cloud-bom-builder` skill directory:

```text
tmp/esource-price-list/
  oracle-paas-iaas-public-cloud-global-price-list.pdf
  oracle-paas-iaas-public-cloud-global-price-list.metadata.json
```

Recommended metadata:

```json
{
  "source_url": "https://esource.oraclecorp.com/sites/eSource/ContentAsset_1530207473152",
  "document_title": "ORACLE PAAS AND IAAS PUBLIC CLOUD GLOBAL PRICE LIST.pdf",
  "document_date": "June 11, 2026",
  "retrieved_at": "2026-06-25",
  "cached_file": "oracle-paas-iaas-public-cloud-global-price-list.pdf"
}
```

## Runtime Extraction

Temporary extracted CSVs can be used as script input, but they are not authoritative across runs. Regenerate them from the verified current PDF whenever supplemental pricing is needed.

When a user supplies an explicit SKU, search the verified PDF by exact SKU first. Extract only that row and any adjacent text needed to confirm description, metric, minimum, notes, billing basis, and document date.

Example: `B91390` resolves to `Gen 2 Exadata Cloud at Customer Installation and Activation Service` in the June 11, 2026 cached PDF. It is an `Each` installation and activation service, mandatory per rack, and should be treated as a one-time row when the user asks to include it in annual cost.
