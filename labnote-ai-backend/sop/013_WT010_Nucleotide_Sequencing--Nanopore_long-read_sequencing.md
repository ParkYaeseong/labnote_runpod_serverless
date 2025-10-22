---
title: WT010 Nucleotide Sequencing - Nanopore_long-read_sequencing
experimenter: Wonjae Seong
created_date: '2025-08-19'
last_updated_date: '2025-08-19'
---

## [WT010 Nucleotide Sequencing] Nanopore_long-read_sequencing
| Briefly describe this workflow (edit the template below to fit your purpose)
| This workflow runs next-generation sequencing (NGS) instruments to generate raw data (e.g., fastq files) from sequencing-ready libraries. It covers flow cell/chip loading, run setup, on-instrument QC/monitoring, and data offloading/demultiplexing. Transcriptome-scale assays (e.g., RNA-seq) are executed here once libraries have been prepared in the dedicated library preparation workflow. For Sanger sequencing, this involves preparing DNA templates and primers, performing cycle sequencing reactions, and basecalling on capillary electrophoresis equipment to generate .ab1 chromatogram files. Typical applications include targeted gene/plasmid verification and small-scale sequencing; transcriptome-scale RNA sequencing is performed via NGS workflows (e.g., RNA-seq).

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.


<!-- UNITOPERATION_LIST_START -->
------------------------------------------------------------------------
### \[UHW270 Long-read Sequence Analysis\] Long-read Sequencing

-   **Description**: Long-read-based sequencing using platforms such as Nanopore or PacBio. It provides comprehensive insights into complex genomic regions and structural variations.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-17 13:42'
-   End_date: ''

#### Input

-   Sequencing-ready library in a 1.5 mL LoBind tube.

#### Reagent

-   Invitrogen Qubit 1X dsDNA HS Assay Kit (Room #Biofoundry, Refrigerator 4℃)
    -   Qubit 1X dsDNA HS Working Solution (protect from light; aliquoted into 50 mL conical tube wrapped with aluminum foil)
    -   Qubit 1X dsDNA HS Standard #1
    -   Qubit 1X dsDNA HS Standard #2
-   Flow Cell Flush (FCF)
-   Flow Cell Tether (FCT)
-   Sequencing Buffer (SB)
-   Library Beads (LIB)

#### Consumables

-   Pipette tips
-   1.5 mL LoBind tubes
-   Invitrogen Qubit Assay Tubes

#### Equipment

-   Pipettes
-   Ice and ice bucket
-   Vortex mixer
-   Microcentrifuge
-   Invitrogen Qubit 4 Fluorometer
-   Flow cell (FLO-MIN114)
-   GridION device

#### Method

-   Thaw SB, LIB (or LIS for viscous libraries), FCT, and FCF at RT. Vortex and spin down, then place on ice.
-   Prepare Qubit assay: 190 μL working solution in two standard tubes; 199.8 μL in sample tube. Add 10 μL standards or 0.2 μL sample. Vortex and measure concentration using **Qubit 4 Fluorometer (1X dsDNA HS program)**. Multiply sample concentration by 10 due to reduced sample volume.
-   Determine library input based on fragment length:

| Fragment Library Length | Flow Cell Loading Amount |
|:-----------------------:|:------------------------:|
|   Very short (\<1 kb)   |         100 fmol         |
|     Short (1–10 kb)     |        35–50 fmol        |
|     Long (\>10 kb)      |          300 ng          |

-   Prepare priming mix:
    -   1 mL FCF + 30 μL FCT, pipette to mix.

**Original protocol composition:**

|                Reagent                |   Volume   |
|:-------------------------------------:|:----------:|
|         Flow Cell Flush (FCF)         |   1170μL   |
| Bovine Serum Albumin (BSA) at 50mg/mL |    5μL     |
|        Flow Cell Tether (FCT)         |    30μL    |
|               **Total**               | **1205μL** |

-   Insert flow cell into GridION, run `flow cell check`
    -   Required active pores depends on required data yield (number of samples).
    -   At least 100 active pores is enough for plasmid sequencing (up to 100 samples).
-   Open priming port. Using P1000 pipette set to 200 μL, draw back 20–30 μL to remove bubbles (do not exceed 30 μL).
    -   If the frozen salt is blocking the liquid path, heat the flowcell by running `flow cell check` in the GridION software.
-   Load 800 μL priming mix dropwise into priming port, incubate 5 min.
-   Prepare library mixture:

|         Reagent          |  Volume   |
|:------------------------:|:---------:|
|  Sequencing Buffer (SB)  |  37.5 μL  |
|   Library Beads (LIB)    |  25.5 μL  |
| DNA library (14.2 ng/μL) |   12 μL   |
|        **Total**         | **75 μL** |

-   Load 200 μL priming mix into priming port, then load 75 μL library dropwise into sample port.\

-   Close all port covers and cover flow cell with light shield.

-   Open **MinKNOW software**.\

-   Configure: Start → Experiment setup → Flow cell position → Select kit (Rapid Barcoding Kit, RBK114) → Super-accurate basecalling.
    -   Select appropriate running time based on required data yield. It can be adjust by real-time data yield.

- If collect approximately data, Stop the run (Stop only sequencing still basecalling).
-   Export run report to file path

#### Output

-   Sample sequencing data (FASTQ files)

#### Results & Discussions
- 
------------------------------------------------------------------------

<!-- UNITOPERATION_LIST_END -->

