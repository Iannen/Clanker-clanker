import { BaseComponent, register } from './base-component.js';

const html = `<div class="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 pointer-events-none bg-emerald-600 text-white text-xs px-4 py-2 rounded-lg shadow-lg opacity-0 transition-opacity duration-300"></div>`;

class ToastNotification extends BaseComponent {
    html = html;

    #timeout = null;

    onConnect() { this.toastElement = this.querySelector('div'); }

    show(message) {
        this.toastElement.textContent = message;
        this.toastElement.classList.replace('opacity-0', 'opacity-100');

        clearTimeout(this.#timeout);
        this.#timeout = setTimeout(() => {
            this.toastElement.classList.replace('opacity-100', 'opacity-0');
        }, 2500);
    }
}

register('toast-notification', ToastNotification);