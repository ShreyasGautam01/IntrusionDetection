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
| Protocol | `PROTOCOL` | `PROTOCOL` | Preserve numeric IP protocol identifier byte | Supplied dictionary defines this as the IP protocol identifier byte; observed code sets differ, so retain the shared code semantics and do not remap values |
| TCP flags | `TCP_FLAGS` | `TCP_FLAGS` | Preserve the common v3 field | Supplied dictionary defines both as cumulative of all TCP flags; no client/server recombination is proposed |
| Packets per second | Derived from total packets and duration | Same | `total_packets / (duration_ms / 1000)` | Zero-duration flows produce missing values; inspect count and apply the frozen source-training-only replacement policy if approved |

## Required checks before freezing

1. Verify the dataset dictionary’s duration units and the meaning of `PROTOCOL` codes in both audited files.
2. Review `representation_input_check.json`: the narrow feature-only pass found 122,493 source zero-duration flows and no target zero-duration flows. The derived packet-rate feature must therefore map zero-duration source cases to missing before source-training-only median replacement; never divide by zero or drop those rows.
3. The supplied v3 dictionary defines `PROTOCOL` as an IP protocol identifier byte and `TCP_FLAGS` as cumulative TCP flags, allowing direct v3 column alignment. The feature-only scan found 255 distinct source protocol codes and six target codes; codes 1, 2, 6, 17, and 47 are shared, while 58 occurs only in the target. The [IANA protocol-number registry](https://www.iana.org/assignments/protocol-numbers) identifies these as standardized protocol numbers, including target code 58 (IPv6-ICMP). This supports preserving numeric codes but does not make their marginal distributions equivalent.
4. Resolve whether ports are allowed as predictive inputs in this specifically named sensitivity. TAN-IDS includes bounded numeric ports, while the current project registry flags them as identifier-like pending review.
5. Freeze the exact operation order, derived-column names, and source-only missing-value behavior before any E1 fitting.

The cited TAN-IDS description maps duration, packet/byte totals, source/destination ports, protocol, TCP flags, and packet rate into its eight-dimensional representation. The v3 feature dictionary directly resolves the protocol and cumulative TCP flag fields. Packet rate remains a derived field; the formula above and its zero-duration policy are a draft. These details motivate this proposal but do not adopt TAN-IDS's data preparation or evaluation protocol. [TAN-IDS article and Table 5](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0346801)
