# labnote-ai-backend/main.py

import os
import logging
import datetime
import uuid
import re
import asyncio
import json
import redis.asyncio as redis
import sqlite3
import ollama
import signal
import time
import difflib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union, Tuple, Set
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from rapidfuzz import fuzz
import git
from fastapi.middleware.cors import CORSMiddleware


# Local imports
import rag_pipeline as rag_module
from agents import run_agent_team
from llm_utils import call_llm_api, _post_process_content

# embedding
from rag_pipeline import get_embeddings

# .env 파일 로드 및 로깅 설정
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ROUTER_MODEL_NAME = os.getenv("LLM_ROUTER_MODEL") or os.getenv("LLM_ROUTER_MODEL_NAME") or "llama3.1:70b"

# --- 서버리스 환경을 위한 전역 초기화 ---
# main.py가 TestClient에 의해 로드될 때 RAG 파이프라인을 초기화합니다.
if os.getenv("RUNPOD_SERVERLESS", "false").lower() == "true":
    logger.info("Initializing RAG pipeline within main.py for serverless environment...")
    try:
        rag_module.get_rag_pipeline()
        logger.info("RAG pipeline initialized successfully from main.py.")
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to initialize RAG pipeline during serverless warmup: %s", exc)

# --- [DIAGNOSIS] Unexpected Shutdown Signal Handler ---
def handle_shutdown_signal(signum, frame):
    logger.warning(f"SHUTDOWN-DIAGNOSIS: Server received signal {signal.Signals(signum).name}. This is the likely cause of the unexpected shutdown.")
    # Uvicorn will proceed with the graceful shutdown after this handler.

signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)
logger.info("SHUTDOWN-DIAGNOSIS: Custom signal handlers for SIGTERM and SIGINT have been registered.")
# --- End of Diagnosis Code ---


