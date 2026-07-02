# Exadata Cloud@Customer X11M Configuration Reference

Use this reference when preparing or validating BOM rows for Oracle Exadata Database Service on Cloud@Customer X11M. Sources supplied by the user:

- `exadb-cc-x11m-ds.pdf`: `Exadata Database Service on Cloud@Customer X11M`, Version 1.4, Oracle public datasheet, copyright 2026.
- `/Users/PWSTEPHE/Downloads/exadb-cc-x11m-ds (1).pdf`: same public datasheet, Version 1.4, 13 pages, ingested 2026-06-26.
- `ExaC@C X11M-config.pptx`: `Exadata Cloud@Customer X11M Technical Overview`, Oracle Exadata Product Management, April 2026.
- `Announcing Oracle Exadata X11 Storage Servers and Zero Data Loss Recovery Appliance RA26_RA26-Z _ exadata.pdf`: Oracle Exadata Product Management blog print, June 30, 2026.
- `ORACLE+PAAS+AND+IAAS+PUBLIC+CLOUD+GLOBAL+PRICE+LIST.pdf`: Oracle PaaS and IaaS Public Cloud Global Price List, `Last updated: July 1, 2026`.

This reference captures configuration rules and sizing facts that affect BOM preparation. It is not a pricing source.

For current Cloud@Customer X11/X11M price-list rows, read `references/exadata-database-machine-x11m.md`. It includes July 1, 2026 eSource rows for X11M Extreme Flash, X11 High Capacity, X11 Extreme Flash, data/device retention, and partner-hardware variants.

## Configuration Rules

- Each rack should be modeled as prepopulated with 2 database servers.
- Base System starts with 2 Base database servers and 3 Base storage servers.
- Elastic configurations start at 2 database servers and 3 storage servers.
- Elastic configurations can scale up to 16 total database plus storage servers in the initial rack.
- Elastic configurations can scale across multiple racks up to 32 database servers and 64 storage servers.
- Maximum total racks, including the initial rack: 6.
- Expansion racks can contain up to 18 total servers.
- Expansion racks require at least 4 servers.
- Minimum expansion-rack configuration starts with 1 storage server plus at least 3 additional database or storage servers.
- Database server choices are Base, Standard, Large, and Extra Large.
- Storage server choices are Base, High Capacity, and Extreme Flash from the Cloud@Customer X11M datasheet.
- The June 30, 2026 Oracle announcement adds Exadata X11 High Capacity and X11 Extreme Flash storage servers for Cloud@Customer with Exadata X11M and later database servers. X11 storage servers do not include XRMEM unless memory is added later.
- Exadata X11 High Capacity-Z is available for on-premises Exadata Database Machine, not Cloud@Customer, based on the June 30, 2026 announcement.
- The storage server model selected when the Cloud@Customer system is initially deployed determines the storage server model that can be added for future storage expansions.
- Any database server type can be combined with any storage server type.
- All database servers in one system must be the same type.
- All storage servers in one system must be the same type.
- The Base System example uses Base database servers and Base storage servers.
- A BOM may still use the Base System Rack price-list row with separately requested storage-server rows, such as High Capacity storage servers, when the user explicitly asks for a Base rack with non-Base storage. Keep the rack SKU and storage SKU assumptions visible in separate rows.
- Standard, Large, and Extra Large database servers include XRMEM; Base database servers do not.
- Extreme Flash storage includes flash cache and flash storage.
- High Capacity storage includes flash cache and disk storage.
- X11M HC, EF, and HC-Z storage includes XRMEM. X11 HC, EF, and HC-Z storage does not include XRMEM unless memory is added later.
- Usable storage capacity is after ASM high redundancy and drive-failure recovery overhead, before database compression.
- Additional database servers increase available database compute capacity, including usable memory and database cores/ECPUs.
- Three storage servers are the minimum storage-server count because three storage subsystems are required for high redundancy.
- Default storage redundancy should be High unless the user or source architecture explicitly specifies Normal redundancy.
- High redundancy keeps two mirrored copies of the original data and can survive failure of two HDAs.
- Normal redundancy keeps one mirrored copy of the original data, provides more usable storage capacity than high redundancy, and can survive failure of one HDA.
- Infrastructure subscription minimum term is 4 years.
- Infrastructure subscription includes disk/flash, IOPS, and memory for the selected configuration. Exadata Database Service software licensing is based on ECPUs allocated to a VM Cluster.
- Supported software license models are License Included and BYOL. BYOL supports Oracle Database Enterprise Edition entitlements; Oracle Database Standard Edition is not supported.
- The same Exadata Cloud@Customer infrastructure can run Exadata Database Service and Autonomous Database side by side.

## VM And Cluster Limits

