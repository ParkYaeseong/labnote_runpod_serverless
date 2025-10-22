---
title: WB030 DNA Assembly Level 0 to 1 Goldengate assembly
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB030 DNA Assembly] Level 0 to 1 Goldengate assembly
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow is dedicated to assembling double-stranded DNA fragments into sequences that are several kilobases or larger. It includes the assembly of multiple DNA fragments, such as parts or operon-level sequences, in a specific order to achieve the desired genetic construct.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>

### [UH400 Manual] Golden Gate Assembly Mixture Preparation

- **Description**: Any general process of experiment including preparation of reagents, labware, and manual operations. It encompasses traditional laboratory techniques and procedures.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 02:28'
- End_date: ''

#### Input
-   Experiment design documents
#### Reagent
-   Distilled Water (DW)
-   T4 DNA ligase (NEB) (400,000 unit/ml)
-   BsaI-HFv2 restriction enzyme (NEB) (20,000 units/ml)
-   10x T4 DNA ligase buffer (NEB)

#### Consumables:

-   Pipette tips
-   2 ml tube
-   384 plates


#### Equipment:

-   Pipettes (10 µL, 2.5 µL, 200 µL, 1000 µL)
-   Freezer


#### Method:

-   Keep the BsaI restriction enzyme and T4 DNA ligase on ice.
-   Thaw 10x T4 DNA ligase buffer at room temperature.
-   Vortex the thawed buffer, then perform a light spin-down to collect the liquids.
-   Prepare the Golden Gate reaction mixture by combining the following components in a 2mL tube. The volume is depending on the number of samples.
    -   0.04 µL T4 DNA ligase
    -   0.04 µL BsaI-HF (restriction enzyme)
    -   0.1 µL 10x T4 DNA ligase buffer
    -   Fill up Distilled Water (DW) to 1 µL after subtracting the volume of the DNA parts (adjust based on total DNA part volume).
-   Mix thoroughly by pipetting or vortexing, then perform a spin-down.
-   Keep the prepared mixture on ice.
-   In this experiment, Addng 2 µL, ligase, 2 µL BsaI, 5 µL buffer, and 32 µL DW, total 41 µL mixture
-   add in 384 plate (source plate for echo525)
 

#### Output:

-   Golden Gate mixture in 384 plate (SP001)
#### Results & Discussions
-   Mixture의 위치와 양을 기록하여 추후 mapping file 제작에 사용



### [UH010 Liquid Handling] Golden Gate reaction source plate preparation

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:22'
- End_date: ''

#### Input
- 센서 제작을 위한 파트 리스트 

#### Reagent:

-   DNA parts (e.g., promoter, RBS, CDS, terminator, spacer, amplified DNA)

#### Consumables:

-   384-well PP plate
-   Pipet tips (for JANUS G3, OT-2 or 10 µL, 2.5 µL, 200 µL, 1000 µL)

#### Equipment:

-   JANUS G3, OT-2 (automated liquid handler) or manual ( Pipettes (10 µL, 2.5 µL, 200 µL, 1000 µL))
-   Freezer

#### Method:

-   Thaw the DNA parts at room temperature.
    - All of DNA parts should be duplex primer or PCR-product containing BsaI restriction enzyme recognition site and overhang sites
-   Vortex the thawed DNA parts, then perform a light spin-down to collect the liquids.
-   Place the tube containing the DNA part into the JANUS G3 rack
-   Dispense 40 µL of DNA parts into the 384-well PP plate using JANUS G3.
    -   Refer to the JANUS G3 mapping file for precise dispensing
-   Source_plate_information: ....
-   add at least 30 µL for refill

#### Output:

-   Source plate for GoldenGate assembly (SP001)

#### Results & Discussions
-   Nano liter liquid handler mapping file 제작 시 이용



### [UH255 Centrifuge] Remove bubbles for level 1 Golden Gate assembly

