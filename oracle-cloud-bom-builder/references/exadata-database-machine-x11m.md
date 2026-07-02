# Exadata Database Machine X11M And X11 Storage Reference

Use this reference when preparing or validating BOM rows for on-premises Oracle Exadata Database Machine X11M, Exadata Storage Expansion Rack X11M, Exadata X11 storage-server additions, or Zero Data Loss Recovery Appliance RA26/RA26-Z rows.

Sources supplied by the user:

- `Exadata-X11M-DS-FINAL_v1.4.pdf`: `Oracle Exadata Database Machine X11M Data Sheet`, Version 1.4, Oracle public datasheet, copyright 2026.
- `Announcing Oracle Exadata X11 Storage Servers and Zero Data Loss Recovery Appliance RA26_RA26-Z _ exadata.pdf`: Oracle Exadata Product Management blog print, June 30, 2026.

This reference captures configuration and sizing facts that affect BOM preparation. The technical facts are from the datasheet and blog. The SKU rows below are from `ORACLE+PAAS+AND+IAAS+PUBLIC+CLOUD+GLOBAL+PRICE+LIST.pdf`, `Last updated: July 1, 2026`. When the current Oracle pricing calculator exposes these same SKUs and prices, use the calculator/export as the working BOM source because it also provides the active configuration quantities and monthly costs.

## Product Family Updates

- Exadata X11 storage servers add lower-cost storage options without Exadata RDMA Memory (XRMEM).
- Exadata X11M storage servers remain the highest-performance options and include XRMEM.
- New X11 storage-server options are:
  - X11 High Capacity.
  - X11 Extreme Flash.
  - X11 High Capacity-Z.
- X11 High Capacity and X11 Extreme Flash are available for on-premises Exadata Database Machine and Exadata Cloud@Customer.
- X11 High Capacity-Z is available for on-premises Exadata Database Machine.
- For on-premises Exadata Database Machine, X11 storage servers can be deployed with existing Exadata X8M or later systems.
- For Exadata Cloud@Customer, X11 storage servers can be deployed with Exadata X11M and later database servers.
- The storage server model selected at initial Exadata Cloud@Customer deployment determines the model that can be added for future storage expansions.
- Exadata X11 storage servers require Exadata System Software 26ai release 26.1.0 or later, or Exadata System Software 25ai release 25.1.17 or 25.2.10 or later.
- RA26 and RA26-Z are new Zero Data Loss Recovery Appliance generations using 26 TB drives and ZDLRA 23.1 storage optimizations.

## Configuration Rules

- Minimum Exadata configuration is 2 database servers and 3 HC, EF, or HC-Z storage servers.
- Database Server-Z and High Capacity-Z storage servers can be combined with standard servers in the same rack.
- Elastic configurations can add database or storage servers to a quarter rack.
- An elastic rack cannot exceed 19 servers or 38 RU.
- Maximum database servers per elastic rack: 15.
- Maximum storage servers per elastic rack: 17 for HC or EF.
- Maximum HC-Z storage servers per rack: 17.
- Maximum XT storage servers per rack: 14.
- Storage Expansion Rack starts with 4 HC or EF storage servers and can expand with additional storage servers.
- The same storage-server type must be used when expanding existing storage servers, such as EF expanding EF storage.
- When adding a new storage-server type, use at least 2 servers for Normal redundancy and 3 servers for High redundancy.
- XT storage can provide an ASM disk group, an Exascale storage pool, or both.
- XT storage requires at least 2 storage servers for ASM and 3 storage servers for Exascale.
- XT storage cannot be used without at least 3 HC, HC-Z, or EF storage servers in the configuration.
- Up to 14 Exadata Database Machine racks or Exadata Storage Expansion Racks can be connected through the RoCE fabric; larger configurations require external RoCE switches.

## Per-Server Technical Values

### Database Servers

