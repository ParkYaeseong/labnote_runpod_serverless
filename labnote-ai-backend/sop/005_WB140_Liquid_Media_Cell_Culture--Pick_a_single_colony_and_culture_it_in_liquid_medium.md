---
title: WB140 Liquid Media Cell Culture - Pick a single colony and culture it in liquid medium
experimenter: Wonjae
created_date: '2025-08-16'
last_updated_date: '2025-08-16'
---

## [WB140 Liquid Media Cell Culture] Pick a single colony and culture it in liquid medium
| 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
| This workflow covers growing cells in liquid media. It includes inoculum culture and subsequent batch culture processes in liquid medium, optimizing conditions for cell growth and productivity.

## 🗂️ 관련 유닛오퍼레이션
| 관련된 유닛오퍼레이션 목록을 아래 표시 사이에 입력합니다.
| `F1`, `New HW/SW Unit Operation` 명령 수행시 해당 목록은 표시된 위치 사이에 자동 추가됩니다.

<!-- UNITOPERATION_LIST_START -->





------------------------------------------------------------------------

### [UHW060 Colony Picking] Candidate colony picking

- **Description**: The process of isolating individual bacterial or yeast colonies from an agar plate and transferring them to a liquid culture or multi-well plate for downstream applications. This unit operation is essential for microbial strain selection and screening.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 12:42'
- End_date: ''

#### Input
- LB media plate with colonies (LP001)

#### Reagent
- Fresh LB broth with antibiotics

#### Consumables

- Pipette tip
- 96-well plate


#### Equipment

- Colony picker 
- Pipette

#### Method

- Fill the 96-well plate with LB and antibiotics (200 $\mu $ L for each well) 
- Operate colony picker and pick a colony
- Picked(spotted) tips soak into 96-well plate containing LB media

#### Output
- LB media plate with colonies (LMP001)

#### Results & Discussions
- 

------------------------------------------------------------------------



------------------------------------------------------------------------

### [UHW180 Incubation] Main culture

- **Description**: Maintaining specific conditions for cells or chemical reactions to promote growth or desired reactions. It is essential for cell culture and biochemical assays.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-17 12:43'
- End_date: ''

#### Input
- LB media plate with colonies (LMP001)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Shaking incubator

#### Method

- put plate on incubator 37℃ setting with 300 rpm shacking
- Incubation for overnight (~16 h)

#### Output
- Incubated colonies with liquid culture (LMP001)

#### Results & Discussions
- 

------------------------------------------------------------------------


------------------------------------------------------------------------

### [UHW010 Liquid Handling] Cell stock preparation

- **Description**: This unit operation involves basic and fundamental liquid sample operations in laboratory processes, such as reagent preparation, sample distribution, dilution, mixing, and washing. It ensures precision and efficiency in handling liquid samples across various experimental setups.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-18 04:46'
- End_date: ''

#### Input
- Incubated colonies with liquid culture (LMP001)

#### Reagent
- 50% glycerol solution (autoclaved)

#### Consumables
- Pipette tips
- 96-tube rack with cryotubes (with screw cap)
- 1-well plate for glycerol reserve

#### Equipment
- Zephyr G3

#### Method

- Pour 50% glycerol solution into a 1-well plate
- Transfer 70 μl of culture medium from the deep well plate containing the culture medium to an empty cryotube
- Add 30 μl of 50% glycerol solution to each cryotube containing the culture medium and mix
- Close the tube cap and store at -80°C.

#### Output
- Culture medium stock stored in cryotubes (Sample stock #)

#### Results & Discussions
- 

------------------------------------------------------------------------

<!-- UNITOPERATION_LIST_END -->

