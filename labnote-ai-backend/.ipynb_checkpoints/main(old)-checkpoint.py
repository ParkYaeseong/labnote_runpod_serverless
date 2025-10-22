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
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
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

async def keep_gpu_warm():
    while True:
        try:
            logger.info("[Keep-Alive] Running scheduled GPU health check...")
            await ollama.AsyncClient().chat(
                model='llama3.1:70b',
                messages=[{'role': 'user', 'content': 'Health check. Respond with "OK".'}],
                options={'num_predict': 1}
            )
            logger.info("[Keep-Alive] Successfully kept llama3.1:70b model warm.")
        except Exception as e:
            logger.error(f"[Keep-Alive] Error during GPU health check: {e}", exc_info=True)
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is not set.")
    logger.info(f"Creating Redis connection pool for {redis_url}")
    
    logger.info("Initializing RAG pipeline...")
    rag_module.rag_pipeline = rag_module.RAGPipeline()
    
    redis_pool = redis.ConnectionPool.from_url(redis_url, decode_responses=True)
    logger.info("Starting background task to keep GPU warm...")
    asyncio.create_task(keep_gpu_warm())
    yield
    logger.info("Closing Redis connection pool.")
    await redis_pool.disconnect()

# FastAPI 앱 초기화
app = FastAPI(
    title="LabNote AI Assistant Backend",
    version="2.8.2", # Final Refactored version
    description="Interactive lab note generation with user-edit DPO feedback loop and consent management.",
    lifespan=lifespan
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
conversation_histories: Dict[str, Dict[str, Any]] = {}

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

class PopulateNoteResponse(BaseModel):
    uo_id: str
    section: str
    options: List[str]

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
    conversation_id: Optional[str] = None
    file_content: Optional[str] = None
    experiment_goal: Optional[str] = None

class CompletionFeedbackRequest(BaseModel):
    file_content: str
    completion_type: str
    workflow_title: str
    experiment_topic: str

class ChatResponse(BaseModel):
    response: str
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
    for message in reversed(messages or []):
        content = _normalize_message_content(message.get("content"))
        if not content:
            continue
        code_blocks = re.findall(r"```[^\n]*\n([\s\S]*?)```", content)
        if code_blocks:
            # Use the last code block assuming it contains the freshest lab note snapshot
            return code_blocks[-1].strip()
    return None

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

def _chunk_text_for_stream(content: str, max_chunk_size: int = 800) -> List[str]:
    """Split assistant responses into manageable pieces for SSE streaming."""
    if not content:
        return [""]
    return [content[i:i + max_chunk_size] for i in range(0, len(content), max_chunk_size)]

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

    chosen_original = options[chosen_index]
    chosen_edited = chosen_original

    if edit_instruction:
        edit_prompt = (
            f"Apply the following edit to the text below: '{edit_instruction}'\n\nTEXT:\n{chosen_original}"
        )
        chosen_edited = await call_llm_api(
            "You are a text editor.",
            edit_prompt,
            "llama3.1:70b"
        )

    rejected_options = [opt for i, opt in enumerate(options) if i != chosen_index]
    uo_id = context.get("uo_id")
    section = context.get("section")

    if not uo_id or not section:
        uo_id, section = _find_last_populate_command(messages)

    if not uo_id or not section:
        logger.error("Unable to determine UO ID or section while processing DPO feedback.")
        return "선택을 반영할 수 없습니다. '/populate <UO_ID> <Section>' 형식으로 다시 시도해주세요."

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
        chosen_edited.strip()
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

    response_lines = [
        "✅ 피드백을 성공적으로 기록하고 AI 모델 학습에 반영했습니다.",
        "",
        "--- 최종 선택된 답변 ---",
        chosen_edited.strip()
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
    repo_url_with_token = repo_url.replace("https://", f"https://oauth2:{token}@")

    if local_path.exists():
        repo = git.Repo(local_path)
    else:
        logger.info(f"Cloning DPO repository to {local_path}...")
        repo = git.Repo.clone_from(repo_url_with_token, local_path)

    origin = repo.remote(name='origin')
    origin.set_url(repo_url_with_token)
    
    if repo.is_dirty() or "rebase" in repo.git.status():
        logger.warning("Repository is in a dirty or rebase state. Resetting to origin/main...")
        if "rebase" in repo.git.status():
            repo.git.rebase('--abort')
        repo.git.reset('--hard', 'origin/main')
        
    logger.info("Fetching latest changes from DPO repository...")
    origin.fetch()

    logger.info("Resetting local branch to match the remote branch...")
    repo.git.reset('--hard', 'origin/main')

    data_dir = local_path / "data"
    data_dir.mkdir(exist_ok=True)
    file_name = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}.json"
    file_path = data_dir / file_name
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(preference_data, f, ensure_ascii=False, indent=2)
    logger.info(f"DPO data saved to {file_path}")

    repo.index.add([str(file_path.resolve())])
    repo.index.commit(commit_message)
    
    logger.info("Pushing DPO data to remote repository...")
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
        agent_result = await run_agent_team(
            request.query,
            request.file_content,
            request.section,
            request.uo_id
        )
        
        if not agent_result or not agent_result.get("options"):
            raise HTTPException(status_code=500, detail="Agent team failed to generate options.")
        
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
    pass

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
        conversation_id = request.conversation_id
        query = next((msg['content'] for msg in reversed(request.messages) if msg['role'] == 'user'), '')

        # --- Conversation History Management ---
        if not conversation_id or conversation_id not in conversation_histories:
            conversation_id = str(uuid.uuid4())
            logger.info(f"Starting new conversation with ID: {conversation_id}")
            conversation_histories[conversation_id] = { "messages": request.messages, "context": {} }
        else:
            conv = conversation_histories[conversation_id]
            if query and (not conv["messages"] or conv["messages"][-1]['content'] != query):
                conv["messages"].append({"role": "user", "content": query})
        
        conversation = conversation_histories[conversation_id]
        context = conversation.get("context", {})
        generated_text = ""

        # --- Simplified Branching Logic ---

        populate_match = re.search(r"^\s*/populate\s+(?P<user_input>[^\n`]+)", query, re.IGNORECASE | re.MULTILINE) if query else None
        dpo_feedback_response = await _handle_dpo_feedback(query, request, conversation, request.messages)

        if dpo_feedback_response is not None:
            generated_text = dpo_feedback_response
        elif request.model == "labnote-backend" and populate_match:
            # 1. Dedicated flow for the "labnote-backend" model (Section Population)
            logger.info("Labnote Backend Logic model selected. Executing section population flow.")
            logger.info("Raw user query for population flow: %s", query)

            user_input = populate_match.group('user_input').strip()
            parts = user_input.split(maxsplit=1)

            if len(parts) < 2:
                generated_text = "Error: Invalid format. Please use: /populate <UO_ID> <Section>"
            else:
                uo_id = parts[0].upper()
                section = parts[1].strip()

                file_content = request.file_content
                experiment_goal = request.experiment_goal

                if not file_content or not experiment_goal:
                    generated_text = "Error: To populate a section, the full content of the lab note must be available in the context."
                else:
                    logger.info(f"Executing populate for UO: {uo_id}, Section: {section}")
                    agent_result = await run_agent_team(experiment_goal, file_content, section, uo_id)

                    if agent_result and agent_result.get("options"):
                        options = agent_result["options"]
                        conversation["context"] = {
                            "state": "awaiting_dpo_feedback", "options": options, "uo_id": uo_id,
                            "section": section, "file_content": file_content,
                            "experiment_goal": experiment_goal,
                            "file_path": "continue_populate_refactored",
                            "last_selection_signature": None,
                            "last_selected_index": None
                        }
                        formatted_options = [f"{i+1}.\n---\n{opt}" for i, opt in enumerate(options)]
                        options_text = "\n\n".join(formatted_options)
                        generated_text = (
                            "다음은 AI가 제안하는 내용입니다. 마음에 드는 번호를 선택하거나, 수정사항과 함께 알려주세요.\n"
                            "(예: '1번 선택', '2번 선택, 하지만 버퍼 농도를 50mM로 수정해줘')\n\n"
                            f"{options_text}\n\n"
                            "어느 번호를 선택할까요? 번호와 함께 추가 수정 요청이 있으면 알려주세요."
                        )
                    else:
                        generated_text = "AI 에이전트 팀이 답변을 생성하지 못했습니다. 입력 형식을 확인해주세요."
        else:
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

            response = await ollama.AsyncClient().chat(
                model=llm_model_name,
                messages=messages,
                options={'temperature': 0.1}
            )
            raw_text = response['message']['content'].strip()
            logger.info(f"DIAGNOSIS: Raw text from LLM: '{raw_text}'")

            generated_text = _post_process_content(raw_text)
            logger.info(f"DIAGNOSIS: Processed text: '{generated_text}'")

        # Final response preparation
        conversation["messages"].append({"role": "assistant", "content": generated_text})
        return ChatResponse(response=generated_text, conversation_id=conversation_id)

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        if 'conversation_id' in locals() and conversation_id in conversation_histories:
            del conversation_histories[conversation_id]
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clear_history/{conversation_id}", summary="Clear Conversation History")
def clear_history(conversation_id: str):
    if conversation_id in conversation_histories:
        del conversation_histories[conversation_id]
        logger.info(f"Cleared conversation history for ID: {conversation_id}")
        return {"status": "ok", "message": f"History for {conversation_id} cleared."}
    else:
        raise HTTPException(status_code=404, detail="Conversation ID not found.")

@app.get("/", summary="Health Check")
def health_check():
    return {"status": "ok", "version": app.version}

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

@app.post("/v1/chat/completions")
async def openai_compat(request: dict):
    messages = request.get("messages", [])
    stream = bool(request.get("stream"))
    stream_options = request.get("stream_options") or {}
    if not isinstance(stream_options, dict):
        stream_options = {}
    include_usage = bool(stream_options.get("include_usage"))

    conversation_id = request.get("conversation_id")
    logger.info(
        "OpenAI compatibility handler invoked: model=%s, messages=%d, conversation_id=%s, stream=%s",
        request.get("model"),
        len(messages) if messages else 0,
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

    labnote_response = await chat(
        ChatRequest(
            model=request.get("model"),
            messages=messages,
            conversation_id=conversation_id,
            file_content=file_content,
            experiment_goal=experiment_goal,
        )
    )
    logger.info(
        "OpenAI compatibility returning conversation_id=%s, response_preview=%s",
        labnote_response.conversation_id,
        (labnote_response.response[:200] + "...") if labnote_response.response and len(labnote_response.response) > 200 else labnote_response.response,
    )
    response_model_name = request.get("model") or os.getenv("LLM_MODEL", "labnote-backend")
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    created_ts = int(time.time())
    assistant_content = labnote_response.response or ""
    usage_payload = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

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
                }
                if idx == len(content_chunks) - 1 and labnote_response.conversation_id:
                    chunk["conversation_id"] = labnote_response.conversation_id
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
            }
            if labnote_response.conversation_id:
                final_chunk["conversation_id"] = labnote_response.conversation_id
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
        "conversation_id": labnote_response.conversation_id,
        "usage": usage_payload,
    }