# --- 데이터 사전 처리 ---
WORKFLOW_GUIDE_DATA = '''
# Workflows Guide
## Design (설계)
- WD010: General Design of Experiment (General optimization of experimental conditions using Design of Experiments (DOE))
- WD020: Adaptive Laboratory Evolution Design (Top-down design through random mutation and artificial evolution)
- WD030: Growth Media Design (Optimization of growth media for strain cultivation through data-driven experimental design)
- WD040: Parallel Cell Culture/Fermentation Design (Design of conditions for large-scale protein/enzyme cultivation or strain activity testing)
- WD050: DNA Oligomer Pool Design (Design of an oligomer pool for assembling target DNA sequences)
- WD060: Genetic Circuit Design (Design of genetic circuits for specific purposes such as biosensors, logic gates, etc.)
- WD070: Vector Design (Design of DNA constructs in vector forms such as plasmids, BACs, YACs, etc.)
- WD080: Artificial Genome Design (Design of new genomes, including genome compression, codon redesign, etc.)
- WD090: Genome Editing Design (Design of gRNA for CRISPR-based genome editing)
- WD100: Protein Library Design (Design of libraries for optimizing protein activity, specificity, and expression)
- WD110: De novo Protein/Enzyme Design (Design of new proteins or enzymes using deep learning tools)
- WD120: Retrosynthetic Pathway Design (Design of production pathways for target metabolites through retrosynthetic analysis)
- WD130: Pathway Library Design (Design of DNA part libraries for optimizing metabolic pathway functions)
## Build (구축)
- WB005: Nucleotide Quantification (Quantification and purity assessment of nucleic acids through UV absorbance and fluorescence analysis)
- WB010: DNA Oligomer Assembly (Accurate assembly of DNA sequences from a DNA oligomer pool)
- WB020: DNA Library Construction (Construction of DNA mutation, metagenome, and pathway libraries)
- WB025: Sequencing Library Preparation (Preparation of DNA/RNA libraries for Next-Generation Sequencing (NGS))
- WB030: DNA Assembly (Assembly of multiple DNA fragments in a specific order to create genetic constructs)
- WB040: DNA Purification (Purification of high-purity DNA from crude DNA extracts using columns, beads, etc.)
- WB045: DNA Extraction (Extraction of DNA from biological samples through cell lysis)
- WB050: RNA Extraction (Isolation of RNA from biological samples for gene expression analysis, etc.)
- WB060: DNA Multiplexing (Assigning barcodes to cells for identification and pooling DNA for NGS)
- WB070: Cell-free Mixture Preparation (Preparation of master solutions and cell extracts for cell-free reactions)
- WB080: Cell-free Protein/Enzyme Expression (Production of target proteins or enzymes in a cell-free reaction system)
- WB090: Protein Purification (High-throughput, high-purity protein purification using automated equipment)
- WB100: Growth Media Preparation and Sterilization (Large-scale production, sterilization, and storage of designed solid and liquid media)
- WB110: Competent Cell Construction (Construction of high-efficiency competent cells for transformation)
- WB120: Biology-mediated DNA Transfers (Automated transformation of designed vector plasmids into cells)
- WB125: Colony Picking (Isolation and cultivation of single colonies using an automated colony picker)
- WB130: Solid Media Cell Culture (Cell culture, screening, and single colony isolation on solid media)
- WB140: Liquid Media Cell Culture (Inoculation and batch culture processes in liquid media)
- WB150: PCR-based Target Amplification (Amplification of specific gene sequences from complex templates using PCR)
## Test (시험)
- WT010: Nucleotide Sequencing (Generation of sequence data using NGS or Sanger sequencing)
- WT012: Targeted mRNA Expression Measurement (Measurement of specific transcript levels using RT-qPCR, ddPCR, etc.)
- WT015: Nucleic Acid Size Verification (Verification of DNA/RNA fragment size and integrity using electrophoresis)
- WT020: Protein Expression Measurement (Quantification of target protein expression levels via gel electrophoresis, LC-MS, etc.)
- WT030: Protein/Enzyme Activity Measurement (Measurement of the activity of purified proteins or enzymes by specific methods)
- WT040: Parallel Cell-free Protein/Enzyme Reaction (Simultaneous measurement of protein expression and activity in a cell-free system)
- WT045: Mammalian Cell Cytotoxicity Assay (Quantification of viability and cytotoxic effects in mammalian/eukaryotic cells)
- WT046: Microbial Viability and Cytotoxicity Assay (Measurement of growth inhibition and viability of microbial cells (MIC/MBC, etc.))
- WT050: Sample Pretreatment (Pretreatment for separation and analysis of metabolites from culture broth)
- WT060: Metabolite Measurement (Quantitative analysis of metabolites using GC-MS, LC-MS, etc.)
- WT070: High-throughput Single Metabolite Measurement (High-speed measurement of a single type of metabolite using biosensors, etc.)
- WT080: Image Analysis (Analysis of cell growth, morphology, and location using high-speed optical instruments)
- WT085: Mycoplasma Contamination Test (Screening for mycoplasma contamination in mammalian cell cultures)
- WT090: High-speed Cell Sorting (High-speed separation of specific cell populations based on genetic circuit signals)
- WT100: Micro-scale Parallel Cell Culture (Micro-scale parallel cell culture in 96-deep-well plates)
- WT110: Micro-scale Parallel Cell Fermentation (Micro-scale fermentation with monitoring of OD, pH, temperature, DO)
- WT120: Parallel Cell Fermentation (15-250ml scale parallel cell fermentation with real-time monitoring)
- WT130: Parallel Mammalian Cell Fermentation (Parallel fermentation of animal cells to maximize protein production)
- WT140: Lab-scale Fermentation (Development of lab-scale fermentation processes under 10L)
- WT150: Pilot-scale Fermentation (Pilot-scale fermentation processes from 10L to 500L)
- WT160: Industrial-scale Fermentation (Large-scale fermentation processes over 500L at an industrial scale)
## Learn (학습)
- WL010: Sequence Variant Analysis (Comparative analysis of variants in template DNA sequences such as genes, plasmids, etc.)
- WL020: Genome Resequencing Analysis (Analysis of genomic variants such as SNPs in organisms with a reference genome)
- WL030: De novo Genome Analysis (Genome assembly and analysis of new organisms without a reference genome)
- WL040: Metagenomic Analysis (Gene and strain identification, and functional prediction from large-scale metagenomic sequence data)
- WL050: Transcriptome Analysis (Analysis of transcriptome (mRNA) data and gene expression differences under various conditions)
- WL055: Single Cell Analysis (Analysis of cellular heterogeneity and function through single-cell RNA sequencing, etc.)
- WL060: Metabolic Pathway Optimization Model Development (Development of metabolic pathway optimization models and analysis of measured metabolite data)
- WL070: Phenotypic Data Analysis (Elucidation of genotype-phenotype relationships through processing and analysis of phenotypic data)
- WL080: Protein/Enzyme Optimization Model Development (Development of models for optimizing protein/enzyme characteristics (activity, solubility, etc.))
- WL090: Fermentation Optimization Model Development (Exploration of optimal conditions for target compound production based on fermentation data)
- WL100: Foundation Model Development (Training of foundation models using large-scale sequence datasets)
'''
UNIT_OPERATION_GUIDE_DATA = '''
# Unit Operations Guide
## Hardware (UHW)
- UHW010: Liquid Handling (Basic operations such as precise dispensing, dilution, and mixing of liquid reagents)
- UHW015: Bulk Liquid Dispenser (Rapid dispensing of large-volume liquids such as media and buffers)
- UHW020: 96 Channel Liquid Handling (High-throughput simultaneous liquid dispensing/transfer on a 96-well platform)
- UHW030: Nanoliter Liquid Dispensing (Ultra-fine precision dispensing of liquids in the nanoliter range)
- UHW040: Desktop Liquid Handling (A compact liquid handling system for small-scale automated experiments)
- UHW050: Single Cell Sequencing Preparation (Cell encapsulation and library preparation for single-cell analysis)
- UHW060: Colony Picking (Isolating single colonies from agar plates for liquid culture)
- UHW070: Cell Sorting (High-speed cell classification and selection based on the biological characteristics of cells)
- UHW080: Cell Lysis (Disrupting cells to extract internal components (DNA, proteins, etc.))
- UHW090: Electroporation (Introducing external molecules such as DNA, RNA into cells using an electric field)
- UHW100: Thermocycling (Repetitive temperature cycling to facilitate reactions such as PCR)
- UHW110: Real-time PCR (Amplification and real-time quantitative analysis of specific DNA/RNA sequences)
- UHW120: Plate Handling (Moving plates between automated equipment using a robotic arm)
- UHW130: Sealing (Sealing plates for sample integrity during PCR, cultivation, and storage)
- UHW140: Peeling (Removing plate covers for automated processes)
- UHW150: Capping Decapping (Automated opening and closing of sample tube caps)
- UHW160: Sample Storage (Automated storage and retrieval system for DNA or cell samples)
- UHW170: Plate Storage (Automated plate storage and retrieval for high-throughput experiments)
- UHW180: Incubation (Maintaining specific conditions (temperature, humidity, etc.) for cell growth and reactions)
- UHW190: HT Aerobic Fermentation (High-throughput parallel microbial/cell culture under aerobic conditions)
- UHW200: HT Anaerobic Fermentation (High-throughput parallel microbial/cell culture under anaerobic conditions)
- UHW210: Microbioreactor Fermentation (Micro-scale bioreactor cultivation with advanced monitoring capabilities)
- UHW220: Bioreactor Fermentation (Cell cultivation in liter-scale bioreactors (batch, fed-batch, continuous))
- UHW230: Nucleic Acid Fragment Analysis (Size-based separation, identification, and characterization of nucleic acid fragments)
- UHW240: Protein Fragment Analysis (Study of the structure, size, modifications, and interactions of protein fragments)
- UHW250: Nucleic Acid Purification (High-purity DNA/RNA purification using automated devices)
- UHW255: Centrifuge (Separation of components by density within a sample using centrifugal force)
- UHW260: Short-read Sequence Analysis (Short sequence-based sequencing using NGS technology)
- UHW265: Sanger Sequencing (Traditional sequencing for targeted gene/plasmid verification)
- UHW270: Long-read Sequence Analysis (Long sequence-based sequencing for analyzing complex genomic regions)
- UHW280: Sequence Quality Control (Quality assessment of sequencing data for single-cell analysis)
- UHW290: LC-MS-MS (High-performance liquid chromatography combined with tandem mass spectrometry)
- UHW300: LC-MS (Liquid chromatography combined with a mass spectrometer)
- UHW310: HPLC (High-performance liquid chromatography)
- UHW320: UPLC (Ultra-performance liquid chromatography)
- UHW330: GC (Gas chromatography)
- UHW340: GC-MS (Gas chromatography combined with a mass spectrometer)
- UHW350: GC-MS-MS (Gas chromatography combined with tandem mass spectrometry)
- UHW355: SPE-MS-MS (Solid-phase extraction and tandem mass spectrometry)
- UHW360: FPLC (Fast protein liquid chromatography optimized for purifying biomolecules like proteins)
- UHW365: Rapid Sugar Analyzer (Rapid quantification of specific sugars (e.g., glucose) using enzyme-based sensors)
- UHW370: Oligomer Synthesis (Parallel synthesis of custom DNA/RNA oligomers using chemical methods)
- UHW380: Microplate Reading (Quantifying protein/cell activity by measuring fluorescence, OD, etc.)
- UHW390: Microscopy Imaging (Capturing microscope images of biological samples such as animal cells)
- UHW400: Manual (All manual experimental processes, including reagent preparation, labware setup, etc.)
## Software (USW)
- USW005: Biological Database (Searching and selecting from a standard biological parts database)
- USW010: DNA Oligomer Pool Design (Designing an oligomer pool for efficient DNA assembly)
- USW020: Primer Design (Designing primers for PCR, mutagenesis, etc.)
- USW030: Vector Design (Designing a vector map considering the insert sequence and plasmid backbone)
- USW040: Sequence Optimization (Codon optimization to maximize protein expression in a specific host)
- USW050: Synthesis Screening (Screening for potentially hazardous DNA sequences for biosecurity)
- USW060: Structure-based Sequence Generation (Generating sequences based on protein structure using AI models)
- USW070: Protein Structure Prediction (Predicting the 3D structure of proteins using AI models)
- USW080: Protein Structure Generation (Generating protein structures with new functions using AI models)
- USW090: Retrosynthetic Pathway Design (Predicting biosynthetic pathways and discovering new ones through retrosynthetic analysis)
- USW100: Enzyme Identification (Searching for suitable enzymes within a pathway through database search or prediction)
- USW110: Sequence Alignment (Comparing sequence similarity and identifying homologous sequences)
- USW120: Sequence Trimming and Filtering (Removing low-quality sequencing reads to improve data quality)
- USW130: Read Mapping and Alignment (Mapping and aligning sequencing reads to a reference sequence)
- USW140: Sequence Assembly (Assembling sequencing reads to reconstruct entire genes, pathways, or chromosomes)
- USW145: Metagenomic Assembly (Reconstructing genomes from complex microbial communities)
- USW150: Sequence Quality Control (Quality control (QC) of sequencing files such as FastQ, Fast5, etc.)
- USW160: Demultiplexing (Separating NGS reads into individual samples based on barcodes)
- USW170: Variant Calling (Detecting variants such as SNPs, indels based on read mapping)
- USW180: RNA-Seq Analysis (Processing transcriptome data and quantifying gene expression)
- USW185: Gene Set Enrichment Analysis (Analyzing significant biological pathways from gene expression data)
- USW190: Proteomics Data Analysis (Processing mass spectrometry data and identifying/quantifying proteins)
- USW200: Phylogenetic Analysis (Analyzing phylogenetic relationships based on sequence similarity)
- USW210: Metabolic Flux Analysis (Modeling and analyzing metabolic flux for cell metabolism and pathway optimization)
- USW220: Deep Learning Data Preparation (Preparing and batching datasets for training and evaluating AI models)
- USW230: Sequence Embedding (Converting biological sequences into numerical representations for machine learning)
- USW240: Deep Learning Model Training (Training deep learning models using training data)
- USW250: Model Evaluation (Evaluating model performance using metrics like accuracy, precision, etc.)
- USW260: Hyperparameter Tuning (Tuning model hyperparameters using Bayesian optimization, etc.)
- USW270: Model Deployment (Deploying trained models as services)
- USW280: Monitoring and Reporting (Monitoring the performance and resource usage of deployed AI models)
- USW290: Phenotype Data Preprocessing (Preprocessing of measured phenotypic data, including cleaning, structuring, and transformation)
- USW300: XCMS Analysis (Analysis and visualization of chromatography and mass spectrometry data)
- USW310: Flow Cytometry Analysis (Analysis and visualization of flow cytometry data)
- USW320: DNA Assembly Simulation (Simulation to improve the success rate of DNA assembly methods like Golden Gate, Gibson, etc.)
- USW325: Gene Editing Simulation (Simulation to predict the results and off-target effects of CRISPR gene editing)
- USW330: Well Plate Mapping (Well plate mapping software for high-throughput screening)
- USW340: Computation (General data collection, preprocessing, and analysis processes)
'''

def _precompute_data():
    logger.info("Pre-computing static data (ALL_UOS, ALL_WORKFLOWS)...")
    all_uos = {m.group(1): m.group(2).strip() for m in re.finditer(r'- ([A-Z]{2,3}\d{3}): (.*)', UNIT_OPERATION_GUIDE_DATA)}
    all_workflows = {m.group(1): m.group(2).strip() for m in re.finditer(r'- ([A-Z]{2}\d{3}): (.*)', WORKFLOW_GUIDE_DATA)}
    logger.info(f"Loaded {len(all_workflows)} workflows and {len(all_uos)} unit operations.")
    return all_uos, all_workflows

ALL_UOS_DATA, ALL_WORKFLOWS_DATA = _precompute_data()

# --- Redis 연결 관리 ---
redis_pool = None

# FastAPI 앱 초기화
app = FastAPI(
    title="LabNote AI Assistant Backend",
    version="2.8.2", # Final Refactored version
    description="Interactive lab note generation with user-edit DPO feedback loop and consent management.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(templates_dir))

# --- Pydantic 모델 정의 ---


class CreateScaffoldRequest(BaseModel):
    query: str
    workflow_id: str
    unit_operation_ids: List[str]
    experimenter: Optional[str] = "AI Assistant"

class LabNoteResponse(BaseModel):
    files: Dict[str, str]

class PopulateNoteRequest(BaseModel):
    file_content: str
    uo_id: str
    section: str
    query: str
    file_path: Optional[str] = None

class PopulateNoteResponse(BaseModel):
    uo_id: str
    section: str
    options: List[str]
    feedback: Optional[str] = None

class GitFeedbackRequest(BaseModel):
    prompt: str
    chosen: str
    rejected: List[str]
    metadata: Dict

class PreferenceRequest(BaseModel):
    uo_id: str
    section: str
    chosen_original: str
    chosen_edited: str
    rejected: List[str]
    query: str
    file_content: str
    file_path: str
    supervisor_evaluations: List[Dict]

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Dict[str, str]]
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    file_content: Optional[str] = None
    experiment_goal: Optional[str] = None
    file_path: Optional[str] = None

