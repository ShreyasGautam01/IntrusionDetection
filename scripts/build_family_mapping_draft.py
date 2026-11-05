"""Build conservative active-pair family mapping artifacts from audited labels."""
import csv
from pathlib import Path

COUNTS=Path('reports/nf_v3_audit/target_value_counts.csv')
OUT=Path('reports/nf_v3_audit')
UQ='https://staff.itee.uq.edu.au/marius/NIDS_datasets/'
UNB='https://www.unb.ca/cic/datasets/ids-2018.html'

UNSW={
 'Analysis':('Analysis','Exact dataset family; UQ describes a broad class of web, port, email, and script threats.'),
 'Backdoor':('Backdoor','Exact dataset family; direct category name.'),
 'DoS':('DoS','Exact dataset family; UQ defines denial of service.'),
 'Exploits':('Exploitation','Exact dataset family; UQ describes control via known vulnerabilities.'),
 'Fuzzers':('Fuzzing','Exact dataset family; UQ describes randomized inputs used to crash/discover vulnerabilities.'),
 'Generic':('Generic','Exact dataset family; retain dataset-local meaning; do not infer a broader attack class.'),
 'Reconnaissance':('Reconnaissance','Exact dataset family; UQ describes probing/gathering host information.'),
 'Shellcode':('Shellcode','Exact dataset family; UQ describes malware code used to control a victim host.'),
 'Worms':('Worms','Exact dataset family; UQ describes self-replicating spread.'),
}
CIC={
 'Bot':('Bot','Direct dataset category; UQ describes remote control of hijacked computers.'),
 'Brute_Force_-Web':('WebAttacks','Inference from UQ aggregate: raw web and XSS labels plus SQL_Injection sum to the published Web Attacks count.'),
 'Brute_Force_-XSS':('WebAttacks','Inference from UQ aggregate: raw web and XSS labels plus SQL_Injection sum to the published Web Attacks count.'),
 'DDOS_attack-HOIC':('DDoS','Raw label maps to the documented DDoS scenario.'),
 'DDOS_attack-LOIC-UDP':('DDoS','Raw label maps to the documented DDoS scenario.'),
 'DDoS_attacks-LOIC-HTTP':('DDoS','Raw label maps to the documented DDoS scenario.'),
 'DoS_attacks-GoldenEye':('DoS','Raw label maps to the documented DoS scenario.'),
 'DoS_attacks-Hulk':('DoS','Raw label maps to the documented DoS scenario.'),
 'DoS_attacks-SlowHTTPTest':('DoS','Raw label maps to the documented DoS scenario.'),
 'DoS_attacks-Slowloris':('DoS','Raw label maps to the documented DoS scenario.'),
 'FTP-BruteForce':('BruteForce','Raw FTP brute-force label; direct dataset scenario.'),
 'Infilteration':('Infiltration','Preserve raw spelling; canonicalize to UQ/UNB Infiltration category.'),
 'SQL_Injection':('WebAttacks','Inference from UQ aggregate: raw web and XSS labels plus SQL_Injection sum to the published Web Attacks count.'),
 'SSH-Bruteforce':('BruteForce','Raw SSH brute-force label; direct dataset scenario.'),
}

