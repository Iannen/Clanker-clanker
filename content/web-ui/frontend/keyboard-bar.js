import { BaseComponent, register } from './base-component.js';
import { apiClient } from './api-client.js';

const sharedDomKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];
const pudDomKeys = ['q', 'w', 'e', 'r'];
const promptKeys = ['a', 's', 'd', 'f'];

const boundKeys = new Set([...sharedDomKeys, ...pudDomKeys, ...promptKeys]);

function buildRow(label, keys) {
    const buttons = keys.map(key =>
        `<button type="button" class="kb-btn kb-inactive" data-key="${key}">
            <span class="key-badge">${key}</span>
        </button>`
    ).join('\n            ');

    return `
        <div class="mb-3">
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
        }
        .kb-btn .key-badge {
            font-weight: 700;
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

    <div class="p-4 flex flex-col h-full">
        ${buildRow('Shared-Dom', sharedDomKeys)}
        ${buildRow('Pud-Dom', pudDomKeys)}
        ${buildRow('Prompt', promptKeys)}

        <div class="status-line mt-4 text-xs font-mono text-[#9ca3af]"></div>
    </div>
`;

const className = 'flex-1 overflow-y-auto p-4 w-full bg-[#111827]';

class KeyboardBar extends BaseComponent {
    html = html;
    className = className;

    #statusLine;
    #activeBtn = null;
    #busy = false;

    #handleKeydown = (event) => {
        if (event.ctrlKey || event.altKey || event.metaKey) return;

        if (!boundKeys.has(event.key)) return;

        const btn = this.querySelector(`.kb-btn[data-key="${event.key}"]`);
        if (!btn) return;

        event.stopPropagation();
        event.preventDefault();
        this.#onButtonClick(btn);
    };

    onConnect() {
        this.tabIndex = 0;

        this.#statusLine = this.querySelector('.status-line');
        this.#statusLine.textContent = 'Ready.';

        this.querySelectorAll('.kb-btn').forEach(btn => {
            btn.addEventListener('click', () => this.#onButtonClick(btn));
        });

        this.addEventListener('keydown', this.#handleKeydown);
    }

    disconnectedCallback() {
        this.removeEventListener('keydown', this.#handleKeydown);
    }

    #setStateClass(btn, state) {
        btn.classList.remove('kb-active', 'kb-highlighted', 'kb-inactive');
        btn.classList.add(`kb-${state}`);
    }

    #formatStatus(response) {
        const { result_type, key, domain } = response;
        switch (result_type) {
            case 'bootstrap_success':
                return 'Bootstrap complete.';
            case 'domain_selected':
                return `Selected domain "${domain ?? ''}" [${key}]`;
            case 'uninhabited_domain':
                return `Domain [${key}] has no content`;
            case 'uninhabited_prompt':
                return `Prompt [${key}] has no content`;
            case 'unbound_key':
                return `No action bound to key "${key}"`;
            case 'prompt_render':
                return `Rendered prompt for [${key}]`;
            default:
                return `Key "${key}" pressed`;
        }
    }

    async #onButtonClick(btn) {
        if (this.#busy) return;
        this.#busy = true;

        const key = btn.dataset.key;
        try {
            const response = await apiClient.sendChar(key);

            for (const [k, info] of Object.entries(response.buttons)) {
                const el = this.querySelector(`.kb-btn[data-key="${k}"]`);
                if (el) this.#setStateClass(el, info.state);
            }

            const pressedEl = this.querySelector(`.kb-btn[data-key="${response.key}"]`);
            this.#activeBtn = pressedEl || null;

            this.#statusLine.textContent = this.#formatStatus(response);

            if (response.result_type === 'prompt_render' && response.prompt_text) {
                this.dispatchEvent(new CustomEvent('prompt-ready', { detail: response.prompt_text }));
            }
        } catch (error) {
            this.#statusLine.textContent = '❌ ' + (error.message || 'Request failed');
        } finally {
            this.#busy = false;
        }
    }
}

register('keyboard-bar', KeyboardBar);