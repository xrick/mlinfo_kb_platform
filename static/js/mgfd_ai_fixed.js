// static/js/mgfd_ai_fixed.js
// mgfd_ai_fixed.js - Fixed Double Bubble Issue
// Modified: 2025-10-02
// Fix: Prevents double bubble messages in progressive streaming

console.log("using mgfd_ai_fixed.js - Double bubble issue resolved");
let salesAIInitialized = false;

// ✨ Progressive Streaming Feature Flag
let USE_PROGRESSIVE_STREAMING = true;  // Set to false to use traditional streaming

// Custom markdown table parser as fallback
function parseMarkdownTable(markdownText) {
    console.log('🔧 Using custom markdown table parser');

    try {
        const lines = markdownText.trim().split('\n');

        if (lines.length < 3) {
            return markdownText;
        }

        const hasFirstLinePipe = lines[0].includes('|');
        const hasSecondLineSeparator = lines[1].includes('---');

        if (!hasFirstLinePipe || !hasSecondLineSeparator) {
            return markdownText;
        }

        const headerCells = lines[0].split('|').map(cell => cell.trim()).filter(cell => cell);
        const dataRows = [];

        for (let i = 2; i < lines.length; i++) {
            if (lines[i].includes('|')) {
                const rowCells = lines[i].split('|').map(cell => cell.trim()).filter(cell => cell);
                dataRows.push(rowCells);
            }
        }

        let html = '<table>\n<thead>\n<tr>\n';
        headerCells.forEach((header) => {
            const cleanHeader = header.replace(/\*\*(.*?)\*\*/g, '$1');
            html += `<th>${cleanHeader}</th>\n`;
        });
        html += '</tr>\n</thead>\n<tbody>\n';

        dataRows.forEach((row) => {
            html += '<tr>\n';
            row.forEach((cell) => {
                const cleanCell = cell.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                html += `<td>${cleanCell}</td>\n`;
            });
            html += '</tr>\n';
        });

        html += '</tbody>\n</table>';
        return html;
    } catch (error) {
        console.error('❌ Custom markdown table parser failed:', error);
        return markdownText;
    }
}

function configureMarkedJS() {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            gfm: true,
            tables: true,
            breaks: false,
            pedantic: false,
            sanitize: false,
            smartLists: true,
            smartypants: false
        });
        console.log('✅ marked.js configured');
        return true;
    }
    return false;
}

function renderMarkdownContent(markdownText) {
    if (!markdownText || typeof markdownText !== 'string') {
        return markdownText;
    }

    const hasTable = markdownText.includes('|') && markdownText.includes('---');

    if (!hasTable) {
        if (typeof marked !== 'undefined' && marked.parse) {
            return marked.parse(markdownText);
        }
        return markdownText.replace(/\n/g, '<br>');
    }

    if (typeof marked !== 'undefined' && marked.parse) {
        try {
            const markedResult = marked.parse(markdownText);
            const hasTableElement = markedResult.includes('<table>');
            const hasThElement = markedResult.includes('<th>');

            if (hasTableElement && hasThElement) {
                return markedResult;
            }
        } catch (error) {
            console.error('marked.js failed:', error);
        }
    }

    return parseMarkdownTable(markdownText);
}

