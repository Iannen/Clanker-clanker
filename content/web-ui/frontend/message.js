import { BaseComponent, register } from './base-component.js';

const html = `
    <div tabindex="-1" class="flex flex-col w-full transition-all duration-200 rounded-xl p-2">
        <style>
            /* Scoped-like Markdown styling for this component */
            .markdown-body h1 { font-size: 1.5rem; font-weight: bold; margin-top: 1rem; margin-bottom: 0.5rem; color: #f9fafb; }
            .markdown-body h2 { font-size: 1.25rem; font-weight: bold; margin-top: 1rem; margin-bottom: 0.5rem; color: #f9fafb; }
            .markdown-body h3 { font-size: 1.1rem; font-weight: bold; margin-top: 0.75rem; margin-bottom: 0.25rem; color: #f9fafb; }
            .markdown-body p { margin-bottom: 0.75rem; line-height: 1.5; }
            .markdown-body ul { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 0.75rem; }
            .markdown-body ol { list-style-type: decimal; padding-left: 1.5rem; margin-bottom: 0.75rem; }
            .markdown-body li { margin-bottom: 0.25rem; }
            .markdown-body blockquote { border-left: 4px solid #374151; padding-left: 1rem; color: #9ca3af; margin-bottom: 0.75rem; font-style: italic; }
            .markdown-body hr { border-color: #1f2937; margin: 1.5rem 0; }
            .markdown-body table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
            .markdown-body th, .markdown-body td { border: 1px solid #1f2937; padding: 0.5rem 0.75rem; text-align: left; }
            .markdown-body th { background-color: #111827; color: #6ee7b7; font-weight: 600; }
            .markdown-body tr:nth-child(even) { background-color: rgba(17, 24, 39, 0.4); }
            .markdown-body code:not(pre code) { background-color: #111827; color: #6ee7b7; padding: 0.15rem 0.35rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.875rem; border: 1px solid #1f2937; }
            .markdown-body a { color: #6ee7b7; text-decoration: underline; }
        </style>

        <details
            class="reasoning-section hidden mb-2 rounded-lg border border-[#1f2937] bg-[#030712]/60"
        >
            <summary
                tabindex="-1"
                class="cursor-pointer select-none px-3 py-2 text-xs font-mono text-[#6ee7b7] list-none"
            >
                Reasoning: 0 characters
            </summary>

            <div
                class="reasoning-body px-3 pt-1 pb-3 text-xs leading-relaxed text-[#9ca3af] font-mono whitespace-pre-wrap"
            ></div>
        </details>

        <details
            open
            class="content-section mb-2 rounded-lg border border-[#1f2937] bg-[#030712]/60 w-full"
        >
            <summary
                tabindex="-1"
                class="cursor-pointer select-none px-3 py-2 text-xs font-mono text-[#6ee7b7] list-none"
            >
                Content: 0 characters
            </summary>

            <div
                class="content-body w-full text-left leading-[1.6]"
            ></div>
        </details>

        <div
            class="prefill-bar w-full max-w-[48rem] px-3 pt-2 mt-2 border-t border-[#1f2937]/50"
        >
            <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-mono font-bold text-[#6ee7b7]">Prefill</span>
                <span class="prefill-stats text-[10px] leading-relaxed text-[#6b7280] font-mono"></span>
            </div>
            <div class="w-full bg-[#030712] rounded-full border border-[#1f2937] h-1.5 overflow-hidden">
                <div
                    class="prefill-fill h-full bg-[#059669] transition-[width] duration-150"
                    style="width: 0%"
                ></div>
            </div>
        </div>

        <div
            class="performance-footer hidden w-full max-w-[48rem] px-3 pt-2 mt-2 border-t border-[#1f2937]/50 text-[10px] leading-relaxed text-[#6b7280] font-mono"
        ></div>
    </div>
`;

const className = 'flex flex-col w-full my-4';

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

class Message extends BaseComponent {
    html = html;
    className = className;

    messageRole = 'assistant';
    counter = 0;
    collapsed = false;

    #content = '';
    #reasoning = '';
    #timings = null;
    #complete = false;
    #prefillState = null;

    get content() {
        return this.#content;
    }

    set content(value) {
        this.#content = String(value ?? '');

        if (this.initialized) {
            this.#renderContent();
            this.#renderSummaries();
        }
    }

    get reasoning() {
        return this.#reasoning;
    }

