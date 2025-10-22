---
title: WB040 DNA Purification Size-selection bead-based DNA purification for removing debris
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB040 DNA Purification] Size-selection bead-based DNA purification for removing debris
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow refines crude DNA extracts to achieve high purity suitable for downstream applications. It typically involves methods like column chromatography, magnetic beads, or precipitation to remove contaminants such as proteins, RNA, and salts.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>

### [UH140 Peeling] PCR plate film peeling

- **Description**: Plate cover removal after PCR, culturing, storing, and other applications. It facilitates easy access to samples while maintaining workflow efficiency.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:27'
- End_date: ''

#### Input
-   PCR product prepared for purification (DP001)

#### Reagent:

-   None

#### Consumables:

-   None

#### Equipment:

-   Plate peeler

#### Method:

-   Peel the PCR product in 96-well skirted plate using plate peeler.

#### Output:

-   Peeled PCR product in 96-well skirted plate (DP001)

#### Results & Discussions
-  장비 동작 확인



### [UH250 Nucleic Acid Purification] Left-side size selection using magnetic beads

- **Description**: The process of purifying DNA or RNA from biological samples using an automated device. It ensures high purity and yield for downstream applications.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:34'
- End_date: ''

#### Input
- Peeled PCR product in 96-well skirted plate (DP001)


#### Reagent
-   SPRIselect Beads - 1 mL
-   85% Ethanol (EtOH) -8.5 mL EtOH + 1.5 mL DW
-   Distilled Water (DW) or TE Buffer

#### Consumables:

-   Two 96-well conical plates
-   One deep one-well plate
-   Pipette tips (200 µL, 10 µL, 2.5 µL)
-   One 96-well skirted plate (PP001)

#### Equipment:

-   Pipette
-   Vortex mixer
-   Zephyr G3 (with magnetic stand)

#### Method
-   Prepare SPRIselect Beads:
    -   Vortex the SPRIselect beads thoroughly to mix at room temperature.
    -   Determine the bead ratio based on the desired size cutoff. For a 0.5x ratio, add 25 µL of beads for 50 µL of PCR product.
-   Distribute Reagents:
    -   Dispense 25 µL of SPRIselect beads into each well of the 96-well conical plate.
    -   Pour 85% ethanol (EtOH) into the deep one-well plate.
-   Dispense 40 µL of DW or TE buffer into each well of the second 96-well conical plate.

-   Prepare Plates for zephyr operation:
    -   One fresh 96-well skirted plate for final DNA transfer
    -   Two 96-well conical plates containing beads and elution buffer
    -   One 96-deep well plate containing 85% EtOH
-   Set purification protocol
    -   Pipette the SPRIselect beads and PCR product mixture 10 times to ensure thorough mixing.
    -   Incubate at room temperature for 1 minute.
    -   Place the plate on the magnetic stand and allow the beads to fully bind. (The time required increases with volume.)
    -   Once bound, remove the supernatant carefully, ensuring the beads remain attached to the magnetic stand.
    -   Add 180 µL of 85% ethanol to each well and let sit for 30 seconds at room temperature.
    -   Carefully remove the ethanol without disturbing the beads.
    -   Repeat the ethanol wash step once more.
    -   Remove the plate from the magnetic stand.
    -   Add at least 20 µL of DW or TE buffer to cover the beads, pipette 10 times to resuspend, and incubate for 1 minute at room temperature.
    -   Optionally, vortex for 1 minute if the volume is 40 µL or more. (This study, 45 µL)
    -   Place the plate back on the magnetic stand and wait until the solution clears.
    -   Transfer the clear supernatant to a fresh 96-well plate for the final purified DNA.


#### Output
-   Purified PCR product with fragments smaller than the selected size removed, ready for downstream applications (PP001)

#### Results & Discussions
-  log 확인을 통한 장비 작동 확인



### [UH010 Liquid Handling] Reagent preparation for DNA concentration measure

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:43'
- End_date: ''

#### Input
-   Purified PCR product with fragments smaller than the selected size removed, ready for downstream applications (PP001)
-   Janus mapping file

#### Reagent
-   Qubit Buffer
-   Standard solution #1 (0 mg/mL) and Standard solution #2 (500 mg/mL)

#### Consumables
-   Pipette tips (200 µL, 10 µL, 2.5 µL)

-   96-well black plate (BP001)

#### Equipment
-   JANUS G3

#### Method

-   Prepare the Qubit Buffer:
    -   Transfer 190 µL of Qubit buffer into two BP001 for the standard solutions.
    -   Transfer 198-199 µL of Qubit buffer into rest of wells in BP001 for each DNA sample
-   Add Standards and DNA Samples:
    -   Add 10 µL of Standard #1 to the first standard tube and 10 µL of Standard #2 to the second standard tube, ensuring the total volume reaches 200 µL.
    -   Add 1-2 µL of each DNA sample to the respective sample tubes, bringing the total volume to 200 µL.
