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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const logic = __importStar(require("./logic"));
const fetch = require('node-fetch');
const IMAGE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']);
function toPosixPath(p) {
    return p.split(path.sep).join('/');
}
const chatSessions = new Map();
// Cache last saved content per file to detect meaningful section changes for auto DPO
const lastSavedTextByFile = new Map();
// --- 상수 및 전역 헬퍼 ---
const realFsProvider = {
    exists: (p) => fs.existsSync(p),
    mkdir: (p) => fs.mkdirSync(p, { recursive: true }),
    readDir: (p) => fs.readdirSync(p, { withFileTypes: true }),
    readTextFile: (p) => fs.readFileSync(p, 'utf-8'),
    writeTextFile: (p, content) => fs.writeFileSync(p, content),
};
function getApiHeaders() {
    const config = vscode.workspace.getConfiguration('labnote.ai');
    const token = config.get('vesslApiToken');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}
function getBaseUrl() {
    const config = vscode.workspace.getConfiguration('labnote.ai');
    const url = config.get('backendUrl');
    if (!url) {
        vscode.window.showErrorMessage("Backend URL is not set. Please check the `labnote.ai.backendUrl` setting."); // This is already in English, no change needed.
        return null;
    }
    return url;
}
function normalizeEndpointPath(endpointPath) {
    if (!endpointPath.startsWith('/')) {
        return `/${endpointPath}`;
    }
    return endpointPath;
}
function joinUrl(baseUrl, endpointPath) {
    return `${baseUrl.replace(/\/+$/, '')}${endpointPath}`;
}
function parseRunpodConfig(baseUrl) {
    const trimmed = (baseUrl || '').trim();
    if (!trimmed) {
        return null;
    }
    if (trimmed.startsWith('runpod://')) {
        const endpointId = trimmed.substring('runpod://'.length).replace(/\//g, '').trim();
        if (endpointId) {
            return { endpointId, apiBase: `https://api.runpod.ai/v2/${endpointId}` };
        }
    }
    try {
        const parsed = new URL(trimmed);
        if (parsed.hostname.endsWith('.runpod.run')) {
            const endpointId = parsed.hostname.split('.')[0];
            if (endpointId) {
                return { endpointId, apiBase: `https://api.runpod.ai/v2/${endpointId}` };
            }
        }
        if (parsed.hostname === 'api.runpod.ai') {
            const segments = parsed.pathname.split('/').filter(Boolean);
            const v2Index = segments.indexOf('v2');
            if (v2Index !== -1 && v2Index + 1 < segments.length) {
                const endpointId = segments[v2Index + 1];
                if (endpointId) {
                    return { endpointId, apiBase: `https://api.runpod.ai/v2/${endpointId}` };
                }
            }
        }
    }
    catch (error) {
        return null;
    }
    return null;
}
async function safeReadText(response) {
    try {
        return await response.text();
    }
    catch (error) {
        return '<no body>';
    }
}
async function callRunpodServerless(config, path, init) {
    const settings = vscode.workspace.getConfiguration('labnote.ai');
    const apiKey = (settings.get('vesslApiToken') || '').trim();
    if (!apiKey) {
        vscode.window.showErrorMessage('RunPod API key is not set. Please configure `labnote.ai.vesslApiToken`.');
        throw new Error('RunPod API key is not configured.');
    }
    const method = init.method ?? 'POST';
    const jobInput = {
        method,
        path,
        body: method === 'GET' ? undefined : init.body ?? {}
    };
    init.outputChannel?.appendLine(`[RunPod] Job payload for ${method} ${path}: ${JSON.stringify(jobInput).slice(0, 500)}...`);
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
    };
    const submitResponse = await fetch(`${config.apiBase}/run`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ input: jobInput })
    });
    if (!submitResponse.ok) {
        const errorText = await safeReadText(submitResponse);
        throw new Error(`RunPod job submission failed (HTTP ${submitResponse.status}): ${errorText}`);
    }
    const submitData = await submitResponse.json();
    const jobId = submitData.id;
    if (!jobId) {
        if (submitData.status && submitData.output !== undefined) {
            init.outputChannel?.appendLine(`[RunPod] Synchronous response received (status=${submitData.status}).`);
            if (submitData.status.toUpperCase() === 'COMPLETED') {
                return submitData.output;
            }
            const serialized = JSON.stringify(submitData);
            throw new Error(`RunPod synchronous call did not complete successfully: ${serialized}`);
        }
        const serialized = JSON.stringify(submitData);
        throw new Error(`RunPod job submission did not return a job ID. Raw response: ${serialized}`);
    }
    init.outputChannel?.appendLine(`[RunPod] Submitted job ${jobId} for ${method} ${path} (status=${submitData.status || 'UNKNOWN'})`);
    const timeoutMs = init.timeoutMs ?? 300000;
    const pollIntervalMs = 2000;
    const startTime = Date.now();
    let lastStatus = null;
    while (true) {
        if (Date.now() - startTime > timeoutMs) {
            throw new Error(`RunPod job ${jobId} timed out after ${(timeoutMs / 1000).toFixed(0)} seconds.`);
        }
        await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
        const statusResponse = await fetch(`${config.apiBase}/status/${jobId}`, {
            method: 'GET',
            headers
        });
        if (!statusResponse.ok) {
            const errorText = await safeReadText(statusResponse);
            throw new Error(`RunPod status check failed (HTTP ${statusResponse.status}): ${errorText}`);
        }
        const statusData = await statusResponse.json();
        const status = statusData.status || 'UNKNOWN';
        if (status !== lastStatus) {
            init.outputChannel?.appendLine(`[RunPod] Job ${jobId} status: ${status}`);
            lastStatus = status;
        }
        if (status === 'COMPLETED') {
            if (statusData.output === undefined) {
                throw new Error(`RunPod job ${jobId} completed without output.`);
            }
            return statusData.output;
        }
        if (status === 'FAILED' || status === 'CANCELLED' || status === 'TIMED_OUT') {
            const errorDetail = statusData.error ? `: ${JSON.stringify(statusData.error)}` : '';
            throw new Error(`RunPod job ${jobId} ${status.toLowerCase()}${errorDetail}`);
        }
    }
}
async function callBackendJson(baseUrl, rawPath, init = {}) {
    const method = init.method ?? 'POST';
    const path = normalizeEndpointPath(rawPath);
    // Allow forcing direct-HTTP mode by appending a marker to backendUrl, e.g. "#http" or "?mode=http"
    let forceHttp = false;
    let cleanBaseUrl = baseUrl;
    try {
        // Prefer URL parsing when possible to strip markers cleanly
        const parsed = new URL(baseUrl);
        if (parsed.hash && parsed.hash.toLowerCase().includes('http')) {
            forceHttp = true;
            parsed.hash = '';
            cleanBaseUrl = parsed.toString();
        }
        else if (parsed.searchParams.get('mode') === 'http' || parsed.searchParams.get('direct') === '1') {
            forceHttp = true;
            parsed.searchParams.delete('mode');
            parsed.searchParams.delete('direct');
            cleanBaseUrl = parsed.toString();
        }
    }
    catch {
        // Fallback: simple suffix stripping
        if (cleanBaseUrl.endsWith('#http')) {
            forceHttp = true;
            cleanBaseUrl = cleanBaseUrl.replace(/#http$/i, '');
        }
    }
    const runpodConfig = forceHttp ? null : parseRunpodConfig(cleanBaseUrl);
    if (runpodConfig) {
        return callRunpodServerless(runpodConfig, path, { ...init, method, body: init.body });
    }
    const url = joinUrl(cleanBaseUrl, path);
    const headers = { ...getApiHeaders() };
    const requestInit = {
        method,
        headers
    };
    if (method === 'POST') {
        requestInit.body = JSON.stringify(init.body ?? {});
    }
    const response = await fetch(url, requestInit);
    if (!response.ok) {
        const errorText = await safeReadText(response);
        throw new Error(`${method} ${path} failed (HTTP ${response.status}): ${errorText}`);
    }
    if (response.status === 204) {
        return undefined;
    }
    return await response.json();
}
// --- 확장 프로그램 활성화/비활성화 ---
function activate(context) {
    const outputChannel = vscode.window.createOutputChannel("LabNote AI");
    outputChannel.appendLine("LabNote AI/Manager extension is now active.");
    initializeResources(context);
    registerCommands(context, outputChannel);
    registerEventListeners(context);
    registerChatParticipant(context, outputChannel);
}
function deactivate() { }
// --- 초기화 및 등록 헬퍼 ---
function initializeResources(context) {
    const globalStoragePath = context.globalStorageUri.fsPath;
    if (!realFsProvider.exists(globalStoragePath)) {
        realFsProvider.mkdir(globalStoragePath);
    }
}
async function completeWorkflowCommand(context, outputChannel) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("Please open a workflow file first."); // This is already in English, no change needed.
        return;
    }
    const document = editor.document;
    if (!logic.isValidWorkflowPath(document.uri.fsPath)) {
        vscode.window.showErrorMessage("This command can only be run from a workflow file (*.md) inside a labnote folder."); // This is already in English, no change needed.
        return;
    }
    try {
        const content = document.getText();
        const wfFrontMatter = logic.parseWorkflowFrontMatter(content);
        if (wfFrontMatter && wfFrontMatter.end_date) {
            vscode.window.showInformationMessage("This workflow has already been completed."); // This is already in English, no change needed.
            return;
        }
        // 모든 유닛 오퍼레이션의 end_date가 채워졌는지 확인하는 로직 추가
        const uoRegex = /###\s*\[U[A-Z]{2,3}\d{3,4}.*?\][\s\S]*?End_date:\s*'([^']*)'/g;
        let match;
        let allUosCompleted = true;
        let uoFound = false;
        while ((match = uoRegex.exec(content)) !== null) {
            uoFound = true;
            if (match[1].trim() === '') {
                allUosCompleted = false;
                break;
            }
        }
        if (uoFound && !allUosCompleted) {
            vscode.window.showWarningMessage("Not all Unit Operations in this workflow are complete. Please fill in all 'End_date' fields for each Unit Operation first."); // This is already in English, no change needed.
            return;
        }
        if (wfFrontMatter) {
            const now = new Date();
            const newFrontMatter = {
                ...wfFrontMatter,
                end_date: logic.getSeoulDateTimeString(now),
                last_updated_date: logic.getSeoulDateString(now)
            };
            const yaml = require('js-yaml');
            const newYamlText = yaml.dump(newFrontMatter, { sortKeys: false, lineWidth: -1 });
            const newContent = content.replace(/^---([\s\S]+?)---/, `---\n${newYamlText}---`);
            await editor.edit(editBuilder => {
                const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(content.length));
                editBuilder.replace(fullRange, newContent);
            });
            await document.save();
            vscode.window.showInformationMessage(`Workflow completed. 'end_date' has been set to the current time.`); // This is already in English, no change needed.
            // README.md 업데이트를 직접 호출하여 체크박스 상태를 즉시 반영합니다.
            await updateReadmeOnWorkflowSave(document);
            sendCompletionFeedback(context, outputChannel, document, 'workflow');
        }
        else {
            vscode.window.showWarningMessage("Could not find valid front matter in this file."); // This is already in English, no change needed.
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error completing workflow: ${error.message}`);
    }
}
async function completeUnitOperationCommand(context, outputChannel) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("Please open a workflow file first."); // This is already in English, no change needed.
        return;
    }
    const document = editor.document;
    if (!logic.isValidWorkflowPath(document.uri.fsPath)) {
        vscode.window.showErrorMessage("This command can only be run from a workflow file (*.md) inside a labnote folder."); // This is already in English, no change needed.
        return;
    }
    const cursorPosition = editor.selection.active;
    try {
        const { uoBlock, uoName } = findUoBlockAtCursor(document, cursorPosition);
        if (!uoBlock) {
            vscode.window.showWarningMessage("Could not find a Unit Operation block at the current cursor position."); // This is already in English, no change needed.
            return;
        }
        const endDateRegex = /End_date:\s*''/;
        const match = uoBlock.text.match(endDateRegex);
        if (match && match.index !== undefined) {
            const now = new Date();
            const newEndDateLine = `End_date: '${logic.getSeoulDateTimeString(now)}'`;
            // ⭐️ [수정] End_date가 포함된 정확한 줄을 찾도록 로직 변경
            const lines = uoBlock.text.split('\n');
            let lineIndex = -1;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes("End_date: ''")) {
                    lineIndex = i;
                    break;
                }
            }
            if (lineIndex === -1)
                throw new Error("Could not find the line containing End_date: ''.");
            const startPos = new vscode.Position(uoBlock.startLine + lineIndex, lines[lineIndex].indexOf("End_date: ''"));
            const endPos = new vscode.Position(uoBlock.startLine + lineIndex, lines[lineIndex].indexOf("End_date: ''") + match[0].length);
            const editRange = new vscode.Range(startPos, endPos);
            await editor.edit(editBuilder => {
                editBuilder.replace(editRange, newEndDateLine);
            });
            await document.save();
            vscode.window.showInformationMessage(`Unit Operation '${uoName}' completed.`); // This is already in English, no change needed.
            sendCompletionFeedback(context, outputChannel, document, 'unit_operation', cursorPosition);
        }
        else {
            vscode.window.showInformationMessage(`Unit Operation '${uoName}' has already been completed.`); // This is already in English, no change needed.
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error completing Unit Operation: ${error.message}`);
    }
}
function findUoBlockAtCursor(document, position) {
    let uoHeaderLine = -1;
    let uoName = null;
    for (let i = position.line; i >= 0; i--) {
        const line = document.lineAt(i);
        const match = line.text.match(/^###\s*\[(U[A-Z]{2,3}\d{3,4}.*?)\].*/);
        if (match) {
            uoHeaderLine = i;
            uoName = match[1];
            break;
        }
    }
    if (uoHeaderLine === -1) {
        return { uoBlock: null, uoName: null };
    }
    let endLine = document.lineCount - 1;
    for (let i = uoHeaderLine + 1; i < document.lineCount; i++) {
        if (document.lineAt(i).text.startsWith('### [')) {
            endLine = i - 1;
            break;
        }
    }
    const uoRange = new vscode.Range(new vscode.Position(uoHeaderLine, 0), document.lineAt(endLine).range.end);
    return { uoBlock: { text: document.getText(uoRange), startLine: uoHeaderLine }, uoName };
}
async function updateReadmeOnWorkflowSave(workflowDoc) {
    const content = workflowDoc.getText();
    const frontMatter = logic.parseWorkflowFrontMatter(content);
    if (!frontMatter)
        return;
    const workflowDir = path.dirname(workflowDoc.uri.fsPath);
    const readmePath = path.join(workflowDir, 'README.md');
    const workflowFileName = path.basename(workflowDoc.uri.fsPath);
    try {
        const readmeUri = vscode.Uri.file(readmePath);
        let readmeDoc;
        try {
            readmeDoc = await vscode.workspace.openTextDocument(readmeUri);
        }
        catch (e) {
            // README.md 파일이 없으면 아무것도 하지 않음
            return;
        }
        let originalContent = readmeDoc.getText();
        let newContent = originalContent;
        // 1. 체크박스 자동 변경은 비활성화 (수동으로만 체크하도록 유지)
        const escapedFileName = workflowFileName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // 2. Title 변경에 따른 링크 텍스트 업데이트
        const titleRegex = new RegExp(`^(\\[[ x]\\] \\[)(.*?)(\\]\\(\\.\\/${escapedFileName}\\))`, 'm');
        newContent = newContent.replace(titleRegex, `$1${frontMatter.title}$3`);
        if (originalContent !== newContent) {
            const edit = new vscode.WorkspaceEdit();
            edit.replace(readmeUri, new vscode.Range(readmeDoc.positionAt(0), readmeDoc.positionAt(originalContent.length)), newContent);
            const success = await vscode.workspace.applyEdit(edit);
            if (success) {
                // 변경 사항이 적용된 후 문서를 저장합니다.
                await readmeDoc.save();
            }
        }
    }
    catch (error) {
        // README.md가 없거나 읽기 오류 발생 시 무시
    }
}
async function removeWorkflowLinkFromReadme(deletedWorkflowPath) {
    const workflowDir = path.dirname(deletedWorkflowPath);
    const readmePath = path.join(workflowDir, 'README.md');
    const deletedFileName = path.basename(deletedWorkflowPath);
    try {
        const readmeUri = vscode.Uri.file(readmePath);
        const readmeDoc = await vscode.workspace.openTextDocument(readmeUri);
        const originalContent = readmeDoc.getText();
        // 삭제할 파일 이름을 포함하는 링크 라인 전체를 찾기 위한 정규식
        const escapedFileName = deletedFileName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`^.*\\(\\.\\/${escapedFileName}\\)\\s*\\r?\\n?`, 'm');
        const newContent = originalContent.replace(regex, '');
        if (originalContent !== newContent) {
            const edit = new vscode.WorkspaceEdit();
            edit.replace(readmeUri, new vscode.Range(readmeDoc.positionAt(0), readmeDoc.positionAt(originalContent.length)), newContent);
            await vscode.workspace.applyEdit(edit);
            await readmeDoc.save();
        }
    }
    catch (error) {
        // README.md가 없거나 읽기/쓰기 오류 발생 시 무시
    }
}
async function newWorkflowCommand(customWorkflowsPath) {
    try {
        const activeUri = getActiveFileUri();
        if (!activeUri || !logic.isValidReadmePath(activeUri.fsPath)) {
            vscode.window.showErrorMessage("This command can only be run from a 'labnote/<number>_topic/README.md' file."); // This is already in English, no change needed.
            return;
        }
        const customWorkflowsContent = realFsProvider.readTextFile(customWorkflowsPath);
        const workflowItems = logic.parseWorkflows(customWorkflowsContent);
        const selectedWorkflow = await vscode.window.showQuickPick(workflowItems, { placeHolder: "Select a standard workflow" }); // This is already in English, no change needed.
        if (!selectedWorkflow)
            return;
        const description = await vscode.window.showInputBox({ prompt: `Enter a specific description for "${selectedWorkflow.label}"` }); // This is already in English, no change needed.
        if (description === undefined)
            return;
        const result = logic.createNewWorkflow(realFsProvider, activeUri.fsPath, selectedWorkflow, description);
        const doc = await vscode.workspace.openTextDocument(activeUri);
        const insertPos = findInsertPosBeforeEndMarker(doc, '');
        const we = new vscode.WorkspaceEdit();
        we.insert(activeUri, insertPos, result.textToInsert);
        await vscode.workspace.applyEdit(we);
        await doc.save();
        vscode.window.showInformationMessage(`Workflow '${path.basename(result.workflowFilePath)}' has been created.`); // This is already in English, no change needed.
    }
    catch (error) {
        vscode.window.showErrorMessage(`[New Workflow] Error: ${error.message}`);
    }
}
function createUnitOperationCommand(fsProvider, uoFilePath) {
    return async () => {
        const activeUri = getActiveFileUri();
        if (!activeUri || !logic.isValidWorkflowPath(activeUri.fsPath)) {
            vscode.window.showErrorMessage("This command can only be run from a workflow file inside a 'labnote' experiment folder."); // This is already in English, no change needed.
            return;
        }
        try {
            const uoContent = fsProvider.readTextFile(uoFilePath);
            const uoItems = logic.parseUnitOperations(uoContent);
            const selectedUo = await vscode.window.showQuickPick(uoItems, { placeHolder: "Select a Unit Operation" }); // This is already in English, no change needed.
            if (!selectedUo)
                return;
            const userDescription = await vscode.window.showInputBox({ prompt: `Enter a specific description for "${selectedUo.name}"` }); // This is already in English, no change needed.
            if (userDescription === undefined)
                return;
            const workflowDir = path.dirname(activeUri.fsPath);
            const readmePath = path.join(workflowDir, 'README.md');
            let experimenter = '';
            if (fsProvider.exists(readmePath)) {
                const readmeContent = fsProvider.readTextFile(readmePath);
                const parsedFrontMatter = logic.parseReadmeFrontMatter(readmeContent);
                experimenter = parsedFrontMatter?.author || '';
            }
            const now = new Date();
            const textToInsert = logic.createUnitOperationContent(selectedUo, userDescription, now, experimenter);
            const wfDoc = await vscode.workspace.openTextDocument(activeUri);
            // 워크플로 파일의 Front Matter에 End_date가 비어있는지 확인하고, 비어있다면 현재 시간으로 채웁니다.
            const wfContent = wfDoc.getText();
            const wfFrontMatter = logic.parseWorkflowFrontMatter(wfContent);
            if (wfFrontMatter && wfFrontMatter.end_date === '') {
                const newFrontMatter = { ...wfFrontMatter, last_updated_date: logic.getSeoulDateString(now), end_date: logic.getSeoulDateTimeString(now) };
                const newYamlText = require('js-yaml').dump(newFrontMatter, { sortKeys: false, lineWidth: -1 });
                const newWfContent = wfContent.replace(/^---([\s\S]+?)---/, `---\n${newYamlText}---`);
                const fullRange = new vscode.Range(wfDoc.positionAt(0), wfDoc.positionAt(wfContent.length));
                await vscode.window.activeTextEditor?.edit(editBuilder => editBuilder.replace(fullRange, newWfContent));
            }
            const pos = findInsertPosBeforeEndMarker(wfDoc, ''); // 유닛 오퍼레이션 삽입 위치 찾기
            const we = new vscode.WorkspaceEdit();
            we.insert(wfDoc.uri, pos, textToInsert);
            await vscode.workspace.applyEdit(we);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Error creating Unit Operation: ${error.message}`);
        }
    };
}
async function manageTemplatesCommand(paths) {
    const template = await vscode.window.showQuickPick(logic.getManagableTemplates(paths), { placeHolder: 'Select a template file to manage' } // This is already in English, no change needed.
    );
    if (!template)
        return;
    const doc = await vscode.workspace.openTextDocument(template.filePath);
    await vscode.window.showTextDocument(doc);
}
async function insertTableCommand() {
    const editor = vscode.window.activeTextEditor;
    if (!editor)
        return;
    const columns = await vscode.window.showInputBox({ prompt: "Number of columns for the table:", value: '3' }); // This is already in English, no change needed.
    if (!columns)
        return;
    const rows = await vscode.window.showInputBox({ prompt: "Number of rows for the table (excluding header):", value: '2' }); // This is already in English, no change needed.
    if (!rows)
        return;
    const numCols = parseInt(columns, 10);
    const numRows = parseInt(rows, 10);
    let table = `\n| ${Array(numCols).fill('Header').join(' | ')} |\n`;
    table += `| ${Array(numCols).fill('---').join(' | ')} |\n`;
    for (let i = 0; i < numRows; i++) {
        table += `| ${Array(numCols).fill(' ').join(' | ')} |\n`;
    }
    editor.edit(editBuilder => editBuilder.insert(editor.selection.active, table));
}
async function reorderWorkflowsCommand() {
    const activeUri = getActiveFileUri();
    if (!activeUri || !logic.isValidReadmePath(activeUri.fsPath)) {
        vscode.window.showErrorMessage("This command can only be run from a 'labnote/<number>_topic/README.md' file."); // This is already in English, no change needed.
        return;
    }
    await reorderWorkflowFiles(activeUri.fsPath);
}
async function reorderLabnotesCommand() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showErrorMessage("A workspace must be open."); // This is already in English, no change needed.
        return;
    }
    const labnoteRoot = path.join(workspaceFolders[0].uri.fsPath, 'labnote');
    await reorderLabnoteFolders(labnoteRoot);
}
function registerCommands(context, outputChannel) {
    const customPaths = {
        workflows: resolveConfiguredPath(context, 'workflowsPath', 'workflows_en.md'),
        hwUnitOperations: resolveConfiguredPath(context, 'hwUnitOperationsPath', 'unitoperations_hw_en.md'),
        swUnitOperations: resolveConfiguredPath(context, 'swUnitOperationsPath', 'unitoperations_sw_en.md'),
    };
    context.subscriptions.push(
    // 채팅 UI의 버튼과 연동될 명령어들
    vscode.commands.registerCommand('labnote.ai.generate.chat', () => {
        // Only create the Lab Note folder + README (no workflows/UOs)
        return createNewLabnoteCommand();
    }), vscode.commands.registerCommand('labnote.ai.populateSection.chat', () => {
        vscode.commands.executeCommand('workbench.action.chat.open', '@labnote /populate');
    }), 
    // Command Palette 등 다른 곳에서 실행될 수 있는 기존 명령어들
    vscode.commands.registerCommand('labnote.ai.generate', createNewLabnoteCommand), vscode.commands.registerCommand('labnote.ai.populateSection', () => populateSectionFlow(context, outputChannel)), vscode.commands.registerCommand('labnote.ai.populateSectionFromVisualEditor', () => populateSectionFromVisualEditorFlow(context, outputChannel)), vscode.commands.registerCommand('labnote.manager.newWorkflow', () => newWorkflowCommand(customPaths.workflows)), vscode.commands.registerCommand('labnote.manager.newHwUnitOperation', createUnitOperationCommand(realFsProvider, customPaths.hwUnitOperations)), vscode.commands.registerCommand('labnote.manager.newSwUnitOperation', createUnitOperationCommand(realFsProvider, customPaths.swUnitOperations)), vscode.commands.registerCommand('labnote.manager.manageTemplates', () => manageTemplatesCommand(customPaths)), vscode.commands.registerCommand('labnote.manager.insertTable', insertTableCommand), vscode.commands.registerCommand('labnote.manager.reorderWorkflows', reorderWorkflowsCommand), vscode.commands.registerCommand('labnote.manager.reorderLabnotes', reorderLabnotesCommand), vscode.commands.registerCommand('labnote.manager.completeWorkflow', () => completeWorkflowCommand(context, outputChannel)), vscode.commands.registerCommand('labnote.manager.completeUnitOperation', () => completeUnitOperationCommand(context, outputChannel)));
    context.subscriptions.push(vscode.commands.registerCommand('labnote.manager.completeUnitOperation.chat', () => completeUnitOperationFromChat(context, outputChannel)), vscode.commands.registerCommand('labnote.manager.completeWorkflow.chat', () => vscode.commands.executeCommand('labnote.manager.completeWorkflow')));
}
function registerEventListeners(context) {
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(async (document) => {
        const filePath = document.uri.fsPath;
        if (logic.isValidWorkflowPath(filePath)) {
            await updateReadmeOnWorkflowSave(document);
            try {
                const cfg = vscode.workspace.getConfiguration('labnote.ai');
                const enabled = cfg.get('autoDpoOnEdit', true);
                if (!enabled) {
                    lastSavedTextByFile.set(filePath, document.getText());
                }
                else {
                    await autoDpoOnSave(document);
                }
            }
            catch (e) {
                console.warn('[LabNote AI] autoDpoOnEdit error:', e?.message || e);
            }
        }
    }), vscode.workspace.onDidCreateFiles(async (event) => {
        for (const fileUri of event.files) {
            try {
                await handleNewAssetPlacement(fileUri);
            }
            catch (assetError) {
                console.warn('Failed to relocate new asset:', assetError);
            }
        }
    }), vscode.workspace.onDidDeleteFiles(async (e) => {
        for (const fileUri of e.files) {
            if (logic.isValidWorkflowPath(fileUri.fsPath)) {
                await removeWorkflowLinkFromReadme(fileUri.fsPath);
            }
        }
    }));
}
async function autoDpoOnSave(document) {
    const filePath = document.uri.fsPath;
    const prev = lastSavedTextByFile.get(filePath) || '';
    const curr = document.getText();
    lastSavedTextByFile.set(filePath, curr);
    if (prev === curr)
        return;
    const cfg = vscode.workspace.getConfiguration('labnote.ai');
    const minChars = Math.max(50, cfg.get('autoDpoMinChars', 200));
    const prevMap = buildSectionTextMap(prev);
    const currMap = buildSectionTextMap(curr);
    const baseUrl = getBaseUrl();
    if (!baseUrl)
        return;
    for (const [key, newText] of currMap.entries()) {
        const oldText = prevMap.get(key) || '';
        if (newText && newText.trim() !== oldText.trim() && newText.trim().length >= minChars) {
            const [uoId, section] = key.split('::');
            const body = {
                uo_id: uoId,
                section,
                prompt: 'auto:file_edit',
                generated_text: newText,
                edited_text: newText,
                file_content: curr,
                file_path: filePath,
                supervisor_evaluations: []
            };
            try {
                await callBackendJson(baseUrl, '/record_chat_preference', { body });
                vscode.window.setStatusBarMessage(`LabNote: Auto-saved DPO for ${uoId}/${section}`, 3000);
            }
            catch (e) {
                console.warn('[LabNote AI] Failed to auto-save DPO:', e?.message || e);
            }
        }
    }
}
function buildSectionTextMap(content) {
    const map = new Map();
    const lines = content.split(/\r?\n/);
    let currentUo = null;
    const sections = [];
    for (let i = 0; i < lines.length; i++) {
        const lineText = lines[i];
        const uoMatch = lineText.match(/^###\s*\[(U[A-Z]{2,3}\d{3,4}).*?\]/);
        if (uoMatch) {
            currentUo = uoMatch[1];
        }
        const secMatch = lineText.match(/^####\s*(.*?)\s*$/);
        if (secMatch && currentUo) {
            sections.push({ uo: currentUo, name: secMatch[1].trim(), start: i, end: -1 });
        }
    }
    for (let i = 0; i < sections.length; i++) {
        sections[i].end = (i + 1 < sections.length) ? sections[i + 1].start - 1 : (lines.length - 1);
    }
    for (const s of sections) {
        const contentStart = s.start + 1;
        const text = lines.slice(contentStart, s.end + 1).join('\n').trim();
        map.set(`${s.uo}::${s.name}`, text);
    }
    return map;
}
async function handleNewAssetPlacement(fileUri) {
    const ext = path.extname(fileUri.fsPath).toLowerCase();
    if (!ext) {
        return;
    }
    const isImage = IMAGE_EXTENSIONS.has(ext);
    const isResource = !isImage && ext !== '.md';
    if (!isImage && !isResource) {
        return;
    }
    const experimentRoot = findExperimentRootDir(fileUri.fsPath);
    if (!experimentRoot) {
        return;
    }
    const imagesDir = path.join(experimentRoot, 'images');
    const resourcesDir = path.join(experimentRoot, 'resources');
    if (isImage && isPathInside(fileUri.fsPath, imagesDir)) {
        return;
    }
    if (isResource && isPathInside(fileUri.fsPath, resourcesDir)) {
        return;
    }
    const targetDir = isImage ? imagesDir : resourcesDir;
    ensureDirectory(targetDir);
    const targetPath = ensureUniqueFilePath(targetDir, path.basename(fileUri.fsPath));
    const targetUri = vscode.Uri.file(targetPath);
    await vscode.workspace.fs.rename(fileUri, targetUri, { overwrite: false });
    await updateReferencesAfterMove(fileUri, targetUri, experimentRoot);
}
function findExperimentRootDir(startPath) {
    let current = path.dirname(startPath);
    while (true) {
        const readmeCandidate = path.join(current, 'README.md');
        const parent = path.dirname(current);
        if (fs.existsSync(readmeCandidate) && path.basename(parent).toLowerCase() === 'labnote') {
            return current;
        }
        if (parent === current) {
            break;
        }
        current = parent;
    }
    return null;
}
function ensureDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}
function isPathInside(child, parent) {
    const relative = path.relative(parent, child);
    return relative !== '' && !relative.startsWith('..') && !path.isAbsolute(relative);
}
function ensureUniqueFilePath(dir, fileName) {
    let candidate = path.join(dir, fileName);
    if (!fs.existsSync(candidate)) {
        return candidate;
    }
    const parsed = path.parse(fileName);
    let counter = 1;
    while (true) {
        candidate = path.join(dir, `${parsed.name}_${counter}${parsed.ext}`);
        if (!fs.existsSync(candidate)) {
            return candidate;
        }
        counter++;
    }
}
async function updateReferencesAfterMove(originalUri, targetUri, experimentRoot) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }
    const document = editor.document;
    if (document.languageId !== 'markdown') {
        return;
    }
    const docPath = document.uri.fsPath;
    if (!isPathInside(docPath, experimentRoot)) {
        return;
    }
    const docDir = path.dirname(docPath);
    const originalText = document.getText();
    let updatedText = originalText;
    const newRelativeRaw = toPosixPath(path.relative(docDir, targetUri.fsPath));
    const newRelative = newRelativeRaw.startsWith('.') || newRelativeRaw.startsWith('..')
        ? newRelativeRaw
        : `./${newRelativeRaw}`;
    const originalRelativeRaw = toPosixPath(path.relative(docDir, originalUri.fsPath));
    const searchTokens = new Set();
    if (originalRelativeRaw) {
        searchTokens.add(originalRelativeRaw);
        if (!originalRelativeRaw.startsWith('.') && !originalRelativeRaw.startsWith('..')) {
            searchTokens.add(`./${originalRelativeRaw}`);
        }
    }
    searchTokens.add(path.basename(originalUri.fsPath));
    let replaced = false;
    for (const token of searchTokens) {
        const needle = `](${token})`;
        if (updatedText.includes(needle)) {
            updatedText = updatedText.split(needle).join(`](${newRelative})`);
            replaced = true;
        }
    }
    if (replaced && updatedText !== originalText) {
        const edit = new vscode.WorkspaceEdit();
        edit.replace(document.uri, new vscode.Range(document.positionAt(0), document.positionAt(originalText.length)), updatedText);
        await vscode.workspace.applyEdit(edit);
    }
}
function registerChatParticipant(context, outputChannel) {
    const handler = async (request, chatContext, stream, token) => {
        const sessionId = "default_session"; // 단일 세션 관리를 위해 고정 ID 사용
        let session = chatSessions.get(sessionId);
        // --- 명시적 대화 시작 명령어 처리 ---
        if (request.prompt.startsWith('/')) {
            const command = request.prompt.split(' ')[0];
            if (command === '/generate') {
                chatSessions.set(sessionId, {
                    flow: 'generate_labnote',
                    state: 'awaiting_topic',
                    data: {},
                    context: {} // 새 context 초기화
                });
                stream.markdown("🔬 Okay. What is the main topic of the lab note to be generated?"); // This is already in English, no change needed.
                return {};
            }
            if (command === '/populate') {
                const editor = vscode.window.activeTextEditor;
                if (!editor) {
                    stream.markdown("⚠️ Please open the workflow file to populate first."); // This is already in English, no change needed.
                    chatSessions.delete(sessionId);
                    return {};
                }
                const sections = parseAllSections(editor.document);
                if (sections.length === 0) {
                    stream.markdown("⚠️ No Unit Operation sections that can be populated were found in the current file."); // This is already in English, no change needed.
                    chatSessions.delete(sessionId);
                    return {};
                }
                chatSessions.set(sessionId, {
                    flow: 'populate_section',
                    state: 'awaiting_section_choice',
                    data: { documentUri: editor.document.uri },
                    context: {}
                });
                stream.markdown("✍️ Please select a section to populate with AI."); // This is already in English, no change needed.
                sections.forEach(s => {
                    const commandPayload = encodeURIComponent(JSON.stringify({ uoId: s.uoId, section: s.section }));
                    stream.button({
                        title: `[${s.uoId}] ${s.section}`,
                        command: 'labnote.ai.internal.chatSelectSection',
                        arguments: [commandPayload]
                    });
                });
                return {};
            }
            if (command === '/cancel') {
                chatSessions.delete(sessionId);
                stream.markdown("✅ The operation has been canceled."); // This is already in English, no change needed.
                stream.button({ title: 'View other tasks', command: 'labnote.ai.showMainMenu.chat' }); // This is already in English, no change needed.
                return {};
            }
        }
        // --- 상태 기반 대화 흐름 처리 ---
        if (session) {
            if (session.flow === 'generate_labnote') {
                await handleGenerateFlow(session, request, stream, context, outputChannel);
                return {};
            }
            if (session.flow === 'populate_section') {
                stream.markdown("Please select a section by clicking one of the buttons above."); // This is already in English, no change needed.
                return {};
            }
        }
        // --- 기본 동작: 메뉴 표시 또는 일반 채팅 ---
        if (!request.prompt) {
            stream.markdown("Hello! I'm the LabNote AI Assistant. What can I help you with? 🚀"); // This is already in English, no change needed.
            stream.button({ title: '🔬 Create New Lab Note', command: 'labnote.ai.generate.chat' }); // This is already in English, no change needed.
            stream.button({ title: '✍️ Populate Section (AI)', command: 'labnote.ai.populateSection.chat' }); // This is already in English, no change needed.
            stream.button({ title: '➕ Add Workflow', command: 'labnote.manager.newWorkflow' }); // This is already in English, no change needed.
            stream.button({ title: '➕ Add Unit Operation', command: 'labnote.manager.newHwUnitOperation' }); // This is already in English, no change needed.
            stream.button({ title: '🔄 Reorder Workflows', command: 'labnote.manager.reorderWorkflows' }); // This is already in English, no change needed.
            stream.button({ title: '🗂️ Reorder Experiment Folders', command: 'labnote.manager.reorderLabnotes' }); // This is already in English, no change needed.
            stream.button({ title: '✅ Complete Unit Operation', command: 'labnote.manager.completeUnitOperation.chat' }); // This is already in English, no change needed.
            stream.button({ title: '🏁 Complete Current Workflow', command: 'labnote.manager.completeWorkflow.chat' }); // This is already in English, no change needed.
            return {};
        }
        // 일반 채팅 API 호출 (상태 관리 포함)
        const currentSession = chatSessions.get(sessionId) || { flow: 'generate_labnote', state: 'init', data: {}, context: {} };
        const chatResult = await callChatApi(request.prompt, outputChannel, stream, currentSession.context);
        if (chatResult) {
            // 새로운 context로 세션 업데이트
            currentSession.context = chatResult.context;
            chatSessions.set(sessionId, currentSession);
        }
        return {};
    };
    const participant = vscode.chat.createChatParticipant('labnote.participant', handler);
    participant.iconPath = vscode.Uri.file(path.join(context.extensionPath, 'images', 'icon.png'));
    participant.followupProvider = {
        provideFollowups(result, context, token) {
            if (chatSessions.has("default_session")) {
                return [{ prompt: '/cancel', label: 'Cancel current task', command: 'labnote.ai.cancel.chat' }]; // This is already in English, no change needed.
            }
            return [{ prompt: '', label: 'View other tasks', command: 'labnote.ai.showMainMenu.chat' }]; // This is already in English, no change needed.
        }
    };
    context.subscriptions.push(participant);
    // 내부 명령어 등록
    context.subscriptions.push(vscode.commands.registerCommand('labnote.ai.internal.chatSelectSection', async (payload) => {
        const { uoId, section } = JSON.parse(decodeURIComponent(payload));
        const session = chatSessions.get("default_session");
        if (session && session.flow === 'populate_section' && session.data.documentUri) {
            await populateSectionFromWebview(context, outputChannel, session.data.documentUri, uoId, section);
            chatSessions.delete("default_session");
        }
    }), vscode.commands.registerCommand('labnote.ai.showMainMenu.chat', () => {
        vscode.commands.executeCommand('workbench.action.chat.open', '@labnote');
    }), vscode.commands.registerCommand('labnote.ai.cancel.chat', () => {
        vscode.commands.executeCommand('workbench.action.chat.open', '@labnote /cancel');
    }));
}
async function createNewLabnoteCommand() {
    const experimentTitle = await vscode.window.showInputBox({
        prompt: 'Enter the topic for the new lab note.',
        placeHolder: 'e.g., Plasmid construction'
    });
    if (!experimentTitle) {
        vscode.window.showInformationMessage('Lab note creation was canceled.');
        return;
    }
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showErrorMessage("Please open a workspace first.");
        return;
    }
    // ⭐️ [수정] 항상 최상위 workspace 폴더를 기준으로 labnote 폴더를 찾도록 수정
    const rootPath = workspaceFolders[0].uri.fsPath;
    try {
        const { newReadmePath, newDirName } = logic.createNewLabnote(realFsProvider, rootPath, experimentTitle);
        vscode.window.showInformationMessage(`Lab note '${newDirName}' has been created.`);
        // ⭐️ [수정] 파일이 생성된 후 문서를 열기 전에 잠시 대기하여 파일 시스템이 업데이트될 시간을 줍니다.
        // 이렇게 하면 '파일을 찾을 수 없음' 오류를 방지할 수 있습니다.
        setTimeout(async () => {
            try {
                const doc = await vscode.workspace.openTextDocument(newReadmePath);
                await vscode.window.showTextDocument(doc);
            }
            catch (docError) {
                vscode.window.showErrorMessage(`Error opening the created file: ${docError.message}`);
            }
        }, 200);
    }
    catch (error) {
        vscode.window.showErrorMessage(`An error occurred while creating the lab note: ${error.message}`);
    }
}
async function interactiveGenerateFlow(context, userInput, outputChannel, workflowId, uoIds) {
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LabNote AI Analyzing...", // This is already in English, no change needed.
        cancellable: true
    }, async (progress) => {
        try {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) {
                throw new Error("Please open a workspace first to create a lab note.");
            }
            const rootPath = workspaceFolders[0].uri.fsPath;
            const labnoteRoot = path.join(rootPath, 'labnote');
            if (!fs.existsSync(labnoteRoot))
                fs.mkdirSync(labnoteRoot);
            const entries = fs.readdirSync(labnoteRoot, { withFileTypes: true });
            const existingDirs = entries.filter(e => e.isDirectory() && /^\d{3}_/.test(e.name)).map(e => parseInt(e.name.substring(0, 3), 10));
            const nextId = existingDirs.length > 0 ? Math.max(...existingDirs) + 1 : 1;
            const formattedId = nextId.toString().padStart(3, '0');
            const safeTitle = userInput.replace(/[\s/\\?%*:|"<>]/g, '_');
            const newDirName = `${formattedId}_${safeTitle}`;
            const newDirPath = path.join(labnoteRoot, newDirName);
            fs.mkdirSync(newDirPath, { recursive: true });
            fs.mkdirSync(path.join(newDirPath, 'images'), { recursive: true });
            fs.mkdirSync(path.join(newDirPath, 'resources'), { recursive: true });
            outputChannel.appendLine(`[Info] Created new experiment folder: ${newDirPath}`);
            progress.report({ increment: 10, message: "Analyzing experiment structure..." }); // This is already in English, no change needed.
            const baseUrl = getBaseUrl();
            if (!baseUrl)
                return;
            let finalWorkflowId = workflowId;
            let finalUoIds = uoIds;
            if (!finalWorkflowId) {
                const { ALL_WORKFLOWS } = await fetchConstants(context, baseUrl, outputChannel);
                finalWorkflowId = await showWorkflowSelectionMenu(ALL_WORKFLOWS);
                if (!finalWorkflowId)
                    return;
            }
            if (!finalUoIds || finalUoIds.length === 0) {
                const { ALL_UOS } = await fetchConstants(context, baseUrl, outputChannel);
                finalUoIds = await showUnifiedUoSelectionMenu(ALL_UOS, []);
                if (!finalUoIds || finalUoIds.length === 0)
                    return;
            }
            progress.report({ increment: 60, message: "Creating lab note and workflow files..." }); // This is already in English, no change needed.
            const scaffoldData = await callBackendJson(baseUrl, '/create_scaffold', {
                body: {
                    query: userInput,
                    workflow_id: finalWorkflowId,
                    unit_operation_ids: finalUoIds,
                    experimenter: 'AI Assistant'
                },
                outputChannel
            });
            progress.report({ increment: 90, message: "Saving and displaying files..." }); // This is already in English, no change needed.
            for (const fileName in scaffoldData.files) {
                const content = scaffoldData.files[fileName];
                const filePath = path.join(newDirPath, fileName);
                fs.writeFileSync(filePath, content);
                outputChannel.appendLine(`[Success] Created file: ${filePath}`);
            }
            const readmePath = path.join(newDirPath, 'README.md');
            await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(readmePath), { preview: false });
        }
        catch (error) {
            vscode.window.showErrorMessage('An error occurred during a LabNote AI operation: ' + error.message);
            outputChannel.appendLine(`[ERROR] ${error.message}`);
            throw error;
        }
    });
}
async function populateSectionFlow(extensionContext, outputChannel) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("There is no active text editor."); // This is already in English, no change needed.
        return;
    }
    try {
        const sectionContext = findSectionContext(editor.document, editor.selection.active);
        if (!sectionContext) {
            vscode.window.showErrorMessage("Could not find a populatable Unit Operation section (and placeholder) at the current cursor position."); // This is already in English, no change needed.
            return;
        }
        await processAndApplyPopulation(extensionContext, outputChannel, editor.document.uri, sectionContext, false);
    }
    catch (error) {
        vscode.window.showErrorMessage(`An error occurred during a LabNote AI operation: ${error.message}`);
    }
}
async function populateSectionFromWebview(extensionContext, outputChannel, documentUri, uoId, section) {
    try {
        const document = await vscode.workspace.openTextDocument(documentUri);
        const sectionContext = findSectionContext(document, { uoId, section });
        if (!sectionContext) {
            vscode.window.showErrorMessage(`Could not find section '${section}'. (UO: ${uoId})`); // This is already in English, no change needed.
            return;
        }
        await processAndApplyPopulation(extensionContext, outputChannel, documentUri, sectionContext, true);
    }
    catch (error) {
        vscode.window.showErrorMessage(`An error occurred during a LabNote AI operation: ${error.message}`);
    }
}
async function populateSectionFromVisualEditorFlow(context, outputChannel) {
    const activeUri = getActiveFileUri();
    if (!activeUri) {
        vscode.window.showWarningMessage("There is no active file."); // This is already in English, no change needed.
        return;
    }
    try {
        const document = await vscode.workspace.openTextDocument(activeUri);
        const sections = parseAllSections(document);
        if (sections.length === 0) {
            vscode.window.showErrorMessage("Could not find any Unit Operation sections in the document."); // This is already in English, no change needed.
            return;
        }
        const selectedSection = await vscode.window.showQuickPick(sections.map(s => ({
            label: `[${s.uoId}] ${s.section}`,
            description: `Line ${s.startLine + 1}`,
            detail: `Unit Operation: ${s.uoId}`,
            uoId: s.uoId,
            section: s.section
        })), { placeHolder: "Select a section to populate with AI" } // This is already in English, no change needed.
        );
        if (!selectedSection)
            return;
        const sectionContext = findSectionContext(document, { uoId: selectedSection.uoId, section: selectedSection.section });
        if (!sectionContext) {
            vscode.window.showErrorMessage(`Could not find section '${selectedSection.section}'. (UO: ${selectedSection.uoId})`); // This is already in English, no change needed.
            return;
        }
        await processAndApplyPopulation(context, outputChannel, activeUri, sectionContext, true);
    }
    catch (error) {
        vscode.window.showErrorMessage(`An error occurred during a LabNote AI operation: ${error.message}`);
    }
}
async function processAndApplyPopulation(extensionContext, outputChannel, documentUri, sectionContext, isFromVisualEditor) {
    const consent = extensionContext.globalState.get('labnoteAiConsent');
    if (consent !== 'given') {
        const selection = await vscode.window.showInformationMessage('To improve LabNote AI, your selected and edited content will be used anonymously for model training. Do you agree? For details, please see the "Data Usage and Copyright Policy" in the project README.', // This is already in English, no change needed.
        { modal: true }, 'Agree', 'Decline' // This is already in English, no change needed.
        );
        if (selection === 'Agree') {
            await extensionContext.globalState.update('labnoteAiConsent', 'given');
        }
        else {
            await extensionContext.globalState.update('labnoteAiConsent', 'denied');
            vscode.window.showInformationMessage("You have not consented to the use of AI features. The 'Populate Section' feature will be disabled."); // This is already in English, no change needed.
            return;
        }
    }
    const { uoId, section, query, fileContent, placeholderRange } = sectionContext;
    const currentFilePath = documentUri.fsPath;
    outputChannel.appendLine(`[Action] Populate section request for UO '${uoId}', Section '${section}'`);
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `LabNote AI: Generating '${section}' section...`, // This is already in English, no change needed.
        cancellable: true
    }, async (progress) => {
        progress.report({ increment: 20, message: "Calling AI agent team..." }); // This is already in English, no change needed.
        const baseUrl = getBaseUrl();
        if (!baseUrl)
            return;
        const populateData = await callBackendJson(baseUrl, '/populate_note', {
            body: {
                file_content: fileContent,
                uo_id: uoId,
                section,
                query,
                file_path: currentFilePath // file_path도 함께 전달
            },
            outputChannel
        });
        if (!populateData.options || populateData.options.length === 0) {
            vscode.window.showInformationMessage("No drafts were generated by the AI."); // This is already in English, no change needed.
            return;
        }
        const panel = createPopulateWebviewPanel(section, populateData.options, isFromVisualEditor);
        panel.webview.onDidReceiveMessage(async (message) => {
            const { command, chosen_original, chosen_edited } = message;
            if (command === 'applyAndLearn' || command === 'copyAndLearn') {
                void callBackendJson(baseUrl, '/record_preference', {
                    body: {
                        uo_id: uoId,
                        section,
                        chosen_original,
                        chosen_edited,
                        rejected: populateData.options.filter(opt => opt !== chosen_original),
                        query,
                        file_content: (await vscode.workspace.openTextDocument(documentUri)).getText(),
                        file_path: currentFilePath,
                        supervisor_evaluations: populateData.supervisor_evaluations || []
                    },
                    outputChannel
                }).catch((err) => {
                    outputChannel.appendLine(`[WARN] Failed to record DPO data: ${err.message}`);
                });
                if (command === 'applyAndLearn') {
                    // ⭐️ [수정] '활성' 편집기 대신 '보이는' 편집기들 중에서 올바른 파일을 찾도록 변경
                    const editor = vscode.window.visibleTextEditors.find((e) => e.document.uri.toString() === documentUri.toString());
                    if (editor) {
                        await editor.edit(editBuilder => {
                            editBuilder.replace(placeholderRange, chosen_edited);
                        });
                        vscode.window.showInformationMessage(`'${section}' section has been updated, and the AI will learn from your edits.`); // This is already in English, no change needed.
                    }
                    else {
                        // 만약 사용자가 파일을 닫아버린 경우
                        await vscode.env.clipboard.writeText(chosen_edited);
                        vscode.window.showWarningMessage(`Could not find an editor window to apply changes for '${section}'. The modified content has been copied to your clipboard.`); // This is already in English, no change needed.
                    }
                }
                else { // command === 'copyAndLearn'
                    await vscode.env.clipboard.writeText(chosen_edited);
                    vscode.window.showInformationMessage(`The modified content has been copied to your clipboard. Paste it into the Visual Editor.`); // This is already in English, no change needed.
                }
                panel.dispose();
            }
        }, undefined, extensionContext.subscriptions);
    });
}
function resolveConfiguredPath(context, settingKey, defaultFileName) {
    const config = vscode.workspace.getConfiguration('labnote.manager');
    let configured = (config.get(settingKey) || '').trim();
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
    if (configured) {
        if (workspaceRoot) {
            configured = configured.replace(/\$\{workspaceFolder\}/g, workspaceRoot);
        }
        if (workspaceRoot && !path.isAbsolute(configured)) {
            configured = path.join(workspaceRoot, configured);
        }
        if (fs.existsSync(configured)) {
            return configured;
        }
        else {
            vscode.window.showWarningMessage(`[Labnote Manager] The configured path could not be found. Falling back to the default template: ${configured}`); // This is already in English, no change needed.
        }
    }
    return path.join(context.extensionPath, 'out', 'resources', defaultFileName);
}
async function reorderLabnoteFolders(labnoteRoot) {
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Reordering experiment folder numbers...", // This is already in English, no change needed.
        cancellable: false
    }, async (progress) => {
        try {
            if (!fs.existsSync(labnoteRoot)) {
                vscode.window.showInformationMessage("The 'labnote' folder could not be found."); // This is already in English, no change needed.
                return;
            }
            const entries = fs.readdirSync(labnoteRoot, { withFileTypes: true });
            const labnoteDirs = entries
                .filter(e => e.isDirectory() && /^\d{3}_/.test(e.name))
                .map(e => e.name)
                .sort();
            if (labnoteDirs.length === 0) {
                vscode.window.showInformationMessage("There are no experiment folders to reorder."); // This is already in English, no change needed.
                return;
            }
            progress.report({ increment: 10, message: "Analyzing folder list..." });
            const renames = [];
            let needsReordering = false;
            for (let i = 0; i < labnoteDirs.length; i++) {
                const newIndex = i + 1;
                const newPrefix = String(newIndex).padStart(3, '0');
                const oldDirName = labnoteDirs[i];
                const oldPrefix = oldDirName.substring(0, 3);
                if (oldPrefix !== newPrefix) {
                    needsReordering = true;
                    const restOfDirName = oldDirName.substring(4);
                    const newDirName = `${newPrefix}_${restOfDirName}`;
                    renames.push({
                        oldPath: path.join(labnoteRoot, oldDirName),
                        newPath: path.join(labnoteRoot, newDirName)
                    });
                }
            }
            if (!needsReordering) {
                vscode.window.showInformationMessage("Experiment folder numbers are already in order."); // This is already in English, no change needed.
                return;
            }
            progress.report({ increment: 30, message: "Planning renames..." }); // This is already in English, no change needed.
            const edit = new vscode.WorkspaceEdit();
            for (const r of renames) {
                edit.renameFile(vscode.Uri.file(r.oldPath), vscode.Uri.file(r.newPath + '.tmp'), { overwrite: true });
            }
            await vscode.workspace.applyEdit(edit);
            const finalEdit = new vscode.WorkspaceEdit();
            for (const r of renames) {
                finalEdit.renameFile(vscode.Uri.file(r.newPath + '.tmp'), vscode.Uri.file(r.newPath), { overwrite: true });
            }
            await vscode.workspace.applyEdit(finalEdit);
            progress.report({ increment: 100 });
            vscode.window.showInformationMessage("Experiment folder numbers have been reordered successfully."); // This is already in English, no change needed.
        }
        catch (error) {
            vscode.window.showErrorMessage(`An error occurred while reordering experiment folders: ${error.message}`);
        }
    });
}
async function reorderWorkflowFiles(readmePath) {
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Reordering workflow numbers...", // This is already in English, no change needed.
        cancellable: false
    }, async (progress) => {
        try {
            const dir = path.dirname(readmePath);
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            const workflowFiles = entries
                .filter(e => !e.isDirectory() && /^\d{3}_.+\.md$/.test(e.name))
                .map(e => e.name)
                .sort();
            if (workflowFiles.length === 0) {
                vscode.window.showInformationMessage("There are no workflow files to reorder."); // This is already in English, no change needed.
                return;
            }
            progress.report({ increment: 10, message: "Analyzing file list..." }); // This is already in English, no change needed.
            const renameQueue = [];
            let needsReordering = false;
            for (let i = 0; i < workflowFiles.length; i++) {
                const newIndex = i + 1;
                const newPrefix = String(newIndex).padStart(3, '0');
                const oldFileName = workflowFiles[i];
                const oldPrefix = oldFileName.substring(0, 3);
                if (oldPrefix !== newPrefix) {
                    needsReordering = true;
                    const restOfFileName = oldFileName.substring(4);
                    const newFileName = `${newPrefix}_${restOfFileName}`;
                    renameQueue.push({
                        oldPath: path.join(dir, oldFileName),
                        newPath: path.join(dir, newFileName)
                    });
                }
            }
            if (!needsReordering) {
                vscode.window.showInformationMessage("Workflow numbers are already in order."); // This is already in English, no change needed.
                return;
            }
            progress.report({ increment: 30, message: "Planning renames..." }); // This is already in English, no change needed.
            const tempEdit = new vscode.WorkspaceEdit();
            for (const item of renameQueue) {
                tempEdit.renameFile(vscode.Uri.file(item.oldPath), vscode.Uri.file(item.newPath + ".tmp"), { overwrite: true });
            }
            await vscode.workspace.applyEdit(tempEdit);
            const finalEdit = new vscode.WorkspaceEdit();
            for (const item of renameQueue) {
                finalEdit.renameFile(vscode.Uri.file(item.newPath + ".tmp"), vscode.Uri.file(item.newPath), { overwrite: true });
            }
            await vscode.workspace.applyEdit(finalEdit);
            progress.report({ increment: 70, message: "Updating links in README.md..." }); // This is already in English, no change needed.
            // README.md의 링크 목록을 재정렬하고 업데이트합니다.
            const readmeUri = vscode.Uri.file(readmePath);
            const readmeDoc = await vscode.workspace.openTextDocument(readmeUri);
            const originalContent = readmeDoc.getText();
            const workflowSectionRegex = /(## 🗂️ Related Workflows[\s\S]*?>.*?\n>.*?\n>.*?\n\n)([\s\S]*?)(?=\n## |\n?$)/;
            const sectionMatch = workflowSectionRegex.exec(originalContent);
            if (!sectionMatch || sectionMatch.index === undefined) {
                vscode.window.showWarningMessage("Could not find the 'Related Workflows' section in README.md to update links.");
                return;
            }
            const sectionStart = sectionMatch.index + sectionMatch[1].length;
            const sectionEnd = sectionMatch.index + sectionMatch[0].length;
            const reorderedFiles = fs.readdirSync(dir)
                .filter(f => /^\d{3}_.+\.md$/i.test(f) && f.toLowerCase() !== 'readme.md')
                .sort();
            // 현재 README 섹션의 체크 상태를 보존하기 위해 파일명 -> 체크박스 상태 매핑을 먼저 추출
            const existingSection = sectionMatch[2] || '';
            const checkboxStateByFile = new Map(); // fileName -> "[x]" | "[ ]"
            const lineRegex = /^\s*(\[[ x]\])\s*\[[^\]]*\]\(\.\/([^\)\s]+)\)/;
            for (const line of existingSection.split(/\r?\n/)) {
                const m = line.match(lineRegex);
                if (m) {
                    checkboxStateByFile.set(m[2], m[1]);
                }
            }
            const newLinkLines = reorderedFiles.map(fileName => {
                const filePath = path.join(dir, fileName);
                let frontMatter = null;
                try {
                    const fileContent = fs.readFileSync(filePath, 'utf-8');
                    frontMatter = logic.parseWorkflowFrontMatter(fileContent);
                }
                catch (err) {
                    frontMatter = null;
                }
                const seq = fileName.substring(0, 3);
                const humanReadableName = frontMatter?.title
                    ? `${seq} ${frontMatter.title}`
                    : `${seq} ${path.basename(fileName, '.md').substring(4).replace(/_/g, ' ')}`;
                const checkbox = checkboxStateByFile.get(fileName) ?? '[ ]';
                return `${checkbox} [${humanReadableName}](./${fileName})`;
            });
            const replacement = newLinkLines.length > 0 ? `${newLinkLines.join('\n')}\n\n` : '\n\n';
            const readmeEdit = new vscode.WorkspaceEdit();
            readmeEdit.replace(readmeUri, new vscode.Range(readmeDoc.positionAt(sectionStart), readmeDoc.positionAt(sectionEnd)), replacement);
            await vscode.workspace.applyEdit(readmeEdit);
            await readmeDoc.save();
            progress.report({ increment: 100 });
            vscode.window.showInformationMessage("Workflow numbers have been reordered successfully."); // This is already in English, no change needed.
        }
        catch (error) {
            vscode.window.showErrorMessage(`An error occurred during reordering: ${error.message}`);
        }
    });
}
function getActiveFileUri() {
    const editor = vscode.window.activeTextEditor;
    if (editor)
        return editor.document.uri;
    const activeTab = vscode.window.tabGroups.activeTabGroup?.activeTab;
    const input = activeTab?.input;
    if (input instanceof vscode.TabInputText)
        return input.uri;
    if (input instanceof vscode.TabInputTextDiff)
        return input.modified;
    if (input && typeof input === 'object' && 'uri' in input) {
        return input.uri;
    }
    return null;
}
function findInsertPosBeforeEndMarker(doc, endMarker) {
    for (let i = doc.lineCount - 1; i >= 0; i--) {
        const line = doc.lineAt(i);
        if (line.text.includes(endMarker)) {
            if (i > 0 && doc.lineAt(i - 1).isEmptyOrWhitespace) {
                return new vscode.Position(i - 1, 0);
            }
            return new vscode.Position(i, 0);
        }
    }
    return new vscode.Position(doc.lineCount, 0);
}
async function completeUnitOperationFromChat(context, outputChannel) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("Please open a workflow file first to use this command."); // This is already in English, no change needed.
        return;
    }
    const document = editor.document;
    if (!logic.isValidWorkflowPath(document.uri.fsPath)) {
        vscode.window.showErrorMessage("This command can only be run from a workflow file (*.md) inside a labnote folder."); // This is already in English, no change needed.
        return;
    }
    const sections = parseAllSections(document);
    const uoMap = new Map();
    sections.forEach(s => {
        if (!uoMap.has(s.uoId)) {
            uoMap.set(s.uoId, { uoId: s.uoId, startLine: s.startLine });
        }
    });
    const uoItems = Array.from(uoMap.values()).map(uo => ({
        label: `[${uo.uoId}]`,
        description: `Starts on line ${uo.startLine + 1}`,
        uoId: uo.uoId,
        startLine: uo.startLine
    }));
    if (uoItems.length === 0) {
        vscode.window.showInformationMessage("No Unit Operations found in the current file."); // This is already in English, no change needed.
        return;
    }
    const selectedUo = await vscode.window.showQuickPick(uoItems, {
        placeHolder: "Select a Unit Operation to complete" // This is already in English, no change needed.
    });
    if (!selectedUo) {
        return;
    }
    // Move cursor to the selected UO block to reuse the existing command logic
    const position = new vscode.Position(selectedUo.startLine, 0);
    editor.selection = new vscode.Selection(position, position);
    editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
    // A short delay might be needed for the selection to update before the command runs
    setTimeout(async () => {
        await completeUnitOperationCommand(context, outputChannel);
    }, 100);
}
async function sendCompletionFeedback(context, outputChannel, document, completionType, cursorPosition) {
    const consent = context.globalState.get('labnoteAiConsent');
    if (consent !== 'given') {
        return; // 사용자가 동의하지 않았으면 아무것도 하지 않음
    }
    try {
        const baseUrl = getBaseUrl();
        if (!baseUrl)
            return;
        let contentToSend;
        if (completionType === 'unit_operation' && cursorPosition) {
            const { uoBlock } = findUoBlockAtCursor(document, cursorPosition);
            contentToSend = uoBlock?.text || document.getText(); // uoBlock을 못찾으면 전체 텍스트 전송
        }
        else {
            contentToSend = document.getText();
        }
        const fileContent = document.getText(); // workflow_title, experiment_topic 파싱을 위해 전체 내용은 유지
        const wfFrontMatter = logic.parseWorkflowFrontMatter(fileContent);
        const workflowTitle = wfFrontMatter?.title || path.basename(document.uri.fsPath);
        // 상위 README.md에서 실험 주제 가져오기
        const readmePath = path.join(path.dirname(document.uri.fsPath), 'README.md');
        const readmeContent = await vscode.workspace.fs.readFile(vscode.Uri.file(readmePath));
        const readmeFrontMatter = logic.parseReadmeFrontMatter(new TextDecoder().decode(readmeContent)); // This is already in English, no change needed.
        const experimentTopic = readmeFrontMatter?.title || 'Unknown Topic';
        outputChannel.appendLine(`[Feedback] Sending completion data for '${workflowTitle}' (${completionType})`);
        // 백엔드에 새로운 엔드포인트 /record_completion_feedback 가 있다고 가정
        void callBackendJson(baseUrl, '/record_completion_feedback', {
            body: {
                file_content: contentToSend,
                completion_type: completionType,
                workflow_title: workflowTitle,
                experiment_topic: experimentTopic
            },
            outputChannel
        }).then(() => {
            outputChannel.appendLine(`[Feedback] Successfully sent completion feedback for '${workflowTitle}'.`);
        }).catch((err) => {
            outputChannel.appendLine(`[WARN] Failed to send completion feedback: ${err.message}`);
        });
    }
    catch (error) {
        outputChannel.appendLine(`[ERROR] Could not send completion feedback due to a local error: ${error.message}`);
    }
}
async function callChatApi(userInput, outputChannel, stream, context = null) {
    try {
        stream.progress("Requesting from LabNote AI backend..."); // This is already in English, no change needed.
        const baseUrl = getBaseUrl();
        if (!baseUrl) {
            stream.markdown("Error: Backend URL is not set."); // This is already in English, no change needed.
            return null;
        }
        // 백엔드로 보낼 메시지 배열 구성. 여기서는 간단히 마지막 사용자 입력만 보냅니다.
        // 실제 애플리케이션에서는 전체 대화 기록을 보내야 할 수 있습니다.
        const messages = [{ role: 'user', content: userInput }];
        const chatData = await callBackendJson(baseUrl, '/api/chat', {
            body: {
                messages,
                context
            },
            outputChannel
        });
        stream.markdown(chatData.response);
        return { response: chatData.response, context: chatData.context }; // 응답과 함께 새로운 context 반환
    }
    catch (error) {
        stream.markdown(`An error occurred while chatting with the AI: ${error.message}`);
        outputChannel.appendLine(`[ERROR] callChatApi: ${error.stack}`);
        return null;
    }
}
async function handleGenerateFlow(session, request, stream, context, outputChannel) {
    const sessionId = "default_session";
    switch (session.state) {
        case 'awaiting_topic':
            session.data.topic = request.prompt;
            session.state = 'awaiting_workflow';
            chatSessions.set(sessionId, session);
            stream.markdown(`Got it. Topic: **"${session.data.topic}"**\n\nNow, please select a base workflow.`); // This is already in English, no change needed.
            const { ALL_WORKFLOWS } = await fetchConstants(context, getBaseUrl(), outputChannel);
            const wfId = await showWorkflowSelectionMenu(ALL_WORKFLOWS);
            if (!wfId) {
                stream.markdown("❌ Operation canceled."); // This is already in English, no change needed.
                chatSessions.delete(sessionId);
                return;
            }
            session.data.workflowId = wfId;
            session.state = 'awaiting_uos';
            chatSessions.set(sessionId, session);
            stream.markdown(`Workflow **[${wfId}]** has been selected.\n\nNow, please select the required Unit Operations.`);
            const { ALL_UOS } = await fetchConstants(context, getBaseUrl(), outputChannel);
            const uoIds = await showUnifiedUoSelectionMenu(ALL_UOS, []);
            if (!uoIds || uoIds.length === 0) {
                stream.markdown("❌ Operation canceled."); // This is already in English, no change needed.
                chatSessions.delete(sessionId);
                return;
            }
            session.data.uoIds = uoIds;
            stream.markdown("✅ All information has been collected. Starting to generate the lab note..."); // This is already in English, no change needed.
            await interactiveGenerateFlow(context, session.data.topic, outputChannel, session.data.workflowId, session.data.uoIds);
            stream.markdown("✅ The lab note has been successfully generated."); // This is already in English, no change needed.
            chatSessions.delete(sessionId);
            break;
    }
}
function escapeHtml(value) {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}
function isMetadataLine(line) {
    const normalized = line.replace(/\uFEFF/g, '').trim();
    if (!normalized) {
        return true;
    }
    const lower = normalized.toLowerCase();
    if (normalized === '⏎')
        return true;
    if (normalized.startsWith('✅'))
        return true;
    if (['chat', 'markdown', 'apply', 'labnote backend logic'].includes(lower))
        return true;
    if (lower.startsWith('다음은 ai'))
        return true;
    if (lower.startsWith('어느 번호'))
        return true;
    if (lower.startsWith('마음에 드는 번호'))
        return true;
    if (lower.startsWith('추가로 손보고'))
        return true;
    if (lower.startsWith('선택된 초안'))
        return true;
    if (lower.startsWith('피드백을 성공적으로 기록'))
        return true;
    if (lower.startsWith('모델 메타데이터'))
        return true;
    if (lower.startsWith('model metadata'))
        return true;
    if (lower.startsWith('모델:'))
        return true;
    if (lower.startsWith('model:'))
        return true;
    if (/^\d+번$/.test(normalized))
        return true;
    if (/^---.*---$/.test(normalized)) {
        if (lower.includes('제안') || lower.includes('proposal') || lower.includes('suggestion') || lower.includes('quality') || lower.includes('score') || lower.includes('점수') || lower.includes('초안')) {
            return true;
        }
    }
    return false;
}
function sanitizeSuggestionForEditor(option) {
    const lines = option.split(/\r?\n/);
    let startIndex = 0;
    while (startIndex < lines.length) {
        const rawLine = lines[startIndex];
        const trimmedLine = rawLine.trim();
        if (!trimmedLine) {
            startIndex++;
            continue;
        }
        if (isMetadataLine(trimmedLine)) {
            startIndex++;
            continue;
        }
        break;
    }
    const sanitized = lines.slice(startIndex).join('\n').replace(/^\s+/, '');
    return sanitized ? sanitized : option.trimStart();
}
function createPopulateWebviewPanel(section, options, isFromVisualEditor) {
    const panel = vscode.window.createWebviewPanel('labnoteAiPopulate', `AI Suggestions: ${section}`, // This is already in English, no change needed.
    vscode.ViewColumn.Beside, {
        enableScripts: true,
        retainContextWhenHidden: true
    });
    panel.webview.html = getPopulateWebviewContent(section, options, isFromVisualEditor);
    return panel;
}
function getPopulateWebviewContent(section, options, isFromVisualEditor) {
    const optionCards = options.map((option) => {
        const escapedOption = escapeHtml(option);
        const sanitizedOption = sanitizeSuggestionForEditor(option);
        const encodedOption = Buffer.from(option).toString('base64');
        const encodedSanitizedOption = Buffer.from(sanitizedOption).toString('base64');
        return `<div class="option-card" data-original-content="${encodedOption}" data-editor-content="${encodedSanitizedOption}">
                    <pre><code>${escapedOption}</code></pre>
                </div>`;
    }).join('');
    const buttonText = isFromVisualEditor ? "Copy Modified Content & Learn" : "Apply & Learn"; // This is already in English, no change needed.
    const buttonCommand = isFromVisualEditor ? "copyAndLearn" : "applyAndLearn";
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Suggestions: ${section}</title> <!-- This is already in English, no change needed. -->
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 1em; color: var(--vscode-editor-foreground); background-color: var(--vscode-editor-background); }
            h1, p { text-align: center; }
            #options-container { margin-bottom: 2em; }
            .option-card { border: 1px solid var(--vscode-editorWidget-border, #454545); border-radius: 5px; padding: 1em; margin-bottom: 1em; cursor: pointer; transition: all 0.2s ease-in-out; }
            .option-card:hover { border-color: var(--vscode-focusBorder, #007ACC); }
            .option-card.selected { border: 2px solid var(--vscode-focusBorder, #007ACC); box-shadow: 0 0 8px var(--vscode-focusBorder, #007ACC)66; }
            pre { white-space: pre-wrap; word-wrap: break-word; background-color: var(--vscode-editor-background); padding: 10px; border-radius: 4px; }
            #editor-section { display: none; }
            textarea { width: 100%; height: 250px; box-sizing: border-box; background-color: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 5px; padding: 10px; font-family: var(--vscode-editor-font-family); font-size: var(--vscode-editor-font-size); }
            button { padding: 10px 15px; border: none; background-color: var(--vscode-button-background, #0E639C); color: var(--vscode-button-foreground, #FFFFFF); border-radius: 5px; cursor: pointer; font-size: 1em; width: 100%; margin-top: 1em; }
            button:hover { background-color: var(--vscode-button-hoverBackground, #1177BB); }
        </style>
    </head>
    <body>
        <h1>AI Suggestions for "${section}"</h1> <!-- This is already in English, no change needed. -->
        <p>1. Select one of the suggestions below. 2. Edit the content if needed. 3. Click the button at the bottom.</p> <!-- This is already in English, no change needed. -->
        <div id="options-container">${optionCards}</div>
        <div id="editor-section">
            <h2>Edit Window</h2> <!-- This is already in English, no change needed. -->
            <textarea id="editor-textarea"></textarea>
            <button id="action-btn">${buttonText}</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            const cards = document.querySelectorAll('.option-card');
            const editorSection = document.getElementById('editor-section');
            const editorTextarea = document.getElementById('editor-textarea');
            const actionBtn = document.getElementById('action-btn');
            let selectedOriginalContent = '';
            let selectedEditorContent = '';

            cards.forEach(card => {
                card.addEventListener('click', () => {
                    cards.forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    selectedOriginalContent = card.dataset.originalContent ? atob(card.dataset.originalContent) : '';
                    selectedEditorContent = card.dataset.editorContent ? atob(card.dataset.editorContent) : selectedOriginalContent;
                    editorTextarea.value = selectedEditorContent;
                    editorSection.style.display = 'block';
                });
            });

            actionBtn.addEventListener('click', () => {
                const editedContent = editorTextarea.value;
                if (selectedOriginalContent) {
                    vscode.postMessage({
                        command: '${buttonCommand}',
                        chosen_original: selectedOriginalContent,
                        chosen_edited: editedContent
                    });
                }
            });
        </script>
    </body>
    </html>`;
}
function findSectionContext(document, positionOrContext) {
    const fileContent = document.getText();
    const yamlMatch = fileContent.match(/^---\s*[\r\n]+title:\s*["']?(.*?)["']?[\r\n]+/);
    const query = yamlMatch ? yamlMatch[1].replace(/\[AI Generated\]\s*/, '').trim() : "Untitled Experiment";
    const structureMap = [];
    let currentUoId = null;
    for (let i = 0; i < document.lineCount; i++) {
        const lineText = document.lineAt(i).text;
        const uoMatch = lineText.match(/^###\s*\\?\[(U[A-Z]{2,3}\d{3,4}).*?\\?\]/);
        if (uoMatch) {
            currentUoId = uoMatch[1];
        }
        const sectionMatch = lineText.match(/^####\s*(.*?)\s*$/);
        if (sectionMatch && currentUoId) {
            if (structureMap.length > 0) {
                structureMap[structureMap.length - 1].endLine = i - 1;
            }
            structureMap.push({
                uoId: currentUoId,
                section: sectionMatch[1].trim(),
                startLine: i,
                endLine: document.lineCount - 1
            });
        }
    }
    let targetSection;
    if (positionOrContext instanceof vscode.Position) {
        const cursorLine = positionOrContext.line;
        targetSection = structureMap.find(s => cursorLine >= s.startLine && cursorLine <= s.endLine);
    }
    else {
        targetSection = structureMap.find(s => s.uoId === positionOrContext.uoId && s.section === positionOrContext.section);
    }
    if (!targetSection) {
        return null;
    }
    const contentStartLine = targetSection.startLine + 1;
    let contentEndLine = targetSection.endLine;
    for (let i = targetSection.endLine; i >= contentStartLine; i--) {
        if (!document.lineAt(i).isEmptyOrWhitespace) {
            contentEndLine = i;
            break;
        }
    }
    if (contentStartLine > contentEndLine) {
        const pos = new vscode.Position(contentStartLine, 0);
        return {
            uoId: targetSection.uoId,
            section: targetSection.section,
            query,
            fileContent,
            placeholderRange: new vscode.Range(pos, pos)
        };
    }
    const startPos = document.lineAt(contentStartLine).range.start;
    const endPos = document.lineAt(contentEndLine).range.end;
    return {
        uoId: targetSection.uoId,
        section: targetSection.section,
        query,
        fileContent,
        placeholderRange: new vscode.Range(startPos, endPos)
    };
}
function parseAllSections(document) {
    const sections = [];
    let currentUoId = null;
    for (let i = 0; i < document.lineCount; i++) {
        const lineText = document.lineAt(i).text;
        const uoMatch = lineText.match(/^###\s*\\?\[(U[A-Z]{2,3}\d{3,4}).*?\\?\]/);
        if (uoMatch) {
            currentUoId = uoMatch[1];
        }
        const sectionMatch = lineText.match(/^####\s*(.*?)\s*$/);
        if (sectionMatch && currentUoId) {
            sections.push({
                uoId: currentUoId,
                section: sectionMatch[1].trim(),
                startLine: i
            });
        }
    }
    return sections;
}
async function fetchConstants(context, baseUrl, outputChannel) {
    try {
        return await callBackendJson(baseUrl, '/constants', {
            method: 'GET',
            outputChannel
        });
    }
    catch (e) {
        outputChannel.appendLine(`[Error] Could not fetch constants from backend: ${e.message}. Using local fallback.`);
        const workflowPath = resolveConfiguredPath(context, 'workflowsPath', 'workflows_en.md');
        const hwUoPath = resolveConfiguredPath(context, 'hwUnitOperationsPath', 'unitoperations_hw_en.md');
        const swUoPath = resolveConfiguredPath(context, 'swUnitOperationsPath', 'unitoperations_sw_en.md');
        const workflowContent = fs.readFileSync(workflowPath, 'utf-8');
        const hwUoContent = fs.readFileSync(hwUoPath, 'utf-8');
        const swUoContent = fs.readFileSync(swUoPath, 'utf-8');
        const workflows = logic.parseWorkflows(workflowContent);
        const hwUos = logic.parseUnitOperations(hwUoContent);
        const swUos = logic.parseUnitOperations(swUoContent);
        const allWorkflows = {};
        for (const wf of workflows) {
            allWorkflows[wf.id] = wf.name;
        }
        const allUos = {};
        for (const uo of [...hwUos, ...swUos]) {
            allUos[uo.id] = uo.name;
        }
        if (Object.keys(allWorkflows).length === 0 && Object.keys(allUos).length === 0) {
            outputChannel.appendLine(`[Error] Could not read local fallback files either. Using default constants.`);
            return {
                ALL_WORKFLOWS: { "WD070": "Vector Design" },
                ALL_UOS: { "UHW400": "Manual" }
            };
        }
        return {
            ALL_WORKFLOWS: allWorkflows,
            ALL_UOS: allUos
        };
    }
}
async function showWorkflowSelectionMenu(workflows) {
    const allWorkflowItems = Object.keys(workflows).map(id => ({ id, label: `[${id}]`, description: workflows[id] })); // This is already in English, no change needed.
    const selectedItem = await vscode.window.showQuickPick(allWorkflowItems, { title: 'Select Workflow', matchOnDescription: true, placeHolder: 'Search by name or ID...' }); // This is already in English, no change needed.
    return selectedItem?.id;
}
async function showUnifiedUoSelectionMenu(uos, recommendedIds) {
    const recommendedSet = new Set(recommendedIds);
    const allUoItems = Object.keys(uos).map(id => ({ id, label: `[${id}]`, description: uos[id], picked: recommendedSet.has(id) })); // This is already in English, no change needed.
    allUoItems.sort((a, b) => {
        const aIsRecommended = recommendedSet.has(a.id);
        const bIsRecommended = recommendedSet.has(b.id);
        if (aIsRecommended && !bIsRecommended)
            return -1;
        if (!aIsRecommended && bIsRecommended)
            return 1;
        return a.id.localeCompare(b.id);
    });
    const selectedItems = await vscode.window.showQuickPick(allUoItems, {
        title: 'Select Unit Operations (multiple selections possible)', // This is already in English, no change needed.
        canPickMany: true,
        matchOnDescription: true,
        placeHolder: 'Click checkboxes to select/deselect, then press Enter', // This is already in English, no change needed.
    });
    return selectedItems?.map(item => item.id);
}
//# sourceMappingURL=extension.js.map
