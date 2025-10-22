---
title: WB120 Biology-mediated DNA Transfers Transformation using DH5a
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB120 Biology-mediated DNA Transfers] Transformation using DH5a
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow focuses on transforming designed vector plasmids into cells. It includes 96/384-well plate-based automated or semi-automated transformation procedures, as well as conjugation or other DNA transfer protocols (e.g., phage-mediated).

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>


### [UH140 Peeling] Plate peeling for transformation

- **Description**: Plate cover removal after PCR, culturing, storing, and other applications. It facilitates easy access to samples while maintaining workflow efficiency.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:22'
- End_date: ''

#### Input
- 96-well skirt plate with Goldengate assembly mixture (assembled) (DS002)

#### Reagent

- None

#### Consumable

- None

#### Equipment

- Peeler

- Peeling selected plate 

#### Output

- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP002)

#### Results & Discussions
- 



### [UH020 96 Channel Liquid Handling] Transformation and spotting

- **Description**: This unit operation enables high-throughput, simultaneous dispensing or transferring of liquids across a 96-well platform. It is commonly used for NGS library preparation and includes magnetic bead-based purification, enhancing throughput and consistency in sample processing.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:25'
- End_date: ''

#### Input
- Film-peeled 96-well skirt plate with Goldengate assembly mixture (assembled) in Peeler (DP002)

#### Reagent
- Competent cell (30 $\mu$ L per samples)
- SOC 15 mL (150 $\mu$ L per samples)

#### Consumable

- 96-well skirt plate
- 96-deep-well plate
- pipette tips (200 p)
- Reservoir
- LB squre plate (Chloram phenicol added)
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


> <!-- UNITOPERATION_LIST_END -->
