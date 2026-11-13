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
            class="stats-footer hidden w-full max-w-[48rem] px-3 pt-2 mt-2 border-t border-[#1f2937]/50 text-xs leading-relaxed text-[#9ca3af] font-mono"
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
    sentChars = 0;

    #content = '';
    #reasoning = '';
    #timings = null;
    #complete = false;
    #phase = null; // null | 'prefill' | 'reasoning' | 'content' | 'final'
    #charsPerToken = null;

    // Phase timers (ms, relative to performance.now())
    #prefillStart = null;
    #prefillEnd = null;
    #prefillData = null; // { processed, total, time_ms, cache }
    #reasoningStart = null;
    #reasoningEnd = null;
    #contentStart = null;

    get content() {
        return this.#content;
    }

    set content(value) {
        this.#content = String(value ?? '');

        if (this.initialized) {
            this.#renderContent();
            this.#renderSummaries();
            this.#maybeAdvancePhase();
        }
    }

    get reasoning() {
        return this.#reasoning;
    }

    set reasoning(value) {
        this.#reasoning = String(value ?? '');

        if (this.initialized) {
            this.#renderSummaries();
            this.#maybeAdvancePhase();
        }
    }

    onConnect() {
        this.wrapper = this.firstElementChild;
        if (!this.wrapper) return;

        this.reasoningElement = this.wrapper.querySelector('.reasoning-section');
        this.contentElement = this.wrapper.querySelector('.content-section');
        this.statsElement = this.wrapper.querySelector('.stats-footer');

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
            this.statsElement?.classList.add('hidden');
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
        this.#maybeAdvancePhase();
    }

    // Surface a single prompt_progress tick.
    onPrefill(pp) {
        if (this.messageRole !== 'assistant') return;

        if (this.#phase === null) {
            this.#phase = 'prefill';
            this.#prefillStart = performance.now();
            if (this.sentChars > 0 && pp.total > 0) {
                this.#charsPerToken = this.sentChars / pp.total;
            }
        }

        this.#prefillData = pp;
        this.#renderStats();
    }

    #maybeAdvancePhase() {
        if (this.messageRole !== 'assistant') return;
        if (this.#phase === 'final') return;

        if (this.#phase === 'prefill' && this.#reasoning.length > 0) {
            this.#prefillEnd = performance.now();
            this.#phase = 'reasoning';
            this.#reasoningStart = performance.now();
        }

        if (this.#phase === 'reasoning' && this.#content.length > 0) {
            this.#reasoningEnd = performance.now();
            this.#phase = 'content';
            this.#contentStart = performance.now();
        }
    }

    setPerformanceTimings(timings) {
        this.#timings = timings;
        this.#complete = true;
        this.#phase = 'final';

        if (this.initialized) {
            this.#renderStats();
        }
    }

    #renderStats() {
        if (!this.statsElement) return;
        if (this.#phase === null) {
            this.statsElement.classList.add('hidden');
            return;
        }

        this.statsElement.classList.remove('hidden');
        this.statsElement.textContent = this.#buildStatsLine();
    }

    #buildStatsLine() {
        const parts = [];

        // --- Prefill segment ---
        if (this.#prefillData) {
            const pd = this.#prefillData;
            const prefillTok = pd.total || pd.processed;
            if (this.#phase === 'final' && this.#timings) {
                const t = this.#timings;
                parts.push(`Prefill: ${t.prompt_n} tok · ${Number(t.prompt_per_second).toFixed(2)} tok/s`);
                if (t.cache_n != null && t.prompt_n > 0) {
                    parts.push(`cache: ${Math.round((t.cache_n / t.prompt_n) * 100)}%`);
                }
            } else if (this.#phase === 'prefill') {
                const elapsed = ((pd.time_ms ?? 0) / 1000).toFixed(1);
                const pct = pd.total > 0 ? Math.round((pd.processed / pd.total) * 100) : 0;
                let tps = '';
                if (pd.time_ms > 0 && pd.processed > 0) {
                    tps = ` · ${Math.round(pd.processed / (pd.time_ms / 1000))} tok/s`;
                }
                const cacheStr = pd.cache != null
                    ? ` · cache: ${Math.round(pd.cache <= 1 ? pd.cache * 100 : pd.cache)}%`
                    : '';
                parts.push(`⏳ Prefill: ${pd.processed}/${pd.total} tok (${pct}%) · ${elapsed}s${tps}${cacheStr}`);
            } else {
                // frozen prefill (reasoning, content, or final without timings)
                const elapsed = ((pd.time_ms ?? 0) / 1000).toFixed(1);
                let tps = '';
                if (pd.time_ms > 0 && pd.processed > 0) {
                    tps = ` · ${Math.round(pd.processed / (pd.time_ms / 1000))} tok/s`;
                }
                const cacheStr = pd.cache != null
                    ? ` · cache: ${Math.round(pd.cache <= 1 ? pd.cache * 100 : pd.cache)}%`
                    : '';
                parts.push(`Prefill: ${pd.total} tok · ${elapsed}s${tps}${cacheStr}`);
            }
        }

        // --- Reasoning segment ---
        if (this.#phase === 'final' && this.#timings) {
            const t = this.#timings;
            const totalGen = this.#reasoning.length + this.#content.length;
            if (t.predicted_n > 0 && totalGen > 0) {
                const rTok = Math.round(t.predicted_n * (this.#reasoning.length / totalGen));
                const cTok = t.predicted_n - rTok;
                parts.push(`Gen: ${t.predicted_n} tok · ${Number(t.predicted_per_second).toFixed(2)} tok/s (~${rTok} reasoning, ~${cTok} reply)`);
            } else {
                parts.push(`Gen: ${t.predicted_n} tok · ${Number(t.predicted_per_second).toFixed(2)} tok/s`);
            }
            if (t.draft_n != null && t.draft_n_accepted != null) {
                const mtpPct = Math.round((t.draft_n_accepted / t.draft_n) * 100);
                parts.push(`mtp ${mtpPct}%`);
            }
        } else if (this.#phase === 'reasoning' || (this.#phase === 'content' && this.#reasoning.length > 0)) {
            if (this.#phase === 'reasoning') {
                const elapsed = ((performance.now() - this.#reasoningStart) / 1000).toFixed(1);
                const estTok = this.#charsPerToken
                    ? `~${Math.round(this.#reasoning.length / this.#charsPerToken)} tok`
                    : `~${this.#reasoning.length} chars`;
                parts.push(`Reasoning: ${estTok} (${this.#reasoning.length} chars) · ${elapsed}s`);
            } else {
                // frozen reasoning in content phase
                const rElapsed = ((this.#reasoningEnd - this.#reasoningStart) / 1000).toFixed(1);
                const rTok = this.#charsPerToken
                    ? `~${Math.round(this.#reasoning.length / this.#charsPerToken)}`
                    : this.#reasoning.length;
                parts.push(`Reasoning: ~${rTok} tok · ${rElapsed}s`);
            }
        }

        // --- Content segment (running) ---
        if (this.#phase === 'content') {
            const elapsed = ((performance.now() - this.#contentStart) / 1000).toFixed(1);
            const estTok = this.#charsPerToken
                ? `~${Math.round(this.#content.length / this.#charsPerToken)} tok`
                : `~${this.#content.length} chars`;
            parts.push(`Content: ${estTok} (${this.#content.length} chars) · ${elapsed}s`);
        }

        return parts.join(' │ ');
    }

    appendError(message) {
        this.content += `\n[Error: ${message}]`;

        this.contentBody.classList.remove('text-[#f3f4f6]');
        this.contentBody.classList.add('text-[#f87171]');
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