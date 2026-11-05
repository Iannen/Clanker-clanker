//All components inherit BaseComponent directly or transitively
export class BaseComponent extends HTMLElement {
    initialized = false;
    connectedCallback() {
        if (this.className) this.setAttribute('class', this.className);
        if (this.html) {
            const template = document.createElement('template');
            template.innerHTML = this.html.trim();
            this.appendChild(template.content.cloneNode(true));
        }
        this.onConnect();
        this.initialized = true;
    }
    onConnect() {}
}

export function register(tagName, klass) { if (!customElements.get(tagName)) customElements.define(tagName, klass); }