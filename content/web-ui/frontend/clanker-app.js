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
        <keyboard-bar></keyboard-bar>    
        <messages-box></messages-box>
        <input-box></input-box>
    </div>
    <sidepanel-right></sidepanel-right>
    <toast-notification></toast-notification>
`;

const className = 'flex flex-col h-screen overflow-hidden antialiased lg:lg grid lg:grid-cols-[260px_1fr_260px] bg-[#030712] text-[#f3f4f6] font-sans';

class ClankerApp extends BaseComponent {
    html = html;
    className = className;

    refs = {
        inputBox: 'input-box',
        messagesBox: 'messages-box',
        keyboardBar: 'keyboard-bar',
        toast: 'toast-notification',
    };

    #handleGlobalKeydown = (event) => {
        if (event.shiftKey) return;

        if (event.ctrlKey && (event.key === 'I' || event.key === 'i')) {
            event.preventDefault();
            this.#toggleKeyboardBar();
            return;
        }

        if (event.ctrlKey && event.key === 'Enter') {
            event.preventDefault();
            this.#copySelected();
            return;
        }

        if (event.altKey && event.key === 'Enter') {
            event.preventDefault();
            this.#ingestSelected();
            return;
        }

        if (event.ctrlKey && event.key === '1') {
            event.preventDefault();
            this.messagesBox.toggleReasoning();
            return;
        }

        if (event.ctrlKey && event.key === '2') {
            event.preventDefault();
            this.messagesBox.toggleContent();
            return;
        }
    };

    listeners = [
        { target: 'inputBox', event: 'submit', handler: (e) => { this.#generateResponse(e.detail); } },
        { target: 'keyboardBar', event: 'prompt-selected', handler: () => {
            this.keyboardBar.setExpanded(false);
            this.messagesBox.classList.remove('hidden');
            this.inputBox.classList.remove('hidden');
            this.inputBox.focus();
        } },
        { target: 'keyboardBar', event: 'prompt-copied', handler: () => {
            this.toast.show('📋 Prompt copied to clipboard');
        } },
        { target: 'self', event: 'toggle-scroll-lock', handler: () => {
            this.messagesBox.setScrollLocked();
        } },
        { target: 'messagesBox', event: 'focus-input', handler: () => {
            this.inputBox.focus();
        } },
        { target: 'inputBox', event: 'focus-message', handler: (e) => {
            if (!this.messagesBox.hasMessages()) {
                this.toast.show('No messages yet');
                return;
            }
            const detail = e.detail;
            if (detail === 'first') {
                this.messagesBox.setSelected('focusFirst');
            } else if (detail === 'last') {
                this.messagesBox.setSelected('focusLast');
            }
        } },
        { target: 'document', event: 'keydown', handler: this.#handleGlobalKeydown },
    ];

    #toggleKeyboardBar() {
        if (this.keyboardBar.isExpanded()) {
            this.keyboardBar.setExpanded(false);
            this.messagesBox.classList.remove('hidden');
            this.inputBox.classList.remove('hidden');
            this.inputBox.focus();
        } else {
            this.keyboardBar.setExpanded(true);
            this.messagesBox.classList.add('hidden');
            this.inputBox.classList.add('hidden');
            this.keyboardBar.focus();
        }
    }
    // can the keyboardbar not initialize with this value to false? why must we set it?
    setup() {
        this.keyboardBar.setExpanded(false);
    }

    async onConnect() {
        await this.#bootSystem();
    }

    async #bootSystem() {
        this.inputBox.setDisabled(true);
        try {
            const boot = await apiClient.boot();

            if (boot.type === 'terminate') {
                const crits = boot.report?.critical_complaints?.length || 0;
                this.toast.show('❌ Boot failed: ' + crits + ' critical complaint(s)');
            } else if (boot.type === 'clankerize') {
                this.toast.show('⚠️ Workspace needs clankerization');
            } else {
                this.keyboardBar.setDomains(boot.shared_domains, boot.pud_domains);
                this.messagesBox.welcomeText.textContent = "Bootstrap completed successfully";
            }
        } catch (error) {
            this.toast.show('❌ ' + (error.message || 'Boot failed'));
        }
        this.inputBox.setDisabled(false);
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

    async #ingestContent(content, { silentEmpty = false } = {}) {
        if (!content) return null;

        try {
            const { status, data } = await apiClient.ingestFileChanges(content);

            if (status === 500) {
                this.toast.show('❌ Server error: ' + (data?.error || 'Ingest failed'));
                return null;
            }

            if (status === 400) {
                const parts = [];
                if (data.parse_errors?.length) parts.push(`parse errors (${data.parse_errors.length})`);
                if (data.missing_paths?.length) parts.push(`missing: ${data.missing_paths.join(', ')}`);
                if (data.unexpected_paths?.length) parts.push(`unexpected: ${data.unexpected_paths.join(', ')}`);
                this.toast.show('❌ ' + parts.join(' · '));
                return null;
            }

            const parts = [];
            if (data.created?.length) parts.push(`${data.created.length} created`);
            if (data.updated?.length) parts.push(`${data.updated.length} updated`);
            if (data.deleted?.length) parts.push(`${data.deleted.length} deleted`);

            if (parts.length === 0 && silentEmpty) {
                // suppress empty toast to avoid noise on auto-ingest
            } else {
                this.toast.show('✅ ' + (parts.join(', ') || 'No changes applied'));
            }

            return data;
        } catch (error) {
            this.toast.show('❌ ' + (error.message || 'Ingest failed'));
            return null;
        }
    }

    async #ingestSelected() {
        const content = this.messagesBox.getSelectedContent();
        if (!content) {
            this.toast.show('No message selected to ingest');
            return;
        }

        const data = await this.#ingestContent(content);
        if (data?.expanded?.length) {
            await this.keyboardBar.expandPaths(data.expanded);
        }
    }

    async #generateResponse(prompt) {
        let userMsg = document.createElement('chat-message');
        userMsg.messageRole = 'user';
        userMsg.content = prompt;
        let assistantMsg;
        try {
            while (true) {
                assistantMsg = document.createElement('chat-message');
                assistantMsg.messageRole = 'assistant';

                this.messagesBox.addMessages(userMsg, assistantMsg);
                this.inputBox.setDisabled(true);
                let prevContent = '';
                let prevReasoning = '';
                const fullHistory = [...this.keyboardBar.getMsgs(), ...this.messagesBox.getHistory()];
                const totalChars = fullHistory.reduce((sum, m) => sum + (m.content?.length ?? 0), 0);
                assistantMsg.sentChars = totalChars;

                let reasoningSnapshot = '';

                const result = await apiClient.streamChatCompletion({
                    messages: fullHistory,
                    onToken: (token, fullText) => {
                        assistantMsg.content = prevContent + fullText;
                        this.messagesBox.scrollIfLocked();
                    },
                    onReasoning: (reasoningToken, reasoningText) => {
                        reasoningSnapshot = reasoningText;
                        assistantMsg.updateReasoning(prevReasoning + reasoningText);
                        this.messagesBox.scrollIfLocked();
                    },
                    onPrefill: (pp) => assistantMsg.onPrefill(pp),
                });
                assistantMsg.setPerformanceTimings(result.timings);

                prevContent = assistantMsg.content;
                prevReasoning += reasoningSnapshot;

                const data = await this.#ingestContent(prevContent, { silentEmpty: true });

                if (!data?.expanded?.length) break;
                const grew = await this.keyboardBar.expandPaths(data.expanded);
                if (!grew) break;

                userMsg = document.createElement('chat-message');
                userMsg.messageRole = 'user';
                userMsg.content = '[The actions have been carried out]';
            }
        } catch (error) {
            assistantMsg.appendError(error.message);
        } finally {
            this.inputBox.setDisabled(false);
        }
    }
}

register('clanker-app', ClankerApp);