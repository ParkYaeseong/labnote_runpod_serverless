---
title: WB140 Liquid Media Cell Culture Colony incubation for plasmid prep
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB140 Liquid Media Cell Culture] Colony incubation for plasmid prep
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow covers growing cells in liquid media. It includes inoculum culture and subsequent batch culture processes in liquid medium, optimizing conditions for cell growth and productivity.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>


### [UH060 Colony Picking] Candidate colony picking

- **Description**: The process of isolating individual bacterial or yeast colonies from an agar plate and transferring them to a liquid culture or multi-well plate for downstream applications. This unit operation is essential for microbial strain selection and screening.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:37'
- End_date: ''

#### Input
- LB media plate with colonies (LP001)


#### Reagents

- LB broth with antibiotics

#### Consumable

- Pipette tip
- 96-well plate
- LB solid broth plate with antibiotics (optional)

#### Equipment

- Colony picker 
- Pipette

#### Method

- Fill the 96-well plate with LB and antibiotics (200 $\mu $ L for each well) 
- Operate colony picker and pick a colony
- (optional) spotting conolies into LB solid broth plate to recording (master plate)
- Picked(spotted) tips soak into 96-well plate containing LB media

#### Output

- LB media plate with colonies (LMP001)
- Master plate (optional) 

#### Results & Discussions
- 6종류 3반복으로 배양



### [UH180 Incubation] Colony seed culture

- **Description**: Maintaining specific conditions for cells or chemical reactions to promote growth or desired reactions. It is essential for cell culture and biochemical assays.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:41'
- End_date: ''

#### Input
- LB media plate with colonies (LMP001)

#### Reagents

- None

#### Consumable

- None

#### Equipment

- shacking incubator


#### Method

- put plate on incubator 37℃ setting with 300 rpm shacking
- Incubation for overnight (~16 h)

#### Output

- Incubated colonies with liquid culture (LMP001)


#### Results & Discussions
- 



> <!-- UNITOPERATION_LIST_END -->