def main():
    with COUNTS.open(encoding='utf-8-sig',newline='') as f: counts=list(csv.DictReader(f))
    inventory=[]; family_counts={}
    for row in counts:
        if row['column']!='Attack': continue
        ds,label=row['dataset'],row['value']; count=int(row['count'])
        if label.casefold()=='benign': canon='Benign'; rationale='Exact benign value in the audited file.'; src=UQ
        elif ds=='NF-UNSW-NB15-v3': canon,rationale=UNSW[label]; src=UQ
        else: canon,rationale=CIC[label]; src=UQ if canon!='Infiltration' else UNB
        inventory.append({'dataset':ds,'raw_label':label,'rows':count,'binary_label':0 if canon=='Benign' else 1,'canonical_family':canon,'mapping_status':'documented_with_local_count' if ds=='NF-UNSW-NB15-v3' or canon not in ('WebAttacks','Infiltration') else 'inferred_aggregate_or_canonical_spelling','mapping_basis':rationale,'source_url':src})
        if canon!='Benign': family_counts[(ds,canon)]=family_counts.get((ds,canon),0)+count
    with (OUT/'family_mapping_draft.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=inventory[0].keys());w.writeheader();w.writerows(inventory)

    ambiguities={
      ('Analysis','WebAttacks'):'UQ describes UNSW Analysis as including web-related threats, while CIC Web Attacks is a specific scenario group; overlap is plausible but not equivalent.',
      ('Backdoor','Infiltration'):'CIC Infiltration includes a backdoor as one stage of a multi-stage inside attack; it is not the same family as UNSW Backdoor.',
      ('DoS','DDoS'):'UQ distinguishes DDoS by distributed sources; UNSW has only a DoS label, so granularity is unresolved.',
      ('Exploitation','Infiltration'):'CIC Infiltration includes exploitation, but is a composite scenario rather than the UNSW Exploits family.',
      ('Exploitation','WebAttacks'):'Vulnerability exploitation may overlap web attacks, but the labels do not establish semantic equivalence.',
      ('Reconnaissance','Infiltration'):'CIC Infiltration includes scanning after compromise; this does not establish equivalence to standalone reconnaissance.',
    }
    sf=[x for x in family_counts if x[0]=='NF-UNSW-NB15-v3']; tf=[x for x in family_counts if x[0]=='NF-CSE-CIC-IDS2018-v3']
    src_fams=sorted(x[1] for x in sf); tgt_fams=sorted(x[1] for x in tf); matrix=[]
    for s in src_fams:
      for t in tgt_fams:
        rationale=ambiguities.get((s,t))
        if s=='DoS' and t=='DoS': status='documented_shared'
        elif rationale: status='ambiguous_possible_overlap'
        else: status='no_documented_equivalence'
        matrix.append({'source_family':s,'source_rows':family_counts[('NF-UNSW-NB15-v3',s)],'target_family':t,'target_rows':family_counts[('NF-CSE-CIC-IDS2018-v3',t)],'relation':status,'target_exclusive_claim':'withheld_pending_review','rationale':rationale or ('Same documented canonical category.' if status=='documented_shared' else 'No direct semantic correspondence found in the cited dataset descriptions; do not infer equivalence from maliciousness alone.'),'source_url':UQ,'target_url':UNB if t=='Infiltration' else UQ})
    with (OUT/'family_matrix_draft.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=matrix[0].keys());w.writeheader();w.writerows(matrix)

    # A compact, human-readable companion to the row-level machine artifacts.
    grouped={}
    for row in inventory:
        grouped.setdefault((row['dataset'],row['canonical_family']),[]).append(row)
    report=['# Active-Pair Family Mapping Audit (Draft)','','**Status:** Draft; no family mapping has been frozen. This audit reads the already-audited label counts and does not train or evaluate a model.','',
            '## Scope and method','','Only NF-UNSW-NB15-v3 (source candidate) and NF-CSE-CIC-IDS2018-v3 (target candidate) are included. NF-ToN-IoT-v3 is outside the active experiment. Raw `Attack` values and audited row counts are retained. Binary labels are shown only as dataset metadata; this artifact does not use labels to make modeling decisions.','',
            'Canonical groupings below are a documentation crosswalk, not relabeling of data. UNSW `Exploits` is rendered as `Exploitation`, `Fuzzers` as `Fuzzing`, and CIC `Infilteration` as `Infiltration` for readable canonical names while exact raw values remain in the CSV. CIC `WebAttacks` is inferred because the three local raw web labels sum exactly to the UQ catalogue aggregate (2,538).','',
            '## Audited local family inventory','','Counts come from `target_value_counts.csv`, not catalogue estimates.']
    for ds in ('NF-UNSW-NB15-v3','NF-CSE-CIC-IDS2018-v3'):
        report += ['',f'### {ds}','','| Canonical family | Rows | Raw `Attack` values |','|---|---:|---|']
        for (dataset,fam), rows in sorted(grouped.items()):
            if dataset!=ds or fam=='Benign': continue
            raw_values=', '.join('`{}` ({:,})'.format(x['raw_label'],int(x['rows'])) for x in rows)
            report.append(f"| {fam} | {sum(int(x['rows']) for x in rows):,} | {raw_values} |")
    report += ['', '## Cross-dataset interpretation','',
               '- The only direct shared category supported by this conservative crosswalk is **DoS**. This means shared category name/documentation, not identical attack implementations or feature distributions.',
               '- UNSW DoS vs CIC DDoS is **ambiguous**: UNSW does not split its family by distributed source while CIC does.',
               '- UNSW Analysis vs CIC WebAttacks, Exploitation vs WebAttacks/Infiltration, Backdoor vs Infiltration, and Reconnaissance vs Infiltration are marked possible semantic overlap, not equivalence.',
               '- All target-exclusive claims remain withheld pending explicit human review of the frozen ontology. No family is declared unseen from string mismatch alone.',
               '- Every source/target family pair and rationale appears in `family_matrix_draft.csv`; raw values and mapping basis appear in `family_mapping_draft.csv`.','',
               '## Sources and inference','','- UQ NetFlow v3 catalogue and family descriptions: '+UQ,
               '- Official CIC-IDS2018 scenario documentation: '+UNB,
               '- CIC `WebAttacks` aggregate correspondence is an inference from exact local raw-label counts: 1,618 + 480 + 440 = 2,538, matching the published aggregate. Retain this as provisional until reviewed.','']
    (OUT/'FAMILY_MAPPING_DRAFT.md').write_text('\n'.join(report),encoding='utf-8')

if __name__=='__main__': main()
