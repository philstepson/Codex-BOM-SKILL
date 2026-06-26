# Requirements Gathering

Use this reference when a cloud architect describes an Oracle Cloud architecture or system configuration but has not provided complete Oracle Cost Estimator line items.

The goal is to collect enough quantities and configuration values to create estimator-ready BOM rows. Ask only the questions needed for the services mentioned by the user.

## General Questions

Ask these when missing:

- Workload or project name.
- Region and realm, defaulting to `PUBLIC` only if the user does not specify.
- Currency, defaulting to `USD` only if not specified.
- Number of environments, such as production, non-production, test, and disaster recovery.
- Environment assignment for each resource group or SKU row. Ask which environment is being described when the user provides resources without an environment label.
- Expected hours per month, usually `744` for always-on resources.
- Desired discount percentage. The generated workbook accepts either whole-number entry such as `15` or decimal entry such as `0.15`.
- License model: BYOL, license included, Universal Credits, or unknown.
- Whether pricing should be list-price only, discounted estimate, or both.
- Whether the customer-facing BOM should show list price only. If yes, keep discount calculations out of the customer-facing view.
- Any explicit add-on SKUs the user wants included, including service, installation, activation, or other non-product price-list rows.

## Environment Modeling

Use this section for customer proposal workbooks, multi-environment BOMs, migration assessments, and any request based on current-state database or server consumption metrics.

Ask:

- Which environment each described workload belongs to: production, non-production, test/dev, disaster recovery, shared/common, or a customer-specific label.
- Whether each environment needs separate SKU quantities, hours, discount assumptions, ramp timing, or inclusion flags.
- Whether shared infrastructure should be allocated to one environment, duplicated across environments, or tracked as a separate shared environment.
- Whether the customer wants the workbook to show multiple environments in one BOM, such as Production, Test/Dev, and DR.
- Whether a separate customer-facing BOM sheet is required. For customer-facing output, show all SKUs, quantities, metrics or billing basis, and list prices.
- Whether a configured-system summary is desired, showing requested versus configured versus available processor, memory, and storage resources.
- Whether an optional Draw.io-style block diagram would be useful for the proposal.

Do not infer environment assignment from row order or service name. If the user gives only resources or SKUs, ask for the environment before building a multi-environment workbook.

## Database Services

Use this section for Autonomous Database, Exadata Database Service, Base Database Service, MySQL HeatWave, and named database platform services.

Ask:

- Database service type: Autonomous, Exadata dedicated infrastructure, Base Database Service, MySQL HeatWave, or other.
- Deployment model: shared, dedicated, serverless, Cloud@Customer, or unknown.
- Compute measure required by the service: ECPUs, OCPUs, database servers, storage servers, or HeatWave nodes.
- Storage amount in GB/TB.
- Number of database instances or clusters.
- Hours per month.
- License model.
- Backup retention period and backup storage assumptions.
- HA/DR requirements: single AD, multiple ADs, cross-region standby, Data Guard, Autonomous Data Guard, or none.

For Exadata Database Service, also ask:

- Platform: OCI Dedicated Exadata, Database@Azure, Database@Google Cloud, Database@AWS, or Exadata Cloud@Customer.
- Infrastructure generation or model if known.
- Number of database servers.
- Number of storage servers.
- Database server model/SKU when known, especially for Exadata Cloud@Customer.
- Storage server model/SKU when known, especially for Exadata Cloud@Customer.
- Rack configuration, expansion rack details, or other Cloud@Customer infrastructure components when applicable.
- ECPU quantity.
- Dedicated infrastructure or Cloud@Customer.

For standard Exadata Dedicated Infrastructure and Database@Azure, Database@Google Cloud, or Database@AWS:

- Use the Oracle pricing calculator output as the source of truth for SKU rows, quantities, unit prices, and monthly costs.
- Treat Database@Azure, Database@Google Cloud, and Database@AWS as Exadata Dedicated Cloud pricing, not Exadata Cloud@Customer pricing.
- For X11M configurations, read `references/exadata-dedicated-infrastructure-x11m.md` before sizing or validating the BOM.
- Ask for BYOL or License Included when the prompt does not specify the license model.
- Ask for the Exadata generation/model if the user might need a prior version. If omitted and the user has not requested a prior generation, state that the latest calculator model is assumed.
- Start from the calculator default quarter rack, 2 database servers, and 3 storage servers unless the user asks for another base configuration.
- Ask for any additional database servers or storage servers because those change the relevant calculator SKU quantities.
- Ask whether the architecture is Base System or elastic X11M. Base System is fixed and non-expandable; elastic X11M starts with 2 database servers and 3 storage servers and can scale to 32 database servers and 64 storage servers.
- Ask whether local backups are required when maximum database size is part of the sizing model.

For Exadata Database Service on Cloud@Customer X11M, read `references/exadata-cloud-at-customer-x11m.md` and gather:

- Base System or elastic configuration.
- Database server type: Base, Standard, Large, or Extra Large.
- Storage server type: Base, High Capacity, or Extreme Flash.
- Database server count and storage server count.
- Whether the design is single-rack or multi-rack.
- Storage redundancy: High redundancy or Normal redundancy. Default to High when unspecified.
- Number of expansion racks and expansion-rack server counts, when multi-rack is in scope.
- VM cluster count and VMs per database server, when VM layout is in scope.
- Required local storage per VM and Oracle homes file-system size assumptions.
- Whether local backups are required, because maximum database size differs with and without local backups.
- License model: License Included or Bring Your Own License.
- Network option for database servers and control plane servers, if the BOM covers rack or facilities inputs.
- Whether installation and activation should be included as a one-time annual-cost row, such as `B91390`.

For a Cloud@Customer X11M Base rack request, use the Base System Rack row when pricing is available. Keep separately requested storage-server type and quantity explicit. A Base rack with High Capacity storage servers should show the Base rack SKU and the High Capacity storage SKU as separate rows rather than hiding the storage selection in the rack row.

For Autonomous Database, also ask:

- Autonomous Transaction Processing, Autonomous Data Warehouse, JSON Database, or other.
- Serverless or dedicated.
- ECPUs.
- Auto-scaling enabled or disabled.
- Database storage.

## Compute

Ask:

- Shape or shape family, such as E5, E4, A1, DenseIO, GPU, or unknown.
- OCPUs per instance.
- Memory per instance.
- Instance count.
- Boot volume size.
- Additional block volume size.
- Hours per month.
- Operating system or image family if relevant.
- Public IP requirements.

## Storage

For Block Volume, ask:

- Volume count.
- Size per volume.
- Performance tier or VPUs/GB.
- Backup policy and retention.
- Cross-region replication requirement.

For Object Storage or Archive Storage, ask:

- Stored data in GB/TB.
- Monthly write/read volume if known.
- Request volume if known.
- Replication, versioning, lifecycle, or retention requirements.

For File Storage, ask:

- File system count.
- Stored data size.
- Snapshot/backup assumptions.
- Mount target count if relevant.

## Networking

Ask only for named networking services or when the architecture implies them:

- Number of VCNs.
- Number of load balancers and bandwidth shape.
- Public or private load balancing.
- NAT gateway count.
- Service gateway count.
- DRG count and attachments.
- FastConnect port speed, provider, and redundant circuit count.
- Site-to-site VPN tunnel count.
- Estimated egress/data transfer if relevant.

## Containers and Kubernetes

For OKE, ask:

- Cluster count.
- Worker node shape.
- Worker node count.
- OCPUs and memory per worker node.
- Hours per month.
- Load balancers required.
- Block volumes or file storage required.
- Registry, logging, and monitoring assumptions.

## Security and Observability

Ask only when these services are in scope or required by the architecture:

- WAF policy count and traffic assumptions.
- Logging volume and retention.
- Monitoring metrics, alarms, and notifications.
- Vault keys and secrets count.
- Bastion sessions or private access requirements.
- Security Zones or Cloud Guard requirements.

## BOM Row Handling

When the user cannot answer a required pricing parameter:

- Create the BOM row anyway if the service belongs in the architecture.
- Leave SKU, unit price, and calculated price fields blank if pricing cannot be determined.
- Add a note explaining the missing input.
- Preserve formulas where possible so values calculate after the missing inputs are entered.

Do not invent Oracle SKU prices. Use user-provided Oracle Cost Estimator data, authenticated Oracle pricing calculator output, or current Oracle pricing sources only when explicitly requested and verified.

Legacy or sample Excel BOMs may contain stale embedded price-list sheets. Use those files as layout, formula, and workflow references only unless their pricing tabs have been refreshed from a current Oracle source and date-verified for the active BOM.

When the user supplies an explicit SKU to add to a BOM:

- Ask for the intended quantity if the user did not provide one and the row is not obviously a single add-on service.
- Search the verified current Oracle eSource price-list PDF by exact SKU first when the SKU is not already present in calculator or estimator rows.
- Use description matching only after exact SKU lookup fails, and ask the user before substituting a similar row.
- Preserve the price-list billing basis in `Custom Note`, especially for one-time, non-metered, installation, or activation service SKUs.
- Add the source document date to the row note when the price came from the eSource PDF or date-verified PDF cache.
- If the SKU is one-time and should be included in the annual estimate, leave recurring monthly cost blank and calculate the discounted annual cost once from quantity and unit price.

Before asking the user to authenticate to eSource, determine whether Oracle Cost Estimator or the Oracle pricing calculator can cover the requested rows. Use the calculator first for nearly all non-Cloud@Customer BOMs. For Exadata Cloud@Customer and other resources that Oracle Cost Estimator or the Oracle pricing calculator does not fully cover, use the user's current authenticated Oracle eSource PDF as a supplemental fallback pricing source when available. A local PDF cache may be used only after checking the current eSource document date. Replace the cached PDF if eSource has a newer document date, then extract only the relevant runtime rows, capture the document date from the PDF front page, and add a BOM note for any row priced from that PDF. Do not treat previously extracted pricing tables as authoritative across runs.