- Minimum database cores per VM: 2.
- Maximum VMs per database server: 8.
- Maximum VMs per database server for systems containing Base database servers: 4.
- Maximum VM clusters per system with 2 database servers: 12.
- Maximum VM clusters per system with more than 2 database servers: 24.
- Maximum VM clusters per system is the same whether or not the system contains Base database servers.
- Maximum usable local storage per database server: 2,243 GB.
- Maximum usable local storage per Base System database server: 1,084 GB.
- VM image size minimum and default: 244 GB, including 60 GB for `/u02`.
- Oracle homes file system can be up to 900 GB per VM, but the actual maximum can be lower because it is limited by total local storage used by all VM file systems.

## Per-Server Technical Values

### Database Servers

| Database server type | Usable database cores | Total ECPUs | Memory available for VMs |
| --- | ---: | ---: | ---: |
| Base | 30 | 120 | 660 GB |
| Standard | 190 | 760 | 1,390 GB |
| Large | 190 | 760 | 2,090 GB |
| Extra Large | 190 | 760 | 2,800 GB |

### Storage Servers

| Storage server type | Storage cores | XRMEM capacity | Flash cache capacity | Usable storage capacity |
| --- | ---: | ---: | ---: | ---: |
| Base | 32 | 0 TB | 12.8 TB | 35.6 TB |
| Extreme Flash | 64 | 1.25 TB | 27.2 TB | 37.2 TB |
| High Capacity | 64 | 1.25 TB | 27.2 TB | 80.0 TB |

## Datasheet Example Configurations

These examples are representative configurations from the datasheet, not the only valid combinations.

| Example | Database servers | Storage servers | Total DB cores | Total ECPUs | Max VM clusters | Total usable storage |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Base System | 2 Base | 3 Base | 60 | 240 | 12 | 106 TB Base storage |
| Elastic Example 1 | 2 Standard, Large, or Extra Large | 3 High Capacity or Extreme Flash | 380 | 1,520 | 12 | 240 TB HC disk or 111 TB EF flash |
| Elastic Example 2 | 8 Standard, Large, or Extra Large | 8 High Capacity or Extreme Flash | 1,520 | 6,080 | 24 | 640 TB HC disk or 298 TB EF flash |
| Elastic Example 3 | 2 Standard, Large, or Extra Large | 14 High Capacity or Extreme Flash | 380 | 1,520 | 12 | 1,120 TB HC disk or 521 TB EF flash |

## Datasheet Capacity And Performance Examples

Use these values as technical sizing reference points when current-state database consumption needs to be projected into future-state Cloud@Customer resources. They are not SKU prices.

| Example | XRMEM | Flash cache | EF usable flash | HC usable disk | Max DB size HC no local backup | Max DB size HC local backup | Max SQL read IOPS | Max SQL write IOPS | Max flash bandwidth | Max XRMEM bandwidth | Max disk bandwidth | Max data load rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base System | n/a | 38.4 TB | n/a | 106 TB | 85 TB | 42 TB | 597,000 | 544,000 | 37.5 GB/s | n/a | 2.7 GB/s | 3.8 TB/hr |
| Elastic Example 1 | 3.75 TB | 81.6 TB | 111 TB | 240 TB | 192 TB | 96 TB | 5,600,000 | 3,000,000 | 300 GB/s | 1,500 GB/s | 5.4 GB/s | 7.5 TB/hr |
| Elastic Example 2 | 10 TB | 217.6 TB | 298 TB | 640 TB | 512 TB | 256 TB | 22,400,000 | 8,000,000 | 800 GB/s | 4,000 GB/s | 14.4 GB/s | 20.0 TB/hr |
| Elastic Example 3 | 17.5 TB | 380.8 TB | 521 TB | 1,120 TB | 896 TB | 448 TB | 5,600,000 | 5,000,000 | 1,400 GB/s | 7,000 GB/s | 25.0 GB/s | 7.5 TB/hr |

## Per-Server Performance Values

| Database server type | Max SQL flash bandwidth | Max SQL read IOPS | Max SQL write IOPS |
| --- | ---: | ---: | ---: |
| Base | n/a | 298,500 | 272,000 |
| Standard, Large, Extra Large | n/a | 2,800,000 | 2,500,000 |

| Storage server type | Max SQL flash bandwidth | Max SQL XRMEM bandwidth | Max SQL read IOPS | Max SQL write IOPS |
| --- | ---: | ---: | ---: | ---: |
| Base | 12.5 GB/s | n/a | 298,500 | 260,000 |
| Extreme Flash | 100 GB/s | 500 GB/s | 2,800,000 | 1,000,000 |
| High Capacity | 100 GB/s | 500 GB/s | 2,800,000 | 1,000,000 |

## Sizing And Migration Guidance

- Use ECPU scaling for database software consumption; customers pay for ECPUs allocated to VM Clusters and can scale ECPUs online.
- Use database server type/count for available cores, ECPUs, and VM memory constraints.
- Use storage server type/count for usable capacity, XRMEM, flash cache, IOPS, and bandwidth constraints.
- Treat maximum DB size as dependent on local-backup assumptions. Ask whether local backups are required before presenting maximum database size.
- Treat data load rate as a reference point only. The datasheet notes that load rates are typically limited by database server CPU and vary based on load method, indexes, data types, compression, and partitioning.
- For migration proposals, current-state CPU, memory, storage, IOPS, and throughput should be adjusted by agreed modernization factors before mapping to server counts and ECPU quantities.