| Server type | CPU | Memory choices | Raw local flash | Max SQL read IOPS | Max SQL write IOPS |
| --- | --- | --- | ---: | ---: | ---: |
| X11M Database Server | 2 x 96-core AMD EPYC 9J25 | 512 GB, 1,536 GB, 2,304 GB, or 3,072 GB | 7.68 TB | 2,800,000 | 2,500,000 |
| X11M Database Server-Z | 1 x 32-core AMD EPYC 9J15 | 768 GB or 1,152 GB | 7.68 TB | 1,400,000 | 1,250,000 |

### Storage Servers

| Storage server type | XRMEM | Max SQL flash bandwidth | Max SQL XRMEM bandwidth | Max SQL read IOPS | Max SQL write IOPS | Read latency | Perf flash raw | Disk raw | Capacity flash raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| X11M High Capacity | 1,280 GB | 100 GB/s | 500 GB/s | 2,800,000 | 1,000,000 | ~14 us | 27.2 TB | 264 TB | n/a |
| X11 High Capacity | n/a | 100 GB/s | n/a | 1,200,000 | 1,000,000 | ~150 us | 27.2 TB | 264 TB | n/a |
| X11M Extreme Flash | 1,280 GB | 100 GB/s | 500 GB/s | 2,800,000 | 1,000,000 | ~14 us | 27.2 TB | n/a | 122.88 TB |
| X11 Extreme Flash | n/a | 100 GB/s | n/a | 1,200,000 | 1,000,000 | ~150 us | 27.2 TB | n/a | 122.88 TB |
| X11M High Capacity-Z | 576 GB | 50 GB/s | 250 GB/s | 1,400,000 | 500,000 | ~14 us | 13.6 TB | 132 TB | n/a |
| X11 High Capacity-Z | n/a | 50 GB/s | n/a | 600,000 | 500,000 | ~150 us | 13.6 TB | 132 TB | n/a |
| X11M Extended | n/a | 50 GB/s | n/a | 600,000 | 500,000 | ~150 us | 13.6 TB | 264 TB | n/a |

## Rack Examples

| Example | Database servers | Storage servers | Raw HC disk | Raw EF capacity flash | Raw perf flash | XRMEM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Quarter Rack | 2 standard DB servers | 3 HC or EF | 792 TB | 368.6 TB | 81.6 TB | up to 3.75 TB |
| Quarter Rack with Database Server-Z | 2 DB Server-Z | 3 HC-Z, HC, or EF | 396 TB with HC-Z or 792 TB with HC | 368.6 TB with EF | 40.8 TB with HC-Z or 81.6 TB with HC/EF | up to 1.69 TB with HC-Z or 3.75 TB with HC/EF |
| Elastic Example 1 | 9 DB servers | 9 HC or EF | 2,376 TB | 1,105.9 TB | 244.8 TB | up to 11.25 TB |
| Elastic Example 2 | 2 DB servers | 17 HC or EF | 4,488 TB | 2,088 TB | 462.4 TB | up to 21.25 TB |

## Usable Capacity Examples

| Example | Storage | Normal redundancy usable | High redundancy usable | Max data load rate |
| --- | --- | ---: | ---: | ---: |
| Elastic Example 1 | HC | 983.2 TB | 720.3 TB | 22.5 TB/hour |
| Elastic Example 1 | EF | 457.6 TB | 335.2 TB | 22.5 TB/hour |
| Elastic Example 2 | HC | 1,857.2 TB | 1,360.6 TB | 8.8 TB/hour |
| Elastic Example 2 | EF | 864.2 TB | 633.1 TB | 8.8 TB/hour |
| Quarter Rack | HC-Z | 153.1 TB | 120 TB | 3.8 TB/hour |
| Quarter Rack | HC | 306.1 TB | 240.1 TB | 7.5 TB/hour |
| Quarter Rack | EF | 142.5 TB | 111.7 TB | 7.5 TB/hour |

## Recovery Appliance RA26 And RA26-Z

