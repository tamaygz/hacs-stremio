/**
 * Stremio Stream Dialog
 * 
 * Modal dialog to display available streams for a media item
 * with clipboard copy functionality.
 * 
 * @customElement stremio-stream-dialog
 * @extends LitElement
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
      appleTvEntity: { type: String },
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
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
        line-height: 1.3;
      }

      .stream-meta {
        font-size: 0.8em;
        color: var(--secondary-text-color);
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        align-items: center;
      }

      .stream-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        background: var(--card-background-color);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
        white-space: nowrap;
      }

      .stream-meta-item ha-icon {
        --mdc-icon-size: 12px;
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

    // Use configured entity or fallback to hardcoded default
    const deviceId = this.appleTvEntity || 'media_player.apple_tv';
    
    this.hass.callService('stremio', 'handover_to_apple_tv', {
      device_id: deviceId,
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

  /**
   * Get stream metadata, using pre-parsed data from backend if available.
   * Falls back to client-side parsing for backward compatibility.
   */
  _getStreamMetadata(stream) {
    // Use pre-parsed metadata from stremio_client if available
    if (stream.parsed_metadata) {
      return stream.parsed_metadata;
    }
    
    // Fallback: parse client-side for backward compatibility
    return this._parseStreamMetadataFallback(stream);
  }

  /**
   * Fallback client-side parsing for streams without pre-parsed metadata.
   * This mirrors the logic in stremio_client.py parse_stream_metadata().
   */
  _parseStreamMetadataFallback(stream) {
    const metadata = {
      addon: null,
      size: null,
      seeders: null,
      codec: null,
      hdr: null,
      audio: null,
    };
    
    // Get addon name
    metadata.addon = stream.addon || stream.source || null;
    
    // Combine name and title for parsing
    const text = `${stream.name || ''} ${stream.title || ''}`;
    
    // Extract file size (e.g., "1.5 GB", "15.2GB", "800 MB")
    const sizeMatch = text.match(/(\d+(?:\.\d+)?)\s*(GB|MB|TB)/i);
    if (sizeMatch) {
      metadata.size = `${sizeMatch[1]} ${sizeMatch[2].toUpperCase()}`;
    }
    
    // Extract seeders (e.g., "👤 150", "S: 45", "seeders: 100")
    const seedersMatch = text.match(/(?:👤|⬆️|seeders?[:\s]*|S[:\s]*)(\d+)/i);
    if (seedersMatch) {
      metadata.seeders = seedersMatch[1];
    }
    
    // Extract video codec
    if (/\b(HEVC|H\.?265|x265)\b/i.test(text)) {
      metadata.codec = 'HEVC';
    } else if (/\b(AVC|H\.?264|x264)\b/i.test(text)) {
      metadata.codec = 'x264';
    } else if (/\bAV1\b/i.test(text)) {
      metadata.codec = 'AV1';
    }
    
    // Extract HDR type
    if (/\b(Dolby.?Vision|DV)\b/i.test(text)) {
      metadata.hdr = 'DV';
    } else if (/\bHDR10\+/i.test(text)) {
      metadata.hdr = 'HDR10+';
    } else if (/\bHDR10?\b/i.test(text)) {
      metadata.hdr = 'HDR';
    }
    
    // Extract audio format
    if (/\b(Atmos)\b/i.test(text)) {
      metadata.audio = 'Atmos';
    } else if (/\b(DTS[-:]?X)\b/i.test(text)) {
      metadata.audio = 'DTS-X';
    } else if (/\b(TrueHD)\b/i.test(text)) {
      metadata.audio = 'TrueHD';
    } else if (/\b(DTS[-:]?HD)\b/i.test(text)) {
      metadata.audio = 'DTS-HD';
    }
    
    return metadata;
  }

  _renderStreamItem(stream, index) {
    const isCopied = this._copiedIndex === index;
    const streamName = stream.name || stream.title || `Stream ${index + 1}`;
    const meta = this._getStreamMetadata(stream);

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
            ${meta.addon ? html`
              <span class="stream-meta-item">
                <ha-icon icon="mdi:puzzle"></ha-icon>
                ${meta.addon}
              </span>
            ` : ''}
            ${meta.size ? html`
              <span class="stream-meta-item">
                <ha-icon icon="mdi:file"></ha-icon>
                ${meta.size}
              </span>
            ` : ''}
            ${meta.seeders ? html`
              <span class="stream-meta-item">
                <ha-icon icon="mdi:account-group"></ha-icon>
                ${meta.seeders}
              </span>
            ` : ''}
            ${meta.codec ? html`
              <span class="stream-meta-item">${meta.codec}</span>
            ` : ''}
            ${meta.hdr ? html`
              <span class="stream-meta-item">${meta.hdr}</span>
            ` : ''}
            ${meta.audio ? html`
              <span class="stream-meta-item">${meta.audio}</span>
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
  show(hass, mediaItem, streams, appleTvEntity) {
    let dialog = document.querySelector('stremio-stream-dialog');
    if (!dialog) {
      dialog = document.createElement('stremio-stream-dialog');
      document.body.appendChild(dialog);
    }
    dialog.hass = hass;
    dialog.mediaItem = mediaItem;
    dialog.streams = streams || [];
    dialog.appleTvEntity = appleTvEntity;
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
