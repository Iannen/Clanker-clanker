import { BaseComponent, register } from './base-component.js';

const html = `
    <div
        tabindex="-1"
        class="flex flex-col w-full transition-all duration-200 rounded-xl p-2"
    >
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
            class="performance-footer hidden w-full max-w-[48rem] px-3 pt-2 mt-2 border-t border-[#1f2937]/50 text-[10px] leading-relaxed text-[#6b7280] font-mono"
        ></div>
    </div>
`;

const className = 'flex flex-col w-full my-4';

class Message extends BaseComponent {
    html = html;
    className = className;

    messageRole = 'assistant';
    counter = 0;

    #content = '';
    #reasoning = '';
    #timings = null;
    #complete = false;

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
        this.reasoningElement = this.wrapper.children[0];
        this.contentElement = this.wrapper.children[1];
        this.performanceElement = this.wrapper.children[2];

        this.reasoningSummary = this.reasoningElement.querySelector('summary');
        this.reasoningBody = this.reasoningElement.querySelector('.reasoning-body');
        this.contentSummary = this.contentElement.querySelector('summary');
        this.contentBody = this.contentElement.querySelector('.content-body');

        this.setAttribute('data-index', String(this.counter));

        if (this.messageRole === 'user') {
            this.wrapper.classList.add('items-end');

            this.contentElement.classList.add(
                'text-[#e5e7eb]',
                'rounded-2xl',
                'max-w-[36rem]'
            );
            this.contentBody.classList.add('px-4', 'whitespace-pre-wrap');

            this.reasoningElement.classList.add('hidden');
            this.performanceElement.classList.add('hidden');
        } else {
            this.wrapper.classList.add('items-start');

            this.contentElement.classList.add(
                'text-[#f3f4f6]',
                'max-w-[48rem]'
            );
            this.contentBody.classList.add('py-2', 'px-3');
        }

        this.#renderSummaries();
        this.#renderContent();
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
        if (this.messageRole === 'user') {
            const icon = this.contentElement.open ? '▼' : '▶';
            this.contentSummary.textContent = `(${icon}, ctrl+2) Content: ${this.#content.length} characters`;
            return;
        }

        const rIcon = this.reasoningElement.open ? '▼' : '▶';
        this.reasoningSummary.textContent = `(${rIcon}, ctrl+1) Reasoning: ${this.#reasoning.length} characters`;

        const cIcon = this.contentElement.open ? '▼' : '▶';
        this.contentSummary.textContent = `(${cIcon}, ctrl+2) Content: ${this.#content.length} characters`;
    }

    #renderContent() {
        if (this.messageRole === 'assistant') this.contentBody.innerHTML = this.content
            ? marked.parse(this.content)
            : '';
        else this.contentBody.textContent = this.content;
    }

    updateContent(text) { this.content = text; }

    updateReasoning(text) {
        this.reasoning = text;

        if (this.messageRole !== 'assistant') return;

        if (!this.#reasoning) {
            this.reasoningElement.classList.add('hidden');
            return;
        }

        this.reasoningElement.classList.remove('hidden');

        this.reasoningBody.textContent = this.#reasoning;
    }

    setPerformanceTimings(timings) {
        this.#timings = timings;
        this.#complete = true;

        if (this.initialized) this.#renderPerformance();
    }

    #renderPerformance() {
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
    }

    setSelected(selected) {
        this.wrapper.classList.toggle('bg-[#111827]/80', Boolean(selected));
        this.wrapper.classList.toggle('shadow-[0_0_0_1px_#10b981]', Boolean(selected));
    }

    scrollIntoView(options = {}) { this.wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest', ...options }); }
}

register('chat-message', Message);