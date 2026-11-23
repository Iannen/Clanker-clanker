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

    #keyboardBar;

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

    #toggleKeyboardBar() {
        if (this.#keyboardBar.isExpanded()) {
            this.#keyboardBar.setExpanded(false);
            this.messagesBox.classList.remove('hidden');
            this.inputBox.classList.remove('hidden');
            this.inputBox.focus();
        } else {
            this.#keyboardBar.setExpanded(true);
            this.messagesBox.classList.add('hidden');
            this.inputBox.classList.add('hidden');
            this.#keyboardBar.focus();
        }
    }

    async onConnect() {
        this.inputBox = this.querySelector('input-box');
        this.messagesBox = this.querySelector('messages-box');
        this.#keyboardBar = this.querySelector('keyboard-bar');
        this.#keyboardBar.setExpanded(false);
        this.toast = this.querySelector('toast-notification');

        this.inputBox.addEventListener('submit', (e) => {
            this.#generateResponse(e.detail);
        });

        this.#keyboardBar.addEventListener('prompt-selected', () => {
            this.#keyboardBar.setExpanded(false);
            this.messagesBox.classList.remove('hidden');
            this.inputBox.classList.remove('hidden');
            this.inputBox.focus();
        });

        this.#keyboardBar.addEventListener('prompt-copied', () => {
            this.toast.show('📋 Prompt copied to clipboard');
        });

        this.addEventListener('toggle-scroll-lock', () => {
            this.messagesBox.toggleScrollLock();
        });

        this.messagesBox.addEventListener('focus-input', () => {
            this.inputBox.focus();
        });

        this.inputBox.addEventListener('focus-message', (e) => {
            if (!this.messagesBox.hasMessages()) {
                this.toast.show('No messages yet');
                return;
            }
            const detail = e.detail;
            if (detail === 'first') {
                this.messagesBox.selectFirst();
            } else if (detail === 'last') {
                this.messagesBox.selectLast();
            }
        });

        await this.#bootSystem();

        document.addEventListener('keydown', this.#handleGlobalKeydown);
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
                this.#keyboardBar.setDomains(boot.shared_domains, boot.pud_domains);
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
            if (!this.#keyboardBar.getRenderedPromptText()) {
                this.toast.show('❌ No prompt selected — cannot expand paths');
            } else {
                await this.#keyboardBar.expandPaths(data.expanded);
            }
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
                const history = this.messagesBox.getHistory();
                const renderedPrompt = this.#keyboardBar.getRenderedPromptText();
                if (renderedPrompt && history.length > 0) {
                    history[0].content = renderedPrompt + '\n\n' + history[0].content;
                }
                const totalChars = history.reduce((sum, m) => sum + (m.content?.length ?? 0), 0);
                if (!prevContent) {
                    assistantMsg.sentChars = totalChars;
                }

                let reasoningSnapshot = '';

                const result = await apiClient.streamChatCompletion({
                    messages: history,
                    onToken: (token, fullText) => {
                        assistantMsg.updateContent(prevContent + fullText);
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
                const grew = await this.#keyboardBar.expandPaths(data.expanded);
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