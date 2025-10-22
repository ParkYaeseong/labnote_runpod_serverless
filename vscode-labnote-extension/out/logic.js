"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.setDefaultExperimenter = setDefaultExperimenter;
exports.getDefaultExperimenter = getDefaultExperimenter;
exports.getSeoulDateString = getSeoulDateString;
exports.getSeoulDateTimeString = getSeoulDateTimeString;
exports.createNewLabnote = createNewLabnote;
exports.createNewWorkflow = createNewWorkflow;
exports.isValidReadmePath = isValidReadmePath;
exports.isValidWorkflowPath = isValidWorkflowPath;
exports.parseWorkflows = parseWorkflows;
exports.createWorkflowFileContent = createWorkflowFileContent;
exports.parseWorkflowFrontMatter = parseWorkflowFrontMatter;
exports.parseReadmeFrontMatter = parseReadmeFrontMatter;
exports.createUnitOperationContent = createUnitOperationContent;
exports.parseUnitOperations = parseUnitOperations;
exports.getManagableTemplates = getManagableTemplates;
const yaml = __importStar(require("js-yaml"));
const path = __importStar(require("path"));
// 모듈 레벨 변수로 defaultExperimenter 관리
let defaultExperimenter = '';
function setDefaultExperimenter(author) {
    defaultExperimenter = author;
}
function getDefaultExperimenter() {
    return defaultExperimenter;
}
function getSeoulDateString(date) {
    // Returns YYYY-MM-DD in Asia/Seoul timezone
    return new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Seoul',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format(date);
}
function getSeoulDateTimeString(date) {
    // Returns YYYY-MM-DD HH:mm in Asia/Seoul timezone (24h)
    const datePart = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Seoul',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format(date);
    const timePart = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Asia/Seoul',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
    return `${datePart} ${timePart}`;
}
function getFormattedDate(date) {
    return getSeoulDateString(date);
}
/**
 * 디렉토리 내의 'XXX_' 형태의 파일/폴더 번호를 분석하여
 * 사용 가능한 다음 번호를 찾아 반환합니다. (예: 001, 003이 있으면 002 반환)
 */
function getNextAvailableIndex(existingItems) {
    const existingIndexes = existingItems.length > 0 ? existingItems
        .map(item => parseInt(item.substring(0, 3), 10))
        .filter(num => !isNaN(num))
        .sort((a, b) => a - b) : [];
    if (existingIndexes.length === 0) {
        return 1;
    }
    // 가장 큰 번호에 1을 더한 값을 다음 번호로 사용합니다.
    const maxIndex = Math.max(...existingIndexes);
    return maxIndex + 1;
}
/**
 * 작업 공간 루트에서 'labnote' 또는 'LABNOTE' 폴더를 찾아 그 경로를 반환합니다.
 * 둘 다 없으면 소문자 'labnote' 경로를 기본값으로 반환합니다.
 */