- RA26 and RA26-Z increase usable capacity by 21% compared with the prior generation.
- RA26 uses 26 TB drives and ZDLRA 23.1 storage optimizations.
- RA26 base rack usable capacity: 332 TB.
- RA26 full rack usable capacity: 1.9 PB.
- RA26-Z base rack usable capacity: 164 TB.
- RA26-Z full rack usable capacity: 943 TB.
- Backup and recovery operations are rated up to 60 TB/hour.
- Treat RA26 and RA26-Z as data-protection infrastructure rows, not Exadata Database Service rows.
- The July 1, 2026 Oracle PaaS and IaaS Public Cloud Global Price List did not contain RA26 or RA26-Z hardware SKU rows by exact text search. It did contain `B93583`, `Oracle Standard Software Installation and Configuration for Oracle Cloud: Zero Data Loss Recovery Appliance for Cloud (up to 10 protected)`, as a one-time `Each` service row at `12,500.00`.

## July 1, 2026 eSource SKU Rows

Use these rows when the active eSource cache metadata confirms `document_date` is `July 1, 2026` or newer and a current calculator/export row is unavailable or incomplete. Preserve the price-list descriptions and source date in BOM row notes. If the current Oracle pricing calculator produces these rows, preserve the calculator rows and add only the normal BOM discount/formula columns.

### Exadata Cloud Infrastructure X11M/X11MV

| SKU | Description | Unit price | Metric | Minimum | Notes |
| --- | --- | ---: | --- | ---: | --- |
| B110627 | Exadata Cloud Infrastructure - Database Server - X11M | 6.3014 | Hosted Environment Per Hour | - | Existing X11M hosted infrastructure database-server row |
| B110629 | Exadata Cloud Infrastructure - Storage Server - X11M | 5.4795 | Hosted Environment Per Hour | - | Existing X11M hosted infrastructure storage-server row |
| B112666 | Exadata Cloud Infrastructure - Database Server - X11MV | 6.3014 | Hosted Environment Per Hour | - | Multicloud listing shows AWS, Azure, and Google Cloud availability |
| B112667 | Exadata Cloud Infrastructure - Storage Server - X11MV | 5.4795 | Hosted Environment Per Hour | - | Multicloud listing shows AWS, Azure, and Google Cloud availability |

### Exadata Cloud@Customer X11M Extreme Flash

| SKU | Description | Monthly subscription price | Metric | Notes |
| --- | --- | ---: | --- | --- |
| B112320 | Exadata Cloud@Customer - Storage Server - X11M - Extreme Flash | 4,800.00 x Rack Term Factor | Hosted Environment Per Month | Includes one X11M EF storage server, 1.25 TB XRMEM, 27.2 TB performance flash cache, and 37.2 TB usable capacity via capacity-optimized flash drives |
| B112321 | Exadata Cloud@Customer - Expansion Rack - X11M - Extreme Flash | 5,130.00 x Rack Term Factor | Hosted Environment Per Month | Includes one X11M EF storage server; requires at least 3 additional expansion servers |

### Exadata Cloud@Customer X11 Storage

These rows are marked `Priced in Advance of Availability` in the July 1, 2026 price list.

| SKU | Description | Monthly subscription price | Metric | Notes |
| --- | --- | ---: | --- | --- |
| B112766 | Exadata Cloud@Customer - High Capacity Storage Server - X11 | 2,400.00 x Rack Term Factor | Hosted Environment Per Month | See eSource Note 16 for Rack Term Factor |
| B112767 | Exadata Cloud@Customer - Extreme Flash Storage Server - X11 | 4,040.00 x Rack Term Factor | Hosted Environment Per Month | See eSource Note 16 for Rack Term Factor |
| B112768 | Exadata Cloud@Customer - Expansion Rack - X11 - High Capacity Storage | 2,730.00 x Rack Term Factor | Hosted Environment Per Month | See eSource Note 16 for Rack Term Factor |
| B112769 | Exadata Cloud@Customer - Expansion Rack - X11 - Extreme Flash Storage | 4,375.00 x Rack Term Factor | Hosted Environment Per Month | See eSource Note 16 for Rack Term Factor |

### Exadata Cloud@Customer Data And Device Retention

