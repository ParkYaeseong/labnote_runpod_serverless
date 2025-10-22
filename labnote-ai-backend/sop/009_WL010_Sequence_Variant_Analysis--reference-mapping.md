---
title: WL010 Sequence Variant Analysis - reference mapping
experimenter: Wonjae
created_date: '2025-08-17'
last_updated_date: '2025-08-17'
---

## [WL010 Sequence Variant Analysis] Map the reads to the reference

| This workflow is designed to confirm clone validation of plasmid DNA. Starting point is demultiplexed fastq files from NGS sequencing. This pipeline includes pre-processing of NGS data, reference mapping, and variant calling. The whole process is implemented in a web application CloneFlow.

## 🗂️ 관련 유닛오퍼레이션
| 관련된 유닛오퍼레이션 목록을 아래 표시 사이에 입력합니다.
| `F1`, `New HW/SW Unit Operation` 명령 수행시 해당 목록은 표시된 위치 사이에 자동 추가됩니다.

<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### [USW120 Sequence Trimming and Filtering] Sequence filtering

- **Description**: Preprocessing for removing low-quality long/short-read sequences. This step is crucial for ensuring data quality in sequencing projects.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-18 07:20'
- End_date: ''

#### Input
- demultiplexed sequence file (fastq)
- minimum length
- maximum length

#### Reagent
- None

#### Consumables
- None

#### Equipment
- None

#### Method
- Filter reads by length using `seqkit`.
    - generaly trim under 2000 bp for plasmid sequencing

#### Output
- Filtered sequence file (fastq)

#### Results & Discussions
- 

------------------------------------------------------------------------





------------------------------------------------------------------------

### [USW130 Read Mapping and Alignment] Read mapping and alignment

- **Description**: Mapping long/short-read sequences to reference sequences. These tools are used for genome assembly, variant calling, and transcriptomics.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-18 07:17'
- End_date: ''

#### Input
- Filtered sequence file (fastq)
- reference map (.fasta)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- None

#### Method
- Map reads to reference using `minimap2` or `bwa`.
    - `minimap2` is generally used for long-read sequencing.
    - `bwa` is generally used for short-read sequencing.
- Convert SAM to BAM using `samtools`.

#### Output
- Mapped sequence (.bam)

#### Results & Discussions
- 

------------------------------------------------------------------------





------------------------------------------------------------------------

### [USW170 Variant Calling] Variant calling

- **Description**: Detecting variants based on read mapping. These tools are used for identifying SNPs, indels, and structural variants in genomic data.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-18 07:20'
- End_date: ''

#### Input
- Mapped sequence (.bam)
- reference map (.fasta)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- None

#### Method
- Variant calling with mapped sequence (.bam) and reference (.fasta)
    - use `medaka` for ONT long-read sequencing.

#### Output
- Variant file (.vcf)

#### Results & Discussions
- 

------------------------------------------------------------------------





------------------------------------------------------------------------

### [USW340 Computation] Report generation

- **Description**: Report generation includes length distribution, depth, and variant calling results. With only vcf file, it is not possible to make a decision on whether the plasmid is validated or not. Therefore, it is necessary to consider with length, depth, and variant calling results.

#### Meta
- Experimenter: Wonjae
- Start_date: '2025-08-20 10:01'
- End_date: ''

#### Input
- Filtered sequence file (.fastq)
- Mapped sequence (.bam)
- reference map (.fasta, .dna, .gb)

#### Reagent
- None

#### Consumables
- None

#### Equipment
- None

#### Method
- generate general stats using `seqkit stats` and filtered sequence file (.fastq)
- generate depth using `samtools depth` and mapped sequence (.bam)


#### Output
- clone validation report

#### Results & Discussions
- 

------------------------------------------------------------------------

<!-- UNITOPERATION_LIST_END -->

