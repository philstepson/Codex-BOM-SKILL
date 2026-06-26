# Exadata Database Service on Dedicated Infrastructure X11M Reference

Use this reference when preparing or validating BOM rows for Oracle Exadata Database Service on Dedicated Infrastructure X11M, including OCI Dedicated Exadata and Database@Azure/Google Cloud/AWS configurations that use Exadata Dedicated Cloud pricing.

Sources supplied by the user:

- `/Users/PWSTEPHE/Downloads/exadb-d-x11m-ds.pdf`: `Exadata Database Service on Dedicated Infrastructure X11M`, Version 1.6, Oracle public datasheet, copyright 2025, 12 pages, ingested 2026-06-26.

This reference captures configuration and sizing facts that affect BOM preparation. It is not a pricing source. For standard Dedicated Exadata and Database@ BOMs, use the Oracle pricing calculator or Cost Estimator export as the source of truth for SKU rows, quantities, unit prices, and monthly costs.

## Configuration Rules

- Exadata Cloud Infrastructure is dedicated to a single tenant.
- Exadata Database Service on Dedicated Infrastructure runs in OCI and partner cloud regions.
- Exadata Cloud Infrastructure can run both Exadata Database Service and Autonomous Database on the same infrastructure.
- Infrastructure is available as pay-per-use with a minimum term of 48 hours.
- Elastic X11M shapes start with 2 database servers and 3 storage servers.
- Elastic X11M shapes can scale up to 32 database servers and 64 storage servers.
- Base System is hardware-generation agnostic, fixed, non-expandable, and supports only a single VM Cluster.
- Elastic Example 1 is the minimum elastic X11M configuration with 2 database servers and 3 storage servers.
- Elastic Example 2 uses 8 database servers and 8 storage servers.
- Elastic Example 3 uses 2 database servers and 14 storage servers.
- XRMEM is included with Elastic configurations; Base System has no XRMEM.
- All disk/flash, IOPS, and memory for the selected configuration are dedicated to the customer and included in the infrastructure price.
- There is no charge for network communication to the Exadata Cloud Infrastructure system.
- Software license models are License Included and BYOL.
- BYOL supports Oracle Database Enterprise Edition entitlements; Oracle Database Standard Edition is not supported.
- Exadata System Software is included in BYOL, so customers do not bring a separate Exadata System Software license entitlement.

## VM And Cluster Limits

- Minimum ECPUs per VM: 8.
- Base System maximum VMs per database server: 1.
- Base System maximum VM Clusters per system: 1.
- Elastic X11M maximum VMs per database server: 8.
- Elastic X11M maximum VM Clusters per system: 8.
- Maximum usable local storage per database server: 2,243 GB for elastic X11M.
- Maximum usable local storage per database server for Base System: 900 GB.
- Maximum usable local storage per VM: 900 GB.
- VM image size minimum and default: 244 GB, including 60 GB for `/u02`.
- Oracle homes `/u02` filesystem can be up to 900 GB per VM, but the actual maximum can be lower because it is limited by local storage used by all VM images and `/u02` filesystems.

## Per-Server Technical Values

### Elastic X11M Database Server

| Server type | Usable database cores | Total ECPUs | Memory available for VMs |
| --- | ---: | ---: | ---: |
| X11M Database Server | 190 | 760 | 1,390 GB |

Maximum count: 32 database servers.

### Elastic X11M Storage Server

| Server type | Storage cores | XRMEM capacity | Flash capacity | Usable disk capacity |
| --- | ---: | ---: | ---: | ---: |
| X11M Storage Server | 64 | 1.25 TB | 27.2 TB | 80 TB |

Maximum count: 64 storage servers.

## Datasheet Example Configurations

These examples are representative configurations from the datasheet, not the only valid combinations.

| Example | Database servers | Storage servers | Total DB cores | Total ECPUs | Max VM clusters | Total usable disk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base System | 2 | 3 | 48 | 192 | 1 | 73 TB |
| Elastic Example 1 | 2 | 3 | 380 | 1,520 | 8 | 240 TB |
| Elastic Example 2 | 8 | 8 | 1,520 | 6,080 | 8 | 640 TB |
| Elastic Example 3 | 2 | 14 | 380 | 1,520 | 8 | 1,120 TB |

