// Progressive Markdown Renderer for ChatGPT-style Streaming
// Author: Claude (SuperClaude)
// Date: 2025-10-01

/**
 * Progressive Markdown Renderer
 *
 * Renders markdown content progressively as tokens arrive from the server,
 * providing a ChatGPT-style streaming experience.
 *
 * Features:
 * - Token-by-token markdown rendering
 * - Real-time table parsing
 * - Phase progress indicators
 * - Auto-scrolling
 * - Error handling
 */
class ProgressiveMarkdownRenderer {
    /**
     * Initialize renderer
     *
     * @param {string} containerSelector - CSS selector for content container
     * @param {string} progressBarSelector - CSS selector for progress bar
     */
    constructor(containerSelector, progressBarSelector) {
        this.container = document.querySelector(containerSelector);
        this.progressBar = document.querySelector(progressBarSelector);
        this.accumulated = "";
        this.currentPhase = 0;
        this.phaseMessages = {};

        // Configure marked.js for better parsing
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                tables: true,
                pedantic: false,
                sanitize: false,
                smartLists: true
            });
            console.log('✅ marked.js configured for progressive rendering');
        } else {
            console.warn('⚠️ marked.js not loaded, using fallback renderer');
        }
    }

    /**
     * Add a markdown token to accumulated text and re-render
     *
     * @param {string} token - Markdown token to add
     */
    addToken(token) {
        // Accumulate token
        this.accumulated += token;

        // Try to parse as markdown
        try {
            const html = this._renderMarkdown(this.accumulated);
            this.container.innerHTML = html;
        } catch (e) {
            console.error('Markdown parsing error:', e);
            // If parsing fails, show as plain text
            this.container.textContent = this.accumulated;
        }

        // Auto-scroll to bottom
        this._autoScroll();
    }

    /**
     * Update progress bar and phase indicator
     *
     * @param {number} phase - Current phase number (1-5)
     * @param {string} message - Progress message
     * @param {number} progress - Progress percentage (0-100)
     */
    updateProgress(phase, message, progress) {
        // Update progress bar
        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
            this.progressBar.setAttribute('data-progress', `${progress}%`);

            // Add phase-specific styling
            this.progressBar.className = 'progress-bar';
            if (phase) {
                this.progressBar.classList.add(`phase-${phase}`);
            }

            // Show message in progress bar
            if (message) {
                this.progressBar.textContent = `${message} (${progress}%)`;
            }
        }

        // Add phase marker if phase changed
        if (phase && phase !== this.currentPhase) {
            this.currentPhase = phase;
            this.phaseMessages[phase] = message;
            this._addPhaseMarker(phase, message);
        }
    }

    /**
     * Add visual separator between phases
     *
     * @param {number} phase - Phase number
     * @param {string} message - Phase message
     */
    _addPhaseMarker(phase, message) {
        // Don't add marker for Phase 4 (streaming content)
        if (phase === 4) {
            return;
        }

        const marker = document.createElement('div');
        marker.className = `phase-marker phase-${phase}`;
        marker.innerHTML = `
            <div class="phase-marker-icon">Phase ${phase}</div>
            <div class="phase-marker-text">${message}</div>
        `;

        // Insert before current content or append
        if (this.container.firstChild) {
            this.container.insertBefore(marker, this.container.firstChild);
        } else {
            this.container.appendChild(marker);
        }
    }

    /**
     * Mark rendering as complete
     */
    complete() {
        // Note: We don't re-render here because Phase 4 has already
        // rendered all tokens progressively. Re-rendering would cause
        // duplicate content display.

        // Only update progress bar and state
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.textContent = '✅ 完成';
            this.progressBar.classList.add('complete');
        }

        console.log('✅ Progressive rendering complete');
        console.log(`📊 Final accumulated length: ${this.accumulated.length} chars`);
    }

    /**
     * Handle error during streaming
     *
     * @param {string} message - Error message
     */
    handleError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="error-icon">⚠️</div>
            <div class="error-text">${message}</div>
        `;
        this.container.appendChild(errorDiv);

        if (this.progressBar) {
            this.progressBar.classList.add('error');
            this.progressBar.textContent = '錯誤';
        }
    }

    /**
     * Render markdown to HTML
     *
     * @param {string} markdownText - Markdown text
     * @returns {string} HTML string
     */
    _renderMarkdown(markdownText) {
        if (!markdownText) {
            return '';
        }

        // Use marked.js if available
        if (typeof marked !== 'undefined' && marked.parse) {
            try {
                return marked.parse(markdownText);
            } catch (e) {
                console.warn('marked.js parsing failed, using fallback:', e);
            }
        }

        // Fallback to simple markdown rendering
        return this._fallbackMarkdownRender(markdownText);
    }

    /**
     * Fallback markdown renderer for when marked.js is unavailable
     *
     * @param {string} text - Markdown text
     * @returns {string} HTML string
     */
    _fallbackMarkdownRender(text) {
        let html = text;

        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        // Tables (basic support)
        if (html.includes('|')) {
            html = this._parseMarkdownTable(html);
        }

        return html;
    }

    /**
     * Parse markdown table
     *
     * @param {string} text - Text containing markdown table
     * @returns {string} HTML with table
     */
    _parseMarkdownTable(text) {
        const lines = text.split('<br>');
        const tableLines = [];
        const nonTableLines = [];
        let inTable = false;

        for (let line of lines) {
            if (line.includes('|')) {
                inTable = true;
                tableLines.push(line);
            } else {
                if (inTable && tableLines.length > 0) {
                    // Convert table
                    nonTableLines.push(this._convertTableToHTML(tableLines));
                    tableLines.length = 0;
                    inTable = false;
                }
                nonTableLines.push(line);
            }
        }

        // Handle remaining table
        if (tableLines.length > 0) {
            nonTableLines.push(this._convertTableToHTML(tableLines));
        }

        return nonTableLines.join('<br>');
    }

    /**
     * Convert markdown table lines to HTML table
     *
     * @param {Array<string>} lines - Table lines
     * @returns {string} HTML table
     */
    _convertTableToHTML(lines) {
        if (lines.length < 2) {
            return lines.join('<br>');
        }

        let html = '<table class="markdown-table">\n';

        // Header
        const headerCells = lines[0].split('|')
            .map(cell => cell.trim())
            .filter(cell => cell);

        html += '<thead><tr>\n';
        headerCells.forEach(cell => {
            const cleanCell = cell.replace(/<strong>(.*?)<\/strong>/g, '$1');
            html += `<th>${cleanCell}</th>\n`;
        });
        html += '</tr></thead>\n';

        // Body
        html += '<tbody>\n';
        for (let i = 2; i < lines.length; i++) {
            const cells = lines[i].split('|')
                .map(cell => cell.trim())
                .filter(cell => cell);

            if (cells.length > 0) {
                html += '<tr>\n';
                cells.forEach(cell => {
                    html += `<td>${cell}</td>\n`;
                });
                html += '</tr>\n';
            }
        }
        html += '</tbody>\n</table>';

        return html;
    }

    /**
     * Auto-scroll container to bottom
     */
    _autoScroll() {
        if (this.container) {
            this.container.scrollTop = this.container.scrollHeight;
        }
    }

    /**
     * Reset renderer state
     */
    reset() {
        this.accumulated = "";
        this.currentPhase = 0;
        this.phaseMessages = {};

        if (this.container) {
            this.container.innerHTML = '';
        }

        if (this.progressBar) {
            this.progressBar.style.width = '0%';
            this.progressBar.textContent = '';
            this.progressBar.className = 'progress-bar';
        }
    }
}

/**
 * Start progressive chat streaming
 *
 * @param {string} query - User query
 * @param {string} endpoint - API endpoint (default: /api/sales/chat-stream)
 * @param {string} containerSelector - Content container selector
 * @param {string} progressSelector - Progress bar selector
 */
function startProgressiveChat(
    query,
    endpoint = '/api/sales/chat-stream',
    containerSelector = '#chat-response',
    progressSelector = '#progress-bar'
) {
    const renderer = new ProgressiveMarkdownRenderer(
        containerSelector,
        progressSelector
    );

    // Reset renderer
    renderer.reset();

    // Create EventSource for SSE
    const eventSource = new EventSource(
        `${endpoint}?query=${encodeURIComponent(query)}`
    );

    console.log(`🚀 Starting progressive chat for query: ${query}`);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 Received:', data.type, data);

            switch (data.type) {
                case 'progress':
                    renderer.updateProgress(
                        data.phase,
                        data.message,
                        data.progress
                    );
                    break;

                case 'phase_result':
                    // Phase completed, log result
                    console.log(`✅ Phase ${data.phase} completed:`, data.data);
                    break;

                case 'markdown_token':
                    renderer.addToken(data.token);
                    break;

                case 'complete':
                    renderer.complete();
                    eventSource.close();
                    console.log('✅ Progressive chat complete');
                    break;

                case 'error':
                    renderer.handleError(data.message);
                    eventSource.close();
                    console.error('❌ Progressive chat error:', data.message);
                    break;

                default:
                    console.warn('Unknown message type:', data.type);
            }
        } catch (e) {
            console.error('Failed to parse event data:', e, event.data);
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        renderer.handleError('連線中斷，請重試');
        eventSource.close();
    };

    return {
        renderer,
        eventSource,
        stop: () => eventSource.close()
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ProgressiveMarkdownRenderer,
        startProgressiveChat
    };
}

// Make available globally
window.ProgressiveMarkdownRenderer = ProgressiveMarkdownRenderer;
window.startProgressiveChat = startProgressiveChat;

console.log('✅ Progressive Markdown Renderer loaded');
