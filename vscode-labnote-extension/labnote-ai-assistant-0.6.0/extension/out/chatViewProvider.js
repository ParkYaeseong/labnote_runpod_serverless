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
exports.ChatViewProvider = void 0;
const vscode = __importStar(require("vscode"));
const fetch = require('node-fetch');
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
        vscode.window.showErrorMessage("Backend URL is not set. Please check the `labnote.ai.backendUrl` setting.");
        return null;
    }
    return url;
}
class ChatViewProvider {
    constructor(_extensionUri) {
        this._extensionUri = _extensionUri;
        this._chatHistory = [];
    }
    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        // 초기 메시지 추가
        const initialMessage = 'Hello! I\'m LabNote AI. How can I help you?';
        this._chatHistory.push({ role: 'assistant', content: initialMessage });
        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.type === 'ask-question') {
                const userInput = data.value;
                if (!userInput)
                    return;
                this._chatHistory.push({ role: 'user', content: userInput });
                // 사용자 질문을 채팅창에 먼저 표시
                this._view?.webview.postMessage({ type: 'add-message', role: 'user', content: userInput });
                try {
                    const baseUrl = getBaseUrl();
                    if (!baseUrl) {
                        this._view?.webview.postMessage({ type: 'add-message', role: 'assistant', content: 'Error: Backend URL is not set.' });
                        return;
                    }
                    const response = await fetch(`${baseUrl}/chat`, {
                        method: 'POST',
                        headers: getApiHeaders(),
                        body: JSON.stringify({
                            query: userInput,
                            conversation_id: null // 사이드바 채팅은 대화 ID를 사용하지 않음
                        }),
                    });
                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Chat failed (HTTP ${response.status}): ${errorText}`);
                    }
                    const chatData = await response.json();
                    this._view?.webview.postMessage({ type: 'add-message', role: 'assistant', content: chatData.response });
                    this._chatHistory.push({ role: 'assistant', content: chatData.response });
                }
                catch (error) {
                    this._view?.webview.postMessage({ type: 'add-message', role: 'assistant', content: `An error occurred: ${error.message}` });
                    this._chatHistory.push({ role: 'assistant', content: `An error occurred: ${error.message}` });
                }
            }
        });
    }
    _getHtmlForWebview(webview) {
        // Webview에 필요한 스크립트와 스타일시트의 URI를 생성합니다.
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'style.css'));
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>LabNote AI Chat</title>
            </head>
            <body>
                <div id="chat-container">
                    <div id="message-list">
                        <div class="message assistant">
                            <p>${this._chatHistory.find(m => m.role === 'assistant')?.content || 'Hello! I\'m LabNote AI.'}</p>
                        </div>
                    </div>
                </div>
                <div id="input-container">
                    <textarea id="user-input" placeholder="Enter your question here..."></textarea>
                    <button id="send-button">Send</button>
                </div>
                <script src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}
exports.ChatViewProvider = ChatViewProvider;
ChatViewProvider.viewType = 'labnote.chatView';
//# sourceMappingURL=chatViewProvider.js.map