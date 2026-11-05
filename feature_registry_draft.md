# Feature Registry Draft

**Status:** Draft — no model training until finalized.  
**Source:** Codex NF-v3 audit, commit 748ddb9.

## Principle

The 53-field NetFlow-v3 dataset is not automatically equivalent to a 53-field predictive feature matrix.

Each field must have a declared role.

## Preliminary categories

### Category A — Candidate predictive features

Numeric flow measurements such as:

- byte counts;
- packet counts;
- durations;
- TTL values;
- packet-length statistics;
- throughput;
- retransmission statistics;
- inter-arrival statistics;
- protocol indicators.

These remain candidates pending source-only preprocessing tests.

### Category B — Audit/split metadata only

The following should not automatically enter the predictive matrix:

- FLOW_START_MILLISECONDS;
- FLOW_END_MILLISECONDS.

They are valuable for chronological splitting and temporal diagnostics, but raw absolute time can encode capture-period identity and create artificial transfer failure.

### Category C — Identifier-like fields requiring explicit decision

- IPV4_SRC_ADDR;
- IPV4_DST_ADDR;
- L4_SRC_PORT;
- L4_DST_PORT;
- DNS_QUERY_ID.

These may encode host, service, transaction, or capture identity.

Before modeling, test whether retaining them creates an unacceptable shortcut/identity effect.

### Category D — Targets

Never predictive:

- Label;
- Attack.

## Current recommendation

Do **not** silently drop Category B/C fields.

Instead:

1. implement them as metadata initially;
2. construct a strict feature registry;
3. run source-only evidence and leakage/shortcut checks;
4. document the final inclusion/exclusion decision;
5. freeze before the pilot.

If the primary 53-feature interpretation in the frozen methodology is judged to require a substantive change, record that as a methodology-change proposal rather than editing the frozen file silently.

## Non-finite policy

UNSW contains empty/+Inf values in:

- SRC_TO_DST_SECOND_BYTES;
- DST_TO_SRC_SECOND_BYTES.

The replacement strategy must be:

- deterministic;
- source-fitted where statistics are required;
- identical at target application time;
- documented before pilot.

The target cannot supply replacement statistics.