class CompletionFeedbackRequest(BaseModel):
    file_content: str
    completion_type: str
    workflow_title: str
    experiment_topic: str

class ChatPreferenceRequest(BaseModel):
    uo_id: str
    section: str
    prompt: str
    generated_text: str
    edited_text: Optional[str] = None
    file_content: Optional[str] = None
    file_path: Optional[str] = None
    supervisor_evaluations: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    response: str
    context: Dict[str, Any]  # 상태 비저장 컨텍스트 (대화 힌트)
    conversation_id: str

# --- 헬퍼 함수 ---
def get_seoul_date_string():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')

def create_unit_operation_template(uo_id: str, uo_name: str, experimenter: str) -> str:
    formatted_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
    return f'''
### [{uo_id} {uo_name}]

#### Meta
- Experimenter: {experimenter}
- Start_date: '{formatted_datetime}'
- End_date: ''

#### Input
- (samples from the previous step)

#### Reagent
- (e.g. enzyme, buffer, etc.)

#### Consumables
- (e.g. filter, well-plate, etc.)

#### Equipment
- (e.g. centrifuge, spectrophotometer, etc.)

#### Method
- (method used in this step)

#### Output
- (samples to the next step)

#### Results & Discussions
- (Any results and discussions. Link file path if needed)
'''

def _extract_section_content(uo_block: str, section_name: str) -> str:
    pattern = re.compile(r"#### " + re.escape(section_name) + r"\n(.*?)(?=\n####|\Z)", re.DOTALL)
    match = pattern.search(uo_block)
    if match:
        content = match.group(1).strip()
        return content if content and not content.startswith('(') else "(not specified)"
    return "(not specified)"

def _normalize_message_content(content: Union[str, List[Dict[str, Any]], None]) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for chunk in content:
            if isinstance(chunk, dict):
                text_value = (
                    chunk.get("text")
                    or chunk.get("input_text")
                    or (chunk.get("content") if isinstance(chunk.get("content"), str) else None)
                )
                if text_value:
                    parts.append(text_value)
            elif isinstance(chunk, str):
                parts.append(chunk)
        return "".join(parts)
    return ""

def _extract_file_content_from_messages(messages: List[Dict[str, Any]]) -> Optional[str]:
    best_block: Optional[str] = None
    best_score = -1

    for message in reversed(messages or []):
        role = (message.get("role") or "").lower()
        if role not in ("user", "system", "context"):
            continue
        content = _normalize_message_content(message.get("content"))
        if not content:
            continue

        for match in re.finditer(r"```(?P<lang>[^\n]*)\n(?P<body>[\s\S]*?)```", content):
            lang = match.group("lang").strip().lower()
            body = match.group("body").strip()
            if not body:
                continue

            score = 0
            if lang in ("markdown", "md", "labnote", "yaml"):
                score += 4
            elif lang == "":
                score += 1

            if body.startswith("---"):
                score += 3
            if "## [" in body or "### [" in body:
                score += 3
            if "####" in body:
                score += 1
            if "Unit Operation" in body or "유닛" in body:
                score += 1
            if len(body) > 200:
                score += 1

            if score > best_score:
                best_block = body
                best_score = score

        if best_block:
            break

    return best_block

def _sanitize_option_text(option: str, section: str) -> Tuple[str, Optional[str]]:
    """
    Remove helper metadata (model name, quality score, trailing prompts) so the text that
    gets inserted into the lab note contains only the section body. Returns the cleaned
    content together with the metadata line, if any.
    """
    if not option:
        return "", None

    text = option.strip()
    meta_line = None

    if text.startswith("---"):
        first_line, _, remainder = text.partition("\n")
        meta_line = first_line.strip()
        text = remainder.lstrip()

    heading_pattern = re.compile(rf"^###\s*{re.escape(section)}\s*\n", re.IGNORECASE)
    text = heading_pattern.sub("", text, count=1)

    text = re.sub(r"\n*어느 번호.*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\n*Which option.*$", "", text, flags=re.IGNORECASE).strip()

    if not text:
        return option.strip(), meta_line

    return text, meta_line

