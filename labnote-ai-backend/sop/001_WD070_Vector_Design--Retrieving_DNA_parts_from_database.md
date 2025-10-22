---
title: WD070 Vector Design - Retrieving DNA parts from the database
experimenter: Wonjae
created_date: '2025-08-15'
last_updated_date: '2025-08-15'
---

## \[WD070 Vector Design\] DmpR sensor design
| Briefly describe this workflow (edit the template below to fit your purpose)
| This workflow covers the design process for constructing DNA in the form of plasmid vectors, BACs, YACs, HACs, etc., ensuring the correct assembly and functionality of the vector for its intended application.

## 🗂️ Related Unit Operations

| Enter the list of related unit operations between the markers below.
| When you execute the `F1`, `New HW/SW Unit Operation` command, the relevant list will be automatically added between the indicated positions.


<!-- UNITOPERATION_LIST_START -->

------------------------------------------------------------------------

### \[USW005 Biological Database\] DNA part selection

- **Description**: Retrieving and utilizing standardized biological parts from curated databases for use in downstream applications. This operation enables users to search, filter, and select genetic elements such as promoters, coding DNA sequences (CDS), and terminators, ensuring compatibility and adherence to established design standards in assembly and characterization.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 08:10'
-   End_date: ''

#### Input

-   (samples from the previous step)
-   [igem part](https://parts.igem.org/Main_Page)
-   [Terminator](https://www.nature.com/articles/nmeth.2515)
-   [Overhang](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0238592)
-   [DmpR and Po promoter](https://www.sciencedirect.com/science/article/pii/S095656632030659X)
-   [sfGFP](https://www.addgene.org/)
-   [Carrier vector](https://www.jmb.or.kr/journal/view.html?doi=10.4014/jmb.2207.07013)
-   [Spacer](https://academic.oup.com/nar/article/43/13/6620/2414202) -for extra TU assembly

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   Database

#### Method

-   Organize part sequences in an Excel file (part_list.xlsx)

#### Output

-   Part list (part_list.xlsx)

#### Results & Discussions

-   None

------------------------------------------------------------------------

------------------------------------------------------------------------

### \[USW030 Vector Design\] Vector design with the selected parts

-   **Description**: Designing vector maps regarding inserts and a plasmid backbone. This might include primer design and DNA assembly processes, facilitating the construction of functional genetic vectors for cloning and expression.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 08:13'
-   End_date: ''

#### Input

-   Part list from the previous step

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   SnapGene etc.

#### Method

-   Register selected parts in SnapGene.
-   Connect parts with overhangs, and use BsaI restriction enzyme to assemble each part.
-   After constructing TUs, link the TUs to create the sensor vector map.

#### Output

-   Vector map 

#### Results & Discussions

-   

------------------------------------------------------------------------

------------------------------------------------------------------------

### \[USW320 DNA Assembly Simulation\] Goldengate assembly simulation

-   **Description**: Simulating DNA assembly such as Golden Gate and Gibson for increasing assembly success rate. This software supports synthetic biology and genetic engineering.

#### Meta

-   Experimenter: Wonjae
-   Start_date: '2025-08-15 13:10'
-   End_date: ''

#### Input

-   Vector map 

#### Reagent

-   None

#### Consumables

-   None

#### Equipment

-   SnapGene or pyDNA with Custom script

#### Method

-   Use SnapGene's 'action' feature to assemble the DNA parts (Promoter, RBS, CDS, and Terminator) and pACBB-carrier via Golden Gate assembly.
-   Compare the completed file with the previously designed file.

#### Output

-   Vectormap file with simulation history

#### Results & Discussions

-   The DNA fragments obtained from each step can be size-predicted using gel simulation, allowing verification that the components have been correctly assembled according to the intended mechanism.


------------------------------------------------------------------------


<!-- UNITOPERATION_LIST_END -->