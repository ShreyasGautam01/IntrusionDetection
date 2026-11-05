
# Dataset Selection and Locking Protocol

**Status:** Working document  
**Last updated:** 2026-11-05

## Active dataset scope

The project will **not** prepare all downloaded datasets at once.

### Core study

Only these two datasets are active for dataset auditing, preprocessing, pilot development, and the initial experiment lock:

- **NF-UNSW-NB15-v3**
- **NF-CSE-CIC-IDS2018-v3**

These two are sufficient for the core scientific question because they provide:

- a common NetFlow-v3 representation;
- materially different traffic environments;
- source→target and reverse target→source transfer;
- a meaningful cross-domain experiment;
- different attack taxonomies, allowing a conservative compound-shift analysis.

TAN-IDS independently uses UNSW-NB15 and NF-CSE-CIC-IDS2018 as its principal two-domain transfer setting and maps them into a common NetFlow representation. citeturn638957search0turn638957search2

### Deferred dataset

**NF-ToN-IoT-v3 is downloaded but deferred.**

It is not part of the initial:

- dataset audit;
- feature registry;
- label-mapping lock;
- pilot;
- experiment lock;
- core results.

It becomes an optional replication/stress-test dataset only after the two-dataset study is complete and stable.

The existence of a third dataset does not create a requirement to use it.

## Why two datasets are enough

The scientific question is primarily about:

> whether a frozen source-side reliability layer transports across a deployment-domain boundary.

A two-domain design already permits:

1. A→A in-domain control.
2. B→B in-domain control.
3. A→B transfer.
4. B→A transfer.

That gives two directions, two in-domain controls, five reliability mechanisms, multiple seeds, compound-shift analysis, family-level analysis, and review-budget evaluation.

Adding ToN-IoT before the core pipeline is validated would primarily increase:

- implementation burden;
- data-processing burden;
- multiple comparisons;
- opportunities for taxonomy/feature confounds;
- paper scope.

It is therefore better treated as replication rather than as a prerequisite.

## Active data directory

For the current phase, place only the two core datasets under the active project data area:

`data/raw/NF-UNSW-NB15-v3/`

`data/raw/NF-CSE-CIC-IDS2018-v3/`

ToN-IoT may remain outside the active project directory or under a clearly marked deferred location.

## Current catalogue facts

The UQ catalogue reports:

### NF-UNSW-NB15-v3
- 2,365,424 flows
- 127,639 attack
- 2,237,731 benign
- nine attack families

### NF-CSE-CIC-IDS2018-v3
- 20,115,529 flows
- 2,600,903 attack
- 17,514,626 benign
- six attack families

These are reference catalogue counts. Exact downloaded-file counts must be generated locally.

Source: https://staff.itee.uq.edu.au/marius/NIDS_datasets/

## Selection rule

The two-dataset pair remains sufficient unless the audit reveals a substantive incompatibility that cannot be resolved without compromising the experiment.

Do not add a third dataset merely to increase apparent breadth.

## Deferred replication criterion

To activate NF-ToN-IoT-v3 later, all of the following must already be true:

- core two-dataset pipeline is reproducible;
- experiment lock is frozen;
- primary results are complete;
- label/family controls are stable;
- compute/storage budget is available;
- the additional dataset adds a scientifically meaningful replication rather than another source of ambiguity.
