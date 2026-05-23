# Requirements Gathering

Use this reference when a cloud architect describes an Oracle Cloud architecture or system configuration but has not provided complete Oracle Cost Estimator line items.

The goal is to collect enough quantities and configuration values to create estimator-ready BOM rows. Ask only the questions needed for the services mentioned by the user.

## General Questions

Ask these when missing:

- Workload or project name.
- Region and realm, defaulting to `PUBLIC` only if the user does not specify.
- Currency, defaulting to `USD` only if not specified.
- Number of environments, such as production, non-production, test, and disaster recovery.
- Expected hours per month, usually `744` for always-on resources.
- Desired discount percentage.
- License model: BYOL, license included, Universal Credits, or unknown.
- Whether pricing should be list-price only, discounted estimate, or both.

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

- Infrastructure generation or model if known.
- Number of database servers.
- Number of storage servers.
- ECPU quantity.
- Dedicated infrastructure or Cloud@Customer.

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

Do not invent Oracle SKU prices. Use user-provided Oracle Cost Estimator data or current Oracle pricing sources only when explicitly requested and verified.
