export class ApiClient {
    async #post(endpoint, options = {}) {
        const response = await fetch(endpoint, {
            method: 'POST',
            ...options
        });

        if (!response.ok) {
            const body = await response.json().catch(() => null);
            const msg = body?.error?.message ?? body?.error ?? response.statusText;
            throw new Error(msg);
        }

        return response.json();
    }

    async boot() {
        const response = await fetch('/api/boot');
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    }

    async renderPrompt(domain, prompt) {
        return this.#post('/api/render-prompt', {
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain, prompt })
        });
    }

    async ingestFileChanges(content) {
        const response = await fetch('/api/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });

        const data = await response.json().catch(() => null);

        return { status: response.status, data };
    }

    async switchDesktopMode() { return this.#post('/api/mode/desktop'); }

    async switchLlamaMode() { return this.#post('/api/mode/llama_cpp'); }

    async switchStrataMode() { return this.#post('/api/mode/strata'); }

    async streamChatCompletion({ messages, max_tokens, onToken, onReasoning, onPrefill } = {}) {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'qwen-47k',
                //model: 'CyberTiel-4',
                messages,
                stream: true,
                return_progress: true,
                ...(max_tokens !== undefined ? { max_tokens: max_tokens } : {})
            })
        });
        if (!response.ok) throw new Error('Server error: ' + response.statusText);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        const toDeltaString = (value) => {
            if (typeof value === 'string') return value;

            if (Array.isArray(value)) return value.filter(part => typeof part === 'string').join('');

            return '';
        };

        let buffer = '';
        let fullResponse = '';
        let fullReasoning = '';
        let timings = null;

        const processLine = (line) => {
            if (!line.startsWith('data: ')) return;

            const dataStr = line.replace('data: ', '').trim();

            if (dataStr === '[DONE]') return;

            try {
                const json = JSON.parse(dataStr);

                if (
                    json.timings &&
                    typeof json.timings === 'object'
                ) timings = json.timings;

                if (json.prompt_progress) {
                    onPrefill?.(json.prompt_progress);
                }

                const delta = json.choices?.[0]?.delta ?? {};

                const reasoningToken =
                    toDeltaString(delta.reasoning_content) ||
                    toDeltaString(delta.reasoning);

                if (reasoningToken) {
                    fullReasoning += reasoningToken;

                    if (typeof onReasoning === 'function') onReasoning(reasoningToken, fullReasoning);
                }

                const token = toDeltaString(delta.content);

                if (token) {
                    fullResponse += token;

                    if (typeof onToken === 'function') onToken(token, fullResponse);
                }
            } catch {}
        };

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, {
                stream: true
            });

            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                processLine(line);
            }
        }

        if (buffer) processLine(buffer);

        return {
            content: fullResponse,
            timings
        };
    }
}

export const apiClient = new ApiClient();