def _infer_experiment_goal(file_content: str) -> Optional[str]:
    if not file_content:
        return None

    front_matter_match = re.search(r"^---\s*\n(.*?)\n---", file_content, re.DOTALL | re.MULTILINE)
    if front_matter_match:
        front_matter = front_matter_match.group(1)
        for key in ("experiment_goal", "experiment-goal", "goal", "title"):
            pattern = re.compile(rf"^{key}\s*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
            match = pattern.search(front_matter)
            if match:
                return match.group(1).strip().strip("'\"")

    workflow_heading_match = re.search(r"^##\s+\[([^\]]+)\]\s*(.*)$", file_content, re.MULTILINE)
    if workflow_heading_match:
        workflow = workflow_heading_match.group(1).strip()
        description = workflow_heading_match.group(2).strip()
        if description:
            return f"{workflow} {description}".strip()
        return workflow

    generic_heading_match = re.search(r"^##\s+(.+)$", file_content, re.MULTILINE)
    if generic_heading_match:
        return generic_heading_match.group(1).strip()

    return None


FILE_PATH_HINT_PATTERNS = [
    re.compile(r"^File(?:path)?\s*[:=]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^Path\s*[:=]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^<!--\s*filepath\s*[:=]\s*(.+?)\s*-->$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*//\s*filepath\s*[:=]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
]

RELATED_CONTEXT_MAX_FILES = 3
RELATED_CONTEXT_MAX_CHARS = 1800


def _extract_file_path_from_messages(messages: List[Dict[str, Any]]) -> Optional[str]:
    """Attempt to recover the active file path from structured chat messages."""
    for message in reversed(messages or []):
        content = _normalize_message_content(message.get("content"))
        if not content:
            continue
        for pattern in FILE_PATH_HINT_PATTERNS:
            match = pattern.search(content)
            if match:
                candidate = match.group(1).strip().strip('`"')
                if candidate:
                    candidate_path = Path(candidate)
                    if not candidate_path.is_absolute():
                        candidate_path = (Path.cwd() / candidate_path).resolve()
                    if candidate_path.exists():
                        return str(candidate_path)
        code_hint = re.search(r"^```[^\n]*\n\s*filepath\s*[:=]\s*(.+)$", content, re.IGNORECASE | re.MULTILINE)
        if code_hint:
            candidate = code_hint.group(1).strip().strip('`"')
            if candidate:
                candidate_path = Path(candidate)
                if not candidate_path.is_absolute():
                    candidate_path = (Path.cwd() / candidate_path).resolve()
                if candidate_path.exists():
                    return str(candidate_path)
    return None


def _extract_uo_block_from_text(file_content: str, uo_id: str) -> Optional[str]:
    if not file_content or not uo_id:
        return None
    pattern = re.compile(
        r"(###\s*\[" + re.escape(uo_id) + r"[^\]]*\][\s\S]*?)(?=\n###\s*\[U[A-Z]{2,3}\d{3}|\Z)",
        re.DOTALL
    )
    match = pattern.search(file_content)
    if match:
        return match.group(1).strip()
    return None


def _looks_like_natural_language(snippet: str) -> bool:
    if not snippet:
        return False

    cleaned = re.sub(r"^\s*\d+[\).\s-]+", "", snippet, flags=re.MULTILINE).strip()
    if not cleaned:
        return False

    code_indicators = [
        r"\bdef\s+\w+\s*\(",
        r"\bclass\s+\w+\s*",
        r"^\s*//",
        r"^\s*#include\b",
        r"^\s*(?:if|for|while)\s*\(",
        r"[{};]{2,}",
        r"```",
        r"^\s*Changes?:",
        r"\breturn\b",
        r"\{\{",
    ]
    for pattern in code_indicators:
        if re.search(pattern, cleaned, re.MULTILINE | re.IGNORECASE):
            return False

    alpha_chars = sum(ch.isalpha() for ch in cleaned)
    structural_chars = sum(cleaned.count(ch) for ch in "{}[]();<>")
    if alpha_chars == 0:
        return False
    if structural_chars > alpha_chars:
        return False

    return True


def _collect_related_workflow_context(
    file_content: str,
    file_path: Optional[str],
    uo_id: str,
    section: str,
    max_files: int = RELATED_CONTEXT_MAX_FILES,
    max_chars: int = RELATED_CONTEXT_MAX_CHARS
) -> str:
    """Aggregate same-folder workflow excerpts for the target UO/section."""
    if not file_content or not uo_id or not section:
        return ""

    candidates: List[Path] = []
    seen_paths: Set[Path] = set()
    current_path: Optional[Path] = None
    base_dir: Optional[Path] = None

    if file_path:
        try:
            current_path = Path(file_path).expanduser().resolve()
            base_dir = current_path.parent
        except Exception as exc:
            logger.debug("Failed to resolve file_path '%s': %s", file_path, exc, exc_info=True)

    if base_dir and base_dir.exists():
        for md_path in sorted(base_dir.glob("*.md")):
            try:
                resolved = md_path.resolve()
            except Exception:
                resolved = md_path
            if current_path and resolved == current_path:
                continue
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            candidates.append(md_path)

    link_pattern = re.compile(r"\[[^\]]+\]\((?:\./)?([^)\s]+\.md)\)", re.IGNORECASE)
    for rel_link in link_pattern.findall(file_content or ""):
        rel_link = rel_link.strip()
        if not rel_link:
            continue
        rel_path = Path(rel_link)
        possible_paths: List[Path] = []
        if base_dir:
            possible_paths.append((base_dir / rel_path).resolve())
        else:
            for matched in Path.cwd().resolve().rglob(rel_path.name):
                possible_paths.append(matched)
                break
        for candidate_path in possible_paths:
            try:
                resolved = candidate_path.resolve()
            except Exception:
                resolved = candidate_path
            if not candidate_path.exists():
                continue
            if current_path and resolved == current_path:
                continue
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            candidates.append(candidate_path)

    contexts: List[str] = []

    for candidate in candidates:
        if len(contexts) >= max_files:
            break
        try:
            candidate_text = candidate.read_text(encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed to read candidate workflow '%s': %s", candidate, exc, exc_info=True)
            continue

        uo_block = _extract_uo_block_from_text(candidate_text, uo_id)
        section_body = _extract_section_content(uo_block or "", section) if uo_block else None

        try:
            if base_dir:
                label = str(candidate.resolve().relative_to(base_dir))
            else:
                label = str(candidate.resolve().relative_to(Path.cwd()))
        except Exception:
            label = candidate.name

        if section_body and section_body not in ("", "(not specified)"):
            snippet = section_body.strip()
            if len(snippet) > max_chars:
                snippet = snippet[:max_chars].rstrip() + "\n..."
            if not _looks_like_natural_language(snippet):
                logger.debug("Skipping related context from '%s' due to code-like content.", label)
                continue
            contexts.append(f"Source file: {label}\n#### {section}\n{snippet}")

    if contexts:
        return "\n\n".join(contexts[:max_files])
    return ""


def _summarize_uo_sections(file_content: Optional[str], max_uos: int = 5, max_sections: int = 6) -> str:
    if not file_content:
        return "No lab note content available."

    summary_parts: List[str] = []
    pattern = re.compile(
        r"###\s*\[(?P<uo>[A-Z]{2,3}\d{3})(?P<label>[^\]]*)\](?P<body>[\s\S]*?)(?=\n###\s*\[U[A-Z]{2,3}\d{3}|\Z)",
        re.MULTILINE
    )

    for idx, match in enumerate(pattern.finditer(file_content)):
        if idx >= max_uos:
            summary_parts.append("…")
            break
        uo_id = match.group("uo")
        label = (match.group("label") or "").strip()
        body = match.group("body") or ""
        section_titles = re.findall(r"^####\s+([^\n]+)", body, flags=re.MULTILINE)
        if section_titles:
            section_titles = section_titles[:max_sections]
        section_list = ", ".join(section_titles) if section_titles else "(no sections)"
        if label:
            summary_parts.append(f"{uo_id} ({label}): {section_list}")
        else:
            summary_parts.append(f"{uo_id}: {section_list}")

    return " | ".join(summary_parts) if summary_parts else "No unit operations detected."


async def _call_router_model(system_prompt: str, user_prompt: str, model_name: str) -> str:
    client = ollama.AsyncClient(timeout=45)
    response = await client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.1, "top_p": 0.8}
    )
    return (response.get("message", {}).get("content") or "").strip()


async def _route_user_intent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    router_model = ROUTER_MODEL_NAME
    if not query or not router_model or router_model.lower() in {"disabled", "none"}:
        return {"action": "chat", "reason": "Router disabled or query empty."}

    file_content = context.get("file_content")
    experiment_goal = context.get("experiment_goal")
    available_summary = _summarize_uo_sections(file_content)

    system_prompt = (
        "You route user requests for a lab note assistant. "
        "Decide whether the user wants to populate a specific Unit Operation section or engage in general chat. "
        "Respond strictly with a JSON object."
    )

    user_prompt = (
        "User message:" + "\n" + query.strip() + "\n\n"
        f"Experiment goal: {experiment_goal or '(unknown)'}\n"
        f"Available unit operations and sections: {available_summary}\n"
        "If the user explicitly requests filling/updating a section, set action to \"populate\" and include inferred 'uo_id' and 'section'. "
        "Otherwise set action to \"chat\".\n"
        "Return JSON: {\"action\": \"populate|chat\", \"uo_id\": <string or null>, \"section\": <string or null>, \"confidence\": <0-1>, \"reason\": <short text>}"
    )

    try:
        raw_response = await _call_router_model(system_prompt, user_prompt, router_model)
        json_match = re.search(r"\{[\s\S]*\}", raw_response)
        if not json_match:
            raise ValueError("Router did not produce JSON")
        decision = json.loads(json_match.group(0))
        logger.info(
            "Router decision: action=%s, uo=%s, section=%s, confidence=%s",
            decision.get("action"),
            decision.get("uo_id"),
            decision.get("section"),
            decision.get("confidence")
        )
        return decision
    except Exception as exc:
        logger.warning("Router fallback: %s", exc)
        return {"action": "chat", "reason": f"router_failed: {exc}"}


def _normalize_section_name(raw_section: str) -> str:
    """Normalize user-provided section names by trimming particles and 'section' markers."""
    if not raw_section:
        return ""
    cleaned = raw_section.strip(" \t`'\"-:,.")
    cleaned = re.sub(r"^(섹션|section)\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(섹션|section)$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(으로|로|을|를|에|에서)$", "", cleaned).strip(" \t`'\"-:,.")
    return cleaned.strip()


def _extract_uo_and_section_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Best-effort extraction of UO ID and section name from a free-form user reply."""
    if not text:
        return None, None

    normalized_text = text.strip()
    if not normalized_text:
        return None, None

    potential_uos = [
        match.group(1)
        for match in re.finditer(r"\b([A-Z]{2,3}\d{3})\b", normalized_text.upper())
        if match.group(1) in ALL_UOS_DATA
    ]

    uo_id = potential_uos[0] if potential_uos else None
    section = None

    if uo_id:
        section_candidate = re.sub(uo_id, "", normalized_text, count=1, flags=re.IGNORECASE).strip()
        section = _normalize_section_name(section_candidate)
    else:
        section = _normalize_section_name(normalized_text)

    return uo_id, section or None
def _chunk_text_for_stream(content: str, max_chunk_size: int = 800) -> List[str]:
    """Split assistant responses into manageable pieces for SSE streaming."""
    if not content:
        return [""]
    return [content[i:i + max_chunk_size] for i in range(0, len(content), max_chunk_size)]


async def _execute_populate_flow(
    conversation: Dict[str, Any],
    request_obj: "ChatRequest",
    uo_id: str,
    section: str
) -> str:
    """Run the populate agent flow and persist context for DPO feedback."""
    logger.info(f"Executing populate for UO: {uo_id}, Section: {section}")
    context = conversation.setdefault("context", {})

    file_content = request_obj.file_content or context.get("file_content")
    experiment_goal = context.get("experiment_goal") or request_obj.experiment_goal
    file_path = request_obj.file_path or context.get("file_path")

    if request_obj.file_path:
        context["file_path"] = request_obj.file_path

    if not file_content or not experiment_goal:
        return "Error: To populate a section, the full content of the lab note must be available in the context."

    uo_block = _extract_uo_block_from_text(file_content, uo_id)
    if not uo_block:
        available_uos = re.findall(r"^###\s*\[([A-Z]{2,3}\d{3})", file_content, re.MULTILINE)
        available_text = ", ".join(sorted(set(available_uos))) if available_uos else "없음"
        return (
            f"현재 문서에서 `{uo_id}` 유닛 오퍼레이션 헤더(예: `### [{uo_id} ...]`)를 찾지 못했습니다.\n"
            f"- 열린 파일에 포함된 UO ID: {available_text}\n"
            "- 올바른 워크플로우/랩노트 파일을 연 뒤 다시 `/populate`를 실행해주세요."
        )

    related_context = _collect_related_workflow_context(file_content, file_path, uo_id, section)
    if related_context:
        logger.info(
            "Including related workflow context for populate. snippet_len=%s",
            len(related_context)
        )

    agent_result = await run_agent_team(
        experiment_goal,
        file_content,
        section,
        uo_id,
        related_context=related_context
    )

    if agent_result and agent_result.get("options"):
        options = agent_result["options"]
        context.update({
            "state": "awaiting_dpo_feedback",
            "options": options,
            "uo_id": uo_id,
            "section": section,
            "file_content": file_content,
            "experiment_goal": experiment_goal,
            "file_path": file_path or context.get("file_path") or "continue_populate_refactored",
            "last_selection_signature": None,
            "last_selected_index": None
        })
        formatted_options = [f"{i + 1}.\n---\n{opt}" for i, opt in enumerate(options)]
        options_text = "\n\n".join(formatted_options)
        return (
            "다음은 AI가 제안하는 내용입니다. 마음에 드는 번호를 선택하거나, 수정사항과 함께 알려주세요.\n"
            "(예: '1번 선택', '2번 선택, 하지만 버퍼 농도를 50mM로 수정해줘')\n\n"
            f"{options_text}\n\n"
            "어느 번호를 선택할까요? 번호와 함께 추가 수정 요청이 있으면 알려주세요."
        )

    return "AI 에이전트 팀이 답변을 생성하지 못했습니다. 입력 형식을 확인해주세요."


async def _handle_interactive_populate_flow(
    conversation: Dict[str, Any],
    request_obj: "ChatRequest",
    query: str,
    populate_triggered: bool,
    has_arguments: bool
) -> Optional[str]:
    """Guide the user through an interactive `/populate` flow when arguments are missing."""
    context = conversation.setdefault("context", {})
    interactive_ctx = context.get("interactive_populate")

    if populate_triggered and has_arguments:
        if interactive_ctx:
            context.pop("interactive_populate", None)
        return None

    if populate_triggered and not has_arguments:
        context["interactive_populate"] = {"uo_id": None, "section": None}
        return (
            "어느 유닛 오퍼레이션을 채울까요? 예: `/populate USW070 Method`\n"
            "`/populate <UO_ID> <Section>` 형식 그대로 입력해주세요."
        )

    if not interactive_ctx:
        return None

    if query and re.search(r"\b(cancel|취소)\b", query, re.IGNORECASE):
        context.pop("interactive_populate", None)
        return "섹션 채우기 흐름을 취소했습니다. 다시 시작하려면 `/populate`를 입력해주세요."

    uo_id = interactive_ctx.get("uo_id")
    section = interactive_ctx.get("section")
    parsed_uo, parsed_section = _extract_uo_and_section_from_text(query or "")

    if parsed_uo and not uo_id:
        uo_id = parsed_uo
        interactive_ctx["uo_id"] = uo_id
    if parsed_section and not section:
        section = parsed_section
        interactive_ctx["section"] = section

    if not uo_id:
        return (
            "유닛 오퍼레이션 ID를 찾지 못했어요. `USW070`, `UHW220`처럼 문서의 헤더에 쓰인 ID를 알려주세요."
        )

    if not section:
        return (
            f"`{uo_id}`의 어떤 섹션을 채울까요? 문서에 있는 `####` 헤더와 동일한 이름을 알려주세요. 예: `Method`, `Reagent`"
        )

    context.pop("interactive_populate", None)
    return await _execute_populate_flow(conversation, request_obj, uo_id, section)

def _replace_section_content(file_content: str, uo_id: str, section: str, new_content: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Replace the body of a specific section under a Unit Operation and return the updated file content
    along with the original section body.
    """
    if not file_content:
        return None, None

    uo_pattern = r"(###\s*\[" + re.escape(uo_id) + r"[^\]]*\][\s\S]*?)" \
                 r"(?=\n###\s*\[U[A-Z]{2,3}\d{3}|\Z)"
    uo_match = re.search(uo_pattern, file_content)
    if not uo_match:
        return None, None

    uo_block = uo_match.group(1)
    section_pattern = (
        r"(####\s*" + re.escape(section) + r"\n)"
        r"([\s\S]*?)(?=\n####\s|\n###\s*\[U[A-Z]{2,3}\d{3}|\Z)"
    )
    section_match = re.search(section_pattern, uo_block)
    if not section_match:
        return None, None

    section_header = section_match.group(1)
    original_body = section_match.group(2)

    normalized_body = original_body.rstrip("\n")
    normalized_new = new_content.strip() + "\n"

    updated_section = section_header + normalized_new
    updated_uo_block = (
        uo_block[:section_match.start()]
        + updated_section
        + uo_block[section_match.end():]
    )

    updated_file_content = (
        file_content[:uo_match.start()]
        + updated_uo_block
        + file_content[uo_match.end():]
    )

    return updated_file_content, normalized_body

def _build_section_diff(old: str, new: str, section: str) -> str:
    """Generate a unified diff between the old and new section bodies."""
    old_lines = (old or "").splitlines()
    new_lines = (new or "").splitlines()
    diff_lines = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{section} (old)",
        tofile=f"{section} (new)",
        lineterm=""
    )
    return "\n".join(diff_lines)

