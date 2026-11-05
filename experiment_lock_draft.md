
# Experiment Lock Draft

**Status:** Draft — not final until active dataset audit and pilot pass.  
**Last updated:** 2026-11-05.

## Initial locked scope

The first experimental lock covers **only**:

- NF-UNSW-NB15-v3
- NF-CSE-CIC-IDS2018-v3

NF-ToN-IoT-v3 is deferred and is not part of the initial lock.

## Core transfer matrix

### In-domain
- UNSW → UNSW
- CIC2018 → CIC2018

### Cross-domain
- UNSW → CIC2018
- CIC2018 → UNSW

### Compound shift
The same two transfer directions will contain a predefined analysis of target attack families that are unsupported by source training, using the conservative label-mapping policy.

## Why the initial lock has two datasets

Two datasets already provide:

- two independent source domains;
- two transfer directions;
- two in-domain controls;
- multiple reliability methods;
- multiple random seeds;
- compound-shift analysis;
- family-level diagnostics;
- review-budget analysis.

The main question is about transport across a domain boundary, not about maximizing the number of datasets.

## Deferred ToN-IoT replication

ToN-IoT-v3 may be added later as a replication experiment.

It must not affect:

- the initial model design;
- signal implementation;
- primary endpoint;
- initial experiment lock;
- method selection.

If activated, it receives its own documented replication configuration and is treated as secondary evidence.

## Everything else remains unchanged

The freeze boundary, target-label firewall, signal definitions, endpoints, statistical plan, sanity controls, and invalid-run rules remain as previously specified.