function initSalesAI() {
    console.log('Initializing Sales AI (Fixed Double Bubble)...');

    if (typeof marked !== 'undefined' && marked.parse) {
        configureMarkedJS();
    }

    if (salesAIInitialized) {
        console.log('Already initialized');
        return;
    }

    salesAIInitialized = true;

    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatMessages = document.getElementById("chatMessages");

    if (!userInput || !sendButton || !chatMessages) {
        console.error('Required DOM elements not found');
        return;
    }

    // ==========================================
    // ✨ FIXED sendMessage - No Double Bubbles
    // ==========================================
    async function sendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        // Step 1: Add user message
        appendMessage({ role: "user", content: query });
        userInput.value = "";
        toggleInput(true);

        // Step 2: Clean up any existing indicators/containers
        cleanupExistingIndicators();

        // Step 3: Get session ID
        let sessionId = getSessionId();

        // Step 4: Route to appropriate streaming method
        try {
            if (USE_PROGRESSIVE_STREAMING) {
                console.log("🚀 Using progressive streaming");
                await sendProgressiveStreamingMessage(query, sessionId);
            } else {
                console.log("📡 Using traditional streaming");
                await sendTraditionalStreamingMessage(query, sessionId);
            }
        } catch (error) {
            console.error("Streaming error:", error);
            // On error, show error message in a single bubble
            appendMessage({
                role: 'assistant',
                content: { error: `請求失敗: ${error.message}` }
            });
        } finally {
            toggleInput(false);
            userInput.focus();
        }
    }

    // ==========================================
    // 🧹 Cleanup Helper - Prevents Double Bubbles
    // ==========================================
    function cleanupExistingIndicators() {
        // Remove thinking indicator if exists
        const thinkingIndicator = document.getElementById('thinking-indicator');
        if (thinkingIndicator) {
            thinkingIndicator.remove();
            console.log('🗑️ Removed thinking indicator');
        }

        // Clean up any orphaned progress bars
        const orphanedProgress = document.querySelectorAll('.progress-container:empty');
        orphanedProgress.forEach(el => el.remove());
    }

    // ==========================================
    // ✨ Progressive Streaming (No Duplicate Containers)
    // ==========================================
    async function sendProgressiveStreamingMessage(query, sessionId) {
        console.log("🚀 Progressive streaming started");

        // Create progress bar (NOT a message bubble)
        let progressContainer = document.querySelector('.progress-container');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'progress-container';
            progressContainer.innerHTML = '<div id="progress-bar" class="progress-bar"></div>';
            chatMessages.appendChild(progressContainer);
        }

        // Ensure we have a usable progress bar and a unique id for selector-based API
        let progressBar = progressContainer.querySelector('.progress-bar') || document.getElementById('progress-bar');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.className = 'progress-bar';
            progressContainer.appendChild(progressBar);
        }
        if (!progressBar.id) {
            const generatedProgressId = `progress-bar-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
            progressBar.id = generatedProgressId;
        }
        const progressBarId = progressBar.id;

        // Create ONE message container for the entire response
        const assistantMessageContainer = createMessageContainer('assistant');
        const contentDiv = assistantMessageContainer.querySelector('.message-content');

        // Assign a unique id to content container for selector-based renderer API
        if (!contentDiv.id) {
            const generatedContentId = `msg-content-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
            contentDiv.id = generatedContentId;
        }
        const contentId = contentDiv.id;

        // Check if ProgressiveMarkdownRenderer is available
        if (typeof ProgressiveMarkdownRenderer === 'undefined') {
            console.error('❌ ProgressiveMarkdownRenderer not loaded!');
            // Fallback to traditional
            progressContainer.remove();
            assistantMessageContainer.remove();
            await sendTraditionalStreamingMessage(query, sessionId);
            return;
        }

        // Create renderer with selector strings per renderer API contract
        const renderer = new ProgressiveMarkdownRenderer(`#${contentId}`, `#${progressBarId}`);
        renderer.reset();

        // Show in-bubble thinking spinner until first token arrives
        const contentDivEl = document.getElementById(contentId);
        if (contentDivEl) {
            contentDivEl.innerHTML = `
                <div class="message-content thinking-indicator">
                    <div class="spinner"></div>
                    <span>AI 正在思考中...</span>
                </div>
            `;
        }

        try {
            const response = await fetch("/api/mgfd/chat-progressive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: query,
                    session_id: sessionId
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonDataString = line.substring(6);
                        if (jsonDataString) {
                            try {
                                const data = JSON.parse(jsonDataString);
                                handleProgressiveUpdate(data, renderer);
                            } catch (e) {
                                console.error('JSON parse error:', e);
                            }
                        }
                    }
                }
            }

            console.log('✅ Progressive streaming complete');

        } catch (error) {
            console.error("Progressive streaming error:", error);
            renderer.handleError(`請求失敗: ${error.message}`);
            throw error;
        }
    }

    function handleProgressiveUpdate(data, renderer) {
        switch (data.type) {
            case 'progress':
                renderer.updateProgress(data.phase, data.message, data.progress);
                break;

            case 'phase_result':
                console.log(`✅ Phase ${data.phase} done`);
                break;

            case 'markdown_token':
                renderer.addToken(data.token);
                break;

            case 'complete':
                // If backend packs final response under data.response, render it before completing
                try {
                    if (data.data && data.data.response) {
                        renderer.addToken(data.data.response);
                    }
                } catch (e) {
                    console.warn('Finalize render failed:', e);
                }
                renderer.complete();
                break;

            case 'error':
                renderer.handleError(data.message);
                break;

            default:
                // Fallback handling: backend may fallback to non-progressive JSON
                try {
                    if (data.message) {
                        renderer.addToken(typeof data.message === 'string' ? data.message : JSON.stringify(data.message));
                    } else if (data.response) {
                        renderer.addToken(data.response);
                    } else if (typeof data === 'string') {
                        renderer.addToken(data);
                    } else {
                        console.warn('Unknown type:', data.type);
                    }
                } catch (e) {
                    console.warn('Fallback render error:', e);
                }
        }
    }

    // ==========================================
    // 📡 Traditional Streaming (Clean, No Duplicates)
    // ==========================================
    async function sendTraditionalStreamingMessage(query, sessionId) {
        console.log("📡 Traditional streaming started");

        // Show thinking indicator (will be replaced by actual content)
        const thinkingBubble = showThinkingIndicator();

        try {
            const response = await fetch("/api/mgfd/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query, session_id: sessionId }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let assistantMessageContainer = null;
            let fullResponseText = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullResponseText += chunk;

                const lines = fullResponseText.split('\n\n');

                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i];
                    if (line.startsWith('data: ')) {
                        const jsonDataString = line.substring(6);
                        if (jsonDataString) {
                            // Remove thinking bubble on first data
                            if (thinkingBubble && document.body.contains(thinkingBubble)) {
                                thinkingBubble.remove();
                            }

                            try {
                                const jsonData = JSON.parse(jsonDataString);

                                // Create container ONCE
                                if (!assistantMessageContainer) {
                                    assistantMessageContainer = createMessageContainer('assistant');
                                }

                                renderMessageContent(
                                    assistantMessageContainer.querySelector('.message-content'),
                                    jsonData
                                );
                            } catch (e) {
                                console.error("JSON parse error:", e);
                            }
                        }
                    }
                }

                fullResponseText = lines[lines.length - 1];
            }
        } catch (error) {
            console.error("Traditional streaming error:", error);
            if (thinkingBubble && document.body.contains(thinkingBubble)) {
                thinkingBubble.remove();
            }
            throw error;
        }
    }

    // ==========================================
    // 🔑 Session Management
    // ==========================================
    function getSessionId() {
        let sessionId = sessionStorage.getItem('mgfd_session_id');
        if (!sessionId) {
            sessionId = generateUUID();
            sessionStorage.setItem('mgfd_session_id', sessionId);
            console.log('🆕 New session:', sessionId);
        }
        return sessionId;
    }

    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // ==========================================
    // 🎨 UI Helpers
    // ==========================================
    function createMessageContainer(role) {
        const messageContainer = document.createElement('div');
        messageContainer.className = `message-container ${role}`;
        messageContainer.dataset.role = role;

        const messageCard = document.createElement('div');
        messageCard.className = 'message-card';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        messageCard.appendChild(messageContent);

        if (role === 'assistant') {
            const copyBtnTemplate = document.getElementById('copy-to-clipboard-template');
            if (copyBtnTemplate) {
                messageCard.insertAdjacentHTML('beforeend', copyBtnTemplate.innerHTML);
                const copyBtn = messageCard.querySelector('.copy-btn');
                if (copyBtn) {
                    copyBtn.addEventListener('click', () => {
                        copyToClipboard(messageContainer.assistantData);
                    });
                }
            }
        }

        messageContainer.appendChild(messageCard);
        chatMessages.appendChild(messageContainer);
        scrollToBottom();

        return messageContainer;
    }

    function appendMessage(message) {
        const messageContainer = createMessageContainer(message.role);
        renderMessageContent(
            messageContainer.querySelector('.message-content'),
            message.content
        );
        if (message.role === 'assistant') {
            messageContainer.assistantData = message.content;
        }
        scrollToBottom();
    }

    function renderMessageContent(container, content) {
        if (!content) {
            container.innerHTML = "<p>收到空的回應</p>";
            return;
        }

        if (typeof content === 'string') {
            container.innerHTML = renderMarkdownContent(content);
            return;
        }

        if (content.error) {
            container.innerHTML = `<p style="color: red;"><strong>錯誤：</strong> ${content.error}</p>`;
            return;
        }

        if (content.type === 'general') {
            const message = content.message || content.response_message || '系統回應';
            container.innerHTML = `<div class="general-response">${renderMarkdownContent(message)}</div>`;
            return;
        }

        // Default: try to render any content
        let markdownString = "";

        if (content.answer_summary) {
            markdownString += `<div class="answer-summary">${content.answer_summary}</div>\n\n`;
        }

        if (content.comparison_table) {
            markdownString += "### 詳細規格比較表：\n\n";
            markdownString += renderMarkdownContent(JSON.stringify(content.comparison_table));
        }

        if (content.conclusion) {
            markdownString += `### 結論建議\n${content.conclusion}\n\n`;
        }

        if (markdownString) {
            container.innerHTML = renderMarkdownContent(markdownString);
        } else {
            const fallback = content.message || JSON.stringify(content, null, 2);
            container.innerHTML = `<div>${fallback}</div>`;
        }
    }

    function showThinkingIndicator() {
        const existingIndicator = document.getElementById('thinking-indicator');
        if (existingIndicator) return existingIndicator;

        const container = document.createElement('div');
        container.id = 'thinking-indicator';
        container.className = 'message-container assistant';
        container.innerHTML = `
            <div class="message-card">
                <div class="message-content thinking-indicator">
                    <div class="spinner"></div>
                    <span>AI 正在思考中...</span>
                </div>
            </div>
        `;
        chatMessages.appendChild(container);
        scrollToBottom();
        return container;
    }

    function toggleInput(disabled) {
        userInput.disabled = disabled;
        sendButton.disabled = disabled;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function copyToClipboard(content) {
        const text = JSON.stringify(content, null, 2);
        navigator.clipboard.writeText(text).then(() => {
            alert("已複製！");
        }).catch(err => {
            console.error('複製失敗:', err);
        });
    }

    // ==========================================
    // Event Listeners
    // ==========================================
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);

    const presetButtons = document.querySelector('.preset-buttons');
    if (presetButtons) {
        presetButtons.addEventListener('click', (e) => {
            if (e.target.classList.contains('preset-btn')) {
                userInput.value = e.target.dataset.question;
                sendMessage();
            }
        });
    }

    console.log('✅ Sales AI initialized (Fixed)');
}

window.initSalesAI = initSalesAI;

console.log('✅ mgfd_ai_fixed.js loaded - Double bubble issue resolved');
