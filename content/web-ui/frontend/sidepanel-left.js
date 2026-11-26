import { BaseComponent, register } from './base-component.js';
import { apiClient } from './api-client.js';

const html = `
    <aside class="flex flex-col bg-[#111827] p-6 gap-4 overflow-y-auto border-r border-[#1f2937] w-full h-full">

        <div class="text-sm font-bold text-[#34d399] tracking-wider uppercase border-b border-[#1f2937] pb-2">
            GPU Box Mode
        </div>

        <div class="flex flex-col gap-3">

            <button
                type="button"
                data-mode="desktop"
                class="w-full p-3 font-bold text-sm border-none rounded-lg cursor-pointer transition-colors text-white bg-[#dc2626] hover:bg-[#ef4444]"
            >
                🖥️ Desktop
            </button>

            <button
                type="button"
                data-mode="llama_cpp"
                class="w-full p-3 font-bold text-sm border-none rounded-lg cursor-pointer transition-colors text-white bg-[#059669] hover:bg-[#10b981]"
            >
                🤖 Llama
            </button>

            <button
                type="button"
                data-mode="strata"
                class="w-full p-3 font-bold text-sm border-none rounded-lg cursor-pointer transition-colors text-white bg-[#2563eb] hover:bg-[#3b82f6]"
            >
                🤖 Strata
            </button>

            <div
                id="status"
                role="status"
                aria-live="polite"
                class="mt-4 p-3 bg-[#030712] rounded-lg border border-[#1f2937]/60 text-xs text-[#9ca3af] font-mono text-center"
            >
                Ready
            </div>

        </div>
    </aside>
`;

const className = 'hidden lg:flex flex-col';

class SidepanelLeft extends BaseComponent {
    html = html;
    className = className;

    #modeActions = {
        'desktop': () => apiClient.switchDesktopMode(),
        'llama_cpp': () => apiClient.switchLlamaMode(),
        'strata': () => apiClient.switchStrataMode()
    };

    #statusLabels = {
        desktop: 'Desktop',
        llama: 'Llama',
        strata: 'Strata'
    };

    onConnect() {
        this.statusElement = this.querySelector('#status');

        this.querySelectorAll('[data-mode]').forEach(button => {
            button.addEventListener('click', () => {
                this.#switchMode(button.dataset.mode);
            });
        });
    }

    #setStatus(message) {
        this.statusElement.textContent = message;
    }

    async #switchMode(mode) {
        const action = this.#modeActions[mode];

        this.#setStatus('Switching...');

        try {
            const response = await action();
            this.#setStatus(this.#statusLabels[response.mode] ?? response.mode);
        } catch (error) {
            this.#setStatus(error.message || 'Error communicating with server.');
        }
    }

}

register('sidepanel-left', SidepanelLeft);