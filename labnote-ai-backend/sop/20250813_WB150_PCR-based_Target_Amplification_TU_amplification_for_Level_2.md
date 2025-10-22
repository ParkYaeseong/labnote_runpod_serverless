---
title: WB150 PCR-based Target Amplification TU amplification for Level 2
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB150 PCR-based Target Amplification] TU amplification for Level 2
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow utilizes designed primers and Polymerase Chain Reaction (PCR) to specifically amplify a target gene sequence from complex templates such as genomic DNA or metagenomic samples, enabling gene screening and retrieval.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>
### [UH140 Peeling] Plate peeling for PCR

- **Description**: Plate cover removal after PCR, culturing, storing, and other applications. It facilitates easy access to samples while maintaining workflow efficiency.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:46'
- End_date: ''

#### Input
- 96-well skirt plate with Goldengate assembly mixture (assembled) (DS001)

#### Reagent

- None

#### Consumable

- None

#### Equipment

- Peeler

#### Input

- Sealed 96-well skirt plate with Goldengate assembly mixture (assembled)

#### Method

- Peeling selected plate 

#### Output

- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP001)

#### Results & Discussions
- 장비가 제대로 동작하는지 확인



### [UH010 Liquid Handling] PCR reaction destination plate prepartion

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 06:55'
- End_date: ''

#### Input
- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP001)
- Janus mapping file

#### Reagent
-   KOD One Polymerase Mastermix (2x) (Toyobo)
-   Distilled Water (DW)


#### Consumables:

-   Pipette tips
-   2 mL Tubes


#### Equipment:

-   Pipettes (10 µL, 2.5 µL, 200 µL, 1000 µL)
-   Freezer
-   spiner
-   JANUS G3 or OT-2 (automated liquid handler) or pipette

#### Method:

-   Pull out a KOD One Mastermix and primers from the freezer
-   Thaw on ice or at room temperature.
-   After thawing, vortex the reagents and perform a brief spin-down using a centrifuge
-   Prepare the PCR mixture by combining KOD Mastermix and DW in a tube based on the number of reactions required
    -   25 µL 2x KOD-one mastermix
    -   23.6 µL DW
    -   25 reaction prepare
-   Mix thoroughly by pipetting or vortexing, then perform a spin-down
-   Keep the prepared mixture on ice (optional)

-   Using JANUS G3 or manually, dispense the reaction mixture (excluding the primer volume, template volume) into the DP001.
    -   Refer to the JANUS G3 mapping file for precise dispensing
-   This study, add 48.6 µL mixture in template (1 µL) 96-well skirt plate


#### Output:

-   Destination plate for PCR (w/o primer) (DP001)

#### Results & Discussions
-   log 관측을 통해 에러 발생여부를 확인
-   계산을 통해 충분한 양의 PCR mixture 제작



### [UH010 Liquid Handling] PCR source plate preparation

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:05'
- End_date: ''

#### Input
- Primer information (list)
- Janus mapping file
#### Reagent:

-   Primers

#### Consumables:

-   384-well PP plate
-   Pipette tips (for JANUS G3, OT-2, or manual)

#### Equipment:

-   JANUS G3 or OT-2 (automated liquid handler)
-   Pipette
-   Vortexor
-   Freezer

#### Method:

-   Thaw the primers at room temperature.
-   Vortex the thawed primers, then perform a light spin-down to collect the liquids.
-   Place the tube containing the DNA part into the JANUS G3 rack
-   Dispense 30 µL of DNA parts into the 384-well PP plate using JANUS G3.
    -   Refer to the JANUS G3 mapping file for precise dispensing
-   Source_plate_information:....


#### Output
-   Source plate for amplification of TUs by PCR (SP002)

#### Results & Discussions
- log 확인하여 에러 발생하지 않았는지 확인



### [UH255 Centrifuge] Remove bubbles for TU amplification PCR

- **Description**: Separating components of different densities within a liquid sample by applying centrifugal force. Used for pelleting cells, clarifying solutions, separating precipitates, and sample preparation steps in various workflows.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:16'
- End_date: ''

#### Input

-   Destination plate for PCR (w/o primer) (DP001)
-   Source plate for amplification of TUs by PCR (SP002)

