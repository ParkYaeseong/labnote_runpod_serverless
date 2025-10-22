---
title: WD070 Vector Design DmpR sensor construction
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WD070 Vector Design] DmpR sensor construction
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow covers the design process for constructing DNA in the form of plasmid vectors, BACs, YACs, HACs, etc., ensuring the correct assembly and functionality of the vector for its intended application.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>
### [USW005: Biological Database] Vector 제작을 위한 DNA 파트 선정

- **Description**: 회로나 벡터 제작용 DNA 파트 서열 정보나 단백질 서열과 같은 biological data를 database에서 확인하고 클로닝에 도입할 수 있도록 선정

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-13 10:42'
- End_date: ''

#### Input
- Part Database 
    - igem part (https://parts.igem.org/Main_Page)
    - Synthetic terminator part paper (https://www.nature.com/articles/nmeth.2515)
    - Overhang sequence (https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0238592)
    - DmpR/Po promoter sequence (https://www.sciencedirect.com/science/article/pii/S095656632030659X)
    - Addgene-sfGFP information (https://www.addgene.org/)
    - Carrier vector information (https://www.jmb.or.kr/journal/view.html?doi=10.4014/jmb.2207.07013) 
    - Spacer part information (https://academic.oup.com/nar/article/43/13/6620/2414202)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Computer

#### Method
- 센서 제작을 위한 유전자 파트 선정
    -  항시 발현 프로모터 1종, RBS 3종, terminator, CDS 각 2종, spacer 4종, overhang 서열 5종, 벡터 1종 으로 구성

#### Output
- 센서 제작을 위한 파트 리스트 (D:\2025\Project\bfapplication\labnote\002_DmpR_sensor_library_construction\resource\part_list.xlsx)

#### Results & Discussions
- 항시 발현 프로모터 1종의 경우 세기가 약한 파트를 선정 
(이전 센서 제작 시 regulator promoter의 세기가 약한 센서의 성능 지표가 좋았음)



### [US030 Vector Design] Part를 이용한 vector design

- **Description**: Designing vector maps regarding inserts and a plasmid backbone. This might include primer design and DNA assembly processes, facilitating the construction of functional genetic vectors for cloning and expression.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-13 10:42'
- End_date: ''

#### Input
- 센서 제작을 위한 파트 리스트 

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Snap gene software

#### Method
- 선별한 바이오파트를 snap gene에 등록
- 파트와 overhang을 연결하고, 이를 BsaI 제한효소와 연결하여 각 파트들을 제작
- TU를 제작한 후, TU를 연결하여 sensor vectormap 제작

#### Output
- Vector map
    - DNA part 포함
- primer list

#### Results & Discussions
- 기존에 자료에 맞게, DmpR이 있는 regulator TU와 reporter TU는 서로 역방향 (<-->) 으로 디자인
    - BsaI과 overhang을 조절하여 프라이머를 디자인




### [US320 DNA Assembly Simulation] GoldenGate assembly를 통한 DmpR sensor 제작 simulation 진행

- **Description**: Simulating DNA assembly such as Golden Gate and Gibson for increasing assembly success rate. This software supports synthetic biology and genetic engineering.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-13 12:01'
- End_date: ''

#### Input
- Vector map
    - DNA part 포함
- primer list

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Snap gene software

#### Method
- 각 파트들을 선정
- Snap gene의 'action'항목을 이용하여 Spacer(L)-promoter-RBS-CDS-Terminator-Spacer(R) 로 구성된 linear한 TU 1, 2를 제작
- Snap gene의 'action'항목을 이용하여 Primer sequence를 이용하여 'PCR' 진행
- Snap gene의 'action'항목을 이용하여 PCR 된 TU1,2와 pACBB-carrier를 이용하여 Goldengate assembly 진행
- 완성된 파일은 이전에 디자인한 파일과 비교

#### Output
- DmpR sensor vectormap file with simulation history

#### Results & Discussions
- 각 과정에서 나온 DNA fragment들은 gel simulation을 통해 크기를 예측해 볼 수 있으며, 해당 부품들이 기작에 맞게 잘 조립되었느지 확인할 수 있음

> <!-- UNITOPERATION_LIST_END -->
