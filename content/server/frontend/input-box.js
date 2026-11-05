import { BaseComponent, register } from './base-component.js';

const html = `
    <div class="max-w-[42rem] mx-auto w-full flex gap-3">
        <textarea
            id="prompt-input"
            rows="2"
            autofocus
            placeholder="Ask a follow-up or start a conversation (Esc to focus here)..."
            class="flex-1 bg-[#030712] border border-[#1f2937] rounded-lg p-3 text-[#f3f4f6] outline-none resize-none font-[inherit] focus:border-[#10b981]"
        ></textarea>

        <button
            id="send-btn"
            type="button"
            class="w-auto flex items-center justify-center px-6 py-3 font-bold text-sm border-none rounded-lg cursor-pointer transition-colors text-white bg-[#059669] hover:bg-[#10b981] disabled:opacity-50 disabled:cursor-not-allowed"
        >
            Send
        </button>
    </div>
`;

const className = 'block bg-[#111827] border-t border-[#1f2937] p-4';

class InputBox extends BaseComponent {
    html = html;
    className = className;

    #highlightTimeout = null;

    onConnect() {
        this.promptInput = this.querySelector('textarea');
        this.sendBtn = this.querySelector('button');

        this.sendBtn.addEventListener('click', () => this.#dispatchSubmit());
    }

    getValue() { return this.promptInput.value.trim(); }

    clear() { this.promptInput.value = ''; }

    #dispatchSubmit() {
        const prompt = this.getValue();
        if (!prompt) return;

        this.clear();
        this.dispatchEvent(new CustomEvent('submit', { detail: prompt }));
    }

    focus() {
        this.promptInput.focus();
        this.promptInput.classList.add('!border-[#10b981]');

        clearTimeout(this.#highlightTimeout);
        this.#highlightTimeout = setTimeout(() => {
            this.promptInput.classList.remove('!border-[#10b981]');
            this.#highlightTimeout = null;
        }, 1000);
    }

    clearFocus() {
        this.promptInput.blur();
        this.promptInput.classList.remove('!border-[#10b981]');

        clearTimeout(this.#highlightTimeout);
        this.#highlightTimeout = null;
    }

    setDisabled(disabled) {
        this.promptInput.disabled = disabled;
        this.sendBtn.disabled = disabled;
    }
}

register('input-box', InputBox);