#### Reagent
-   None

#### Consumables:

-   None

#### Equipment:

-   Centrifuge


#### Method:

-   Perform a quick spin-down of both the 96-well skirted plate and the 384-well PP plate to eliminate any air bubbles.

#### Output:

-   Source plate and destination plate without bubble (DP001), (SP002)

#### Results & Discussions
-   장비 동작 확인, Bubble이 충분히 깨졌는지 확인



### [UH030 Nanoliter Liquid Dispensing] Transfer primers using Echo 525

- **Description**: Specialized for high-precision dispensing of extremely small liquid volumes, typically in the nanoliter range. This unit operation reduces reagent usage, minimizes waste, and allows for scalable, cost-effective workflows, particularly in high-throughput screening applications.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:19'
- End_date: ''

#### Input
-   Source plate and destination plate without bubble (DP001), (SP002)
-   Echo mapping file

#### Reagents:

-   None

#### Consumables:

-   None

#### Equipment:

-   Echo 525 (acoustic liquid handler)

#### Method:

-   Use Echo 525 to transfer primers from the 384 PP plate (source plate) to the 96-well skirted plate (destination plate).
    -   Refer to the Echo 525 mapping file for specific transfer details (0.2 μL Forward/Reverse primers)
-   mapping file: ...

#### Output:

-   PCR mixture prepared for DNA amplification (DP001)

#### Results & Discussions
-  log와 error 확인



### [UH130 Sealing] Destination plate sealing for PCR reaction

- **Description**: Plate sealing for PCR, culturing, storing, and other applications. It ensures sample integrity and prevents contamination during storage and processing.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:24'
- End_date: ''

#### Input
-   PCR mixture prepared for DNA amplification (DP001)

#### Reagent:

-   None

#### Consumables:

-   Heat-resistant sealing film

#### Equipment:

-   Plate sealer
-   Freezer

-   Seal the 96-well skirted plate using heat-resistant film with a plate sealer.
-   Seal the source plate and store it in the refrigerator.
-   After use, close the lids of reagents and return them to the freezer for storage.

#### Output:

-   Sealed 96-well skirted plate ready for efficient DNA amplification (DP001)

#### Results & Discussions
- 장비 동작 확인



### [UH100 Thermocycling] PCR using thermocycler

- **Description**: The process of repeatedly heating and cooling through defined temperature cycles to facilitate reactions. It is used in workflows such as DNA assembly and DNA/RNA amplification, including PCR.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:26'
- End_date: ''

#### Input
-   Sealed 96-well skirted plate ready for efficient DNA amplification (DP001)

#### Reagents:

-   None

#### Consumable:

-   None

#### Equipment:

-   Thermocycler (T-robot)
-   Freezer (Optional)

#### Method:

-   Login to T-robot Thermocycler:
    -   Log in to the T-robot thermocycler using your credentials.
-   Prepare the Thermocycler:
    -   Open the lid of the thermocycler.
    -   Insert the destination plate (containing the PCR mixture) into the thermocycler.
    -   Close the lid securely.
-   Set Thermocycling Conditions:
    -   Program the thermocycler with the following PCR conditions:

| **Step** | **Temperature** | **Time**  | **Description** |
|:--------:|:---------------:|:--------:|:----------------|
| 1        | 98°C            | 5 min   | Initial denaturation |
| 2        | 98°C            | 10 sec   | Denaturation-repeat start step |
| 3        | 55°C            | 10 sec    | Annealing-depending on Tm value |
| 4        | 68°C            | 1 min    | Extension 10 sec / Kbp -repeat end step, 25 cycle |
| 5        | 68°C            | 5 min   | Final extension |
| 6        | 4°C             | ~        | Hold at 4°C for storage |

-   Start the PCR Reaction:
    -   Begin the thermocycling process according to the programmed conditions
    
-   Post-Reaction Handling:
    -   Once the PCR reaction is complete, remove 5 µL of the PCR product and transfer it to a separate tube for fragment analysis or Qubit quantification.
    -   Store the remaining PCR product for further use in Golden Gate assembly.

#### Output:

-   PCR product prepared for purification (DP001)

#### Results & Discussions
-   log 확인












> <!-- UNITOPERATION_LIST_END -->