| SKU | Description | Monthly subscription price | Metric | Notes |
| --- | --- | ---: | --- | --- |
| B112324 | Data and Device Retention Service for ExaDB-C@C - Rack - X11M | 790.00 x Rack Term Factor | Hosted Environment Per Month | X11M/X10M non-metered section |
| B112326 | Data and Device Retention Service for ExaDB-C@C - Storage Server - Extreme Flash - X11M | 580.00 x Rack Term Factor | Hosted Environment Per Month | X11M/X10M non-metered section |
| B112327 | Data and Device Retention Service for ExaDB-C@C - Expansion Rack - Extreme Flash - X11M | 620.00 x Rack Term Factor | Hosted Environment Per Month | X11M/X10M non-metered section |
| B112774 | Data and Device Retention Service for ExaDB-C@C - High Capacity Storage Server - X11 | 290.00 x Rack Term Factor | Hosted Environment Per Month | Priced in Advance of Availability |
| B112775 | Data and Device Retention Service for ExaDB-C@C - Extreme Flash Storage Server - X11 | 485.00 x Rack Term Factor | Hosted Environment Per Month | Priced in Advance of Availability |
| B112776 | Data and Device Retention Service for ExaDB-C@C - Expansion Rack - X11 - High Capacity Storage | 330.00 x Rack Term Factor | Hosted Environment Per Month | Priced in Advance of Availability |
| B112777 | Data and Device Retention Service for ExaDB-C@C - Expansion Rack - X11 - Extreme Flash Storage | 525.00 x Rack Term Factor | Hosted Environment Per Month | Priced in Advance of Availability |

### Partner Hardware Variants

Use these only when the deal qualifies for the Cloud@Customer Partner Hardware model described in Section 3a of the eSource price list.

| SKU | Description | Monthly subscription price | Metric |
| --- | --- | ---: | --- |
| B112322 | Exadata Cloud@Customer - Storage Server - X11M - Extreme Flash - Partner Hardware | 4,800.00 x Rack Term Factor | Hosted Environment Per Month |
| B112323 | Exadata Cloud@Customer - Expansion Rack - X11M - Extreme Flash - Partner Hardware | 5,130.00 x Rack Term Factor | Hosted Environment Per Month |
| B112770 | Exadata Cloud@Customer - High Capacity Storage Server - X11 - Partner Hardware | 2,400.00 x Rack Term Factor | Hosted Environment Per Month |
| B112771 | Exadata Cloud@Customer - Extreme Flash Storage Server - X11 - Partner Hardware | 4,040.00 x Rack Term Factor | Hosted Environment Per Month |
| B112772 | Exadata Cloud@Customer - Expansion Rack - X11 - High Capacity Storage - Partner Hardware | 2,730.00 x Rack Term Factor | Hosted Environment Per Month |
| B112773 | Exadata Cloud@Customer - Expansion Rack - X11 - Extreme Flash Storage - Partner Hardware | 4,375.00 x Rack Term Factor | Hosted Environment Per Month |

## BOM Validation Guidance

When a BOM includes Exadata Database Machine X11M, Exadata X11 storage servers, or RA26/RA26-Z:

- Capture deployment type: on-premises Exadata Database Machine, Exadata Storage Expansion Rack, Exadata Cloud@Customer storage expansion, or Recovery Appliance.
- Capture database server type and count, including whether Database Server-Z is used.
- Capture storage server type and count, including whether X11 or X11M and whether HC, EF, HC-Z, or XT.
- Do not describe X11 storage servers as including XRMEM unless the row explicitly includes an XRMEM memory expansion or the selected server is X11M.
- For Exadata Cloud@Customer, flag X11 High Capacity-Z as on-premises only unless a later source says otherwise.
- For Exadata Cloud@Customer, confirm that future storage expansions match the storage model selected at initial deployment.
- For X11 storage-server pricing, use current Oracle pricing calculator/export rows when available. If using eSource, use the authenticated Oracle eSource PDF dated July 1, 2026 or newer. Do not price these rows from the June 11, 2026 cached PDF.
- If an RA26 or RA26-Z hardware SKU is requested, ask for the current Recovery Appliance calculator/export row, price-list row, or formal quote source. The July 1, 2026 PaaS/IaaS price list available in this repository did not expose RA26/RA26-Z hardware SKU rows.
