---
title: WB045 DNA Extraction Sensor plasmid prep
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WB045 DNA Extraction] Sensor plasmid prep
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow focuses on releasing DNA from biological samples (e.g., cultured cells, tissues) through lysis and initial separation from major cellular components like proteins and lipids.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>


### [UH180 Incubation] Main culture for plasmid prep

- **Description**: Maintaining specific conditions for cells or chemical reactions to promote growth or desired reactions. It is essential for cell culture and biochemical assays.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:45'
- End_date: ''

#### Input
- Incubated colonies with liquid culture (LMP001)

#### Reagents

- LB media
- antibiotics

#### Consumable

- 14 ml round bottom tube
- Pipette tips
- Pipette aid tip (12 ml)


#### Equipment

- shacking incubator
- Pipette
- Pipette aid


#### Method

- mix LB broth with antibiotics
- aliquout LB with antibiotics 3 ml for 14 ml round bottom tubes
- inject 1% of incubated colony solution in to aliquoted 14 ml round bottom tubes
- put tubes on incubator 37℃ setting with 300 rpm shacking
- Incubation for overnight (~16 h)

#### Output

- Incubated liquid culture for Plasmid miniprep (DmpR_sensor_1 to 18)

#### Results & Discussions
- 6종류 3반복으로 배양



### [UH255 Centrifuge] Centrifuge for plasmid prep

- **Description**: Separating components of different densities within a liquid sample by applying centrifugal force. Used for pelleting cells, clarifying solutions, separating precipitates, and sample preparation steps in various workflows.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:48'
- End_date: ''

#### Input
- Incubated liquid culture for Plasmid miniprep (DmpR_sensor_1 to 18)

#### Reagents

- None

#### Consumable

- None

#### Equipment

- centrifuge

#### Method

- turn on the centrifuge to 3000 rpm and 4℃ temperature
- add main culture cell in centrifuge with balance
- centrifuge for 10 min
- remove supernatant

#### Output

- cultured cell without supernatant (DmpR_sensor_1 to 18)


#### Results & Discussions
- 




### [UH400 Manual] Plasmid prep using kit

- **Description**: Any general process of experiment including preparation of reagents, labware, and manual operations. It encompasses traditional laboratory techniques and procedures.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 08:51'
- End_date: ''

#### Input
- cultured cell without supernatant (DmpR_sensor_1 to 18)

#### Reagents

- Plasmid miniprep kit (promega)
    -cell resuspension soulution
    -cell lysis solution
    -alkaline protease
    -renaturation solution
    -washing soultion
- DW or elution buffer

#### Consumable

- 1.5 ml EPtube
- Column for miniprep
- pipette tips
- vortexor

#### Equipment

- table-top centrifuge

#### Method

- Completely resuspend the cell pellet in 250µl of Cell Resuspension
Solution. Transfer the cells to a 1.5ml microcentrifuge tube if necessary.
- Add 250µl of Cell Lysis Solution, 10µl of alkaline protease and mix by inverting the tube 4 times. The cell suspension should clear immediately 
- Add 350µl of Neutralization Solution and mix by inverting the tube 4 times
- Centrifuge the lysate at 10,000 × g in a microcentrifuge for 10 minutes
- transfer supernatant to column and incubation for 1 min in room temperature
- Centrifuge the column at 10,000 × g in a microcentrifuge for 1 minutes
- remove the solution from the column
- add 750µl of washing solution in column
- Centrifuge the column at 10,000 × g in a microcentrifuge for 1 minutes
- remove the solution from the column
- add 350µl of washing solution in column
- Centrifuge the column at 10,000 × g in a microcentrifuge for 2 minutes
- remove the solution from the column
- Centrifuge the column at 10,000 × g in a microcentrifuge for 2 minutes without solution
- Transfer Minicolumn to a new microcentrifuge tube
- Add 50µl of Nuclease-Free Water to the Minicolumn and wait 1 minute
    - For plasmids ≥10kb, use water preheated to 70°C; for plasmids ≥20kb, use water preheated to
80°C
- Centrifuge at 10,000 x g for 1 min at room temperature
- Remove and discard Minicolumn. Store DNA at –20°C or below

#### Output
- Plasmid DNA for sanger sequencing (DmpR_sensor_1 to 18)

#### Results & Discussions
- nanodrop을 이용한 농도 측정이 필요할 수 있음

> <!-- UNITOPERATION_LIST_END -->
