import { BaseComponent, register } from './base-component.js';
import { apiClient } from './api-client.js';

const sharedDomKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];
const pudDomKeys = ['q', 'w', 'e', 'r'];
const promptKeys = ['a', 's', 'd', 'f'];

const boundKeys = new Set([...sharedDomKeys, ...pudDomKeys, ...promptKeys, 'Enter']);

function buildRow(label, keys) {
    const buttons = keys.map(key =>
        `<button type="button" class="kb-btn kb-inactive" data-key="${key}">
            <span class="key-badge">${key}</span>
            <span class="btn-label"></span>
        </button>`
    ).join('\n            ');

    return `
        <div class="kb-row mb-3" data-row="${label}">
            <div class="text-xs font-mono text-[#6b7280] mb-1 uppercase tracking-wider">${label}</div>
            <div class="flex gap-1 flex-wrap">
                ${buttons}
            </div>
        </div>`;
}

const html = `
    <style>
        .kb-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2.25rem;
            min-height: 2.25rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.375rem;
            border: 1px solid #1f2937;
            background: #030712;
            color: #9ca3af;
            font-family: monospace;
            font-size: 0.75rem;
            cursor: pointer;
            transition: background 0.15s, color 0.15s, border-color 0.15s;
            gap: 0.25rem;
        }
        .kb-btn .key-badge {
            font-weight: 700;
        }
        .kb-btn .btn-label {
            font-size: 0.625rem;
            max-width: 8rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .kb-inactive {
            background: #030712;
            color: #6b7280;
            border-color: #1f2937;
        }
        .kb-active {
            background: #064e3b;
            color: #6ee7b7;
            border-color: #10b981;
        }
        .kb-highlighted {
            background: #111827;
            color: #f3f4f6;
            border-color: #374151;
        }
    </style>

    <div class="kb-inner p-4 flex flex-col h-full w-full">
        ${buildRow('Shared-Dom', sharedDomKeys)}
        ${buildRow('Pud-Dom', pudDomKeys)}
        ${buildRow('Prompt', promptKeys)}

        <div class="status-line mt-4 text-xs font-mono text-[#9ca3af]"></div>
    </div>
`;

const className = 'w-full bg-[#111827]';

class KeyboardBar extends BaseComponent {
    html = html;
    className = className;

    #statusLine;
    #busy = false;
    #renderedPrompt = null;
    #selectedPrompt = null;
    #sharedDomains = [];
    #pudDomains = [];
    #selectedDomain = null;
    #expanded = false;