function findLabnoteRoot(provider, workspaceRoot) {
    const entries = provider.readDir(workspaceRoot);
    const labnoteDir = entries.find(e => e.isDirectory() && e.name.toLowerCase() === 'labnote');
    if (labnoteDir) {
        return path.join(workspaceRoot, labnoteDir.name);
    }
    // 기존 폴더가 없으면 소문자로 생성하도록 기본 경로 반환
    return path.join(workspaceRoot, 'labnote');
}
function createNewLabnote(provider, workspaceRoot, experimentTitle) {
    if (!experimentTitle) {
        throw new Error("Experiment title cannot be empty.");
    }
    // ⭐️ [수정] workspaceRoot가 이미 labnote 폴더인 경우, 그 상위 폴더를 기준으로 다시 탐색합니다.
    let searchRoot = workspaceRoot;
    if (path.basename(workspaceRoot).toLowerCase() === 'labnote') {
        searchRoot = path.dirname(workspaceRoot);
    }
    const labnoteRoot = findLabnoteRoot(provider, searchRoot);
    if (!provider.exists(labnoteRoot))
        provider.mkdir(labnoteRoot);
    const entries = provider.readDir(labnoteRoot);
    const existingDirs = entries.filter(e => e.isDirectory() && /^\d{3}_/.test(e.name)).map(e => e.name); // ⭐️ [수정] 타입 일관성을 위해 명시적으로 map(e => e.name) 추가
    const nextId = getNextAvailableIndex(existingDirs);
    const formattedId = nextId.toString().padStart(3, '0');
    const safeTitle = experimentTitle.replace(/\s+/g, '_');
    const newDirName = `${formattedId}_${safeTitle}`;
    const newDirPath = path.join(labnoteRoot, newDirName);
    provider.mkdir(path.join(newDirPath, 'images'));
    provider.mkdir(path.join(newDirPath, 'resources'));
    const formattedDate = getFormattedDate(new Date());
    const readmeFrontMatter = {
        title: experimentTitle,
        author: '',
        experiment_type: 'labnote',
        created_date: formattedDate,
        last_updated_date: formattedDate,
    };
    const yamlText = yaml.dump(readmeFrontMatter, { sortKeys: false, lineWidth: -1 });
    const readmeContent = `---\n${yamlText}---\n\n## 🎯 Experiment Objective\n> Briefly describe the main objective and hypothesis of this experiment.\n\n## 🗂️ Related Workflows\n\n> Enter the list of related workflow files between the markers below.\n> When you run the \`F1\`, \`New workflow\` command, the list will be automatically added between the markers.\n> The name entered in the author: field of the YAML block above will be automatically entered as the experimenter's name when creating workflows and unit operations.\n\n\n\n\n`;
    const newReadmePath = path.join(newDirPath, 'README.md');
    provider.writeTextFile(newReadmePath, readmeContent);
    const parsedFrontMatter = parseReadmeFrontMatter(readmeContent);
    const globalAuthor = parsedFrontMatter?.author || '';
    setDefaultExperimenter(globalAuthor);
    return { newReadmePath, newDirName };
}
function createNewWorkflow(provider, readmePath, selectedWorkflow, description) {
    const today = new Date();
    const safeName = selectedWorkflow.name.replace(/\s+/g, '_');
    const safeDescription = description.replace(/\s+/g, '_');
    const currentDir = path.dirname(readmePath);
    const entries = provider.readDir(currentDir);
    const existingWfFiles = entries
        .filter((e) => !e.isDirectory() && /^\d{3}_.+\.md$/i.test(e.name))
        .map((e) => e.name);
    const nextSeq = getNextAvailableIndex(existingWfFiles);
    const seqString = String(nextSeq).padStart(3, '0');
    const workflowFileName = `${seqString}_${selectedWorkflow.id}_${safeName}${description ? '--' + safeDescription : ''}.md`;
    const workflowFilePath = path.join(currentDir, workflowFileName);
    let experimenter = '';
    try {
        const readmeContent = provider.readTextFile(readmePath);
        const parsedFrontMatter = parseReadmeFrontMatter(readmeContent);
        experimenter = parsedFrontMatter?.author || '';
    }
    catch (error) {
        experimenter = '';
    }
    const workflowContent = createWorkflowFileContent(selectedWorkflow, description, today, experimenter);
    provider.writeTextFile(workflowFilePath, workflowContent);
    const linkText = `${seqString} ${selectedWorkflow.id} ${selectedWorkflow.name}${description ? ' - ' + description : ''}`;
    const textToInsert = `[ ] [${linkText}](./${workflowFileName})\n`;
    return { workflowFilePath, textToInsert };
}
function isValidReadmePath(filePath) {
    if (path.basename(filePath).toLowerCase() !== 'readme.md') {
        return false;
    }
    try {
        const dirPath = path.dirname(filePath);
        const experimentDirName = path.basename(dirPath);
        const labnoteDirPath = path.dirname(dirPath);
        const labnoteDirName = path.basename(labnoteDirPath);
        const isLabnoteDir = labnoteDirName.toLowerCase() === 'labnote';
        const hasCorrectPrefix = /^\d{3}_/.test(experimentDirName);
        return isLabnoteDir && hasCorrectPrefix;
    }
    catch (e) {
        return false;
    }
}
function isValidWorkflowPath(filePath) {
    const base = path.basename(filePath).toLowerCase();
    if (!filePath.toLowerCase().endsWith('.md') || base === 'readme.md') {
        return false;
    }
    try {
        const dirPath = path.dirname(filePath);
        const experimentDirName = path.basename(dirPath);
        const labnoteDirPath = path.dirname(dirPath);
        const labnoteDirName = path.basename(labnoteDirPath);
        return labnoteDirName.toLowerCase() === 'labnote' && /^\d{3}_/.test(experimentDirName);
    }
    catch (e) {
        return false;
    }
}
function parseWorkflows(content) {
    const workflows = [];
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const match = lines[i].match(/^\s*-\s*\*\*(.*?)\*\*:\s*(.*)/);
        if (match) {
            const id = match[1];
            const name = match[2].trim();
            const description = (lines[i + 1] || '').trim().replace(/^- /, '');
            workflows.push({ id, name, description, label: `${id}: ${name}` });
        }
    }
    return workflows;
}
function createWorkflowFileContent(workflow, userDescription, date, experimenter) {
    const formattedDate = getFormattedDate(date);
    const title = `${workflow.id} ${workflow.name}${userDescription ? ` - ${userDescription}` : ''}`;
    const frontMatter = {
        title: title,
        experimenter: experimenter,
        created_date: formattedDate,
        end_date: '',
        last_updated_date: formattedDate,
    };
    const yamlText = yaml.dump(frontMatter, { sortKeys: false, lineWidth: -1 });
    const bodyTitle = `## [${workflow.id} ${workflow.name}]${userDescription ? ` ${userDescription}` : ''}`;
    const bodyDescription = `> Briefly describe this workflow (the description below is a template, modify it to fit your purpose)\n> ${workflow.description}`;
    const unitOperationSection = `## 🗂️ Related Unit Operations\n> Enter the list of related unit operations between the markers below.\n> When you run the \`F1\`, \`New HW/SW Unit Operation\` command, the list will be automatically added between the markers.\n\n\n\n`;
    return `---\n${yamlText}---\n\n${bodyTitle}\n${bodyDescription}\n\n${unitOperationSection}\n`;
}
function parseWorkflowFrontMatter(fileContent) {
    const match = fileContent.match(/^---([\s\S]+?)---/);
    if (!match)
        return null;
    try {
        const parsed = yaml.load(match[1]);
        return (parsed && typeof parsed.title === 'string') ? parsed : null;
    }
    catch (e) {
        return null;
    }
}
function parseReadmeFrontMatter(fileContent) {
    const match = fileContent.match(/^---([\s\S]+?)---/);
    if (!match)
        return null;
    try {
        const parsed = yaml.load(match[1]);
        return (parsed && typeof parsed.title === 'string' && typeof parsed.experiment_type === 'string') ? parsed : null;
    }
    catch (e) {
        return null;
    }
}
function createUnitOperationContent(selectedUo, userDescription, date, experimenter) {
    const formattedDateTime = getSeoulDateTimeString(date);
    const descriptionPart = userDescription ? ` ${userDescription}` : '';
    const uoDescriptionLine = selectedUo.description ? `\n\n- **Description**: ${selectedUo.description}` : '';
    const finalExperimenter = experimenter !== undefined ? experimenter : getDefaultExperimenter();
    return `\n\n---\n\n### [${selectedUo.id} ${selectedUo.name}${descriptionPart}]${uoDescriptionLine}\n\n#### Meta\n- Experimenter: ${finalExperimenter}\n- Start_date: '${formattedDateTime}'\n- End_date: ''\n\n#### Input\n- (samples from the previous step)\n\n#### Reagent\n- (e.g. enzyme, buffer, etc.)\n\n#### Consumables\n- (e.g. filter, well-plate, etc.)\n\n#### Equipment\n- (e.g. centrifuge, spectrophotometer, etc.)\n\n#### Method\n- (method used in this step)\n\n#### Output\n- (samples to the next step)\n\n#### Results & Discussions\n- (Any results and discussions. Link file path if needed)\n\n`;
}
function parseUnitOperations(content) {
    const unitOperations = [];
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const nameMatch = lines[i].match(/^\s*-\s*\*\*((?:USW|UHW|US|UH)\d+)\*\*:\s*(.*)/);
        if (nameMatch) {
            const id = nameMatch[1];
            const name = nameMatch[2].trim();
            let software = '';
            if (i + 1 < lines.length) {
                const softwareMatch = lines[i + 1].match(/^\s+-\s+\*\*Software\*\*:\s*(.*)/);
                if (softwareMatch) {
                    software = softwareMatch[1].trim();
                }
            }
            let description = '';
            if (i + 2 < lines.length) {
                const descriptionMatch = lines[i + 2].match(/^\s+-\s+\*\*Description\*\*:\s*(.*)/);
                if (descriptionMatch) {
                    description = descriptionMatch[1].trim();
                }
            }
            unitOperations.push({
                id,
                name,
                software,
                description,
                label: `${id}: ${name}`
            });
        }
    }
    return unitOperations;
}
function getManagableTemplates(paths) {
    return [
        {
            label: 'Workflows',
            description: 'Manage the list of standard workflows',
            filePath: paths.workflows,
        },
        {
            label: 'HW Unit Operations',
            description: 'Manage the list of hardware unit operations',
            filePath: paths.hwUnitOperations,
        },
        {
            label: 'SW Unit Operations',
            description: 'Manage the list of software unit operations',
            filePath: paths.swUnitOperations,
        },
    ];
}
//# sourceMappingURL=logic.js.map