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

    setSelected(action) {
        if (!this.hasMessages()) return false;
        if (action === 'focusFirst') this.selectMessage(this.#messages[0]);
        else if (action === 'focusLast') this.selectMessage(this.#messages.at(-1));
        return true;
    }

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

    getSelectedContent() {
        if (!this.#selectedMsg) return null;
        return this.#selectedMsg.content || null;
    }

    async copySelected() {
        if (!this.#selectedMsg) return { success: false, reason: 'nothing-selected' };

        const rawText = this.#selectedMsg.content;
        if (!rawText) return { success: false, reason: 'empty-content' };

        try {
            await navigator.clipboard.writeText(rawText);
            return { success: true, counter: this.#selectedMsg.counter ?? 0 };
        } catch (error) {
            return { success: false, reason: 'clipboard-error', error };
        }
    }

    toggleReasoning() {
        if (this.#selectedMsg) {
            this.#selectedMsg.toggleReasoning();
        }
    }

    toggleContent() { if (this.#selectedMsg) this.#selectedMsg.toggleContent(); }

    setScrollLocked(locked = undefined) {
        if (locked === undefined) locked = !this.#scrollLocked;
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

        this.setScrollLocked(true);
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
        this.addEventListener('focusout', this.#handleFocusout);
        this.addEventListener('focusin', this.#handleUnlockScroll);
        this.addEventListener('wheel', this.#handleUnlockScroll);
        this.addEventListener('scroll', this.#handleScroll);
    }

    disconnectedCallback() {
        this.removeEventListener('keydown', this.#handleKeydown);
        this.removeEventListener('focusout', this.#handleFocusout);
        this.removeEventListener('focusin', this.#handleUnlockScroll);
        this.removeEventListener('wheel', this.#handleUnlockScroll);
        this.removeEventListener('scroll', this.#handleScroll);
    }

    #handleKeydown = (event) => {
        if (event.ctrlKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
            if (this.#messages.length === 0) return;
            event.stopPropagation();
            event.preventDefault();
            const moved = event.key === 'ArrowUp'
                ? this.selectPreviousMsg()
                : this.selectNextMsg();
            if (!moved) this.dispatchEvent(new CustomEvent('focus-input'));
            return;
        }

        if (event.key === 'Escape' && !event.ctrlKey && !event.altKey && !event.metaKey) {
            event.stopPropagation();
            event.preventDefault();
            this.dispatchEvent(new CustomEvent('focus-input'));
            return;
        }

        if (event.ctrlKey || event.altKey || event.metaKey) return;

        if (this.#messages.length === 0) return;

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

    #handleFocusout = (event) => {
        if (!this.contains(event.relatedTarget)) {
            if (this.#selectedMsg) this.#selectedMsg.setSelected(false);
            const last = this.#messages.at(-1);
            if (last) {
                this.#selectedMsg = last;
                last.setSelected(true);
            }
        }
    };

    #handleUnlockScroll = () => {
        this.setScrollLocked(false);
    };

    #handleScroll = () => {
        if (this.scrollTop + this.clientHeight >= this.scrollHeight) {
            this.setScrollLocked(true);
        }
    };

    #addMessage(message) {
        this.appendChild(message);
        this.#messages.push(message);
    }
}

register('messages-box', MessagesBox);