---
title: WB120 Biology-mediated DNA Transfers - Transformation_using_Ecoli
experimenter: Wonjae Seong
created_date: '2025-08-19'
last_updated_date: '2025-08-19'
---

## [WB120 Biology-mediated DNA Transfers] Transformation_using_Ecoli
| Briefly describe this workflow (edit the template below to fit your purpose)
| This workflow focuses on transforming designed vector plasmids into cells. It includes 96/384-well plate-based automated or semi-automated transformation procedures, as well as conjugation or other DNA transfer protocols (e.g., phage-mediated).

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.


<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### [UHW140 Peeling] Peeling for transformation

- **Description**: Plate cover removal after PCR, culturing, storing, and other applications. It facilitates easy access to samples while maintaining workflow efficiency.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 12:36'
- End_date: ''

#### Input
- 96-well skirt plate with Goldengate assembly mixture (TU assembled) (DP002)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Peeler

#### Method
- Peeling thermostable films from selected plates

#### Output
- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP002)

#### Results & Discussions
- 

------------------------------------------------------------------------



------------------------------------------------------------------------

### [UHW020 96 Channel Liquid Handling] Transformation and spotting

- **Description**: This unit operation enables high-throughput, simultaneous dispensing or transferring of liquids across a 96-well platform. It is commonly used for NGS library preparation and includes magnetic bead-based purification, enhancing throughput and consistency in sample processing.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 12:37'
- End_date: ''

#### Input
- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP002)

#### Reagent
- Competent cell (30 $\mu$ L per samples)
- Fresh SOC media 15 mL (80 $\mu$ L per samples)

#### Consumable

- 96-well skirt plate
- 96-deep-well plate
- pipette tips (200 p)
- Reservoir
- LB squre plate (Chloram phenicol added) (LP001)
- Zephyr tips

#### Equipment

- pipette (multi channel)
- Ice in Rubber basket 
- Zephyr G3

#### Method

- Thawing the competent cell on Ice
- pull the competent cell on a reservoir (on ice)
- Transfer competent cell to 96-well skirt plate with multi-channel pipette
- Transfer SOC media to 96-deep-well plate with multi-channel pipette
- Put competent cell plate on Zephyr
- Put SOC media on Zephyr
- Add input, prepared reagent, and LB squre plate on Zephyr
- Operating protocol (Transformation)
    - Transfer Competent cell to DNA
    - Cold incubation for 30 min
    - 42℃ heat-shock for 45 sec
    - Cold incubation for 2 min
    - Transfer SOC to competent cell
    - 37℃ recovery for 45 min
    - 9 $\mu$ L spotting on LB+antibiotics plate

#### Output

- Transformants spotted LB media plate (LP001)

#### Results & Discussions
- 
------------------------------------------------------------------------



<!-- UNITOPERATION_LIST_END -->

