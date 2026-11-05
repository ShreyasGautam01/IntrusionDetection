# Proposed Primary Feature Set (Draft)

**Status:** Review draft; not frozen and not used for model fitting.

**Config:** `primary-features-draft-1` · **Generated UTC:** `2026-11-05T20:43:19Z` · **Base commit:** `8ef7a740eed011ebffe5def13688bc0e6c7222a9`.

Dataset SHA-256 values are recorded in `primary_feature_set_draft.json` (`NF-UNSW-NB15-v3` `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`, `NF-CSE-CIC-IDS2018-v3` `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74`).

## Proposal

Include all **46** shared `predictive_candidate` columns from the feature registry, in the audited NetFlow-v3 dictionary order. Keep the complete 53-feature interface visible in the registry. The other **7** features remain present in the source files and audit records but are excluded from this proposed predictive matrix because their draft roles are audit/split metadata or identifier-like.

The complete 53-row decision table is `primary_feature_set_draft.csv`; the ordered model-input list, dataset hashes, and generation provenance are in `primary_feature_set_draft.json`.

## Explicitly excluded from this candidate matrix

| Feature | Draft role | Reason retained outside predictors |
|---|---|---|
| `IPV4_SRC_ADDR` | `identifier_like` | Identifier-like; retain for audit/split only pending explicit review |
| `IPV4_DST_ADDR` | `identifier_like` | Identifier-like; retain for audit/split only pending explicit review |
| `L4_SRC_PORT` | `identifier_like` | Identifier-like; retain for audit/split only pending explicit review |
| `L4_DST_PORT` | `identifier_like` | Identifier-like; retain for audit/split only pending explicit review |
| `DNS_QUERY_ID` | `identifier_like` | Identifier-like; retain for audit/split only pending explicit review |
| `FLOW_START_MILLISECONDS` | `audit_split_metadata` | Retain for chronology/complete-flow checks; raw absolute value excluded pending lock |
| `FLOW_END_MILLISECONDS` | `audit_split_metadata` | Retain for chronology/complete-flow checks; raw absolute value excluded pending lock |

## Required review

This is a translation of the current draft registry, not a scientific decision. Review the candidate set before freezing it, especially the DNS query identifier, absolute timestamps, endpoint addresses and ports, and `FTP_COMMAND_RET_CODE` (which varies in UNSW but is constant in CIC2018). Do not silently alter this list. The compact 8-feature sensitivity has its own crosswalk and port decision.

Target label values do not determine this proposal. Raw datasets were not modified.
