/**
 * Stremio Stream Dialog
 * 
 * Modal dialog to display available streams for a media item
 * with clipboard copy functionality.
 * 
 * @customElement stremio-stream-dialog
 * @extends LitElement
 * @version 0.3.1
 * @cacheBust 20260118
 */

// Safe LitElement access - wait for HA frontend to be ready
const loadCardHelpers = async () => {
  if (customElements.get("ha-panel-lovelace")) {
    return {
      LitElement: Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),
      html: Object.getPrototypeOf(customElements.get("ha-panel-lovelace")).prototype.html,
      css: Object.getPrototypeOf(customElements.get("ha-panel-lovelace")).prototype.css,
    };
  }
  
  await customElements.whenDefined("ha-panel-lovelace");
  const Lit = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
  return { LitElement: Lit, html: Lit.prototype.html, css: Lit.prototype.css };
};

const { LitElement, html, css } = await loadCardHelpers();

class StremioStreamDialog extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      open: { type: Boolean },
      mediaItem: { type: Object },
      streams: { type: Array },
      _loading: { type: Boolean },
      _copiedIndex: { type: Number },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      .overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
      }

      .overlay.open {
        opacity: 1;
        visibility: visible;
      }

      .dialog {
        background: var(--card-background-color);
        border-radius: 12px;
        max-width: 500px;
        width: 95%;
        max-height: 80vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        transform: scale(0.9);
        transition: transform 0.3s ease;
      }

      .overlay.open .dialog {
        transform: scale(1);
      }

      .dialog-header {
        padding: 16px 20px;
        border-bottom: 1px solid var(--divider-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .dialog-header h3 {
        margin: 0;
        font-size: 1.1em;
        color: var(--primary-text-color);
      }

      .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .close-btn:hover {
        background: var(--secondary-background-color);
      }

      .close-btn ha-icon {
        color: var(--secondary-text-color);
      }

      .dialog-content {
        padding: 16px 20px;
        overflow-y: auto;
        flex: 1;
      }

      .stream-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .stream-item {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }

      .stream-info {
        flex: 1;
        min-width: 0;
      }

      .stream-name {
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .stream-meta {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .stream-meta span {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .stream-meta ha-icon {
        --mdc-icon-size: 14px;
      }

      .stream-actions {
        display: flex;
        gap: 8px;
      }

      .action-btn {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 0.85em;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s ease;
      }

      .action-btn:hover {
        filter: brightness(1.1);
      }

      .action-btn.secondary {
        background: var(--card-background-color);
        color: var(--primary-text-color);
        border: 1px solid var(--divider-color);
      }

      .action-btn.success {
        background: var(--success-color, #4caf50);
      }

      .action-btn ha-icon {
        --mdc-icon-size: 16px;
      }

      .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        color: var(--secondary-text-color);
      }

      .loading ha-circular-progress {
        margin-bottom: 16px;
      }

      .empty {
        text-align: center;
        padding: 40px;
        color: var(--secondary-text-color);
      }

      .empty ha-icon {
        --mdc-icon-size: 48px;
        margin-bottom: 12px;
        opacity: 0.5;
      }

      .quality-badge {
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: 500;
      }

      .quality-badge.hd {
        background: #2196f3;
      }

      .quality-badge.fhd {
        background: #4caf50;
      }

      .quality-badge.uhd {
        background: #9c27b0;
      }
    `;
  }

  constructor() {
    super();
    this.open = false;
    this.streams = [];
    this._loading = false;
    this._copiedIndex = -1;
    // Bind keyboard handler for cleanup
    this._handleKeyDown = this._handleKeyDown.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    document.addEventListener('keydown', this._handleKeyDown);
  }

  // Lifecycle: cleanup timers and event listeners when element is removed
  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('keydown', this._handleKeyDown);
    if (this._copiedTimeout) {
      clearTimeout(this._copiedTimeout);
    }
  }

  _handleKeyDown(e) {
    if (this.open && e.key === 'Escape') {
      this._close();
    }
  }

  async _copyToClipboard(url, index) {
    try {
      // Method 1: Modern clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(url);
        this._showCopied(index);
        return;
      }

      // Method 2: Fallback using execCommand
      const textArea = document.createElement('textarea');
      textArea.value = url;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      try {
        document.execCommand('copy');
        this._showCopied(index);
      } finally {
        document.body.removeChild(textArea);
      }
    } catch (err) {
      console.error('Failed to copy:', err);
      // Fallback: Fire event for HA to handle
      this._fireUrlEvent(url);
    }
  }

  _showCopied(index) {
    this._copiedIndex = index;
    // Store timeout ID for cleanup
    this._copiedTimeout = setTimeout(() => {
      this._copiedIndex = -1;
    }, 2000);
  }

  _fireUrlEvent(url) {
    // Fire event for HA to create notification or input_text
    const event = new CustomEvent('hass-notification', {
      bubbles: true,
      composed: true,
      detail: {
        message: `Stream URL: ${url}`,
        duration: 10000,
      },
    });
    this.dispatchEvent(event);

    // Also try to set input_text if available
    if (this.hass) {
      this.hass.callService('input_text', 'set_value', {
        entity_id: 'input_text.stremio_stream_url',
        value: url,
      }).catch(() => {
        // Input text might not exist, that's okay
      });
    }
  }

  _playOnAppleTv(stream) {
    if (!this.hass) return;

    // Show device selection or use default
    this.hass.callService('stremio', 'handover_to_apple_tv', {
      device_id: 'media_player.apple_tv', // User would configure this
      stream_url: stream.url,
    });
  }

  _getQualityClass(quality) {
    if (!quality) return '';
    const q = quality.toLowerCase();
    if (q.includes('2160') || q.includes('4k') || q.includes('uhd')) return 'uhd';
    if (q.includes('1080') || q.includes('fhd')) return 'fhd';
    if (q.includes('720') || q.includes('hd')) return 'hd';
    return '';
  }

  _close() {
    this.open = false;
    this.dispatchEvent(new CustomEvent('close'));
  }

  _handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      this._close();
    }
  }

  render() {
    return html`
      <div 
        class="overlay ${this.open ? 'open' : ''}" 
        @click=${this._handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="stream-dialog-title"
        aria-hidden="${!this.open}"
      >
        <div class="dialog">
          <div class="dialog-header">
            <h3 id="stream-dialog-title">
              ${this.mediaItem?.title || 'Available Streams'}
            </h3>
            <button 
              class="close-btn" 
              @click=${this._close}
              aria-label="Close dialog"
            >
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-content">
            ${this._loading ? this._renderLoading() : 
              this.streams.length > 0 ? this._renderStreams() : this._renderEmpty()}
          </div>
        </div>
      </div>
    `;
  }

  _renderLoading() {
    return html`
      <div class="loading">
        <ha-circular-progress active></ha-circular-progress>
        <div>Loading streams...</div>
      </div>
    `;
  }

  _renderEmpty() {
    return html`
      <div class="empty">
        <ha-icon icon="mdi:movie-off-outline"></ha-icon>
        <div>No streams available</div>
        <p>Try a different source or check your addons</p>
      </div>
    `;
  }

  _renderStreams() {
    return html`
      <div class="stream-list" role="list" aria-label="Available streams">
        ${this.streams.map((stream, index) => this._renderStreamItem(stream, index))}
      </div>
    `;
  }

  _renderStreamItem(stream, index) {
    const isCopied = this._copiedIndex === index;
    const streamName = stream.name || stream.title || `Stream ${index + 1}`;

    return html`
      <div class="stream-item" role="listitem">
        <div class="stream-info">
          <div class="stream-name">
            ${streamName}
            ${stream.quality ? html`
              <span class="quality-badge ${this._getQualityClass(stream.quality)}">
                ${stream.quality}
              </span>
            ` : ''}
          </div>
          <div class="stream-meta">
            ${stream.source ? html`
              <span>
                <ha-icon icon="mdi:server"></ha-icon>
                ${stream.source}
              </span>
            ` : ''}
            ${stream.size ? html`
              <span>
                <ha-icon icon="mdi:file"></ha-icon>
                ${stream.size}
              </span>
            ` : ''}
          </div>
        </div>

        <div class="stream-actions" role="group" aria-label="Stream actions">
          <button 
            class="action-btn secondary ${isCopied ? 'success' : ''}"
            @click=${() => this._copyToClipboard(stream.url, index)}
            aria-label="${isCopied ? 'Copied to clipboard' : `Copy ${streamName} URL to clipboard`}"
          >
            <ha-icon icon="${isCopied ? 'mdi:check' : 'mdi:content-copy'}"></ha-icon>
            ${isCopied ? 'Copied!' : 'Copy'}
          </button>
          <button 
            class="action-btn"
            @click=${() => this._playOnAppleTv(stream)}
            aria-label="Send ${streamName} to Apple TV"
          >
            <ha-icon icon="mdi:apple"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-stream-dialog')) {
  customElements.define('stremio-stream-dialog', StremioStreamDialog);
}

// Global helper to open the dialog
window.StremioStreamDialog = {
  show(hass, mediaItem, streams) {
    let dialog = document.querySelector('stremio-stream-dialog');
    if (!dialog) {
      dialog = document.createElement('stremio-stream-dialog');
      document.body.appendChild(dialog);
    }
    dialog.hass = hass;
    dialog.mediaItem = mediaItem;
    dialog.streams = streams || [];
    dialog.open = true;
    return dialog;
  },

  hide() {
    const dialog = document.querySelector('stremio-stream-dialog');
    if (dialog) {
      dialog.open = false;
    }
  },
};
