---
title: WB030 DNA Assembly - Level_1_to_2_Goldengate_assembly
experimenter: Wonjae Seong
created_date: '2025-08-19'
last_updated_date: '2025-08-19'
---

## [WB030 DNA Assembly] Level_1_to_2_Goldengate_assembly
| Briefly describe this workflow (edit the template below to fit your purpose)
| This workflow is dedicated to assembling double-stranded DNA fragments into sequences that are several kilobases or larger. It includes the assembly of multiple DNA fragments, such as parts or operon-level sequences, in a specific order to achieve the desired genetic construct.

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.


<!-- UNITOPERATION_LIST_START -->


------------------------------------------------------------------------

### \[UHW010 Liquid Handling\] Golden Gate reaction source plate preparation

-   **Description**: A compact liquid handling system designed for small-scale automated experiments or educational use. It provides flexibility and ease of use for routine laboratory tasks, making it ideal for teaching labs or small research groups.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 13:24'
-   End_date: ''

#### Input

-   Purified PCR product with fragments smaller than the selected size removed, ready for downstream applications (PP001)

#### Reagent

-   Distilled Water (DW)
-   T4 DNA ligase (NEB) (400,000 unit/ml)
-   BsaI-HFv2 restriction enzyme (NEB) (20,000 units/ml)
-   10x T4 DNA ligase buffer (NEB)


#### Consumables

-   Pipette tips
-   2 ml tube
-   384 plates
-   384-well PP plate (SP003)
-   Pipet tips (for JANUS G3, OT-2 or 10 µL, 2.5 µL, 200 µL, 1000 µL)

#### Equipment

-   JANUS G3, OT-2 (automated liquid handler) or manual ( Pipettes (10 µL, 2.5 µL, 200 µL, 1000 µL))
-   Freezer
-   Pipettes (10 $\mu L$, 2.5 $\mu L$, 200 $\mu L$, 1000 $\mu L$)
-   Vortexer
-   Table-top centrifuge


#### Method

-   [goldengate assembly enzyme mixture]Keep the BsaI restriction enzyme and T4 DNA ligase on ice.
-   Thaw the 10x T4 DNA ligase buffer at room temperature.
-   Vortex the thawed buffer, then briefly spin down to collect the liquid.
-   Prepare the Golden Gate reaction mixture by combining the following components in a 2 mL tube. Adjust the total volume based on the number of samples:
    -   0.04 µL T4 DNA ligase
    -   0.04 µL BsaI-HF (restriction enzyme)
    -   0.1 µL 10x T4 DNA ligase buffer
    -   Add distilled water (DW) to reach 1 µL, subtracting the volume of DNA parts (adjust according to the total DNA part volume)
-   Mix thoroughly by pipetting or vortexing, then briefly spin down.
-   Keep the prepared mixture on ice.
-   Dispense the mixture into a 384-well plate (source plate for Echo525)
-   [TU part]Thaw the TU DNA parts at room temperature.
    - All of TU DNA parts should be Purified containing BsaI restriction enzyme recognition site and overhang sites
-   Vortex the thawed TU DNA parts, then perform a light spin-down to collect the liquids.
-   Place the tube containing the DNA part into the JANUS G3 rack
-   Dispense 40 µL of DNA parts into the 384-well PP plate using JANUS G3.
    -   Refer to the JANUS G3 mapping file for precise dispensing
-   Source_plate_information: ....
-   add at least 30 µL for refill

#### Output

-   Source plate for GoldenGate assembly (SP003)

#### Results & Discussions

-   Record the position and volume of the mixture in the plate for future use in creating the mapping file.

------------------------------------------------------------------------

------------------------------------------------------------------------

### \[UHW255 Centrifuge\] Remove bubbles in source plate 

-   **Description**: Separating components of different densities within a liquid sample by applying centrifugal force. Used for pelleting cells, clarifying solutions, separating precipitates, and sample preparation steps in various workflows.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 20:26'
-   End_date: ''

#### Input

-   Source plate for GoldenGate assembly (SP003) 

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   Centrifuge

#### Method

-   Perform a quick spin-down of 384-well PP plate to eliminate any air bubbles.

#### Output

-   Source plate without bubble (SP003)

#### Results & Discussions

-   Removing bubbles prevents errors from occurring in the nanoliter liquid handler.

------------------------------------------------------------------------

------------------------------------------------------------------------

### \[UHW030 Nanoliter Liquid Dispensing\] Transfer DNA parts

-   **Description**: Specialized for high-precision dispensing of extremely small liquid volumes, typically in the nanoliter range. This unit operation reduces reagent usage, minimizes waste, and allows for scalable, cost-effective workflows, particularly in high-throughput screening applications.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 20:28'
-   End_date: ''

#### Input

-   Source plate without bubble (SP003)
-   96-well Destination plate (DP002)
-   Echo mapping file

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   Echo 525 (acoustic liquid handler)
-   Echo mapping file

#### Method

-   Use Echo 525 to transfer the DNA parts from the 384-well PP plate (source plate) to the 96-well skirted plate (destination plate).
-   Follow the Echo 525 mapping file for precise transfer and dispense 50 fmol of each DNA part based on the DNA concentration and size.
-   mapping file: ...

#### Output

-   TU mixture prepared for Golden Gate assembly (DP002)

#### Results & Discussions

-   Check the log file and error messages after operation.
-   Dispense based on molar concentration


------------------------------------------------------------------------
------------------------------------------------------------------------

### [UHW255 Centrifuge] Remove bubbles in destination plate 

- **Description**: Separating components of different densities within a liquid sample by applying centrifugal force. Used for pelleting cells, clarifying solutions, separating precipitates, and sample preparation steps in various workflows.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-18 04:22'
- End_date: ''

#### Input
-   TU mixture prepared for Golden Gate assembly (DP002)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Centrifuge

#### Method
- Perform a quick spin-down of 96-well skirt plate to eliminate any air bubbles.

#### Output
- TU mixture prepared for Golden Gate assembly (DP002) prepared for Golden Gate assembly without bubbles

#### Results & Discussions
- Removing bubbles enhances PCR reaction.

------------------------------------------------------------------------

------------------------------------------------------------------------

### [UHW130 Sealing] Sealing the plate 

- **Description**: Plate sealing for PCR, culturing, storing, and other applications. It ensures sample integrity and prevents contamination during storage and processing.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 11:37'
- End_date: ''

#### Input
- TU mixture prepared for Golden Gate assembly (DP002) prepared for Golden Gate assembly without bubbles

#### Reagent
- None

#### Consumables
- Heat-resistant sealing film

#### Equipment
-   Plate sealer
-   Freezer

#### Method
-   Seal the 96-well skirted plate using heat-resistant film with a plate sealer

#### Output
-   Sealed 96-well skirted plate ready for efficient DNA assembly (DP002)

#### Results & Discussions
- 

------------------------------------------------------------------------

------------------------------------------------------------------------

### [UHW100 Thermocycling] GoldenGate assembly reaction

- **Description**: The process of repeatedly heating and cooling through defined temperature cycles to facilitate reactions. It is used in workflows such as DNA assembly and DNA/RNA amplification, including PCR.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 11:44'
- End_date: ''

#### Input
- Sealed 96-well skirted plate ready for efficient DNA assembly (DP002)

#### Reagent
- None

#### Consumables
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


#### Output
- 96-well skirt plate with Goldengate assembly mixture (TU assembled) (DP002)

#### Results & Discussions
- 

------------------------------------------------------------------------


<!-- UNITOPERATION_LIST_END -->

