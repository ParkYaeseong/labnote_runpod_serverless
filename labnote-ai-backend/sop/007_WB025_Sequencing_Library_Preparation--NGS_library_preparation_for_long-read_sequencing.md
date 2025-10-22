---
title: WB025 Sequencing Library Preparation - NGS library preparation for long-read sequencing
experimenter: Wonjae
created_date: '2025-08-18'
last_updated_date: '2025-08-18'
---

## \[WB025 Sequencing Library Preparation\] NGS library preparation for long-read sequencing

| (kun) Prepare plasmid DNA library for ONT long-read sequencing. This workflow includes DNA quantification, transposon-based tagmentation, multiplexing and cleanup. It is performed using the ONT RBK114 kit. The final output is a sequencing-read library. It supports every type of flowcell (FLG114, MIN114, etc.) and it can be store in 4℃ for a short time or -20℃ for long-term storage.

## 🗂️ 관련 유닛오퍼레이션

| 관련된 유닛오퍼레이션 목록을 아래 표시 사이에 입력합니다.
| `F1`, `New HW/SW Unit Operation` 명령 수행시 해당 목록은 표시된 위치 사이에 자동 추가됩니다.

<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### [UH010 Liquid Handling] Reagent preparation for DNA concentration measure

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.
- (kun) The DNA quantification is performed using the Qubit fluorometer, which can measure the only dsDNA concentration. If is necessary to multiplex the samples with equal concentration.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 07:43'
- End_date: ''

#### Input
-   Plasmid DNA for long-read sequencing (Sample plasmid #)
-   Janus mapping file

#### Reagent
-   Invitrogen Qubit 1X dsDNA HS Assay Kit (Room #Biofoundry, Refrigerator 4℃)
    -   Qubit 1X dsDNA HS Working Solution (protect from light; aliquoted into 50 mL conical tube wrapped with aluminum foil)
    -   Qubit 1X dsDNA HS Standard #1
    -   Qubit 1X dsDNA HS Standard #2

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
- 
------------------------------------------------------------------------



------------------------------------------------------------------------
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
-   The concentration of plasmid DNA

#### Results & Discussions
-  
------------------------------------------------------------------------




------------------------------------------------------------------------


### \[UH400 Manual\] Sequencing Library Preparation

**Description**: Library preparation through pre-processing steps prior to sequencing.

(kun) This unit operation is refered to the ONT Rapid Barcoding Kit V14 (RBK114) protocol. The original protocol is available at [ONT Rapid Barcoding Kit V14 (RBK114) protocol](https://nanoporetech.com/document/rapid-sequencing-v14-plasmid-sequencing-sqk-rbk114-96).

#### Meta

-   **Experimenter**: Wonjae Seong
-   **Start date**: '2025-08-14 07:43'
-   **End date**: ''

#### Input

-   Plasmid DNA for long-read sequencing (Sample plasmid #)
-   The concentration of plasmid DNA 

#### Reagents

-   Rapid Barcoding Kit V14 (RBK114)
    -   AMPure XP Beads (AXP)
    -   Rapid Adapter (RA)
    -   Adapter Buffer (ADB)
    -   Rapid Barcode (RB01 - 96)
    -   Elution Buffer (EB)
-   80% ethanol
-   Nuclease-free water

#### Consumables

-   1.5 mL LoBind tubes
-   PCR tubes
-   Pipette tips
-   96-well PCR plate

#### Equipment

-   Ice and ice bucket
-   Hula mixer
-   Magnetic rack
-   Biometra TRobot Ⅱ
-   Vortex mixer
-   Microcentrifuge
-   Thermomixer
-   Pipettes

#### Method

- Thaw kit components at room temperature,, spin down briefly using a microfuge and mix by pipetting.
    - AXP, EB, ADB

- Prepare the plasmid DNA in nuclease-free water at a concentration of 50 ng in 9.5 uL for each sample for barcoding.
- Select a unique barcode for every sample from the Rapid Barcode (RB01 - 96)
- In PCR tubes or plate, mix the following reagents.

| Reagent | Volume |
| :-----------------: | :---------: |
| DNA sample | 9.5 ul |
| Rapid Barcode | 0.5 ul |

-  Mix by flicking the tube or plate, then spin down briefly using a microfuge.
-  Incubate in **Biometra TRobot II**:

| Enzyme Reaction | Enzyme Inactivation | Hold  |
|:---------------:|:-------------------:|:-----:|
|   30℃, 2 min    |     80℃, 2 min      | 4℃, ∞ |

- Spin down the tube or plate briefly using a microfuge to collect the liquid at the bottom.
- Pool all the barcoded samples to a 1.5 mL LoBind tube.
- Resuspend the AMPure XP Beads (AXP) by vortexing.
- Add an equal volume of resuspended AXP to the pooled barcoded sample in LoBind tube.
- Mix by flicking the tube.
- Incubate for 5 min at room temperature on a Hula mixer.
- Spin down
- Place the tube on magnet until the solution is clear (proximately 3 min).
- Discard teh supernatant carefully without disturbing the beads.
- Wash the beads with 200 μL of 80% ethanol while on the magnet and discard the supernatant.
- Repeat the previous step once more.
- Spin down the tube briefly and place the tube back on the magnet.
- Remove residual supernatant using a 10P pipette.
- Remove the tube from the magnet and air dry the beads for 30 seconds.
- Resuspend the beads in 15 uL of Elution Buffer (EB).
- Incubate for 10 min at room temperature.
- Spin down the tube briefly and place the tube on the magnet until the solution is clear (proximately 1 min).
- Transfer 15 μL of the supernatant to a new 1.5 mL LoBind tube, which contains the barcoded DNA library.
- Quantify the eluted DNA library using Qubit fluorometer.
- Transfer 11 μL of the barcoded DNA library to a new 1.5 mL LoBind tube.
- In a new 1.5 mL LoBind tube, mix the following reagents:

| Reagent | Volume |
| :-----------------: | :---------: |
| Rapid Adapter (RA) | 1.5 ul |
| Adapter Buffer (ADB) | 3.5 ul |

- Mix by flicking the tube, then spin down.
- Transfer 1 μL of the diluted Rapid Adapter Mix to the 11 μL of barcoded DNA library.
    - It can add directly diluted reagent to the library (0.3 μL of RA and 0.7 μL of ADB).
- Mix gently by flicking the tube, and spin down.
- Incubate for 5 min at room temperature.
- Store the library on ice until ready to load.
    - Before adding the Rapid Adapter Mix, the library can be stored at 4℃

#### Output

-   Sequencing-ready library in a 1.5 mL LoBind tube

#### Result & Discussions

- 

------------------------------------------------------------------------

<!-- UNITOPERATION_LIST_END -->