    set reasoning(value) {
        this.#reasoning = String(value ?? '');

        if (this.initialized) this.#renderSummaries();
    }

    onConnect() {
        this.wrapper = this.firstElementChild;
        if (!this.wrapper) return;

        this.reasoningElement = this.wrapper.querySelector('.reasoning-section');
        this.contentElement = this.wrapper.querySelector('.content-section');
        this.performanceElement = this.wrapper.querySelector('.performance-footer');
        this.prefillElement = this.wrapper.querySelector('.prefill-bar');
        this.prefillFill = this.prefillElement?.querySelector('.prefill-fill');
        this.prefillStats = this.prefillElement?.querySelector('.prefill-stats');

        this.reasoningSummary = this.reasoningElement?.querySelector('summary');
        this.reasoningBody = this.reasoningElement?.querySelector('.reasoning-body');
        this.contentSummary = this.contentElement?.querySelector('summary');
        this.contentBody = this.contentElement?.querySelector('.content-body');

        this.setAttribute('data-index', String(this.counter));

        if (this.messageRole === 'user') {
            this.wrapper.classList.add('items-end');

            this.contentElement?.classList.add(
                'text-[#e5e7eb]',
                'rounded-2xl',
                'max-w-[70%]'
            );
            this.contentBody?.classList.add('px-4', 'whitespace-pre-wrap');

            this.reasoningElement?.classList.add('hidden');
            this.prefillElement?.classList.add('hidden');
            this.performanceElement?.classList.add('hidden');
        } else {
            this.wrapper.classList.add('items-start');

            this.contentElement?.classList.add(
                'text-[#f3f4f6]',
                'max-w-[70%]'
            );
            this.contentBody?.classList.add('py-2', 'px-3');
        }

        this.#renderSummaries();
        this.#renderContent();
        if (this.collapsed) this.contentElement?.removeAttribute('open');
        this.updateReasoning(this.#reasoning);
        this.#renderPerformance();
    }

    focus() { this.wrapper.focus(); }

    toggleReasoning() {
        this.reasoningElement.toggleAttribute('open');
        this.#renderSummaries();
    }

    toggleContent() {
        this.contentElement.toggleAttribute('open');
        this.#renderSummaries();
    }

    #renderSummaries() {
        if (!this.contentElement || !this.contentSummary) return;

        if (this.messageRole === 'user') {
            const icon = this.contentElement?.open ? '▼' : '▶';
            this.contentSummary.textContent = `(${icon}, ctrl+2) Content: ${this.#content.length} characters`;
            return;
        }

        if (this.reasoningElement && this.reasoningSummary) {
            const rIcon = this.reasoningElement?.open ? '▼' : '▶';
            this.reasoningSummary.textContent = `(${rIcon}, ctrl+1) Reasoning: ${this.#reasoning.length} characters`;
        }

        const cIcon = this.contentElement?.open ? '▼' : '▶';
        this.contentSummary.textContent = `(${cIcon}, ctrl+2) Content: ${this.#content.length} characters`;
    }

    #renderContent() {
        if (!this.contentBody) return;

