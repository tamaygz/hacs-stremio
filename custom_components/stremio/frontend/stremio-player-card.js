/**
 * Stremio Player Card
 * 
 * Displays current Stremio playback with media poster, title, and progress.
 * 
 * @customElement stremio-player-card
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

class StremioPlayerCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _mediaInfo: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      ha-card {
        overflow: hidden;
        position: relative;
      }

      .card-content {
        padding: 16px;
      }

      .player-container {
        display: flex;
        gap: 16px;
      }

      .poster {
        width: 120px;
        height: 180px;
        object-fit: cover;
        border-radius: 8px;
        background: var(--secondary-background-color);
        flex-shrink: 0;
      }

      .poster-placeholder {
        width: 120px;
        height: 180px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .poster-placeholder ha-icon {
        --mdc-icon-size: 48px;
        color: var(--secondary-text-color);
      }

      .info {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-width: 0;
      }

      .title {
        font-size: 1.2em;
        font-weight: 500;
        color: var(--primary-text-color);
        margin: 0 0 4px 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .subtitle {
        font-size: 0.9em;
        color: var(--secondary-text-color);
        margin: 0 0 8px 0;
      }

      .meta {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        margin: 0 0 12px 0;
      }

      .progress-container {
        margin-top: auto;
      }

      .progress-bar {
        height: 4px;
        background: var(--secondary-background-color);
        border-radius: 2px;
        overflow: hidden;
        margin-bottom: 4px;
      }

      .progress-fill {
        height: 100%;
        background: var(--primary-color);
        border-radius: 2px;
        transition: width 0.3s ease;
      }

      .progress-text {
        font-size: 0.75em;
        color: var(--secondary-text-color);
        display: flex;
        justify-content: space-between;
      }

      .state-idle {
        text-align: center;
        padding: 32px 16px;
        color: var(--secondary-text-color);
      }

      .state-idle ha-icon {
        --mdc-icon-size: 48px;
        margin-bottom: 8px;
        opacity: 0.5;
      }

      .actions {
        display: flex;
        gap: 8px;
        margin-top: 12px;
      }

      .action-button {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: background 0.2s ease;
      }

      .action-button:hover {
        background: var(--primary-color);
        filter: brightness(1.1);
      }

      .action-button.secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
      }

      .status-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: var(--success-color, #4caf50);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: 500;
      }

      .status-badge.idle {
        background: var(--secondary-text-color);
      }
    `;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this.config = {
      // Display options
      name: 'Stremio Player',
      show_poster: true,
      show_progress: true,
      show_actions: true,
      show_browse_button: false,
      show_backdrop: false, // Background blur effect
      
      // Layout options
      compact_mode: false, // Smaller card layout
      
      // Device integration
      apple_tv_entity: undefined, // For Apple TV handover
      
      ...config,
    };
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Only update if entity state actually changed
    if (this.config?.entity) {
      const oldState = oldHass?.states?.[this.config.entity];
      const newState = hass?.states?.[this.config.entity];
      
      if (oldState !== newState) {
        this._updateMediaInfo();
        this.requestUpdate();
      }
    }
  }

  get hass() {
    return this._hass;
  }

  // Optimize re-renders - only update when relevant properties change
  shouldUpdate(changedProps) {
    if (changedProps.has('config')) {
      return true;
    }
    if (changedProps.has('_mediaInfo')) {
      return true;
    }
    // hass changes are handled in the setter
    return false;
  }

  _updateMediaInfo() {
    if (!this._hass || !this.config.entity) {
      this._mediaInfo = null;
      return;
    }

    const entity = this._hass.states[this.config.entity];
    if (!entity) {
      this._mediaInfo = null;
      return;
    }

    const attrs = entity.attributes;
    this._mediaInfo = {
      state: entity.state,
      title: attrs.media_title || attrs.friendly_name || 'Unknown',
      type: attrs.type || attrs.media_content_type,
      season: attrs.season,
      episode: attrs.episode,
      year: attrs.year,
      poster: attrs.entity_picture || attrs.poster || attrs.media_image_url,
      progress: attrs.progress_percent || 0,
      position: attrs.media_position || 0,
      duration: attrs.media_duration || 0,
      imdb_id: attrs.imdb_id,
    };
  }

  _formatTime(seconds) {
    if (!seconds || seconds <= 0) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  _getSubtitle() {
    if (!this._mediaInfo) return '';
    const parts = [];
    if (this._mediaInfo.type) {
      parts.push(this._mediaInfo.type === 'series' ? 'TV Series' : 'Movie');
    }
    if (this._mediaInfo.season && this._mediaInfo.episode) {
      parts.push(`S${this._mediaInfo.season}E${this._mediaInfo.episode}`);
    }
    if (this._mediaInfo.year) {
      parts.push(this._mediaInfo.year);
    }
    return parts.join(' • ');
  }

  _openInStremio() {
    if (!this._mediaInfo?.imdb_id) return;
    const type = this._mediaInfo.type === 'series' ? 'series' : 'movie';
    const url = `stremio://detail/${type}/${this._mediaInfo.imdb_id}`;
    window.open(url, '_blank');
  }

  _openBrowse() {
    // Fire event to navigate to browse view or open browse card
    this.dispatchEvent(
      new CustomEvent('stremio-browse-requested', {
        bubbles: true,
        composed: true,
        detail: {},
      })
    );

    // Alternative: Navigate to media browser
    if (this._hass) {
      const hass = this._hass;
      
      // Check if browser_mod.navigate service is available
      const hasBrowserMod =
        hass.services &&
        hass.services.browser_mod &&
        hass.services.browser_mod.navigate;

      if (hasBrowserMod) {
        hass.callService('browser_mod', 'navigate', {
          path: '/media-browser/media-source%3A%2F%2Fstremio%2Fcatalogs',
        }).catch((error) => {
          console.warn('Stremio Player: browser_mod navigation failed:', error);
          // Try to show notification about manual access
          if (hass.services && hass.services.persistent_notification && hass.services.persistent_notification.create) {
            hass.callService('persistent_notification', 'create', {
              title: 'Stremio Player',
              message: 'Could not automatically open the catalog browser. Access it via Media Browser in the sidebar.',
            }).catch(err => console.error('Failed to create notification:', err));
          }
        });
      } else {
        // browser_mod not available, provide user feedback
        console.warn('Stremio Player: browser_mod is not available for navigation.');
        if (hass.services && hass.services.persistent_notification && hass.services.persistent_notification.create) {
          hass.callService('persistent_notification', 'create', {
            title: 'Stremio Player',
            message: 'The browser_mod integration is required for automatic navigation. Please install it or access the catalog via Media Browser in the sidebar.',
          }).catch(err => console.error('Failed to create notification:', err));
        }
      }
    }
  }

  _fireHassEvent(action) {
    this.dispatchEvent(
      new CustomEvent('hass-action', {
        bubbles: true,
        composed: true,
        detail: { action },
      })
    );
  }

  render() {
    try {
      if (!this._hass) {
        return html`<ha-card><div class="card-content">Loading...</div></ha-card>`;
      }

      const isPlaying = this._mediaInfo?.state === 'playing';
      const hasMedia = this._mediaInfo && this._mediaInfo.state !== 'idle' && this._mediaInfo.state !== 'unavailable';

      return html`
        <ha-card>
          ${hasMedia ? html`
            <span class="status-badge" role="status" aria-live="polite">${isPlaying ? 'Playing' : 'Paused'}</span>
          ` : html`
            <span class="status-badge idle" role="status">Idle</span>
          `}
          
          <div class="card-content">
            ${hasMedia ? this._renderPlaying() : this._renderIdle()}
          </div>
        </ha-card>
      `;
    } catch (error) {
      console.error('Stremio Player Card render error:', error);
      return html`
        <ha-card>
          <div class="card-content" style="color: var(--error-color);">
            <ha-icon icon="mdi:alert"></ha-icon>
            Error rendering card: ${error.message}
          </div>
        </ha-card>
      `;
    }
  }

  _renderIdle() {
    return html`
      <div class="state-idle">
        <ha-icon icon="mdi:television-off"></ha-icon>
        <div>Nothing playing</div>
        ${this.config.show_browse_button ? html`
          <button 
            class="action-button" 
            @click="${() => this._openBrowse()}"
            aria-label="Browse Stremio catalog"
            style="margin-top: 16px;"
          >
            <ha-icon icon="mdi:compass"></ha-icon>
            Browse Content
          </button>
        ` : ''}
      </div>
    `;
  }

  _renderPlaying() {
    const m = this._mediaInfo;
    return html`
      <div class="player-container">
        ${this.config.show_poster ? html`
          ${m.poster ? html`
            <img class="poster" src="${m.poster}" alt="${m.title}" />
          ` : html`
            <div class="poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
        ` : ''}
        
        <div class="info">
          <div>
            <h3 class="title">${m.title}</h3>
            <p class="subtitle">${this._getSubtitle()}</p>
          </div>

          ${this.config.show_progress ? html`
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${m.progress}%"></div>
              </div>
              <div class="progress-text">
                <span>${this._formatTime(m.position)}</span>
                <span>${m.progress.toFixed(0)}%</span>
                <span>${this._formatTime(m.duration)}</span>
              </div>
            </div>
          ` : ''}

          ${this.config.show_actions ? html`
            <div class="actions" role="group" aria-label="Media actions">
              <button 
                class="action-button" 
                @click="${this._openInStremio}"
                aria-label="Open ${m.title} in Stremio app"
              >
                <ha-icon icon="mdi:open-in-new"></ha-icon>
                Open in Stremio
              </button>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  getCardSize() {
    return 3;
  }

  // Grid sizing for sections view (HA 2024.8+)
  getGridOptions() {
    return {
      rows: 3,
      columns: 6,
      min_rows: 2,
      min_columns: 3,
    };
  }

  static getConfigElement() {
    return document.createElement('stremio-player-card-editor');
  }

  static getStubConfig() {
    return {
      entity: 'media_player.stremio',
      show_poster: true,
      show_progress: true,
      show_actions: true,
      show_browse_button: false,
      show_backdrop: false,
      compact_mode: false,
    };
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-player-card')) {
  customElements.define('stremio-player-card', StremioPlayerCard);
}

// Editor for visual configuration
class StremioPlayerCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
      _expandedSections: { type: Object },
    };
  }

  constructor() {
    super();
    this._expandedSections = {
      entity: true,
      display: false,
      device: false,
    };
  }

  setConfig(config) {
    this._config = config;
  }

  _toggleSection(section) {
    this._expandedSections = {
      ...this._expandedSections,
      [section]: !this._expandedSections[section],
    };
  }

  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      <div class="card-config">
        <!-- Entity Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('entity')}>
            <ha-icon icon="mdi:link-variant"></ha-icon>
            <span>Entity</span>
            <ha-icon class="expand-icon ${this._expandedSections.entity ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.entity ? html`
            <div class="section-content">
              <p class="helper-text">Select the Stremio media player entity.</p>
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this._config.entity || ''}
                .configValue=${'entity'}
                .includeDomains=${['media_player', 'sensor']}
                @value-changed=${this._valueChanged}
                allow-custom-entity
              ></ha-entity-picker>
            </div>
          ` : ''}
        </div>

        <!-- Display Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('display')}>
            <ha-icon icon="mdi:palette"></ha-icon>
            <span>Display Options</span>
            <ha-icon class="expand-icon ${this._expandedSections.display ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.display ? html`
            <div class="section-content">
              <div class="toggle-group">
                <ha-formfield label="Show Poster">
                  <ha-switch
                    .checked=${this._config.show_poster !== false}
                    .configValue=${'show_poster'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Progress Bar">
                  <ha-switch
                    .checked=${this._config.show_progress !== false}
                    .configValue=${'show_progress'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Action Buttons">
                  <ha-switch
                    .checked=${this._config.show_actions !== false}
                    .configValue=${'show_actions'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Browse Button">
                  <ha-switch
                    .checked=${this._config.show_browse_button === true}
                    .configValue=${'show_browse_button'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Backdrop Effect">
                  <ha-switch
                    .checked=${this._config.show_backdrop === true}
                    .configValue=${'show_backdrop'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Compact Mode">
                  <ha-switch
                    .checked=${this._config.compact_mode === true}
                    .configValue=${'compact_mode'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Device Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('device')}>
            <ha-icon icon="mdi:devices"></ha-icon>
            <span>Device Integration</span>
            <ha-icon class="expand-icon ${this._expandedSections.device ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.device ? html`
            <div class="section-content">
              <p class="helper-text">Select an Apple TV to enable handover functionality.</p>
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this._config.apple_tv_entity || ''}
                .configValue=${'apple_tv_entity'}
                .includeDomains=${['media_player']}
                label="Apple TV Entity"
                allow-custom-entity
                @value-changed=${this._valueChanged}
              ></ha-entity-picker>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  _valueChanged(ev) {
    if (!this._config || !this.hass) return;

    const target = ev.target;
    const configValue = target.configValue;
    const value = target.checked !== undefined ? target.checked : ev.detail?.value;

    if (configValue) {
      this._config = { ...this._config, [configValue]: value };
      this.dispatchEvent(new CustomEvent('config-changed', {
        bubbles: true,
        composed: true,
        detail: { config: this._config },
      }));
    }
  }

  static get styles() {
    return css`
      .card-config {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 8px;
      }

      .config-section {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        overflow: hidden;
      }

      .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: var(--secondary-background-color);
        cursor: pointer;
        user-select: none;
      }

      .section-header:hover {
        background: var(--primary-background-color);
      }

      .section-header span {
        flex: 1;
        font-weight: 500;
      }

      .expand-icon {
        transition: transform 0.2s;
      }

      .expand-icon.expanded {
        transform: rotate(180deg);
      }

      .section-content {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px;
      }

      .toggle-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .helper-text {
        color: var(--secondary-text-color);
        font-size: 0.9em;
        margin: 0;
      }

      ha-entity-picker {
        width: 100%;
      }
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-player-card-editor')) {
  customElements.define('stremio-player-card-editor', StremioPlayerCardEditor);
}
