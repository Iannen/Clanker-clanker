import { BaseComponent, register } from './base-component.js';

const html = `
    <aside class="flex flex-col bg-[#111827] p-6 gap-4 overflow-y-auto border-l border-[#1f2937] w-full h-full">

        <div class="text-sm font-bold text-[#34d399] tracking-wider uppercase border-b border-[#1f2937] pb-2">
            Keyboard Shortcuts
        </div>

        <div class="flex flex-col gap-3 text-xs">

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Enter</div>
                <div class="text-[#9ca3af]">Send prompt message</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Ctrl + Enter</div>
                <div class="text-[#9ca3af]">Copy latest assistant response instantly</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Ctrl + ArrowUp / ArrowDown</div>
                <div class="text-[#9ca3af]">Navigate through messages and return to the input prompt</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Up / Down / PageUp / PageDown</div>
                <div class="text-[#9ca3af]">Scroll chat canvas smoothly when a message is selected</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Ctrl + C</div>
                <div class="text-[#9ca3af]">Copy currently selected message</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Escape</div>
                <div class="text-[#9ca3af]">Return focus to input prompt box</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Ctrl + Y</div>
                <div class="text-[#9ca3af]">Placeholder keybind</div>
            </div>

            <div class="bg-[#030712] p-3 rounded-lg border border-[#1f2937]/60">
                <div class="font-mono text-[#6ee7b7] font-bold mb-1">Ctrl + I</div>
                <div class="text-[#9ca3af]">Placeholder keybind</div>
            </div>

        </div>
    </aside>
`;

const className = 'hidden lg:flex flex-col';

class SidepanelRight extends BaseComponent {
    html = html;
    className = className;
}

register('sidepanel-right', SidepanelRight);