        if (this.messageRole === 'assistant') {
            this.contentBody.className = 'markdown-body text-sm text-[#f3f4f6]';
            this.contentBody.innerHTML = this.content ? marked.parse(escapeHtml(this.content)) : '';
        } else {
            this.contentBody.className = '';
            this.contentBody.textContent = this.content;
        }
    }

    updateContent(text) { 
        this.content = text; 
    }

    updateReasoning(text) {
        this.#reasoning = String(text ?? '');

        if (this.messageRole !== 'assistant' || !this.reasoningElement || !this.reasoningBody) return;

        if (!this.#reasoning) {
            this.reasoningElement.classList.add('hidden');
            return;
        }

        this.reasoningElement.classList.remove('hidden');
        this.reasoningBody.textContent = this.#reasoning;
        this.#renderSummaries();
    }

    // Surface a single prompt_progress tick. `cache` is the llama.cpp KV cache
    // hit ratio in [0,1]; if the gpu-box ever emits it as an already-percentage
    // value (>1), the formatter treats it as such.
    onPrefill(pp) {
        if (this.messageRole !== 'assistant') return;
        this.#renderPrefill(pp);
    }

    #renderPrefill(pp) {
        const { processed, total, time_ms, cache } = pp;
        if (!this.prefillElement) return;
        this.prefillElement.classList.remove('hidden');

        const pct = total > 0 ? processed / total : 0;
        const pctStr = `${Math.round(pct * 100)}%`;

        const prev = this.#prefillState;
        let rateStr = '';
        if (prev) {
            const dtMs = (pp.time_ms ?? 0) - prev.time_ms;
            const dProc = pp.processed - prev.processed;
            if (dtMs > 0 && dProc >= 0) {
                rateStr = ` ${Math.round(dProc / (dtMs / 1000))} tok/s`;
            }
        } else if ((pp.time_ms ?? 0) > 0 && pp.processed > 0) {
            rateStr = ` ${Math.round(pp.processed / (pp.time_ms / 1000))} tok/s`;
        }

        const cacheStr =
            cache != null && cache !== undefined
                ? ` · cache: ${Math.round(cache <= 1 ? cache * 100 : cache)}%`
                : '';

        this.prefillFill.style.width = pctStr;
        this.prefillStats.textContent = `${pctStr}${rateStr} · ${((pp.time_ms ?? 0) / 1000).toFixed(1)}s${cacheStr}`.trim();

        this.#prefillState = { processed: pp.processed, time_ms: pp.time_ms };
    }

    hidePrefillBar() { this.#hidePrefillBar(); }

    #hidePrefillBar() {
        if (this.prefillElement) this.prefillElement.classList.add('hidden');
        this.#prefillState = null;
    }

    setPerformanceTimings(timings) {
        this.#timings = timings;
        this.#complete = true;

        if (this.initialized) {
            this.#renderPerformance();
            // Hide the prefill bar only once the real stats are in, so the user
            // sees the prefill progress until the message completes.
            this.#hidePrefillBar();
        }
    }

    #renderPerformance() {
        if (!this.performanceElement) return;

        if (
            this.messageRole !== 'assistant' ||
            !this.#complete ||
            !this.#timings
        ) {
            this.performanceElement.classList.add('hidden');
            return;
        }

        const {
            prompt_n,
            prompt_per_second,
            predicted_n,
            predicted_per_second
        } = this.#timings;

        const values = [
            prompt_n,
            prompt_per_second,
            predicted_n,
            predicted_per_second
        ];

        if (
            values.some(value =>
                value === undefined ||
                value === null ||
                !Number.isFinite(Number(value))
            )
        ) {
            this.performanceElement.classList.add('hidden');
            return;
        }

        const totalChars = this.#reasoning.length + this.#content.length;

        const reasoningPercentage = totalChars
            ? Math.round((this.#reasoning.length / totalChars) * 100)
            : 0;

        const replyPercentage = totalChars
            ? Math.round((this.#content.length / totalChars) * 100)
            : 0;

        this.performanceElement.textContent =
            `Prefill: ${prompt_n} tokens - ${Number(prompt_per_second).toFixed(2)} tok/s\n` +
            `| Generation: ${predicted_n} tokens - ${Number(predicted_per_second).toFixed(2)} tok/s ` +
            `(${reasoningPercentage}% reasoning, ${replyPercentage}% reply)`;

        this.performanceElement.classList.remove('hidden');
    }

    appendError(message) {
        this.content += `\n[Error: ${message}]`;

        this.contentBody.classList.remove('text-[#f3f4f6]');
        this.contentBody.classList.add('text-[#f87171]');
        this.hidePrefillBar();
    }

    setSelected(selected) {
        this.wrapper.classList.toggle('bg-[#111827]/80', Boolean(selected));
        this.wrapper.classList.toggle('shadow-[0_0_0_1px_#10b981]', Boolean(selected));
    }

    scrollIntoView(options = {}) { this.wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest', ...options }); }
}

register('chat-message', Message);

marked.use({
    renderer: {
        code({ text, lang }) {
            return `
                <div tabindex="-1" class="my-3 rounded-lg border border-[#1f2937] bg-[#030712] overflow-hidden">
                    <div class="bg-[#111827] px-3 py-1 text-xs text-[#6ee7b7] font-mono border-b border-[#1f2937] flex justify-between items-center">
                        <span>${lang || 'code'}</span>
                        <span class="text-[10px] text-[#6b7280]">custom renderer</span>
                    </div>
                    <pre class="p-3 whitespace-pre-wrap text-sm text-[#f3f4f6] font-mono"><code>${text}</code></pre>
                </div>
            `;
        }
    }
});