-   Mix and Incubate:
    -   mix the solution gently 
    -   Let the tubes sit at room temperature for 2 minutes to allow the reaction to stabilize.
-   Be careful to avoid creating bubbles during vortexing.

#### Output
-   96-well black plate (BP001) for measuring DNA concentration

#### Results & Discussions
-  log 확인을 통한 장비 작동 확인


### [UH380 Microplate Reading] DNA concentration measurement using qubit-based method

- **Description**: Quantifying protein/cell activity by measuring fluorescence, OD, etc., on 96 or 384-well plates. It is essential for high-throughput screening and assay development.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:41'
- End_date: ''

#### Input
-   96-well black plate (BP001) for measuring DNA concentration

#### Reagent
-   None

#### Consumables
-   None

#### Equipment
- Plate reader (TECAN spark)

#### Method
- Turn On the plate reader
    -   Power on the TECAN spark and connect to computer software 
-   Calibrate the instrument with the prepared standards:
    -   import the setting method for measuring qubit dye fluorescence
    -   initially, measure the fluorescence of Standard #1 and Standard #2 sequentially.
    -   from the fluorescence value, draw the standard curve
-   Measure DNA Concentration:
    -   Load each DNA sample into the Tecan to measure its concentration.
    -   Record the values for each sample

#### Output
-   The concentration of purified DNA for Golden Gate PCR product, ready for use in subsequent reactions

#### Results & Discussions
-  log 확인을 통한 장비 작동 확인
-   농도 파일을 통해 Level2에 사용할 DNA TU 값 계산



### [UH010 Liquid Handling] Fragment analyzer preparation

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:57'
- End_date: ''

#### Input
-   Purified PCR product with fragments smaller than the selected size removed, ready for downstream applications (PP001)

#### Reagent:

-   DNA Ladder/Marker
-   Sample Buffer

#### Consumables:

-   96-well plate (for Agilent Fragment Analyzer) (FA001)
-   Pipette tips (200 µL, 10 µL)

#### Equipment:

-   Pipettes (200 µL, 10 µL)
-   JANUS G3 or OT-2 (for automated sample dispensing)

##### Method:

-   Prepare DNA Samples:
    -   Prepare the purified DNA samples (PCR product) in a 96-well plate.
    -   Load 2 µL of DNA sample into each well. The loading volume may vary depending on the DNA concentration.
    -   If necessary, adjust the concentration by mixing with an appropriate Sample Buffer.
-   Prepare Buffer and Ladder:
    -   Prepare the DNA Ladder or Marker provided by Agilent.
    -   Add the required volume of Ladder to ensure proper size comparison for all samples.
-   Automated Sample Loading with JANUS G3 or OT-2:
    -   Use the automated liquid handler to dispense samples into the 96-well plate, and add the DNA ladder to appropriate wells.
    -   Set up the JANUS mapping file to dispense the correct amount of sample and buffer into each well.

#### Output:

-   Plates for fragment analyzer (FA001)

#### Results & Discussions
- 



### [UH230 Nucleic Acid Fragment Analysis] Fragment analyzer to confirm DNA size

- **Description**: To separate, identify, and characterize fragments of nucleic acids based on their size. This unit operation is crucial for genetic analysis and quality control.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:03'
- End_date: ''

#### Input
-   Plates for fragment analyzer (FA001)

#### Reagents:

-   Gel Matrix (provided by Agilent)
-   Capillary Conditioning Solution

#### Consumables:

-   96-well plate (for Agilent Fragment Analyzer)
-   Pipette tips (200 µL, 10 µL)

#### Equipment:

-   Agilent Fragment Analyzer
-   Vortex mixer

#### Method:

-   Prepare Capillaries and Instrument:
    -   Load the Gel Matrix and Capillary Conditioning Solution into the Fragment Analyzer.
    -   Ensure that the capillaries are clean and properly prepared for analysis.
-   Set Up the Fragment Analyzer:
    -   Select the appropriate protocol in the Fragment Analyzer software (e.g., Standard Sensitivity NGS Fragment Analysis Kit).
    -   Input the sample loading positions and sample types in the software.
    -   Adjust the settings according to the expected DNA fragment size and start the run.
-   Run and Data Analysis:
    -   The Fragment Analyzer will analyze the samples, providing information on the size and concentration of each DNA sample.
    -   The results can be visualized in graphs and tables, showing the size distribution and quality of the DNA.
-   Interpretation of Results:
    -   Use the results from the Fragment Analyzer to verify if the Golden Gate assembly or PCR products match the expected sizes.
    -   This step helps confirm whether the assembly or amplification has been successful, and if any additional purification or reassembly is required.

#### Output:

-   The Fragment Analyzer provides an accurate analysis of the size and quality of the DNA samples, allowing you to verify the integrity of the DNA after DmpR sensor assembly
-   DNA band photo: ...

#### Results & Discussions
- band size와 DNA concentration을 통해 purification 된 DNA part의 mol concentration을 측정





> <!-- UNITOPERATION_LIST_END -->
