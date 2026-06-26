# Exadata Cloud@Customer X11M Configuration Reference

Use this reference when preparing or validating BOM rows for Oracle Exadata Database Service on Cloud@Customer X11M. Sources supplied by the user:

- `exadb-cc-x11m-ds.pdf`: `Exadata Database Service on Cloud@Customer X11M`, Version 1.4, Oracle public datasheet, copyright 2026.
- `ExaC@C X11M-config.pptx`: `Exadata Cloud@Customer X11M Technical Overview`, Oracle Exadata Product Management, April 2026.

This reference captures configuration rules and sizing facts that affect BOM preparation. It is not a pricing source.

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
- Storage server choices are Base, High Capacity, and Extreme Flash.
- Any database server type can be combined with any storage server type.
- All database servers in one system must be the same type.
- All storage servers in one system must be the same type.
- The Base System example uses Base database servers and Base storage servers.
- A BOM may still use the Base System Rack price-list row with separately requested storage-server rows, such as High Capacity storage servers, when the user explicitly asks for a Base rack with non-Base storage. Keep the rack SKU and storage SKU assumptions visible in separate rows.
- Standard, Large, and Extra Large database servers include XRMEM; Base database servers do not.
- Extreme Flash storage includes flash cache and flash storage.
- High Capacity storage includes flash cache and disk storage.
- Usable storage capacity is after ASM high redundancy and drive-failure recovery overhead, before database compression.
- Additional database servers increase available database compute capacity, including usable memory and database cores/ECPUs.
- Three storage servers are the minimum storage-server count because three storage subsystems are required for high redundancy.
- Default storage redundancy should be High unless the user or source architecture explicitly specifies Normal redundancy.
- High redundancy keeps two mirrored copies of the original data and can survive failure of two HDAs.
- Normal redundancy keeps one mirrored copy of the original data, provides more usable storage capacity than high redundancy, and can survive failure of one HDA.

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

| Example | Database servers | Storage servers | Total ECPUs | Max VM clusters | Total usable storage |
| --- | --- | --- | ---: | ---: | --- |
| Base System | 2 Base | 3 Base | 240 | 12 | 106 TB Base storage |
| Elastic Example 1 | 2 Standard, Large, or Extra Large | 3 High Capacity or Extreme Flash | 1,520 | 12 | 240 TB HC disk or 111 TB EF flash |
| Elastic Example 2 | 8 Standard, Large, or Extra Large | 8 High Capacity or Extreme Flash | 6,080 | 24 | 640 TB HC disk or 298 TB EF flash |
| Elastic Example 3 | 2 Standard, Large, or Extra Large | 14 High Capacity or Extreme Flash | 1,520 | 12 | 1,120 TB HC disk or 521 TB EF flash |

## BOM Validation Guidance

When a BOM includes Exadata Cloud@Customer X11M:

- Capture the database server type and count.
- Capture the storage server type and count.
- Treat 2 database servers as the baseline physical rack population for each rack.
- Confirm whether the design is the Base System or an elastic configuration.
- Reject or flag mixed database server types in one system.
- Reject or flag mixed storage server types in one system.
- Flag configurations below 2 database servers or below 3 storage servers.
- Flag initial rack configurations above 16 total database plus storage servers unless the BOM explicitly includes a multi-rack design.
- For expansion racks, flag fewer than 4 servers, more than 18 total servers, or no storage server.
- For expansion racks, confirm at least 1 storage server plus at least 3 additional database or storage servers.
- Flag multi-rack configurations above 32 database servers or above 64 storage servers.
- Flag multi-rack configurations above 6 total racks.
- Calculate total ECPUs, database cores, memory, storage cores, XRMEM, flash cache, and usable storage from the selected per-server values when explicit totals are not supplied.
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
- Airflow must be front-to-back.
- Operating temperature and humidity: 5 C to 32 C, 10% to 90% relative humidity, non-condensing.
- Operating altitude up to 3,048 m; maximum ambient temperature is derated by 1 C per 300 m above 900 m.