def _find_last_populate_command(messages: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """Extract the most recent '/populate <UO_ID> <Section>' command from the conversation."""
    for message in reversed(messages or []):
        if message.get("role") != "user":
            continue
        content = _normalize_message_content(message.get("content"))
        if not content:
            continue
        match = re.search(r"^\s*/populate\s+(?P<user_input>[^\n`]+)", content, re.IGNORECASE | re.MULTILINE)
        if match:
            user_input = match.group("user_input").strip()
            parts = user_input.split(maxsplit=1)
            if len(parts) >= 2:
                return parts[0].upper(), parts[1].strip()
    return None, None

def _extract_options_from_messages(messages: List[Dict[str, Any]]) -> List[str]:
    """Parse assistant-issued populate options from prior messages."""
    option_pattern = re.compile(r"(\d+)\.\n---\n([\s\S]*?)(?=\n\d+\.\n---\n|\Z)")
    for message in reversed(messages or []):
        if message.get("role") != "assistant":
            continue
        content = _normalize_message_content(message.get("content"))
        if not content:
            continue
        matches = option_pattern.findall(content)
        if matches:
            options = [option_text.strip() for _, option_text in matches]
            if options:
                return options
    return []

async def _handle_dpo_feedback(
    query: str,
    request_obj: ChatRequest,
    conversation: Dict[str, Any],
    messages: List[Dict[str, Any]]
) -> Optional[str]:
    """Handle user selection feedback for populate suggestions."""
    if not query:
        return None

    selection_match = re.search(r"(?<!\d)(\d{1,2})\s*번(?=\s|$|[.,]|으로)", query)
    if not selection_match:
        return None

    context = conversation.setdefault("context", {})
    options = context.get("options") or _extract_options_from_messages(messages)

    if not options:
        logger.warning("DPO feedback detected but no options available in context or history.")
        return "선택지를 찾지 못했습니다. 먼저 '/populate <UO_ID> <Section>' 명령으로 옵션을 생성해주세요."

    chosen_index = int(selection_match.group(1)) - 1
    if not (0 <= chosen_index < len(options)):
        return "잘못된 번호입니다. 다시 선택해주세요."

    edit_instruction = None
    edit_match = re.search(
        r"번(?:\s*(?:선택|선택합니다|선택할게요|으로\s*결정))?\s*(?:,|\s+하지만\s+)(.+)",
        query
    )
    if edit_match:
        edit_instruction = edit_match.group(1).strip()

    uo_id = context.get("uo_id")
    section = context.get("section")

    if not uo_id or not section:
        uo_id, section = _find_last_populate_command(messages)

    if not uo_id or not section:
        logger.error("Unable to determine UO ID or section while processing DPO feedback.")
        return "선택을 반영할 수 없습니다. '/populate <UO_ID> <Section>' 형식으로 다시 시도해주세요."

    chosen_original = options[chosen_index]
    cleaned_text, metadata_line = _sanitize_option_text(chosen_original, section or "")
    chosen_edited = cleaned_text

    if edit_instruction:
        edit_prompt = (
            f"Apply the following edit to the text below: '{edit_instruction}'\n\nTEXT:\n{chosen_edited}"
        )
        chosen_edited = await call_llm_api(
            "You are a text editor.",
            edit_prompt,
            "llama3.1:70b"
        )
        chosen_edited = (chosen_edited or "").strip()
        chosen_edited, _ = _sanitize_option_text(chosen_edited, section or "")

    chosen_edited = (chosen_edited or "").strip()

    rejected_options = [opt for i, opt in enumerate(options) if i != chosen_index]

    experiment_goal = context.get("experiment_goal") or request_obj.experiment_goal
    file_content = context.get("file_content") or request_obj.file_content

    if not file_content:
        logger.error("Missing file content for DPO feedback handling.")
        return "선택을 반영하려면 현재 랩노트 전체 내용을 포함하여 다시 시도해주세요."

    file_path = context.get("file_path", "continue_populate_refactored")

    selection_signature = (
        uo_id,
        section,
        chosen_index,
        chosen_edited
    )

    if context.get("last_selection_signature") == selection_signature:
        logger.info("Duplicate selection detected; skipping DPO save.")
        return (
            "⚠️ 이미 동일한 옵션을 기록했습니다. 다른 초안을 선택하려면 새로운 번호를 입력하거나 "
            "`/populate` 명령으로 초안을 다시 생성해주세요."
        )

    await _save_dpo_data(
        uo_id=uo_id,
        section=section,
        chosen_original=chosen_original,
        chosen_edited=chosen_edited,
        rejected=rejected_options,
        query=experiment_goal or "",
        file_content=file_content,
        file_path=file_path
    )

    updated_file_content, previous_section_body = _replace_section_content(
        file_content,
        uo_id,
        section,
        chosen_edited
    )
    diff_text = None
    if updated_file_content is not None:
        context["file_content"] = updated_file_content
        diff_text = _build_section_diff(
            previous_section_body or "",
            chosen_edited.strip(),
            section
        )

    context.update({
        "state": "awaiting_dpo_feedback",
        "last_selected_index": chosen_index,
        "last_selection_signature": selection_signature,
        "uo_id": uo_id,
        "section": section,
        "options": options,
        "experiment_goal": experiment_goal,
        "file_path": file_path
    })

    selection_label = metadata_line.strip("- ").strip() if metadata_line else f"{chosen_index + 1}번 옵션"
    response_lines = [
        "✅ 피드백을 성공적으로 기록하고 AI 모델 학습에 반영했습니다.",
        "",
        f"선택된 초안: {selection_label}",
        "",
        "```markdown",
        chosen_edited.strip(),
        "```"
    ]

    if diff_text:
        response_lines.extend([
            "",
            "```diff",
            diff_text,
            "```",
            "위 패치를 적용하면 해당 섹션이 최신 초안으로 업데이트됩니다."
        ])

    response_lines.extend(["", "추가로 손보고 싶은 부분이 있다면 말씀해주세요."])

    return "\n".join(response_lines)

def _init_feedback_db():
    db_path = os.getenv("EVALUATION_DB_PATH", "scripts/evaluation_results.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                uo_id TEXT NOT NULL,
                section TEXT NOT NULL,
                edit_distance_ratio REAL NOT NULL
            )
        ''')
        logger.info(f"Feedback metrics table initialized in '{db_path}'")

def _run_git_operations(token: str, repo_url: str, local_path_str: str, preference_data: dict, commit_message: str):
    local_path = Path(local_path_str)

    # Build authenticated URL suitable for GitHub over HTTPS
    # Use x-access-token as username to avoid "password auth not supported" issues
    parsed = urlparse(repo_url)
    if parsed.scheme in {"http", "https"}:
        netloc = parsed.netloc
        if "@" in netloc:
            netloc = netloc.split("@", 1)[-1]
        repo_url_with_token = urlunparse(
            (
                parsed.scheme,
                f"x-access-token:{token}@{netloc}",
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    else:
        # Fallback to original when not HTTPS (e.g., ssh)
        repo_url_with_token = repo_url

    # Clone or open existing repo
    if local_path.exists():
        repo = git.Repo(local_path)
    else:
        logger.info(f"Cloning DPO repository to {local_path}...")
        repo = git.Repo.clone_from(repo_url_with_token, local_path)

    # Ensure origin URL uses token form
    origin = repo.remote(name='origin')
    origin.set_url(repo_url_with_token)

    # Set local user if not present (avoids 'Please tell me who you are')
    try:
        author_name = os.getenv("GIT_AUTHOR_NAME", "labnote-bot")
        author_email = os.getenv("GIT_AUTHOR_EMAIL", "labnote-bot@example.com")
        repo.git.config("user.name", author_name)
        repo.git.config("user.email", author_email)
    except Exception:  # best-effort
        pass

    # Reset problematic states and fetch
    status_out = repo.git.status()
    if repo.is_dirty() or "rebase" in status_out:
        logger.warning("Repository is dirty or in rebase; resetting to remote HEAD...")
        if "rebase" in status_out:
            try:
                repo.git.rebase('--abort')
            except Exception:
                pass
    logger.info("Fetching latest changes from DPO repository...")
    origin.fetch(prune=True)

    # Detect default branch from remote HEAD; fallback to main/master/first
    target_branch = None
    try:
        # e.g. origin/HEAD -> origin/main
        target_branch = origin.refs.HEAD.reference.remote_head  # type: ignore[attr-defined]
    except Exception:
        pass
    if not target_branch:
        remote_heads = [getattr(r, 'remote_head', None) for r in origin.refs]
        remote_heads = [h for h in remote_heads if h]
        for cand in ("main", "master"):
            if cand in remote_heads:
                target_branch = cand
                break
        if not target_branch and remote_heads:
            target_branch = remote_heads[0]

    if target_branch:
        # Ensure we are on a real local branch tracking the remote
        logger.info(f"Checking out local branch '{target_branch}' from origin/{target_branch}...")
        repo.git.checkout('-B', target_branch, f'origin/{target_branch}')
        # Set upstream to avoid detached HEAD and simplify pushes
        try:
            repo.git.branch('--set-upstream-to', f'origin/{target_branch}', target_branch)
        except Exception:
            pass
    else:
        logger.warning("No remote branches found on origin; staying on current HEAD.")

    # Write preference JSON
    data_dir = local_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}.json"
    file_path = data_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(preference_data, f, ensure_ascii=False, indent=2)
    logger.info(f"DPO data saved to {file_path}")

    # Commit and push
    repo.index.add([str(file_path.resolve())])
    repo.index.commit(commit_message)
    logger.info("Pushing DPO data to remote repository...")
    if target_branch:
        # Push current HEAD explicitly to the target branch to handle edge cases
        origin.push(refspec=f'HEAD:refs/heads/{target_branch}')
    else:
        origin.push()
    logger.info("Successfully pushed DPO data to Git.")

async def _save_dpo_data(
    uo_id: str, section: str, chosen_original: str, chosen_edited: str,
    rejected: List[str], query: str, file_content: str, file_path: str = "chat"
):
    """DPO 데이터를 생성하고 Git에 저장하는 로직을 처리하는 헬퍼 함수"""
    repo_url = os.getenv("DPO_TRAINER_REPO_URL")
    token = os.getenv("GIT_AUTH_TOKEN")
    local_path_str = os.getenv("DPO_REPO_LOCAL_PATH", "./labnote-dpo-trainer-data")

    if not repo_url or not token:
        raise HTTPException(status_code=500, detail="DPO Git repository is not configured on the server.")

    uo_name = ALL_UOS_DATA.get(uo_id, "Unknown Operation")
    uo_block_pattern = re.compile(r"(### \[" + re.escape(uo_id) + r".*?\]\n.*?)(?=### \[U[A-Z]{2,3}\d{3}|\Z)", re.DOTALL)
    uo_match = uo_block_pattern.search(file_content)
    uo_block_content = uo_match.group(1) if uo_match else ""
    input_context = _extract_section_content(uo_block_content, "Input")
    output_context = _extract_section_content(uo_block_content, "Output")
    
    prompt = (
        f"Given the experimental context, write the '{section}' section for the Unit Operation '{uo_id}: {uo_name}'.\n"
        f"- Overall Goal: {query}\n"
        f"- Starting Materials (Input): {input_context}\n"
        f"- Desired End-Product (Output): {output_context}\n"
        f"- The initial AI suggestion was: {chosen_original}"
    )

    path_parts = file_path.replace("\\", "/").split("/")
    edit_distance_ratio = fuzz.ratio(chosen_original, chosen_edited) / 100.0
    
    preference_data = {
        "prompt": prompt,
        "chosen": chosen_edited,
        "rejected": [chosen_original] + rejected,
        "metadata": {
            "source": "vscode_extension_feedback",
            "experiment_folder": path_parts[-2] if len(path_parts) > 1 else "unknown_experiment",
            "workflow_file": path_parts[-1] if path_parts else "unknown_workflow",
            "unit_operation_id": uo_id,
            "section": section,
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "supervisor_evaluations": [],
            "edit_distance_ratio": edit_distance_ratio
        }
    }

    try:
        _init_feedback_db()
        db_path = os.getenv("EVALUATION_DB_PATH", "scripts/evaluation_results.db")
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback_metrics (timestamp, uo_id, section, edit_distance_ratio) VALUES (?, ?, ?, ?)",
                (preference_data["metadata"]["timestamp_utc"], uo_id, section, edit_distance_ratio)
            )
        logger.info(f"Saved edit_distance_ratio ({edit_distance_ratio:.2f}) to DB for {uo_id}/{section}")
    except Exception as db_error:
        logger.error(f"Failed to save feedback metric to DB: {db_error}", exc_info=True)

    commit_message = f"feat: Add DPO data for {uo_id}/{section}"
    
    await asyncio.to_thread(
        _run_git_operations, token, repo_url, local_path_str, preference_data, commit_message
    )

# --- API 엔드포인트 ---

@app.post("/create_scaffold", response_model=LabNoteResponse)
async def create_scaffold(request: CreateScaffoldRequest):
    logger.info(f"Corrected multi-file scaffold generation for WF: {request.workflow_id}")
    try:
        experimenter = request.experimenter
        formatted_date = get_seoul_date_string()
        
        wf_id = request.workflow_id
        wf_name = ALL_WORKFLOWS_DATA.get(wf_id, "Custom Workflow")
        
        wf_description = "> 이 워크플로의 설명을 간략하게 작성합니다 (아래 설명은 템플릿으로 사용자 목적에 맞도록 수정합니다)"
        
        workflow_file_name = f"001_{wf_id}_{wf_name.replace(' ', '_')}.md"

        unit_operation_blocks = []
        for uo_id in request.unit_operation_ids:
            uo_name = ALL_UOS_DATA.get(uo_id, "Unknown Operation")
            unit_operation_blocks.append(create_unit_operation_template(uo_id, uo_name, experimenter))
        
        all_uo_blocks_content = "\n\n".join(unit_operation_blocks)

        workflow_content = f'''
---
title: "{wf_id} {wf_name}"
experimenter: "{experimenter}"
created_date: '{formatted_date}'
last_updated_date: '{formatted_date}'
---

## [{wf_id} {wf_name}]
{wf_description}

## 🗂️ 관련 유닛오퍼레이션

{all_uo_blocks_content}
'''
        link_text = f"001 {wf_id} {wf_name}"
        workflow_link = f"[ ] [{link_text}](./{workflow_file_name})"

        readme_content = f'''
---
title: "{request.query}"
experimenter: "{experimenter}"
created_date: '{formatted_date}'
last_updated_date: '{formatted_date}'
experiment_type: labnote
---

## 🎯 실험 목표
> 이 실험의 주된 목표와 가설을 간략하게 작성합니다.

## 🗂️ 관련 워크플로
> 아래 표시 사이에 관련된 워크플로 파일 목록을 입력합니다.
> `F1`, `New workflow` 명령 수행시 해당 목록은 표시된 위치 사이에 자동 추가됩니다.

{workflow_link}
'''
        
        files_to_create = {
            "README.md": readme_content,
            workflow_file_name: workflow_content
        }

        return LabNoteResponse(files=files_to_create)

    except Exception as e:
        logger.error(f"Error during multi-file scaffold creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating scaffold: {e}")


@app.post("/populate_note", response_model=PopulateNoteResponse)
async def populate_note(request: PopulateNoteRequest):
    logger.info(f"Phase 2: Populating section '{request.section}' for UO '{request.uo_id}'")
    try:
        uo_block = _extract_uo_block_from_text(request.file_content, request.uo_id)
        if not uo_block:
            available_uos = re.findall(r"^###\s*\[([A-Z]{2,3}\d{3})", request.file_content, re.MULTILINE)
            available_text = ", ".join(sorted(set(available_uos))) if available_uos else "없음"
            raise HTTPException(
                status_code=400,
                detail=(
                    f"파일에서 '{request.uo_id}' 유닛 오퍼레이션을 찾을 수 없습니다. "
                    f"현재 문서에 존재하는 UO ID: {available_text}"
                )
            )

        related_context = _collect_related_workflow_context(
            request.file_content,
            request.file_path,
            request.uo_id,
            request.section
        )
        if related_context:
            logger.info(
                "Populate endpoint including related workflow context. snippet_len=%s",
                len(related_context)
            )

        agent_result = await run_agent_team(
            request.query,
            request.file_content,
            request.section,
            request.uo_id,
            related_context=related_context
        )

        if not agent_result:
            logger.warning("Populate endpoint received empty agent result; returning fallback message.")
            return PopulateNoteResponse(
                uo_id=request.uo_id,
                section=request.section,
                options=["AI 에이전트가 응답을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."],
                feedback="AI 에이전트가 응답을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."
            )

        options = agent_result.get("options") or []
        if not options:
            feedback_msg = agent_result.get("feedback") or "AI 에이전트가 유의미한 초안을 만들지 못했습니다. 다시 시도해 주세요."
            logger.warning("Agent team returned no options; sending feedback-only response.")
            return PopulateNoteResponse(
                uo_id=request.uo_id,
                section=request.section,
                options=[feedback_msg],
                feedback=feedback_msg
            )

        return PopulateNoteResponse(**agent_result)
    except Exception as e:
        logger.error(f"Error populating note: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error populating note: {e}")


@app.post("/record_preference", status_code=204)
async def record_preference(request: PreferenceRequest):
    logger.info(f"Recording DPO data for UO '{request.uo_id}' via dedicated endpoint.")
    try:
        await _save_dpo_data(
            uo_id=request.uo_id,
            section=request.section,
            chosen_original=request.chosen_original,
            chosen_edited=request.chosen_edited,
            rejected=request.rejected,
            query=request.query,
            file_content=request.file_content,
            file_path=request.file_path
        )
    except git.exc.GitCommandError as e:
        logger.error(f"Git command failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to push DPO data to Git repository: {e.stderr}")
    except Exception as e:
        logger.error(f"Error recording preference to Git: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while recording preference.")

@app.post("/record_completion_feedback", status_code=204)
async def record_completion_feedback(request: CompletionFeedbackRequest):
    try:
        # Derive optional unit operation id if present in the content
        uo_match = re.search(r"^###\s*\[(U[A-Z]{2,3}\d{3,4}).*?\]", request.file_content, re.MULTILINE)
        unit_operation_id = uo_match.group(1) if uo_match else None

        # Build a completion-style payload compatible with the DPO repo schema
        prompt = (
            f"Completion event captured for {request.completion_type}.\n"
            f"- Workflow Title: {request.workflow_title}\n"
            f"- Experiment Topic: {request.experiment_topic}"
        )

        preference_data = {
            "prompt": prompt,
            "chosen": request.file_content,
            "rejected": [],
            "metadata": {
                "source": "completion_event",
                "completion_type": request.completion_type,
                "workflow_title": request.workflow_title,
                "experiment_topic": request.experiment_topic,
                "unit_operation_id": unit_operation_id,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        }

        repo_url = os.getenv("DPO_TRAINER_REPO_URL")
        token = os.getenv("GIT_AUTH_TOKEN")
        local_path_str = os.getenv("DPO_REPO_LOCAL_PATH", "./labnote-dpo-trainer-data")
        if not repo_url or not token:
            raise HTTPException(status_code=500, detail="DPO Git repository is not configured on the server.")

        commit_message = f"chore: record {request.completion_type} completion for '{request.workflow_title}'"
        await asyncio.to_thread(
            _run_git_operations, token, repo_url, local_path_str, preference_data, commit_message
        )
    except git.exc.GitCommandError as e:
        logger.error(f"Git command failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to push completion data to Git repository: {e.stderr}")
    except Exception as e:
        logger.error(f"Error recording completion feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while recording completion feedback.")


@app.post("/record_chat_preference", status_code=204)
async def record_chat_preference(request: ChatPreferenceRequest):
    """Save DPO-style preference data directly from chat results (non-populate flow)."""
    try:
        chosen_original = request.generated_text
        chosen_edited = request.edited_text or chosen_original
        rejected: List[str] = []
        query = request.prompt
        file_content = request.file_content or ""
        file_path = request.file_path or "chat"
        await _save_dpo_data(
            uo_id=request.uo_id,
            section=request.section,
            chosen_original=chosen_original,
            chosen_edited=chosen_edited,
            rejected=rejected,
            query=query,
            file_content=file_content,
            file_path=file_path,
        )
    except git.exc.GitCommandError as e:
        logger.error(f"Git command failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to push DPO data to Git repository: {e.stderr}")
    except Exception as e:
        logger.error(f"Error recording chat preference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while recording chat preference.")

@app.post("/record_git_feedback", status_code=204)
async def record_git_feedback(request: GitFeedbackRequest):
    logger.info(f"Received finalized DPO data from Git for: {request.metadata.get('workflow_file')}")
    pass

@app.get("/constants", summary="Get All Workflows and Unit Operations")
def get_constants():
    return {
        "ALL_WORKFLOWS": ALL_WORKFLOWS_DATA,
        "ALL_UOS": ALL_UOS_DATA
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        query = next((msg['content'] for msg in reversed(request.messages) if msg['role'] == 'user'), '') if request.messages else ''

        # Stateless: 요청에서 직접 context를 가져와 사용합니다.
        incoming_context = request.context.copy() if isinstance(request.context, dict) else {}
        conversation = {
            "messages": request.messages,
            "context": incoming_context
        }

        conversation_id = request.conversation_id or incoming_context.get("conversation_id")
        if not conversation_id:
            conversation_id = f"labnote-{uuid.uuid4().hex}"

        # file_path, file_content, experiment_goal을 요청에서 직접 받아 context에 업데이트합니다.
        context = conversation.setdefault("context", {})
        context["conversation_id"] = conversation_id
        if request.file_path:
            context["file_path"] = request.file_path
        if request.file_content:
            context["file_content"] = request.file_content
        if request.experiment_goal:
            context["experiment_goal"] = request.experiment_goal

        generated_text = ""

        # --- 분기 로직 ---

        populate_match = re.search(r"^\s*/populate\s+(?P<user_input>[^\n`]+)", query, re.IGNORECASE | re.MULTILINE) if query else None
        populate_triggered = re.search(r"^\s*/populate\b", query, re.IGNORECASE | re.MULTILINE) is not None if query else False
        interactive_response = None
        effective_model = request.model or "labnote-backend"

        if effective_model == "labnote-backend":
            interactive_response = await _handle_interactive_populate_flow(
                conversation,
                request,
                query,
                populate_triggered,
                bool(populate_match)
            )
        dpo_feedback_response = await _handle_dpo_feedback(query, request, conversation, request.messages or [])

        if dpo_feedback_response is not None:
            generated_text = dpo_feedback_response
        elif effective_model == "labnote-backend" and interactive_response is not None:
            generated_text = interactive_response
        elif populate_match and effective_model == "labnote-backend":
            # 1. Dedicated flow for the "labnote-backend" model (Section Population)
            logger.info("Labnote Backend Logic model selected. Executing section population flow...")
            logger.info("Raw user query for population flow: %s", query)

            user_input = populate_match.group('user_input').strip()
            parts = user_input.split(maxsplit=1)

            if len(parts) < 2:
                uo_id = parts[0].upper() if parts else ""
                context = conversation.setdefault("context", {})
                context["interactive_populate"] = {"uo_id": uo_id or None, "section": None}
                if uo_id:
                    generated_text = (
                        f"`{uo_id}`의 어떤 섹션을 채울까요? 문서에 있는 `####` 헤더와 동일한 이름을 알려주세요. 예: `Method`, `Reagent`"
                    )
                else:
                    generated_text = "어느 유닛 오퍼레이션을 채울까요? 예: `USW070`"
            else:
                uo_id = parts[0].upper()
                section = parts[1].strip()

                if not section:
                    context = conversation.setdefault("context", {})
                    context["interactive_populate"] = {"uo_id": uo_id, "section": None}
                    generated_text = (
                        f"`/populate {uo_id} Method`처럼 `/populate <UO_ID> <Section>` 형식으로 입력해주세요. "
                        "문서의 `####` 헤더와 같은 섹션명을 사용해야 합니다."
                    )
                else:
                    generated_text = await _execute_populate_flow(conversation, request, uo_id, section)
        elif populate_triggered and effective_model == "labnote-backend":
            generated_text = (
                "어느 유닛 오퍼레이션을 채울까요? `/populate USW070 Method`처럼 "
                "`/populate <UO_ID> <Section>` 형식으로 입력해주세요."
            )
        else:
            router_used = False
            router_decision: Optional[Dict[str, Any]] = None

            if effective_model == "labnote-backend" and query:
                router_decision = await _route_user_intent(query, context)
                if router_decision.get("action") == "populate":
                    candidate_uo = router_decision.get("uo_id")
                    candidate_section = router_decision.get("section")

                    if not candidate_uo or not candidate_section:
                        heuristic_uo, heuristic_section = _extract_uo_and_section_from_text(query)
                        candidate_uo = candidate_uo or heuristic_uo
                        candidate_section = candidate_section or heuristic_section

                    if candidate_uo and candidate_section:
                        generated_text = await _execute_populate_flow(conversation, request, candidate_uo, candidate_section)
                        router_used = True
                    else:
                        logger.info("Router suggested populate but details were insufficient; requesting clarification.")
                        generated_text = (
                            "어느 유닛 오퍼레이션과 섹션을 채워야 할지 정확히 알려주세요. "
                            "예: `/populate USW070 Method`"
                        )
                        router_used = True

            if not router_used:
                # 2. General Conversation
                logger.info(f"Running general chat flow for model: {request.model}")
                llm_model_name = os.getenv("LLM_MODEL", "llama3.1:8b")
                if request.model and request.model != "labnote-backend":
                    llm_model_name = request.model

                messages = conversation["messages"]
                if not any(msg.get('role') == 'system' for msg in messages):
                    system_prompt = {
                        "role": "system",
                        "content": "You are a professional scientific assistant. Your response should be helpful and informative."
                    }
                    messages.insert(0, system_prompt)

                response = await ollama.AsyncClient(timeout=60).chat(
                    model=llm_model_name,
                    messages=messages,
                    options={'temperature': 0.1}
                )
                raw_text = response['message']['content'].strip()
                logger.info(f"DIAGNOSIS: Raw text from LLM: '{raw_text[:300]}'")

                generated_text = _post_process_content(raw_text)
                logger.info(f"DIAGNOSIS: Processed text: '{generated_text}'")

        # Final response preparation
        # 상태 비저장으로 변경: 업데이트된 context를 응답에 포함하여 반환합니다.
        conversation["messages"].append({"role": "assistant", "content": generated_text})
        return ChatResponse(
            response=generated_text,
            context=conversation.get("context", {}),
            conversation_id=conversation_id
        )

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def openai_compat(request: Dict[str, Any]):
    """OpenAI 호환 엔드포인트 (VSCode Continue 등에서 사용)."""
    messages = request.get("messages") or []
    stream = bool(request.get("stream"))
    stream_options = request.get("stream_options") or {}
    if not isinstance(stream_options, dict):
        stream_options = {}
    include_usage = bool(stream_options.get("include_usage"))

    model_name = request.get("model") or "labnote-backend"
    conversation_id = request.get("conversation_id") or f"labnote-{uuid.uuid4().hex}"

    logger.info(
        "OpenAI compatibility handler invoked: model=%s, messages=%d, conversation_id=%s, stream=%s",
        model_name,
        len(messages) if isinstance(messages, list) else 0,
        conversation_id,
        stream,
    )

    if messages:
        last_message = messages[-1]
        last_content = _normalize_message_content(last_message.get("content"))
        logger.info(
            "Last message role=%s, content_preview=%s",
            last_message.get("role"),
            (last_content[:200] + "...") if last_content and len(last_content) > 200 else last_content,
        )

    file_content = request.get("file_content") or _extract_file_content_from_messages(messages)
    experiment_goal = request.get("experiment_goal")
    if not experiment_goal and file_content:
        experiment_goal = _infer_experiment_goal(file_content)
    if not experiment_goal and file_content:
        experiment_goal = "Experiment goal not provided."

    logger.info(
        "Inferred context for Continue: file_content_len=%s, experiment_goal_preview=%s",
        len(file_content) if file_content else 0,
        (experiment_goal[:120] + "...") if experiment_goal and len(experiment_goal) > 120 else experiment_goal,
    )

    context_payload = request.get("context") if isinstance(request.get("context"), dict) else {}
    context_payload.setdefault("conversation_id", conversation_id)

    handshake_payload = (
        not messages
        and not file_content
        and not experiment_goal
        and not request.get("file_path")
        and len(context_payload) <= 1  # only conversation_id present
    )

    logger.info(
        "OpenAI compatibility diagnostics: handshake_candidate=%s | context_keys=%s | file_path=%s | stream=%s",
        handshake_payload,
        list(context_payload.keys()),
        bool(request.get("file_path")),
        stream,
    )

    response_model_name = model_name or os.getenv("LLM_MODEL", "labnote-backend")
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    created_ts = int(time.time())
    usage_payload = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    if handshake_payload:
        logger.info("OpenAI compatibility received empty payload; returning readiness acknowledgement.")
        assistant_content = "LabNote backend is ready."
        return {
            "id": response_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": response_model_name,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": assistant_content},
                "finish_reason": "stop",
            }],
            "conversation_id": conversation_id,
            "usage": usage_payload if include_usage else None,
        }

    chat_request = ChatRequest(
        model=model_name,
        messages=messages,
        context=context_payload,
        conversation_id=conversation_id,
        file_content=file_content,
        experiment_goal=experiment_goal,
        file_path=request.get("file_path"),
    )

    labnote_response = await chat(chat_request)
    assistant_content = labnote_response.response or ""
    context_return = labnote_response.context or {}
    conversation_id = labnote_response.conversation_id or conversation_id

    logger.info(
        "OpenAI compatibility returning response_preview=%s",
        (assistant_content[:200] + "...") if len(assistant_content) > 200 else assistant_content,
    )

    if stream:
        content_chunks = _chunk_text_for_stream(assistant_content)

        async def event_generator():
            for idx, chunk_text in enumerate(content_chunks):
                delta_payload = {"content": chunk_text}
                if idx == 0:
                    delta_payload["role"] = "assistant"

                chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": response_model_name,
                    "choices": [{
                        "index": 0,
                        "delta": delta_payload,
                        "logprobs": None,
                        "finish_reason": None,
                    }],
                    "conversation_id": conversation_id,
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            final_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": response_model_name,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "logprobs": None,
                    "finish_reason": "stop",
                }],
                "conversation_id": conversation_id,
            }
            if include_usage:
                final_chunk["usage"] = usage_payload
            yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return {
        "id": response_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": response_model_name,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": assistant_content},
            "finish_reason": "stop",
        }],
        "conversation_id": conversation_id,
        "usage": usage_payload if include_usage else None,
    }


@app.get("/", summary="Health Check")
def health_check():
    return {"status": "ok", "version": app.version}


@app.get("/debug/ollama", summary="Test Ollama chat response")
async def debug_ollama():
    model_name = os.getenv("LLM_MODEL", "llama3.1:8b")
    try:
        logger.info("Debug Ollama endpoint invoked for model %s", model_name)
        response = await ollama.AsyncClient(timeout=30).chat(
            model=model_name,
            messages=[{"role": "user", "content": "Say a short hello from LabNote AI."}],
            options={"temperature": 0.3, "top_p": 0.9}
        )
        content = (response.get("message", {}).get("content") or "").strip()
        return {
            "model": model_name,
            "content_preview": content[:200],
            "content_length": len(content)
        }
    except Exception as exc:
        logger.error("Debug Ollama endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ollama debug failed: {exc}")


@app.get("/health", summary="GPU Health Check")
def health_check_gpu():
    try:
        embeddings = get_embeddings()
        embeddings.embed_query("health check")
        return {"status": "ok", "message": "GPU is warm and ready."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluation_history", summary="Get Model Evaluation History")
def get_evaluation_history(start_date: Optional[str] = None, end_date: Optional[str] = None):
    db_path = os.getenv("EVALUATION_DB_PATH", "scripts/evaluation_results.db")
    if not os.path.exists(db_path):
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM feedback_metrics"
            params = []
            conditions = []
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(f"{end_date}T23:59:59.999999")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY timestamp ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching evaluation history from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch evaluation history.")

@app.get("/dashboard", response_class=HTMLResponse, summary="View Model Performance Dashboard")
async def view_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/feedback_metrics", summary="Get User Feedback Metrics History")
def get_feedback_metrics(start_date: Optional[str] = None, end_date: Optional[str] = None):
    db_path = os.getenv("EVALUATION_DB_PATH", "scripts/evaluation_results.db")
    if not os.path.exists(db_path):
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM feedback_metrics"
            params = []
            conditions = []
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(f"{end_date}T23:59:59.999999")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY timestamp ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching feedback metrics from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch feedback metrics.")
