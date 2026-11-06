"""Build conservative active-pair family mapping artifacts from audited labels."""
import csv
from pathlib import Path

COUNTS=Path('reports/nf_v3_audit/target_value_counts.csv')
OUT=Path('reports/nf_v3_audit')
UQ='https://staff.itee.uq.edu.au/marius/NIDS_datasets/'
UNB='https://www.unb.ca/cic/datasets/ids-2018.html'
V3_PAPER='https://arxiv.org/html/2503.04404v3'

# Canonical family totals in the NetFlow-v3 release paper's Table 3.
UNSW_RELEASE_COUNTS={
 'Benign':2237731,'Fuzzing':33816,'Analysis':1226,'Backdoor':4659,'DoS':5980,
 'Exploitation':42748,'Generic':19651,'Reconnaissance':17074,'Shellcode':2381,'Worms':158,
}
CIC_RELEASE_COUNTS={
 'Benign':17514626,'BruteForce':575194,'Bot':207703,'DoS':302966,'DDoS':1324350,
 'Infiltration':188152,'WebAttacks':2538,
}
# Current UQ HTML family table differs from the v3 paper for three UNSW counts.
UNSW_UQ_HTML_COUNTS={
 'Benign':2237731,'Fuzzing':33816,'Analysis':2381,'Backdoor':1226,'DoS':5980,
 'Exploitation':42748,'Generic':19651,'Reconnaissance':17074,'Shellcode':4659,'Worms':158,
}
CIC_UQ_HTML_COUNTS=CIC_RELEASE_COUNTS.copy()
UNSW_UQ_HTML_ATTACK_TOTAL=127639
CIC_UQ_HTML_ATTACK_TOTAL=2600903

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
    for item in inventory:
        ds,canon=item['dataset'],item['canonical_family']
        local_family_count=item['rows'] if canon=='Benign' else family_counts[(ds,canon)]
        paper_counts=UNSW_RELEASE_COUNTS if ds=='NF-UNSW-NB15-v3' else CIC_RELEASE_COUNTS
        html_counts=UNSW_UQ_HTML_COUNTS if ds=='NF-UNSW-NB15-v3' else CIC_UQ_HTML_COUNTS
        paper_count=paper_counts[canon]
        html_count=html_counts[canon]
        local_attack_total=sum(v for (dataset, family), v in family_counts.items() if dataset==ds)
        paper_attack_total=sum(v for family, v in paper_counts.items() if family!='Benign')
        html_attack_table_total=sum(v for family, v in html_counts.items() if family!='Benign')
        item.update({
            'local_attack_total':local_attack_total,
            'v3_release_paper_attack_total':paper_attack_total,
            'uq_html_family_table_attack_total':html_attack_table_total,
            'uq_html_prose_attack_total':UNSW_UQ_HTML_ATTACK_TOTAL if ds=='NF-UNSW-NB15-v3' else CIC_UQ_HTML_ATTACK_TOTAL,
            'uq_html_prose_total_matches_local':'yes' if local_attack_total==(UNSW_UQ_HTML_ATTACK_TOTAL if ds=='NF-UNSW-NB15-v3' else CIC_UQ_HTML_ATTACK_TOTAL) else 'no',
            'local_canonical_family_count':local_family_count,
            'v3_release_paper_count':paper_count,
            'local_matches_v3_release_paper':'yes' if local_family_count==paper_count else 'no',
            'uq_html_family_table_count':html_count,
            'local_matches_uq_html_family_table':'yes' if local_family_count==html_count else 'no',
            'v3_release_paper_url':V3_PAPER,
        })
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
        matrix.append({'source_family':s,'source_rows':family_counts[('NF-UNSW-NB15-v3',s)],'source_matches_v3_release_paper':family_counts[('NF-UNSW-NB15-v3',s)]==UNSW_RELEASE_COUNTS[s],'source_matches_uq_html_family_table':family_counts[('NF-UNSW-NB15-v3',s)]==UNSW_UQ_HTML_COUNTS[s],'target_family':t,'target_rows':family_counts[('NF-CSE-CIC-IDS2018-v3',t)],'target_matches_v3_release_paper':family_counts[('NF-CSE-CIC-IDS2018-v3',t)]==CIC_RELEASE_COUNTS[t],'relation':status,'target_exclusive_claim':'withheld_pending_review','rationale':rationale or ('Same documented canonical category.' if status=='documented_shared' else 'No direct semantic correspondence found in the cited dataset descriptions; do not infer equivalence from maliciousness alone.'),'source_url':UQ,'target_url':UNB if t=='Infiltration' else UQ,'release_paper_url':V3_PAPER})
    with (OUT/'family_matrix_draft.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=matrix[0].keys());w.writeheader();w.writerows(matrix)

    # A compact, human-readable companion to the row-level machine artifacts.
    grouped={}
    for row in inventory:
        grouped.setdefault((row['dataset'],row['canonical_family']),[]).append(row)
    report=['# Active-Pair Family Mapping Audit (Draft)','','**Status:** Draft; no family mapping has been frozen. This audit reads the already-audited label counts and does not train or evaluate a model.','',
            '## Scope and method','','Only NF-UNSW-NB15-v3 (source candidate) and NF-CSE-CIC-IDS2018-v3 (target candidate) are included. NF-ToN-IoT-v3 is outside the active experiment. Raw `Attack` values and audited row counts are retained. Binary labels are shown only as dataset metadata; this artifact does not use labels to make modeling decisions.','',
            'Canonical groupings below are a documentation crosswalk, not relabeling of data. UNSW `Exploits` is rendered as `Exploitation`, `Fuzzers` as `Fuzzing`, and CIC `Infilteration` as `Infiltration` for readable canonical names while exact raw values remain in the CSV. CIC `WebAttacks` is inferred because the three local raw web labels sum exactly to the UQ catalogue aggregate (2,538).','',
            '## Release-count reconciliation','',
            'The BagIt-verified local UNSW file matches the family counts in Table 3 of the NetFlow-v3 release paper exactly, including Analysis 1,226, Backdoor 4,659, and Shellcode 2,381. The current UQ catalogue HTML table instead lists 2,381, 1,226, and 4,659 for those labels, respectively. Its prose total says 127,639 attacks, while its own family table sums to 127,693; the local file and v3 release paper both report 127,693. This is a discrepancy in the current catalogue page, not evidence to relabel the local file. Raw labels and BagIt-verified data are retained unchanged; family-level claims use the v3 release paper and remain draft pending review.','',
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
               '## Sources and inference','','- NetFlow-v3 release paper, Table 3 (release-matched family counts): '+V3_PAPER,
               '- UQ NetFlow v3 catalogue HTML (current family descriptions and count discrepancy): '+UQ,
               '- Official CIC-IDS2018 scenario documentation: '+UNB,
               '- CIC `WebAttacks` aggregate correspondence is an inference from exact local raw-label counts: 1,618 + 480 + 440 = 2,538, matching the published aggregate. Retain this as provisional until reviewed.','']
    (OUT/'FAMILY_MAPPING_DRAFT.md').write_text('\n'.join(report),encoding='utf-8')

if __name__=='__main__': main()
