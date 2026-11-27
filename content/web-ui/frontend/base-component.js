export class BaseComponent extends HTMLElement {
    initialized = false;

    refs = {};
    listeners = [];

    #_trackedListeners = [];

    connectedCallback() {
        if (this.className) this.setAttribute('class', this.className);
        if (this.html) {
            const template = document.createElement('template');
            template.innerHTML = this.html.trim();
            this.appendChild(template.content.cloneNode(true));
        }

        for (const [propName, selector] of Object.entries(this.refs)) {
            this[propName] = this.querySelector(selector);
        }

        for (const { target, event, handler } of this.listeners) {
            const t = this.#resolveTarget(target);
            t.addEventListener(event, handler);
        }

        this.setup();
        this.onConnect();
        this.initialized = true;
    }

    disconnectedCallback() {
        for (const { target, event, handler } of this.listeners) {
            const t = this.#resolveTarget(target);
            t.removeEventListener(event, handler);
        }
        for (const { target, event, handler } of this.#_trackedListeners) {
            const t = this.#resolveTarget(target);
            t.removeEventListener(event, handler);
        }
    }

    setup() {}
    onConnect() {}

    addListener(target, event, handler) {
        const t = this.#resolveTarget(target);
        t.addEventListener(event, handler);
        this.#_trackedListeners.push({ target, event, handler });
    }

    #resolveTarget(target) {
        if (typeof target !== 'string') return target;
        if (target === 'self') return this;
        if (target === 'document') return document;
        return this[target];
    }
}

export function register(tagName, klass) { if (!customElements.get(tagName)) customElements.define(tagName, klass); }