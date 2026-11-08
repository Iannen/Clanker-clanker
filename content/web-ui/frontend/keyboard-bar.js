import { BaseComponent, register } from './base-component.js';

const sharedDomKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];
const pudDomKeys = ['q', 'w', 'e', 'r'];
const promptKeys = ['a', 's', 'd', 'f'];

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

    onConnect() {
        this.#statusLine = this.querySelector('.status-line');
        this.#statusLine.textContent = 'Ready.';

        this.querySelectorAll('.kb-btn').forEach(btn => {
            btn.addEventListener('click', () => this.#onButtonClick(btn));
        });
    }

    #onButtonClick(btn) {
        if (this.#activeBtn) {
            this.#activeBtn.classList.remove('kb-active');
            this.#activeBtn.classList.add('kb-inactive');
        }

        btn.classList.remove('kb-inactive');
        btn.classList.add('kb-active');
        this.#activeBtn = btn;

        const key = btn.dataset.key;
        const row = btn.closest('div.flex')?.parentElement?.querySelector('.uppercase')?.textContent ?? '';
        this.#statusLine.textContent = `[${row}] key "${key}" pressed`;
    }
}

register('keyboard-bar', KeyboardBar);