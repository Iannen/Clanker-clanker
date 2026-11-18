import { BaseComponent, register } from './base-component.js';

const html = `
    <div tabindex="-1" class="flex flex-col w-full transition-all duration-200 rounded-xl p-2">
        <details
            class="repo-context-section mb-2 rounded-lg border border-[#1f2937] bg-[#030712]/60"
        >
            <summary
                tabindex="-1"
                class="cursor-pointer select-none px-3 py-2 text-xs font-mono text-[#6ee7b7] list-none"
            >
                (▶, ctrl+1) Repo context: 0 characters
            </summary>
            <div
                class="repo-context-body px-3 pt-1 pb-3 text-xs leading-relaxed text-[#9ca3af] font-mono whitespace-pre-wrap"
            ></div>
        </details>
    </div>
`;

const className = 'flex flex-col w-full my-4';

class RepoContext extends BaseComponent {
    html = html;
    className = className;
    messageRole = 'repo-context';

    #text = '';

    get text() {
        return this.#text;
    }

    set text(value) {
        this.#text = String(value ?? '');
        if (this.initialized) {
            this.#render();
        }
    }

    get content() {
        return this.#text;
    }

    onConnect() {
        this.wrapper = this.firstElementChild;
        if (!this.wrapper) return;

        this.section = this.wrapper.querySelector('.repo-context-section');
        this.summary = this.wrapper.querySelector('summary');
        this.body = this.wrapper.querySelector('.repo-context-body');

        this.#render();
    }

    focus() { this.wrapper.focus(); }

    scrollIntoView(options = {}) {
        this.wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest', ...options });
    }

    toggle() {
        this.section.toggleAttribute('open');
        this.#render();
    }

    setSelected(selected) {
        this.wrapper.classList.toggle('bg-[#111827]/80', Boolean(selected));
        this.wrapper.classList.toggle('shadow-[0_0_0_1px_#10b981]', Boolean(selected));
    }

    #render() {
        if (!this.section || !this.summary || !this.body) return;
        const icon = this.section.open ? '▼' : '▶';
        this.summary.textContent = `(${icon}, ctrl+1) Repo context: ${this.#text.length} characters`;
        this.body.textContent = this.#text;
    }
}

register('repo-context', RepoContext);