## Capacity And Performance Examples

Use these values as technical sizing reference points when current-state database consumption needs to be projected into future-state OCI Dedicated Exadata resources. They are not SKU prices.

| Example | XRMEM | Flash capacity | Usable disk | Max DB size no local backup | Max DB size local backup | Max SQL read IOPS | Max SQL write IOPS | Max flash bandwidth | Max XRMEM bandwidth | Max disk bandwidth | Max data load rate | Network |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Base System | n/a | 38.4 TB | 73 TB | 58 TB | 29 TB | 562,500 | 518,000 | 25 GB/s | n/a | 2.7 GB/s | 3.8 TB/hr | 10 GbE |
| Elastic Example 1 | 3.75 TB | 81.6 TB | 240 TB | 192 TB | 96 TB | 5,600,000 | 3,000,000 | 300 GB/s | 1,500 GB/s | 5.4 GB/s | 7.5 TB/hr | 100 GbE |
| Elastic Example 2 | 10 TB | 217.6 TB | 640 TB | 512 TB | 256 TB | 22,400,000 | 8,000,000 | 800 GB/s | 4,000 GB/s | 14.4 GB/s | 20.0 TB/hr | 100 GbE |
| Elastic Example 3 | 17.5 TB | 380.8 TB | 1,120 TB | 896 TB | 448 TB | 5,600,000 | 5,000,000 | 1,400 GB/s | 7,000 GB/s | 25.0 GB/s | 7.5 TB/hr | 100 GbE |

## Per-Server Performance Values

| Server type | Max SQL flash bandwidth | Max SQL XRMEM bandwidth | Max SQL read IOPS | Max SQL write IOPS |
| --- | ---: | ---: | ---: | ---: |
| X11M Database Server | n/a | n/a | 2,800,000 | 2,500,000 |
| X11M Storage Server | 100 GB/s | 500 GB/s | 2,800,000 | 1,000,000 |

## Sizing And Migration Guidance

- Use ECPU scaling for database software consumption. Customers pay for ECPUs allocated to VM Clusters and can scale database cores online.
- Use database server count for available cores, ECPUs, VM memory, and local storage constraints.
- Use storage server count for usable disk capacity, XRMEM, flash, IOPS, and bandwidth constraints.
- Treat maximum DB size as dependent on local-backup assumptions. Ask whether local backups are required before presenting maximum database size.
- Treat data load rate as a reference point only. The datasheet notes that load rates are typically limited by database server CPU and vary based on load method, indexes, data types, compression, and partitioning.
- For migration proposals, current-state CPU, memory, storage, IOPS, and throughput should be adjusted by agreed modernization factors before mapping to server counts and ECPU quantities.
- For OCI Dedicated Exadata and Database@ platforms, enter requested database/storage server counts and ECPU quantity into the Oracle pricing calculator first, then transpose the calculator rows into the BOM workbook.

## BOM Validation Guidance

When a BOM includes Exadata Database Service on Dedicated Infrastructure X11M:

- Capture platform: OCI Dedicated Exadata, Database@Azure, Database@Google Cloud, or Database@AWS.
- Capture whether the configuration is Base System or elastic X11M.
- Capture database server count and storage server count.
- Capture ECPU quantity and license model.
- Reject or flag Base System requests that try to expand beyond the fixed Base shape or use more than one VM Cluster.
- Flag elastic configurations below 2 database servers or below 3 storage servers.
- Flag elastic configurations above 32 database servers or above 64 storage servers.
- Validate current-state or projected workload requirements against VM memory, usable local storage, Exadata storage capacity, SQL IOPS, SQL bandwidth, and data load-rate constraints when those metrics are provided.
- Use calculator rows for SKU and pricing fields. Do not substitute Cloud@Customer SKU rows for Dedicated Infrastructure rows.