- **Description**: Separating components of different densities within a liquid sample by applying centrifugal force. Used for pelleting cells, clarifying solutions, separating precipitates, and sample preparation steps in various workflows.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:26'
- End_date: ''

#### Input
- Source plate for GoldenGate assembly (SP001) 

#### Reagent
-  None

#### Consumables
-   None

#### Equipment
-   Centrifuge

#### Method
- Perform a quick spin-down of 384-well PP plate to eliminate any air bubbles.

#### Output
- Source plate without bubble (SP001)

#### Results & Discussions
- Bubble을 제거하여 nanoliter liquid handler에 오류가 발생하지 않게 함



### [UH030 Nanoliter Liquid Dispensing] Transfer DNA parts Using Echo 525

- **Description**: Specialized for high-precision dispensing of extremely small liquid volumes, typically in the nanoliter range. This unit operation reduces reagent usage, minimizes waste, and allows for scalable, cost-effective workflows, particularly in high-throughput screening applications.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:38'
- End_date: ''

#### Input
- Source plate without bubble (SP001)
- 96-well Destination plate (DP001)
- Echo mapping file

#### Reagent
- None

#### Consumables
- None

#### Equipment:

-   Echo 525 (acoustic liquid handler)

#### Method:

-   Use Echo 525 to transfer the DNA parts from the 384-well PP plate (source plate) to the 96-well skirted plate (destination plate).
-   Follow the Echo 525 mapping file for precise transfer and dispense 50 fmol of each DNA part based on the DNA concentration and size.
-   mapping file: ...

#### Output:

-   Part mixture prepared for Golden Gate assembly (DP001)

#### Results & Discussions
- 작동 후 log file, error message 확인



### [UH130 Sealing] Golden Gate assembly product added plate sealing

- **Description**: Plate sealing for PCR, culturing, storing, and other applications. It ensures sample integrity and prevents contamination during storage and processing.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:42'
- End_date: ''

#### Input
-   Part mixture prepared for Golden Gate assembly (DP001)

#### Reagent:

-   None

#### Consumables:

-   Heat-resistant sealing film

#### Equipment:

-   Plate sealer
-   Freezer

#### Method:

-   Seal the 96-well skirted plate using heat-resistant film with a plate sealer
-   Seal the source plate and store it in the refrigerator
-   After use, close the lids of reagents and return them to the freezer for storage

#### Output:

-   Sealed 96-well skirted plate ready for efficient DNA assembly (DP001)

#### Results & Discussions
- 장비 동작이 잘 진행되는지 확인



### [UH100 Thermocycling] Golden Gate assembly reaction

- **Description**: The process of repeatedly heating and cooling through defined temperature cycles to facilitate reactions. It is used in workflows such as DNA assembly and DNA/RNA amplification, including PCR.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:44'
- End_date: ''

#### Input
- Sealed 96-well skirted plate ready for efficient DNA assembly (DP001)

#### Reagents

- None

#### Consumable

- None

#### Equipment

- T-robot

#### Method

- Turn on the T-robot
- Put the plate on the T-robot
- Thermocycling as a following method

| **Step** | **Temperature** | **Time**  | **Description** |
|:--------:|:---------------:|:--------:|:----------------|
| 1        | 37°C            | 10 min   | Initial restriction (cutting DNA with restriction enzymes) |
| 2        | 37°C            | 5 min    | Restriction enzyme activity |
| 3        | 16°C            | 5 min    | Ligation, repeat step 2 for 5 cycles |
| 4        | 75°C            | 5 min    | Inactivation of ligase |
| 5        | 80°C            | 10 min   | Inactivation of restriction enzyme |
| 6        | 4°C             | ~        | Hold at 4°C for storage |


#### output

- 96-well skirt plate with Goldengate assembly mixture (assembled) (DS001)

#### Results & Discussions
- 장비 작동 시 lid가 잘 내려가는지 확인







> <!-- UNITOPERATION_LIST_END -->
