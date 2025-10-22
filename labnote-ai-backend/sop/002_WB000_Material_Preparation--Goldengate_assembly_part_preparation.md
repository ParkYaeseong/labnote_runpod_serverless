---
title: WB000 Material Preparation - Goldengate_assembly_part_preparation
experimenter: ''
created_date: '2025-08-20'
last_updated_date: '2025-08-20'
---

## \[WB000 Material Preparation\] Goldengate_assembly_part_preparation

| Briefly describe this workflow (edit the template below to fit your purpose)
| This Workflow for producing parts required for Goldengate assembly. Additional preparation work is required for formats other than plasmid stock, so the preparation process for these is described below.

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.

<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### \[UH400 Manual\] Ordering duplex primers

-   **Description**: Any general process of experiment including preparation of reagents, labware, and manual operations. It encompasses traditional laboratory techniques and procedures.
In this unit operation, we order DNA parts that constitute promoters, RBSs, terminators, and spacers. The length of each of these parts is less than 99 bp.


#### Meta

-   Experimenter: Wonjae Seong
-   Start_date: '2025-08-20 10:55'
-   End_date: ''

#### Input

-   Part list
    - Promoter
        - [LacP-LacO duplex](/labnote/004_Biosensor_library_construction/resources/Part_list/LacP-LacO_duplex.dna)
        - [BBa_J23100](/labnote/004_Biosensor_library_construction/resources/Part_list/BBa_J23100_duplex.dna)
        - [BBa_J23106](/labnote/004_Biosensor_library_construction/resources/Part_list/BBa_J23106_duplex.dna)
    - RBS
        - [BBa_B0030](/labnote/004_Biosensor_library_construction/resources/Part_list/BBa_B0030_duplex.dna)
        - [BBa_B0030](/labnote/004_Biosensor_library_construction/resources/Part_list/BBa_B0032_duplex.dna)
        - [BBa_B0030](/labnote/004_Biosensor_library_construction/resources/Part_list/BBa_B0034_duplex.dna)


#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   None

#### Method

-   Ordering duplex primers (macrogen)
    - Design: 5-blank sequence(4-5bp)-BsaI recognition site-"A" or "T"-overhang-DNA part-"A" or "T"-overhang-BsaI recognition site(reverse)-blank sequence(4-5bp)-3
    - PAGE purification, Do not exceed over 99 bp

#### Output

-   Duplex DNA parts for Goldengate assembly

#### Results & Discussions

-   
------------------------------------------------------------------------

------------------------------------------------------------------------

### \[UH400 Manual\] Manual PCR and purification for DNA part

-   **Description**: Any general process of experiment including preparation of reagents, labware, and manual operations. It encompasses traditional laboratory techniques and procedures.

In this unit operation, we prepare DNA parts with CDSs and inducible promoters with Type IIS restriction enzyme recognition regions and overhangs from DNA templates with no recognition sites and overhangs by PCR and gel purification. Each of these parts is more than 99 bp long.

