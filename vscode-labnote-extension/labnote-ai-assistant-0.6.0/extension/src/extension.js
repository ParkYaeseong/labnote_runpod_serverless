"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
var vscode = require("vscode");
// node-fetch v2는 CommonJS 모듈이므로 require 구문을 사용하는 것이 가장 안정적입니다.
var fetch = require('node-fetch');
function activate(context) {
    var _this = this;
    // **개선점**: 확장 프로그램의 상태를 알려주는 출력 채널을 생성합니다.
    // 이를 통해 사용자는 참고 자료(sources)나 디버깅 정보를 확인할 수 있습니다.
    var outputChannel = vscode.window.createOutputChannel("LabNote AI");
    outputChannel.appendLine('LabNote AI extension is now active.');
    var disposable = vscode.commands.registerCommand('labnote.ai.generate', function () { return __awaiter(_this, void 0, void 0, function () {
        var userInput;
        var _this = this;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, vscode.window.showInputBox({
                        prompt: '생성할 랩노트의 내용을 입력하세요.',
                        placeHolder: '예: DH5a Transformation 프로토콜 알려줘'
                    })];
                case 1:
                    userInput = _a.sent();
                    if (!userInput) {
                        vscode.window.showInformationMessage('입력이 취소되었습니다.');
                        return [2 /*return*/];
                    }
                    // **개선점**: withProgress를 사용하여 사용자에게 명확한 피드백을 제공합니다.
                    return [4 /*yield*/, vscode.window.withProgress({
                            location: vscode.ProgressLocation.Notification,
                            title: "LabNote AI가 작동 중입니다...",
                            cancellable: true // 사용자가 작업을 취소할 수 있도록 설정
                        }, function (progress, token) { return __awaiter(_this, void 0, void 0, function () {
                            var response, errorBody, data, doc, error_1;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        // 작업 취소 리스너
                                        token.onCancellationRequested(function () {
                                            outputChannel.appendLine("사용자가 작업을 취소했습니다.");
                                        });
                                        progress.report({ increment: 10, message: "백엔드 서버에 요청을 보냅니다..." });
                                        outputChannel.appendLine("[Request] \uC0AC\uC6A9\uC790 \uCFFC\uB9AC: \"".concat(userInput, "\""));
                                        _a.label = 1;
                                    case 1:
                                        _a.trys.push([1, 8, , 9]);
                                        return [4 /*yield*/, fetch('http://123.37.5.184:32682/generate_labnote', {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({ query: userInput }),
                                                // **개선점**: 긴 응답을 대비하여 타임아웃을 넉넉하게 설정합니다.
                                                timeout: 60000 // 60초
                                            })];
                                    case 2:
                                        response = _a.sent();
                                        if (token.isCancellationRequested)
                                            return [2 /*return*/];
                                        progress.report({ increment: 40, message: "AI가 응답을 생성 중입니다..." });
                                        if (!!response.ok) return [3 /*break*/, 4];
                                        return [4 /*yield*/, response.text()];
                                    case 3:
                                        errorBody = _a.sent();
                                        throw new Error("HTTP Error: ".concat(response.status, " ").concat(response.statusText, "\n").concat(errorBody));
                                    case 4: return [4 /*yield*/, response.json()];
                                    case 5:
                                        data = _a.sent();
                                        if (token.isCancellationRequested)
                                            return [2 /*return*/];
                                        progress.report({ increment: 90, message: "결과를 표시합니다..." });
                                        return [4 /*yield*/, vscode.workspace.openTextDocument({
                                                content: data.response,
                                                language: 'markdown'
                                            })];
                                    case 6:
                                        doc = _a.sent();
                                        return [4 /*yield*/, vscode.window.showTextDocument(doc, { preview: false })];
                                    case 7:
                                        _a.sent();
                                        // 참고 자료는 출력 채널에 기록합니다.
                                        if (data.sources && data.sources.length > 0) {
                                            outputChannel.appendLine("[Response] \uC0DD\uC131 \uC644\uB8CC. \uCC38\uACE0 \uC790\uB8CC: ".concat(data.sources.join(', ')));
                                        }
                                        else {
                                            outputChannel.appendLine("[Response] \uC0DD\uC131 \uC644\uB8CC. \uCC38\uACE0 \uC790\uB8CC \uC5C6\uC74C.");
                                        }
                                        outputChannel.show(true); // 사용자에게 출력 채널을 보여줍니다.
                                        return [3 /*break*/, 9];
                                    case 8:
                                        error_1 = _a.sent();
                                        // **개선점**: 에러 메시지를 사용자 친화적으로 표시하고, 자세한 내용은 출력 채널에 기록합니다.
                                        vscode.window.showErrorMessage('LabNote AI 생성 중 오류가 발생했습니다. 자세한 내용은 출력 채널을 확인하세요.');
                                        outputChannel.appendLine("[ERROR] ".concat(error_1.message));
                                        outputChannel.show(true);
                                        return [3 /*break*/, 9];
                                    case 9: return [2 /*return*/];
                                }
                            });
                        }); })];
                case 2:
                    // **개선점**: withProgress를 사용하여 사용자에게 명확한 피드백을 제공합니다.
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    context.subscriptions.push(disposable);
}
// 확장 프로그램이 비활성화될 때 호출됩니다.
function deactivate() { }
