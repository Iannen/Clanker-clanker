import './message.js';
import { BaseComponent, register } from './base-component.js';

const html = `
    <div class="welcome-text text-[#6b7280] text-center italic mt-10">
        Type a prompt below to begin chatting...
    </div>
`;

const className = 'flex-1 overflow-y-auto p-6 flex flex-col gap-6 w-full';

class MessagesBox extends BaseComponent {
    html = html;
    className = className;

    #messages = [];
    #selectedMsg = null;
    #scrollLocked = true;

    hasMessages() { return this.#messages.length > 0; }

    getMessagesCount() { return this.#messages.length; }

    setSelected(action) {
        if (!this.hasMessages()) return false;
        if (action === 'focusFirst') this.selectFirst();
        else if (action === 'focusLast') this.selectLast();
        return true;
    }

    selectFirst() { this.selectMessage(this.#messages[0]); }

    selectLast() { this.selectMessage(this.#messages.at(-1)); }

    selectPreviousMsg() {
        const pos = this.#messages.indexOf(this.#selectedMsg);
        if (pos <= 0) return false;
        this.selectMessage(this.#messages[pos - 1]);
        return true;
    }

    selectNextMsg() {
        const pos = this.#messages.indexOf(this.#selectedMsg);
        if (pos >= this.#messages.length - 1) return false;
        this.selectMessage(this.#messages[pos + 1]);
        return true;
    }

    selectMessage(msg) {
        if (this.#selectedMsg) this.#selectedMsg.setSelected(false);
        this.#selectedMsg = msg;
        msg.setSelected(true);
        msg.focus();
        msg.scrollIntoView();
    }

    clearSelection() {
        if (this.#selectedMsg) this.#selectedMsg.setSelected(false);
        this.#selectedMsg = null;
    }

    getSelectedContent() {
        if (!this.#selectedMsg) return null;
        return this.#selectedMsg.content || null;
    }

    async copySelected() {
        if (!this.hasMessages()) return { success: false, reason: 'no-messages' };
        if (!this.#selectedMsg) return { success: false, reason: 'nothing-selected' };

        const rawText = this.#selectedMsg.content;
        if (!rawText) return { success: false, reason: 'empty-content' };

        try {
            await navigator.clipboard.writeText(rawText);
            return { success: true, counter: this.#selectedMsg.counter };
        } catch (error) {
            return { success: false, reason: 'clipboard-error', error };
        }
    }

    toggleReasoning() { if (this.#selectedMsg) this.#selectedMsg.toggleReasoning(); }

    toggleContent() { if (this.#selectedMsg) this.#selectedMsg.toggleContent(); }

    toggleScrollLock() {
        this.#scrollLocked = !this.#scrollLocked;
        if (this.#scrollLocked) this.scrollToBottom();
    }

    setScrollLocked(locked) {
        this.#scrollLocked = locked;
        if (locked) this.scrollToBottom();
    }

    scrollIfLocked() {
        if (this.#scrollLocked) this.scrollToBottom();
    }

    addMessages(userMsg, assistantMsg) {
        if (this.welcomeText) {
            this.welcomeText.remove();
            this.welcomeText = null;
        }

        const base = this.#messages.length;
        userMsg.counter = base;
        assistantMsg.counter = base + 1;

        this.#addMessage(userMsg);
        this.#addMessage(assistantMsg);

        if (this.#selectedMsg) this.#selectedMsg.setSelected(false);
        this.#selectedMsg = assistantMsg;
        assistantMsg.setSelected(true);

        if (this.#scrollLocked) this.scrollToBottom();
    }

    scrollToBottom() { this.scrollTop = this.scrollHeight; }

    getHistory() {
        return this.#messages
            .filter(message => !(message.messageRole === 'assistant' && message.content === ''))
            .map(message => ({ role: message.messageRole, content: message.content }));
    }

    onConnect() {
        this.welcomeText = this.querySelector('.welcome-text');
        this.addEventListener('keydown', this.#handleKeydown);
    }

    disconnectedCallback() {
        this.removeEventListener('keydown', this.#handleKeydown);
    }

    #handleKeydown = (event) => {
        if (this.#messages.length === 0) return;
        if (event.ctrlKey || event.altKey || event.metaKey) return;

        const scrollMap = {
            ArrowUp: -40,
            ArrowDown: 40,
            PageUp: -this.clientHeight * 0.75,
            PageDown: this.clientHeight * 0.75
        };

        const scrollAmount = scrollMap[event.key];
        if (scrollAmount === undefined) return;

        event.preventDefault();
        this.scrollBy({
            top: scrollAmount,
            behavior: event.repeat ? 'auto' : 'smooth'
        });
    };

    #addMessage(message) {
        this.appendChild(message);
        this.#messages.push(message);
    }
}

register('messages-box', MessagesBox);