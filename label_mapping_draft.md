# Label Mapping Draft

**Status:** Draft — must be finalized after exact dataset files are acquired and audited.  
**Last updated:** 2026-11-05.

## 1. Purpose

The primary detector is binary:

- benign
- attack

Attack-family labels remain available for:

- family-level diagnostics;
- compound-shift construction;
- target-exclusive family analysis.

The project must not invent false equivalence between attack taxonomies.

## 2. Primary source/target taxonomies

### NF-UNSW-NB15-v3

Catalogue families:

- Fuzzers
- Analysis
- Backdoor
- DoS
- Exploits
- Generic
- Reconnaissance
- Shellcode
- Worms

### NF-CSE-CIC-IDS2018-v3

Catalogue families:

- BruteForce
- Bot
- DoS
- DDoS
- Infiltration
- Web Attacks

### NF-ToN-IoT-v3

Catalogue families:

- Backdoor
- DoS
- DDoS
- Injection
- MITM
- Password
- Ransomware
- Scanning
- XSS

## 3. Cross-dataset family policy

A family is **strictly source-supported** only when there is a defensible semantic correspondence to source training support.

A family is **target-exclusive** only when:

1. it has a defensible attack-family identity at the target;
2. no equivalent source training family exists under the adopted mapping policy.

A family is **ambiguous** when available descriptions do not establish equivalence.

Ambiguous families must not be labeled unseen merely to strengthen the compound-shift condition.

## 4. Current obvious common categories

The following broad categories appear across multiple datasets but still require conservative handling:

- DoS
- DDoS

"Backdoor" appears in UNSW-NB15 and ToN-IoT, but not as a direct CSE-CIC-IDS2018-v3 category.

Other categories do not have obvious direct equivalents across the primary UNSW/CIC pair.

## 5. Consequence for UNSW ↔ CIC

The two primary datasets do **not** share a clean one-to-one attack-family taxonomy.

Therefore:

- binary attack/benign transfer is the primary model task;
- cross-dataset family overlap will be used only where semantically defensible;
- compound shift can be established using target families absent from source training support;
- family-level target results remain dataset-local unless a cross-dataset mapping is explicitly justified.

## 6. What should not be done

Do not map:

- UNSW "Exploits" to CIC "Web Attacks" merely because both can involve vulnerabilities;
- UNSW "Generic" to CIC "Bot" merely because both are malicious;
- CIC "BruteForce" to UNSW "Fuzzers";
- CIC "Infiltration" to UNSW "Backdoor"

without an explicit semantic and experimental justification.

## 7. Mapping artifact fields

The final CSV should contain:

- dataset;
- original_label;
- binary_label;
- original_family;
- canonical_family;
- source_supported;
- target_exclusive;
- mapping_status;
- mapping_basis;
- notes.

## 8. Finalization requirement

The mapping cannot be frozen until:

1. exact v3 files are acquired;
2. actual label strings are inspected;
3. catalogue labels are compared with file labels;
4. any undocumented aliases are resolved;
5. target-exclusive families are determined independently of experiment performance.
