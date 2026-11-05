# E0/E0.5 completion status

**Status:** Incomplete; no model has been trained.  
**Active pair:** NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3.  
**ToN-IoT:** Excluded from the active project scope.

The inherited `REPORT.md`, `audit.json`, `schema.csv`, and
`target_value_counts.csv` document the completed acquisition and schema audit
for the two active datasets. `feature_registry.csv` records the draft role for
all 53 features and both targets. `e0_e05_design.md` records the proposed
label-blind split and source-fitted missing/non-finite handling rules.

A focused streaming pass was started to calculate CIC2018 duplicate-vector
label conflicts, daily temporal coverage and attack episodes, deterministic
partition counts, and exact feature-vector intersections. It did not produce
a final report: the SQLite overlap join was not indexed by vector key and did
not finish in a practical review window. Its partial temporary database was
discarded. No partial counts are reported as findings.

Remaining before E0 can close:

1. Rerun the focused calculation with indexed or externally sorted vector
   membership so cross-boundary overlaps complete efficiently.
2. Review the proposed hash-based 60/20/20 UNSW split against the temporal
   control and host/session grouping provisions in the frozen methodology.
3. Implement and persist the UNSW-training-fitted median replacement values;
   demonstrate identical application to calibration, source test, and target.
4. Review and freeze the feature registry and conservative source/target
   family matrix before the pilot.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
