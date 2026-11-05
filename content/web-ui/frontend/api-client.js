export class ApiClient {
    async #post(endpoint, options = {}) {
        const response = await fetch(endpoint, {
            method: 'POST',
            ...options
        });

        const responseText = await response.text();

        if (!response.ok) throw new Error(responseText || response.statusText);

        return responseText;
    }

    async getTestPrompt() {
        const response = await fetch('/api/test-prompt');
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    }

    async getPrompt() {
        const response = await fetch('/api/prompt');
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    }

    async switchDesktopMode() { return this.#post('/api/desktop-mode'); }

    async switchInferenceMode() { return this.#post('/api/inference-mode'); }

    async streamChatCompletion({ messages, onToken, onReasoning } = {}) {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages,
                stream: true
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