---
title: WL010 Sequence Variant Analysis Sanger sequence analysis using snapgene
experimenter: Wonjae Seong
created_date: '2025-08-13'
experiment_date: '2025-08-13'
last_updated_date: '2025-08-13'
---

## [WL010 Sequence Variant Analysis] Sanger sequence analysis using snapgene
> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)
- This workflow is designed for verifying the sequence of template DNA, including target genes, pathways, and plasmids. It is essential for activities such as gene cloning and assembly, and includes the comparison and analysis of sequence variants to ensure accuracy and integrity.

## 🗂️ 관련 유닛오퍼레이션
> 이 실험과 관련된 유닛오퍼레이션 목록입니다.
> <!-- UNITOPERATION_LIST_START -->
>

### [US130 Sequence Mapping and Alignment] Sanger sequencing result analysis

- **Description**: Mapping long/short-read sequences to reference sequences. These tools are used for genome assembly, variant calling, and transcriptomics.

#### Meta
- Experimenter: Wonjae Seong
- Start_date: '2025-08-14 09:02'
- End_date: ''

#### Input
- Sanger sequencing datafile (.ab or pdf)
  - DmpR sensor vectormap file with simulation history

#### Reagent
- None

#### Consumables
- None

#### Equipment
- Computer (Sanpgene sofeware)

#### Method
- Open template file by snapgene
- Click 'alignment' and import sanger sequencing data file
- check the mutation

#### Output
- template file with sanger sequencing result (aligned vectorfile)

#### Results & Discussions
- 

> <!-- UNITOPERATION_LIST_END -->