-   PCR Protocol (https://www.toyobo-global.com/sites/default/static_root/products/lifescience/support/manual/KMM-101_201.pdf)

-   PCR product purification (https://www.promega.com/-/media/files/resources/protcards/wizard-sv-gel-and-pcr-clean-up-system-quick-protocol.pdf)

#### Meta

-   Experimenter: Wonjae Seong
-   Start_date: '2025-08-20 11:05'
-   End_date: ''

#### Input
-   Part list
    - Promoter
        - [pRSFduet_pBAD_promoter](/labnote/004_Biosensor_library_construction/resources/Part_list/pRSFduet-pBAD_promoter.dna)
    - CDS
        - [LacI](/labnote/004_Biosensor_library_construction/resources/Part_list/pRSFduet-LacI.dna)
        - [AraC](/labnote/004_Biosensor_library_construction/resources/Part_list/pRSFduet-araC.dna)
        - [sfGFP](/labnote/004_Biosensor_library_construction/resources/Part_list/pRSFduet-sfGFP.dna)
    - Terminator
     -  [rrnB-T1](/labnote/004_Biosensor_library_construction/resources/Part_list/pRSFduet-rrnBT1.dna)

-   Primer list
    - pBAD_Primer (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCCTaagaaaccaattgtccatattgcatcagac
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTAAAGtatggagaaacagtagagagttgcgataaaaagcgtca
    - LacI Primer (Template_DNA : Template_LacI.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGAATAAATCATGAAACCAGTAACGTTATACGATGTCGCAGAGT
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGTTTTATCTCAATCACTGCCCGCTTTCCAGTCGGGAA
    - AraC Primer (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGggattctgcaaaccctatgctactccgtc
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGctctgaatggcgggagtatgaaaagtatggct
    - sfGFP Primer (Template_DNA : pK7_sfGFP_HY.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGTATACATATGAGCAAAGGTGAAGAACTGTTTACCGGCG
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGTTATTGCTCAGCGGTGGCAGCAGCCAA
    - rrnB-T1 Primer (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaggtctcactaaggcatcaaataaaacgaaaggctcag
        - Reverse : ttaattgcgttgcgtgctttggtctctgtgatctagggcggcggatttgtc
-   Template DNA stock (plasmid form)
    - [AraC & pBAD](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pACBB_AraC.dna)
    - [LacI](/labnote/004_Biosensor_library_construction/resources/Template_DNA/Template_LacI.dna)
    - [sfGFP](/labnote/004_Biosensor_library_construction/resources/Template_DNA/pK7_sfGFP_HY.dna)

#### Reagent

-   KOD one DNA polymerase (toyobo)
-   DpnI-HF (NEB)
-   Blue juice
-   1 kb DNA ladder (invitrogen)
-   1% agarose solution including TAE buffer (low melting temperature)
-   Gel purification kit (promega)
-   1x TAE buffer
-   DW

#### Consumables

-   PCR tube
-   Pipette tip
-   1.5 ml EP tube
-   2 ml EP tube
-   Collection tube and silica column (in promega kit)

#### Equipment

-   Thermocycler
-   Electrophoresis device
-   Comb for agarose gel
-   plate for agarose gel
-   Template for agarose gel
-   Cutter
-   Blue light illuminator
-   Table-top centrifuge
-   Pipette
-   Nanodrop
-   Mass balencer
-   Heat-block

#### Method

-   Prepare PCR mixture in PCR tube

| Reagent                | Volume (μl)  |
|------------------------|--------------|
| DNA polymerase mixture | 25           |
| Template               | 0.6          |
| Primers (100 pmol/μl)  | 0.2 per each |
| DW                     | 24           |
| Total                  | 50           |

-   Conduct PCR using a thermocycler

| Step | Temperature (℃) | Time       | Status                       |
|------|-----------------|------------|------------------------------|
| 1    | 98              | 10 sec     | Inital denaturation          |
| 2    | 98              | 10 sec     | Denaturation                 |
| 3    | 55 (Tm-5)       | 5 sec      | Annealing                    |
| 4    | 68              | 10 sec/kbp | Extension (go to step 2 x30) |
| 5    | 68              | 30 sec     | Final extension              |
| 6    | 4               | infinite   | Storage                      |

-   Add 1 μl DpnI-HF enzyme to PCR product and incubate for more than 2 hr at 37℃
-   During enzyme reaction, prepare agarose gel using comb, template, plate
-   Add 5 μl Blue juice solution to DpnI treated PCR product and mix
-   PCR products and DNA ladder are loaded in agarose gel and electrophoresis for 25 min with 100 V
-   Confirm DNA band using blue light illuminator
-   Cutting DNA band and measuring the mass (put in 2 ml EP tube)
-   Gel purification
    -   Add membrane binding buffer as same as DNA band mass (Band 100 mg/100 μl buffer)
    -   Melting gels for 20 min with shaking (300 rpm) at 55℃
    -   Transfer melted gel to slica column with collection tube
    -   incubation in room temperature for 1 or 2 min
    -   Centrifuge 13,000 rpm for 1 min
    -   Discard solution
    -   Add 700 μl of washing buffer
    -   Centrifuge 13,000 rpm for 1 min
    -   Discard solution
    -   Add 500 μl of washing buffer
    -   Centrifuge 13,000 rpm for 2 min
    -   Discard solution
    -   Centrifuge 13,000 rpm for 2 min
    -   Add 50 μl of DW
    -   Incubation for 1 min in room temperature
    -   Change the collection tube to 1.5 ml EP tube
    -   Centrifuge 13,000 rpm for 2 min
    -   Remove silica column
-   Measuring DNA concentration
    -   Turn on the machine and computer
    -   Execute the measuring program
    -   Loading 1 or 2 μl of DW
    -   Click "blank"
    -   Removing DW by kimwipes, and loading 1 or 2 μl of DNA sample
    -   Click "measure"
    -   Reporting measuring value (DNA concentration)

#### Output

-   DNA parts for Goldengate assembly

#### Results & Discussions

-   Primer design: 5-blank sequence(4~5bp)-BsaI-"A"or "T"-overhang-20 bp of template sequence-3


### [UH400 Manual] Additional Gibson assembly

- **Description**: Any general process of experiment including preparation of reagents, labware, and manual operations. It encompasses traditional laboratory techniques and procedures.

#### Meta

- author: Hongyeon Kim
- created_date: '2025-08-25'
- last_updated_date: ''

#### Input
- PCR Product from previous step
    -   Primer list
    - pBAD PCR product (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCCTaagaaaccaattgtccatattgcatcagac
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTAAAGtatggagaaacagtagagagttgcgataaaaagcgtca
    - LacI PCR product (Template_DNA : Template_LacI.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGAATAAATCATGAAACCAGTAACGTTATACGATGTCGCAGAGT
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGTTTTATCTCAATCACTGCCCGCTTTCCAGTCGGGAA
    - AraC PCR product (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGggattctgcaaaccctatgctactccgtc
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGctctgaatggcgggagtatgaaaagtatggct
    - sfGFP PCR prodcut (Template_DNA : pK7_sfGFP_HY.dna 참조)
        - Forward : agttcctcctttcagcattaGGTCTCAGCAGTATACATATGAGCAAAGGTGAAGAACTGTTTACCGGCG
        - Reverse : ttaattgcgttgcgtgctttGGTCTCTTTAGTTATTGCTCAGCGGTGGCAGCAGCCAA
    - rrnB-T1 PCR prodcut (Template_DNA : pACBB_AraC.dna 참조)
        - Forward : agttcctcctttcagcattaggtctcactaaggcatcaaataaaacgaaaggctcag
        - Reverse : ttaattgcgttgcgtgctttggtctctgtgatctagggcggcggatttgtc

- Carrier Vector
    - pRSFduet vector
        - Forward : aaagcacgcaacgcaattaatgtaagttag
        - Reverse : taatgctgaaaggaggaactatatccggat

#### Reagent
-   KOD one DNA polymerase (toyobo)
-   DpnI-HF (NEB)
-   Blue juice
-   1 kb DNA ladder (invitrogen)
-   1% agarose solution including TAE buffer (low melting temperature)
-   Gel purification kit (promega)
-   1x TAE buffer
-   DW
-   2X Gibson assembly master mix (NEB)

#### Consumables

-   PCR tube
-   Pipette tip
-   1.5 ml EP tube
-   2 ml EP tube
-   Collection tube and silica column (in promega kit)

#### Equipment

-   Thermocycler
-   Electrophoresis device
-   Comb for agarose gel
-   plate for agarose gel
-   Template for agarose gel
-   Cutter
-   Blue light illuminator
-   Table-top centrifuge
-   Pipette
-   Nanodrop
-   Mass balencer
-   Heat-block


#### Method

-   Prepare PCR product of carrier vector as [above protocol](#method-1)
-   Prepare Gibson assembly mixture


| Reagent                    | Volume (μl)  |
|----------------------------|--------------|
| 2X G.A master mix          | 10           |
| Carrier vector PCR product | 5            |
| Insert PCR product         | 5            |
| Total                      | 10           |

-   Conduct Gibson assembly using a thermocycler

| Step | Temperature (℃) | Time      | Status                       |
|------|-----------------|------------|------------------------------|
| 1    | 50              | 1 hour     | Aseembly                     |
| 2    | 98              | 5 min      | Inactivation                 |
| 3    | 4               | infinite   | Storage                      |


#### Output
- Gibson assembly product

#### Results & Discussions
- Further experiment is required(Transformation the gibson assembly product to the E.coli competent cell)


## [WB120 Biology-mediated DNA Transfers] Transformation
- This workflow focuses on transforming designed vector plasmids into cells. It includes 96/384-well plate-based automated or semi-automated transformation procedures, as well as conjugation or other DNA transfer protocols (e.g., phage-mediated).


### [UH010 Liquid Handling] DNA transfer

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- status: 0%
- author: 
- created_date: '2025-08-25'
- last_updated_date: '2025-08-25'

#### Input
- Gibson Assembly product
- DH5α competent cell
    - efficiency : ~ 10^8

#### Reagent
- LB Broth
- Ice
- Kanamycin agarose LB x8

#### Consumables
- 1.5 mL EP tube
- Tip (10 p, 200 p, 1000 p)
- Spreader
- petri dish

#### Equipment
- Ice bucket
- Water bath
- Eppendorf Thermomixer
- Incubator(37 ℃)
- Clean bench
- Centrifuge

#### Method
- Take out DH5α competent cells from the deep freezer (100 µL required per transformation sample) and thaw them slowly on ice in an ice bucket.

- Aliquot the DH5α competent cells into 1.5 mL Eppendorf tubes, 100 µL each, making 8 tubes in total.

- Add 10 µL of Gibson Assembly product into 100 µL of DH5α competent cells and incubate on ice for 5 minutes.

- Set the water bath to 42 °C, and carry out heat shock by placing the samples in the water bath for 1 minute 30 seconds.

- Take out the samples and incubate them again on ice for 5–10 minutes (10 minutes in this experiment).

- Add 900 µL of LB broth to each sample.

- Place the samples in a thermomixer and perform recovery at 37 °C, 350 rpm for 45–60 minutes.

- Centrifuge the samples at 13,000 rpm for 1 minute to pellet the cells, then discard the supernatant leaving 100 µL.

- In the clean bench, resuspend the cell pellets thoroughly with a pipette and spread them onto Kanamycin LB agar plates using a spreader.

- Incubate the plates overnight (~16 h) at 37 °C in an incubator.
 
#### Output

- Part inserted in carrier vector amplified in E.coli

#### Results & Discussions

------------------------------------------------------------------------

<!-- UNITOPERATION_LIST_END -->