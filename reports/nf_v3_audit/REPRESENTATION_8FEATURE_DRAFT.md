# Compact 8-Feature Representation Crosswalk (Draft)

**Status:** Proposed mapping for review; not frozen or applied. No dataset values were transformed and no model was trained.

## Purpose

The frozen methodology names a compact 8-feature NetFlow representation inspired by TAN-IDS as a sensitivity analysis. The frozen documents do not enumerate its v3 column mapping. This draft links the eight common attributes in TAN-IDS Table 5 to the audited NetFlow-v3 schema. The machine-readable row-level mapping is in `representation_8feature_draft.csv`.

The crosswalk borrows only the 8-feature interface. It does not import TAN-IDS label taxonomy, sample filtering, split proportions, classifier settings, or target adaptation. This project retains its frozen protocol and data governance.

## Proposed crosswalk

| Common attribute | Source v3 | Target v3 | Proposed operation | Review point |
|---|---|---|---|---|
| Flow duration | `FLOW_DURATION_MILLISECONDS` | `FLOW_DURATION_MILLISECONDS` | Identity, milliseconds | Confirm dictionary units |
| Total packets | `IN_PKTS`, `OUT_PKTS` | `IN_PKTS`, `OUT_PKTS` | Sum the two directions | Derived column; do not rewrite input |
| Total bytes | `IN_BYTES`, `OUT_BYTES` | `IN_BYTES`, `OUT_BYTES` | Sum the two directions | Derived column; do not rewrite input |
| Source port | `L4_SRC_PORT` | `L4_SRC_PORT` | Numeric bounded port | Registry currently marks identifier-like; requires explicit feature-governance approval for this sensitivity |
| Destination port | `L4_DST_PORT` | `L4_DST_PORT` | Numeric bounded port | Same governance issue as source port |
| Protocol | `PROTOCOL` | `PROTOCOL` | Preserve numeric code | Confirm code meanings align; ranges alone are not evidence |
| TCP flags | `TCP_FLAGS` | `CLIENT_TCP_FLAGS` bitwise OR `SERVER_TCP_FLAGS` | Source field; target aggregate | Confirm direction semantics and source/target encoding equivalence |
| Packets per second | Derived from total packets and duration | Same | `total_packets / (duration_ms / 1000)` | Zero-duration flows produce missing values; inspect count and apply the frozen source-training-only replacement policy if approved |

## Required checks before freezing

1. Verify the dataset dictionary’s duration units and the meaning of `PROTOCOL` codes in both audited files.
2. Check only the necessary schema-level facts for the draft mapping: zero-duration count, source/target flag field semantics, and whether the proposed derived calculations are representable without overflow. Do not consult target labels.
3. Resolve whether ports are allowed as predictive inputs in this specifically named sensitivity. TAN-IDS includes bounded numeric ports, while the current project registry flags them as identifier-like pending review.
4. Freeze the exact operation order, derived-column names, and source-only missing-value behavior before any E1 fitting.

The cited TAN-IDS description maps duration, packet/byte totals, source/destination ports, protocol, TCP flags, and packet rate into its eight-dimensional representation. Its target flags use a bitwise aggregation of directional fields; its packet rate is a rate feature. These details motivate this proposal but do not resolve the v3-specific semantics listed above. [TAN-IDS article and Table 5](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0346801)