    isExpanded() { return this.#expanded; }

    getRenderedPromptText() { return this.#renderedPrompt?.text ?? null; }

    setDomains(shared, pud) {
        this.#sharedDomains = shared || [];
        this.#pudDomains = pud || [];
        this.#selectedDomain = null;
        this.#selectedPrompt = null;
        this.#renderedPrompt = null;
        this.#refreshAllStates();
    }

    setExpanded(expanded) {
        this.#expanded = expanded;
        const rows = this.querySelectorAll('.kb-row');

        if (expanded) {
            this.classList.add('flex-1', 'overflow-y-auto', 'p-4');
            this.classList.remove('cursor-pointer');
            rows.forEach(r => r.classList.remove('hidden'));
            this.#statusLine.textContent = 'Ready.';
        } else {
            this.classList.remove('flex-1', 'overflow-y-auto', 'p-4');
            this.classList.add('p-1', 'cursor-pointer');
            rows.forEach(r => r.classList.add('hidden'));
            this.#statusLine.textContent = this.#buildCollapsedStatus();
        }
    }

    toggleExpanded() { this.setExpanded(!this.#expanded); }

    async expandPaths(paths) {
        if (!this.#selectedDomain || !this.#selectedPrompt) return false;
        if (!paths || paths.length === 0) return false;

        if (!this.#selectedPrompt.expanded_paths) {
            this.#selectedPrompt.expanded_paths = [];
        }

        const existing = new Set(this.#selectedPrompt.expanded_paths);
        const newPaths = paths.filter(p => !existing.has(p));

        if (newPaths.length === 0) return false;

        this.#selectedPrompt.expanded_paths.push(...newPaths);

        const response = await apiClient.renderPrompt(this.#selectedDomain, this.#selectedPrompt);
        this.#renderedPrompt = response;

        const lines = response.lines ?? 0;
        const chars = response.chars ?? 0;
        this.#statusLine.textContent =
            `Prompt "${this.#selectedPrompt.name}" of "${this.#selectedDomain.name}" — ${lines} lines, ${chars} chars — press Enter`;

        return true;
    }

    #buildCollapsedStatus() {
        if (!this.#selectedDomain || !this.#selectedPrompt || !this.#renderedPrompt) {
            return 'Ctrl+I to expand';
        }

        const domKey = this.#findDomainKey(this.#selectedDomain);
        const promptKey = this.#findPromptKey(this.#selectedPrompt);
        const lines = this.#renderedPrompt.lines ?? 0;
        const chars = this.#renderedPrompt.chars ?? 0;

        return `Ctrl+I to expand │ Dom: "${this.#selectedDomain.name}" [${domKey}] │ Prompt: "${this.#selectedPrompt.name}" [${promptKey}] · ${lines} lines, ${chars} chars`;
    }

    #findDomainKey(domain) {
        const si = this.#sharedDomains.indexOf(domain);
        if (si >= 0) return sharedDomKeys[si];
        const pi = this.#pudDomains.indexOf(domain);
        if (pi >= 0) return pudDomKeys[pi];
        return '?';
    }

    #findPromptKey(prompt) {
        const idx = this.#selectedDomain?.prompts?.indexOf(prompt) ?? -1;
        return idx >= 0 ? promptKeys[idx] : '?';
    }

    #handleKeydown = (event) => {
        if (event.ctrlKey && event.key === 'Enter') {
            if (!this.#renderedPrompt) return;
            event.stopPropagation();
            event.preventDefault();
            navigator.clipboard.writeText(this.#renderedPrompt.text)
                .then(() => {
                    this.#statusLine.textContent = '📋 Prompt copied to clipboard';
                })
                .catch(() => {
                    this.#statusLine.textContent = '❌ Failed to copy to clipboard';
                });
            return;
        }

        if (event.ctrlKey || event.altKey || event.metaKey) return;

        if (!boundKeys.has(event.key)) return;

        if (event.key === 'Enter') {
            if (!this.#renderedPrompt) return;
            event.stopPropagation();
            event.preventDefault();
            this.dispatchEvent(new CustomEvent('prompt-selected'));
            return;
        }

        event.stopPropagation();
        event.preventDefault();

        if (sharedDomKeys.includes(event.key) || pudDomKeys.includes(event.key)) {
            this.#onDomainKey(event.key);
        } else if (promptKeys.includes(event.key)) {
            this.#onPromptKey(event.key);
        }
    };

    onConnect() {
        this.tabIndex = 0;

        this.#statusLine = this.querySelector('.status-line');
        this.#statusLine.textContent = 'Ready.';

        this.querySelectorAll('.kb-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.dataset.key;
                if (sharedDomKeys.includes(key) || pudDomKeys.includes(key)) {
                    this.#onDomainKey(key);
                } else if (promptKeys.includes(key)) {
                    this.#onPromptKey(key);
                }
            });
        });

        this.addEventListener('keydown', this.#handleKeydown);
        this.addEventListener('click', () => {
            if (!this.#expanded) this.toggleExpanded();
        });
    }

    disconnectedCallback() {
        this.removeEventListener('keydown', this.#handleKeydown);
    }

    #setStateClass(btn, state) {
        btn.classList.remove('kb-active', 'kb-highlighted', 'kb-inactive');
        btn.classList.add(`kb-${state}`);
    }

    #setBtnLabel(btn, label) {
        const labelEl = btn.querySelector('.btn-label');
        if (labelEl) labelEl.textContent = label || '';
    }

    #refreshAllStates() {
        for (const key of sharedDomKeys) {
            const btn = this.querySelector(`.kb-btn[data-key="${key}"]`);
            if (!btn) continue;
            const idx = sharedDomKeys.indexOf(key);
            const dom = this.#sharedDomains[idx];
            if (this.#selectedDomain && dom === this.#selectedDomain) {
                this.#setStateClass(btn, 'highlighted');
            } else if (dom) {
                this.#setStateClass(btn, 'active');
                this.#setBtnLabel(btn, dom.name);
            } else {
                this.#setStateClass(btn, 'inactive');
                this.#setBtnLabel(btn, '');
            }
        }

        for (const key of pudDomKeys) {
            const btn = this.querySelector(`.kb-btn[data-key="${key}"]`);
            if (!btn) continue;
            const idx = pudDomKeys.indexOf(key);
            const dom = this.#pudDomains[idx];
            if (this.#selectedDomain && dom === this.#selectedDomain) {
                this.#setStateClass(btn, 'highlighted');
            } else if (dom) {
                this.#setStateClass(btn, 'active');
                this.#setBtnLabel(btn, dom.name);
            } else {
                this.#setStateClass(btn, 'inactive');
                this.#setBtnLabel(btn, '');
            }
        }

        for (const key of promptKeys) {
            const btn = this.querySelector(`.kb-btn[data-key="${key}"]`);
            if (!btn) continue;
            const idx = promptKeys.indexOf(key);
            const prompt = this.#selectedDomain?.prompts?.[idx];
            if (prompt) {
                this.#setStateClass(btn, 'active');
                this.#setBtnLabel(btn, prompt.name);
            } else {
                this.#setStateClass(btn, 'inactive');
                this.#setBtnLabel(btn, '');
            }
        }
    }

    #onDomainKey(key) {
        let domains = sharedDomKeys.includes(key) ? this.#sharedDomains : this.#pudDomains;
        let keys = sharedDomKeys.includes(key) ? sharedDomKeys : pudDomKeys;
        const idx = keys.indexOf(key);
        const domain = domains[idx];

        if (!domain) {
            this.#statusLine.textContent = `Domain [${key}] has no content`;
            return;
        }

        this.#selectedDomain = domain;
        this.#selectedPrompt = null;
        this.#renderedPrompt = null;
        this.#refreshAllStates();
        this.#statusLine.textContent = `Selected domain "${domain.name}" [${key}]`;
    }

    async #onPromptKey(key) {
        if (this.#busy) return;

        if (!this.#selectedDomain) {
            this.#statusLine.textContent = `Select a domain first`;
            return;
        }

        const idx = promptKeys.indexOf(key);
        const prompt = this.#selectedDomain.prompts?.[idx];

        if (!prompt) {
            this.#statusLine.textContent = `Prompt [${key}] has no content`;
            return;
        }

        this.#busy = true;
        try {
            const response = await apiClient.renderPrompt(this.#selectedDomain, prompt);

            this.#selectedPrompt = prompt;
            this.#renderedPrompt = response;

            const pressedBtn = this.querySelector(`.kb-btn[data-key="${key}"]`);
            if (pressedBtn) this.#setStateClass(pressedBtn, 'highlighted');

            const lines = response.lines ?? 0;
            const chars = response.chars ?? 0;
            this.#statusLine.textContent =
                `Prompt "${prompt.name}" of "${this.#selectedDomain.name}" — ${lines} lines, ${chars} chars — press Enter`;
        } catch (error) {
            this.#statusLine.textContent = '❌ ' + (error.message || 'Prompt render failed');
        } finally {
            this.#busy = false;
        }
    }
}

register('keyboard-bar', KeyboardBar);