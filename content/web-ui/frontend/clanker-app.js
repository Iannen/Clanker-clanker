import { BaseComponent, register } from './base-component.js';
import { apiClient } from './api-client.js';
import './toast.js';
import './messages-box.js';
import './input-box.js';
import './keyboard-bar.js';
import './sidepanel-left.js';
import './sidepanel-right.js';

const html = `
    <sidepanel-left></sidepanel-left>
    <div class="flex flex-col h-screen overflow-hidden">
        <messages-box></messages-box>
        <keyboard-bar></keyboard-bar>
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
    #keyboardBar;

    #inputActions = {
        'Enter': () => this.#submitInput(),
        'Ctrl+ArrowUp': () => this.#selectMessages('focusLast'),
        'Ctrl+ArrowDown': () => this.#selectMessages('focusFirst'),
        'Ctrl+Enter': () => this.#copySelected(),
        'Ctrl+1': () => this.messagesBox.toggleReasoning(),
        'Ctrl+2': () => this.messagesBox.toggleContent(),
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

        // Global view toggles (independent of focus context)
        if (event.ctrlKey) {
            if (event.key === 'Y' || event.key === 'y') {
                event.preventDefault();
                this.#showKeyboardBar();
                return;
            }
            if (event.key === 'I' || event.key === 'i') {
                event.preventDefault();
                this.#showMessagesBox();
                return;
            }
        }

        const actions = this.#selectedElement === this.inputBox
            ? this.#inputActions
            : this.#messageActions;

        const combo = event.ctrlKey ? 'Ctrl+' + event.key : event.key;
        const handler = actions[combo];

        if (!handler) return;

        event.preventDefault();
        handler();
    };

    #showKeyboardBar() {
        this.messagesBox.classList.add('hidden');
        this.#keyboardBar.classList.remove('hidden');
        this.#keyboardBar.focus();
    }

    #showMessagesBox() {
        this.#keyboardBar.classList.add('hidden');
        this.messagesBox.classList.remove('hidden');
    }

    #onPromptReady(promptText) {
        this.#showMessagesBox();
        this.#generateResponse(promptText);
    }

    async onConnect() {
        this.inputBox = this.querySelector('input-box');
        this.messagesBox = this.querySelector('messages-box');
        this.#keyboardBar = this.querySelector('keyboard-bar');
        this.#keyboardBar.classList.add('hidden');
        this.toast = this.querySelector('toast-notification');

        this.#selectedElement = this.inputBox;

        this.inputBox.addEventListener('submit', (e) => {
            this.#generateResponse(e.detail);
        });

        this.#keyboardBar.addEventListener('prompt-ready', (e) => {
            this.#onPromptReady(e.detail);
        });

        await this.#bootSystem();

        document.addEventListener('keydown', this.#handleGlobalKeydown);
    }

    async #bootSystem() {
        this.inputBox.setDisabled(true);
        try {
            const msg = await apiClient.boot();
            this.inputBox.setDisabled(false);
            this.messagesBox.welcomeText.textContent = msg;
        } catch (error) {
            this.inputBox.setDisabled(false);
            this.toast.show('❌ ' + (error.message || 'Boot failed'));
        }
        this.inputBox.focus();
    }

    #submitInput() {
        const prompt = this.inputBox.getValue();
        if (!prompt) return;

        this.inputBox.clear();
        this.#generateResponse(prompt);
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