## BOM Validation Guidance

When a BOM includes Exadata Cloud@Customer X11M:

- Capture the database server type and count.
- Capture the storage server type and count.
- Capture storage generation and XRMEM assumption: X11M with XRMEM, or X11 without XRMEM unless a memory expansion is included.
- Treat 2 database servers as the baseline physical rack population for each rack.
- Confirm whether the design is the Base System or an elastic configuration.
- Reject or flag mixed database server types in one system.
- Reject or flag mixed storage server types in one system.
- For Cloud@Customer storage expansions, confirm the added storage server model matches the model selected at initial deployment.
- Flag X11 High Capacity-Z as on-premises only unless a later current Oracle source says it is available for Cloud@Customer.
- Flag configurations below 2 database servers or below 3 storage servers.
- Flag initial rack configurations above 16 total database plus storage servers unless the BOM explicitly includes a multi-rack design.
- For expansion racks, flag fewer than 4 servers, more than 18 total servers, or no storage server.
- For expansion racks, confirm at least 1 storage server plus at least 3 additional database or storage servers.
- Flag multi-rack configurations above 32 database servers or above 64 storage servers.
- Flag multi-rack configurations above 6 total racks.
- Calculate total ECPUs, database cores, memory, storage cores, XRMEM, flash cache, and usable storage from the selected per-server values when explicit totals are not supplied.
- Validate current-state or projected workload requirements against DB memory, usable local storage, Exadata storage capacity, SQL IOPS, SQL bandwidth, and data load-rate constraints when those metrics are provided.
- Identify storage redundancy as High or Normal when usable storage capacity is part of the BOM; default to High when unspecified.
- If using datasheet usable-storage figures, note that they are based on high redundancy unless a Normal redundancy capacity has been supplied or calculated separately.
- Ask whether local backups are required before using maximum database size values.
- Ask for License Included or Bring Your Own License when software licensing is in scope.
- Ask whether installation and activation should be included as a one-time annual-cost row. Current price-list handling for `B91390` treats it as an `Each` service, excluded from recurring monthly totals and included once in discounted annual cost when requested.
- Treat datasheet capacities and performance metrics as technical sizing references, not list prices.
- Use Oracle Cost Estimator rows or the current approved Oracle pricing source for SKU and price fields.

## Network And Facilities Inputs

Ask for these only when the BOM needs rack/network/facility assumptions:

- Database server network option: 4 x 10/25 Gb SFP28 Ethernet, 4 x 10 Gb RJ45 Ethernet, or 4 x 100 Gb QSFP28 Ethernet.
- 4 x 100 Gb QSFP28 Ethernet is available only with Standard, Large, and Extra Large database servers.
- Control plane server network option: 2 x 10/25 Gb SFP28 Ethernet or 2 x 10 Gb RJ45 Ethernet.
- Minimum internet connectivity for the control plane: 50 Mbps down and 10 Mbps up.
- Database servers and control plane servers connect directly to the customer data center network.
- Customer standard switches can be used, as with on-premises Exadata.
- Switches can optionally be placed inside the Exadata rack.
- Customer controls client network configuration, including flexible VLAN configurations, separate client and backup networks, DNS, NTP, and routers.
- Each rack is 42 RU and includes 2 redundant PDUs, 2 x 36-port QSFP28 100 Gb/s RoCE switches, and 1 x 48-port Cisco Ethernet switch for Oracle Cloud Operations infrastructure administration.
- Multiple-rack configurations also include an additional 36-port QSFP28 100 Gb/s RoCE switch.
- Datasheet example rack environmental values:
  - Base System: 999.4 lb, maximum 6.2 kW / 6.3 kVA, typical 4.3 kW / 4.4 kVA, maximum cooling 21,072 BTU/hr, maximum airflow 976 CFM.
  - Elastic Example 1 with Standard DB and High Capacity storage: 1,035.8 lb, maximum 7.5 kW / 7.7 kVA, typical 5.3 kW / 5.4 kVA, maximum cooling 25,666 BTU/hr, maximum airflow 1,188 CFM.
  - Elastic Example 1 with Standard DB and Extreme Flash storage: 993.8 lb, maximum 7.1 kW / 7.3 kVA, typical 5.0 kW / 5.1 kVA, maximum cooling 24,356 BTU/hr, maximum airflow 1,128 CFM.
- Airflow must be front-to-back.
- Operating temperature and humidity: 5 C to 32 C, 10% to 90% relative humidity, non-condensing.
- Operating altitude up to 3,048 m; maximum ambient temperature is derated by 1 C per 300 m above 900 m.
