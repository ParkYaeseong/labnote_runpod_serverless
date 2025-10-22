---
title: WD070 Vector Design - Design_of_sensor_construction
experimenter: Wonjae, Hongyeon, Haseong
created_date: '2025-08-19'
last_updated_date: '2025-08-19'
---

## [WD070 Vector Design] Design_of_sensor_construction
| Briefly describe this workflow (edit the template below to fit your purpose)
| This workflow covers the design process for constructing DNA in the form of plasmid vectors, BACs, YACs, HACs, etc., ensuring the correct assembly and functionality of the vector for its intended application.

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.


<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### \[USW005 Biological Database\] DNA part selection

- **Description**: Retrieving and using standardized biological parts from curated databases for downstream applications. This operation enables users to search for, filter, and select genetic elements such as promoters, coding sequences (CDS), and terminators, ensuring compatibility and adherence to established design standards for assembly and characterization.

#### Meta

-   Experimenter: Wonjae, Hongyeon, Haseong
-   Start_date: '2025-08-15 08:10'
-   End_date: ''

#### Input

-   Part database 
    -   [igem part](https://parts.igem.org/Main_Page)
    -   [Terminator](https://www.nature.com/articles/nmeth.2515)
    -   [Overhang](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0238592)
    -   [DmpR and Po promoter](https://www.sciencedirect.com/science/article/pii/S095656632030659X)
    -   [sfGFP](https://www.addgene.org/)
    -   [Carrier vector](https://www.jmb.or.kr/journal/view.html?doi=10.4014/jmb.2207.07013)
    -   [Spacer](https://academic.oup.com/nar/article/43/13/6620/2414202) - for extra TU assembly

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   Computer

#### Method

- Retrieve standardized biological parts from database
- Organize the part sequences in an Excel file (part_list.xlsx).


| Category | Part name            | Sequence |
|----------|----------------------|----------|
| Promoter | BBa_J23100           | TTGACGGCTAGCTCAGTCCTAGGTACAGTGCTAGC |
| Promoter | BBa_J23106           | TTTACGGCTAGCTCAGTCCTAGGTATAGTGCTAGC |
| Promoter | pBAD (pRSFduet_pBAD) | AAGAAACCAATTGTCCATATTGCATCAGACATTGCCGTCACTGCGTCTTTTACTGGCTCTTCTCGCTAACCAAACCGGTAACCCCGCTTATTAAAAGCATTCTGTAACAAAGCGGGACCAAAGCCATGACAAAAACGCGTAACAAAAGTGTCTATAATCACGGCAGAAAAGTCCACATTGATTATTTGCACGGCGTCACACTTTGCTATGCCATAGCATTTTTATCCATAAGATTAGCGGATCCTACCTGACGCTTTTTATCGCAACTCTCTACTGTTTCTCCATA |
| Promoter | LacP-LacO            | TTTACACTTTATGCTTCCGGCTCGTATGTTGTGTGGAATTGTGAGCGGATAACAA |
| RBS      | BBa_B0030            | TCTAGAGATTAAAGAGGAGAAATA |
| RBS      | BBa_B0032            | TCTAGAGTCACACAGGAAAGTA |
| RBS      | BBa_B0034            | TCTAGAGAAAGAGGAGAAATA |
| CDS      | LacI                 | ATGAAACCAGTAACGTTATACGATGTCGCAGAGTATGCCGGTGTCTCTTATCAGACCGTTTCCCGCGTGGTGAACCAGGCCAGCCACGTTTCTGCGAAAACGCGGGAAAAAGTGGAAGCGGCGATGGCGGAGCTGAATTACATTCCCAACCGCGTGGCACAACAACTGGCGGGCAAACAGTCGTTGCTGATTGGCGTTGCCACCTCCAGTCTGGCCCTGCACGCGCCGTCGCAAATTGTCGCGGCGATTAAATCTCGCGCCGATCAACTGGGTGCCAGCGTGGTGGTGTCGATGGTAGAACGAAGCGGCGTCGAAGCCTGTAAAGCGGCGGTGCACAATCTTCTCGCGCAACGCGTCAGTGGGCTGATCATTAACTATCCGCTGGATGACCAGGATGCCATTGCTGTGGAAGCTGCCTGCACTAATGTTCCGGCGTTATTTCTTGATGTCTCTGACCAGACACCCATCAACAGTATTATTTTCTCCCATGAAGACGGTACGCGACTGGGCGTGGAGCATCTGGTCGCATTGGGTCACCAGCAAATCGCGCTGTTAGCGGGTCCATTAAGTTCTGTCTCGGCGCGTCTGCGTCTGGCTGGCTGGCATAAATATCTCACTCGCAATCAAATTCAGCCGATAGCGGAACGGGAAGGCGACTGGAGTGCCATGTCCGGTTTTCAACAAACCATGCAAATGCTGAATGAGGGCATCGTTCCCACTGCGATGCTGGTTGCCAACGATCAGATGGCGCTGGGCGCAATGCGCGCCATTACCGAGTCCGGGCTGCGCGTTGGTGCGGATATTTCGGTAGTGGGATACGACGATACCGAAGACAGCTCATGTTATATCCCGCCGTTAACCACCATCAAACAGGATTTTCGCCTGCTGGGGCAAACCAGCGTGGACCGCTTGCTGCAACTCTCTCAGGGCCAGGCGGTGAAGGGCAATCAGCTGTTGCCCGTCTCACTGGTGAAAAGAAAAACCACCCTGGCGCCCAATACGCAAACCGCCTCTCCCCGCGCGTTGGCCGATTCATTAATGCAGCTGGCACGACAGGTTTCCCGACTGGAAAGCGGGCAGTGA |
| CDS      | AraC                 | TTATGACAACTTGACGGCTACATCATTCACTTTTTCTTCACAACCGGCACGGAACTCGCTCGGGCTGGCCCCGGTGCATTTTTTAAATACCCGCGAGAAATAGAGTTGATCGTCAAAACCAACATTGCGACCGACGGTGGCGATAGGCATCCGGGTGGTGCTCAAAAGCAGCTTCGCCTGGCTGATACGTTGGTCCTCGCGCCAGCTTAAGACGCTAATCCCTAACTGCTGGCGGAAAAGATGTGACAGACGCGACGGCGACAAGCAAACATGCTGTGCGACGCTGGCGATATCAAAATTGCTGTCTGCCAGGTGATCGCTGATGTACTGACAAGCCTCGCGTACCCGATTATCCATCGGTGGATGGAGCGACTCGTTAATCGCTTCCATGCGCCGCAGTAACAATTGCTCAAGCAGATTTATCGCCAGCAGCTCCGAATAGCGCCCTTCCCCTTGCCCGGCGTTAATGATTTGCCCAAACAGGTCGCTGAAATGCGGCTGGTGCGCTTCATCCGGGCGAAAGAACCCCGTATTGGCAAATATTGACGGCCAGTTAAGCCATTCATGCCAGTAGGCGCGCGGACGAAAGTAAACCCACTGGTGATACCATTCGCGAGCCTCCGGATGACGACCGTAGTGATGAATCTCTCCTGGCGGGAACAGCAAAATATCACCCGGTCGGCAAACAAATTCTCGTCCCTGATTTTTCACCACCCCCTGACCGCGAATGGTGAGATTGAGAATATAACCTTTCATTCCCAGCGGTCGGTCGATAAAAAAATCGAGATAACCGTTGGCCTCAATCGGCGTTAAACCCGCCACCAGATGGGCATTAAACGAGTATCCCGGCAGCAGGGGATCATTTTGCGCTTCAGCCATACTTTTCAT |
| CDS      | sfGFP                | ATGAGCAAAGGTGAAGAACTGTTTACCGGCGTTGTGCCGATTCTGGTGGAACTGGATGGCGATGTGAACGGTCACAAATTCAGCGTGCGTGGTGAAGGTGAAGGCGATGCCACGATTGGCAAACTGACGCTGAAATTTATCTGCACCACCGGCAAACTGCCGGTGCCGTGGCCGACGCTGGTGACCACCCTGACCTATGGCGTTCAGTGTTTTAGTCGCTATCCGGATCACATGAAACGTCACGATTTCTTTAAATCTGCAATGCCGGAAGGCTATGTGCAGGAACGTACGATTAGCTTTAAAGATGATGGCAAATATAAAACGCGCGCCGTTGTGAAATTTGAAGGCGATACCCTGGTGAACCGCATTGAACTGAAAGGCACGGATTTTAAAGAAGATGGCAATATCCTGGGCCATAAACTGGAATACAACTTTAATAGCCATAATGTTTATATTACGGCGGATAAACAGAAAAATGGCATCAAAGCGAATTTTACCGTTCGCCATAACGTTGAAGATGGCAGTGTGCAGCTGGCAGATCATTATCAGCAGAATACCCCGATTGGTGATGGTCCGGTGCTGCTGCCGGATAATCATTATCTGAGCACGCAGACCGTTCTGTCTAAAGATCCGAACGAAAAA |
| Terminator | rrnB-T1            | CAAATAAAACGAAAGGCTCAGTCGAAAGACTGGGCCTTTCGTTTTATCTGTTGTTTGTCGGTGAACGCTCTCCTGAGTAGGACAAAT |
| Terminator | L3S1P56           | TTTTCGAAAAAAGGCCTCCCAAATCGGGGGGCCTTTTTTATTGATAACAAAA |
| Spacer (L) | VA16              | TATCGCGGGTGCGTGCATCGACAAGCCATGCCCACCTTCTGGTCGATTGGGCTGGCG |
| Spacer (R) | VA3               | GGAGGTACTGGCCTAGCGTCGTGGCCCGGGAGAGACAGTTTAGTAGTGACTCGCGGC |
| Spacer (L) | VA4               | TTGGCGTTAATTGTAGCTTATTTCCCGCCCTGTGATTGAGGCGGGATGGTGTCCCCA |
| Spacer (R) | VA2               | TGACGCTTGGATGCGTGACCCCGTACGTCATGACCCGTCATGGGTATGTAAGCGAAG |
| Overhang   | OA1               | GCCT |
| Overhang   | OA2               | CTTT |
| Overhang   | OA3               | GCAG |
| Overhang   | OA4               | CTAA |
| Overhang   | OA5               | TCAC |


#### Output

-   Part list (part_list.xlsx)

#### Results & Discussions

- TODO
    - [ ] Terminator (L3S1P56) 확인 필요 
    - [ ] 위 부품들 모두 .dna 반영된 상태인지 확인 필요 



------------------------------------------------------------------------

------------------------------------------------------------------------

### \[USW030 Vector Design\] Vector design with the selected parts

 -   **Description**: This step designs duplex oligonucleotide sequences for promoter, RBS, CDS, terminator, and spacer parts by appending Type IIS restriction enzyme recognition sites (e.g., BsaI) and defined overhangs to both ends. Parts with long sequences (e.g., CDSs and other >100 bp elements) are prepared by PCR from template DNA, which must be prepared in advance; primers include a 5' buffer, BsaI recognition site, and defined overhangs to produce Golden Gate–ready amplicons. It also includes vector map design and assembly planning.

#### Meta

-   Experimenter: Wonjae, Hongyeon, Haseong
-   Start_date: '2025-08-15 08:13'
-   End_date: ''

#### Input

-   Part list from the previous step

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   SnapGene

#### Method

-   Register selected parts in SnapGene.
-   Connect parts with overhangs and use the BsaI restriction enzyme to assemble each part.

Option 1 — Duplex oligos (< 100 bp)

-   Scope: short parts such as promoters (short variants), RBSs, terminators, and spacers.
-   Design scheme (both ends): 5' buffer (4–5 bp) – BsaI site – A/T – overhang – PART – A/T – overhang – BsaI site (rev) – 5' buffer.
-   Ensure overhangs match Golden Gate positions and are unique/non-palindromic to minimize misligation.
-   Plan PAGE‑purified duplex oligos (ordering will be executed in a later step); keep total length ≤ 99 bp. If needed, duplex oligos can be inserted into the vector.

Option 2 — PCR from template DNA (≥ 100 bp)

-   Scope: prepare template DNA–derived inserts for Golden Gate (e.g., CDSs and inducible promoters > 100 bp).
-   Primer goal (template assumed): generate a Golden Gate–ready amplicon with 5' buffer – BsaI – overhang – INSERT – overhang – BsaI – buffer. Implement by adding to each primer: 5' buffer (4–5 bp) + BsaI + A/T + overhang + 18–25 bp template-binding region (reverse primer carries the reverse complement of the right overhang).
-   Prepare/verify template plasmid stocks in advance (see Template DNA list).
-   Record primer sequences in the Primer list below and maintain overhang consistency across parts.


| Target  | Template DNA (reference) | Forward (5'→3') | Reverse (5'→3') |
|---------|---------------------------|------------------|------------------|
| pBAD    | [/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna) | agttcctcctttcagcattaGGTCTCAGCCTaagaaaccaattgtccatattgcatcagac | ttaattgcgttgcgtgctttGGTCTCTAAAGtatggagaaacagtagagagttgcgataaaaagcgtca |
| LacP-LacO   |  |  |  |
| LacI    | [/labnote/004_Biosensor_library_construction/resources/Template_DNA/Template_LacI.dna](/labnote/004_Biosensor_library_construction/resources/Template_DNA/Template_LacI.dna) | agttcctcctttcagcattaGGTCTCAGCAGAATAAATCATGAAACCAGTAACGTTATACGATGTCGCAGAGT | ttaattgcgttgcgtgctttGGTCTCTTTAGTTTTATCTCAATCACTGCCCGCTTTCCAGTCGGGAA |
| AraC    | [/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna) | agttcctcctttcagcattaGGTCTCAGCAGggattctgcaaaccctatgctactccgtc | ttaattgcgttgcgtgctttGGTCTCTTTAGctctgaatggcgggagtatgaaaagtatggct |
| sfGFP   | [/labnote/004_Biosensor_library_construction/resources/Template_DNA/pK7_sfGFP_HY.dna](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pK7_sfGFP_HY.dna) | agttcctcctttcagcattaGGTCTCAGCAGTATACATATGAGCAAAGGTGAAGAACTGTTTACCGGCG | ttaattgcgttgcgtgctttGGTCTCTTTAGTTATTGCTCAGCGGTGGCAGCAGCCAA |
| rrnB-T1 | [/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna) | agttcctcctttcagcattaggtctcactaaggcatcaaataaaacgaaaggctcag | ttaattgcgttgcgtgctttggtctctgtgatctagggcggcggatttgtc |
| L3S1P56   |  |  |  |




#### Output

-   Vector map including DNA parts
-   Primer list




#### Results & Discussions

- Primer design was performed by adjusting BsaI and overhang sequences.
- TODO
    - [ ] buffer 서열들 확인 필요 
    - [ ] LacP-LacO, L3S1P56 부품들 DNA template, primer 확인 필요 


------------------------------------------------------------------------

------------------------------------------------------------------------

### \[USW320 DNA Assembly Simulation\] Golden Gate assembly simulation

-   **Description**: Simulating DNA assembly such as Golden Gate and Gibson for increasing assembly success rate. This software supports synthetic biology and genetic engineering.

#### Meta

-   Experimenter: Wonjae, Hongyeon, Haseong
-   Start_date: '2025-08-15 13:10'
-   End_date: ''

#### Input

-   part_list.xlsx
-   Primer list (from USW030, see Primer list table)
-   DNA files for simulation
    -   Part files under resources/Part_list (SnapGene .dna)
    -   Template DNA under resources/Template_DNA (SnapGene .dna)
    -   Carrier/backbone vector (.dna)

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   SnapGene or pyDNA with a custom script

#### Method

-   Use SnapGene's 'action' feature to construct linear TU1 and TU2 with the structure Spacer(L)-promoter-RBS-CDS-Terminator-Spacer(R).
-   Use SnapGene's 'action' feature to simulate PCR using primer sequences.
-   Use SnapGene's 'action' feature to simulate assembly of the DNA parts (Promoter, RBS, CDS, and Terminator) and carrier via Golden Gate.
-   Compare the completed file with the previously designed file.

#### Output

-   Assembled vector (.dna/.gb) with simulation/action history
-   Predicted fragment sizes (in-silico gel) for intermediates and final constructs
-   Restriction analysis summary (e.g., absence of internal BsaI sites)
-   Validation checklist status (overhang compatibility/uniqueness, TU orientation, RBS–CDS frame, start/stop codons)

#### Results & Discussions

-   The DNA fragments obtained from each step can be size-predicted using gel simulation, allowing verification that the components have been correctly assembled according to the intended mechanism.


------------------------------------------------------------------------


<!-- UNITOPERATION_LIST_END -->
[//begin]: # "auto-reference"
[//end]: # "end-reference"