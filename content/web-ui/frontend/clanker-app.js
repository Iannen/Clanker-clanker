import { BaseComponent, register } from './base-component.js';
import { apiClient } from './api-client.js';
import './toast.js';
import './messages-box.js';
import './input-box.js';
import './sidepanel-left.js';
import './sidepanel-right.js';

const html = `
    <sidepanel-left></sidepanel-left>
    <div class="flex flex-col h-screen overflow-hidden">
        <messages-box></messages-box>
        <input-box></input-box>
    </div>
    <sidepanel-right></sidepanel-right>
    <toast-notification></toast-notification>
`;

const className = 'flex flex-col h-screen overflow-hidden antialiased lg:grid lg:grid-cols-[260px_1fr_260px] bg-[#030712] text-[#f3f4f6] font-sans';

class ClankerApp extends BaseComponent {
    html = html;
    className = className;

    #selectedElement;

    #inputActions = {
        'Enter': () => this.#submitInput(),
        'Ctrl+ArrowUp': () => this.#selectMessages('focusLast'),
        'Ctrl+ArrowDown': () => this.#selectMessages('focusFirst'),
        'Ctrl+Enter': () => this.#copySelected(),
        'Ctrl+1': () => this.messagesBox.toggleReasoning(),
        'Ctrl+2': () => this.messagesBox.toggleContent(),
        'Ctrl+y': () => this.#pullRealPrompt(),
        'Ctrl+i': () => this.#pullTestPrompt(),
        'Escape': () => this.messagesBox.toggleScrollLock(),
    };

    #messageActions = {
        'Ctrl+ArrowUp': () => this.#navMessages('up'),
        'Ctrl+ArrowDown': () => this.#navMessages('down'),
        'Ctrl+Enter': () => this.#copySelected(),
        'Ctrl+1': () => this.messagesBox.toggleReasoning(),
        'Ctrl+2': () => this.messagesBox.toggleContent(),
        'Escape': () => this.#focusInput(),
    };

    #handleGlobalKeydown = (event) => {
        if (event.shiftKey) return;

        const actions = this.#selectedElement === this.inputBox
            ? this.#inputActions
            : this.#messageActions;

        const combo = event.ctrlKey ? 'Ctrl+' + event.key : event.key;
        const handler = actions[combo];

        if (!handler) return;

        event.preventDefault();
        handler();
    };

    onConnect() {
        this.inputBox = this.querySelector('input-box');
        this.messagesBox = this.querySelector('messages-box');
        this.toast = this.querySelector('toast-notification');

        this.#selectedElement = this.inputBox;

        this.inputBox.addEventListener('submit', (e) => {
            this.#generateResponse(e.detail);
        });

        document.addEventListener('keydown', this.#handleGlobalKeydown);
    }

    #submitInput() {
        const prompt = this.inputBox.getValue();
        if (!prompt) return;

        this.inputBox.clear();
        this.#generateResponse(prompt);
    }

    async #pullRealPrompt() {
        this.inputBox.setDisabled(true);
        try {
            const prompt = await apiClient.getPrompt();
            this.#generateResponse(prompt);
        } catch (error) {
            this.inputBox.setDisabled(false);
            this.toast.show('❌ ' + (error.message || 'Failed to fetch real prompt'));
        }
    }

    async #pullTestPrompt() {
        this.inputBox.setDisabled(true);
        try {
            const prompt = await apiClient.getTestPrompt();
            this.#generateResponse(prompt);
        } catch (error) {
            this.inputBox.setDisabled(false);
            this.toast.show('❌ ' + (error.message || 'Failed to fetch test prompt'));
        }
    }

    #selectMessages(action) {
        if (!this.messagesBox.setSelected(action)) {
            this.toast.show('No messages yet');
            return;
        }
        this.#selectedElement = this.messagesBox;
        this.messagesBox.setScrollLocked(false);
    }

    #navMessages(dir) {
        const moved = dir === 'up'
            ? this.messagesBox.selectPreviousMsg()
            : this.messagesBox.selectNextMsg();

        if (!moved) this.#focusInput();
    }

    #focusInput() {
        this.messagesBox.selectLast();
        this.#selectedElement = this.inputBox;
        this.inputBox.focus();
    }

    async #copySelected() {
        const result = await this.messagesBox.copySelected();

        if (result.success) {
            this.toast.show(`📋 Copied message #${result.counter + 1} (raw markdown)!`);
        } else if (result.reason === 'no-messages') {
            this.toast.show('No messages yet');
        } else {
            this.toast.show('❌ Failed to copy to clipboard');
        }
    }

    async #generateResponse(prompt) {
        const userMsg = document.createElement('chat-message');
        userMsg.messageRole = 'user';
        userMsg.content = prompt;

        const assistantMsg = document.createElement('chat-message');
        assistantMsg.messageRole = 'assistant';

        this.messagesBox.addMessages(userMsg, assistantMsg);
        this.inputBox.setDisabled(true);

        try {
            const result = await apiClient.streamChatCompletion({
                messages: this.messagesBox.getHistory(),
                onToken: (token, fullText) => {
                    assistantMsg.updateContent(fullText);
                    this.messagesBox.scrollIfLocked();
                },
                onReasoning: (reasoningToken, reasoningText) => {
                    assistantMsg.updateReasoning(reasoningText);
                    this.messagesBox.scrollIfLocked();
                }
            });
            assistantMsg.setPerformanceTimings(result.timings);
        } catch (error) {
            assistantMsg.appendError(error.message);
        } finally {
            this.inputBox.setDisabled(false);
            if (this.#selectedElement === this.inputBox) this.inputBox.focus();
        }
    }
}

register('clanker-app', ClankerApp);