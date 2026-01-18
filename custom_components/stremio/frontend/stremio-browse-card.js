/**
 * Stremio Browse Card
 * 
 * Browse popular movies, TV shows, and new content from Stremio catalogs.
 * 
 * @customElement stremio-browse-card
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

class StremioBrowseCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _viewMode: { type: String },
      _mediaType: { type: String },
      _selectedGenre: { type: String },
      _catalogItems: { type: Array },
      _loading: { type: Boolean },
      _selectedItem: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      ha-card {
        overflow: hidden;
      }

      .header {
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
      }

      .header-title {
        font-size: 1.2em;
        font-weight: 500;
        margin: 0 0 12px 0;
        color: var(--primary-text-color);
      }

      .control-row {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
      }

      .control-button {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.9em;
        transition: all 0.2s;
      }

      .control-button:hover {
        background: var(--secondary-background-color);
      }

      .control-button.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .catalog-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 12px;
        padding: 16px;
      }

      @media (max-width: 768px) {
        .catalog-grid {
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 8px;
          padding: 12px;
        }
      }

      .catalog-item {
        cursor: pointer;
        border-radius: 8px;
        overflow: hidden;
        transition: transform 0.2s;
        position: relative;
      }

      .catalog-item:hover {
        transform: scale(1.05);
      }

      .catalog-poster {
        width: 100%;
        aspect-ratio: 2/3;
        object-fit: cover;
        background: var(--secondary-background-color);
      }

      .catalog-title {
        padding: 8px;
        font-size: 0.85em;
        color: var(--primary-text-color);
        text-align: center;
        background: var(--card-background-color);
        line-height: 1.2;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .loading-spinner {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px;
        color: var(--primary-color);
      }

      .empty-state {
        padding: 40px;
        text-align: center;
        color: var(--secondary-text-color);
      }

      .modal-overlay {
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
      }

      .item-detail {
        background: var(--card-background-color);
        border-radius: 12px;
        padding: 20px;
        max-width: 400px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
      }

      .detail-header {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }

      .detail-poster {
        width: 100px;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
      }

      .detail-info h3 {
        margin: 0 0 8px 0;
        color: var(--primary-text-color);
      }

      .detail-info p {
        margin: 4px 0;
        font-size: 0.9em;
        color: var(--secondary-text-color);
      }

      .detail-actions {
        display: flex;
        gap: 8px;
        margin-top: 16px;
      }

      .detail-button {
        flex: 1;
        padding: 10px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }

      .detail-button.primary {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .detail-button.secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
      }

      .close-button {
        position: absolute;
        top: 10px;
        right: 10px;
        background: var(--secondary-background-color);
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    `;
  }

  constructor() {
    super();
    this._viewMode = 'popular';
    this._mediaType = 'movie';
    this._selectedGenre = null;
    this._catalogItems = [];
    this._loading = false;
    this._selectedItem = null;
    this._genres = [
      'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
      'Documentary', 'Drama', 'Family', 'Fantasy', 'History', 'Horror',
      'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western'
    ];
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = {
      // Stremio account (for multi-account support)
      entity: undefined, // Stremio media player entity
      
      // Display options
      title: 'Browse Stremio',
      show_view_controls: true,
      show_type_controls: true,
      show_genre_filter: true,
      show_title: true, // Show titles below posters
      show_rating: true, // Show rating badge
      
      // Layout options
      columns: 4,
      max_items: 50,
      card_height: 0, // 0 for auto
      poster_aspect_ratio: '2/3', // 2/3, 16/9, 1/1, 4/3
      horizontal_scroll: false, // Horizontal carousel mode
      
      // Behavior options
      default_view: 'popular',
      default_type: 'movie',
      tap_action: 'details', // details, play, streams
      
      // Device integration
      apple_tv_entity: undefined, // For Apple TV handover
      
      ...config,
    };
    this._viewMode = this.config.default_view;
    this._mediaType = this.config.default_type;
  }

  // Define card type for UI editor
  static getConfigElement() {
    return document.createElement('stremio-browse-card-editor');
  }

  static getStubConfig() {
    return {
      type: 'custom:stremio-browse-card',
      entity: undefined,
      title: 'Browse Stremio',
      default_view: 'popular',
      default_type: 'movie',
      show_view_controls: true,
      show_type_controls: true,
      show_genre_filter: true,
      show_title: true,
      show_rating: true,
      columns: 4,
      max_items: 50,
      card_height: 0,
      poster_aspect_ratio: '2/3',
      horizontal_scroll: false,
      tap_action: 'details',
    };
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Load catalog on first hass set
    if (!oldHass && hass) {
      this._loadCatalog();
    }
  }

  get hass() {
    return this._hass;
  }

  async _loadCatalog() {
    if (!this._hass || this._loading) return;

    this._loading = true;
    this.requestUpdate();

    try {
      // Build catalog ID from view mode and media type
      const catalogId = this._getCatalogId();
      const mediaSource = `media-source://stremio/${catalogId}`;

      const response = await this._hass.callWS({
        type: 'media_source/browse_media',
        media_content_id: mediaSource,
      });

      if (response && response.children) {
        this._catalogItems = response.children.slice(0, this.config.max_items);
      } else {
        this._catalogItems = [];
      }
    } catch (err) {
      console.error('Failed to load catalog:', err);
      this._catalogItems = [];
    } finally {
      this._loading = false;
      this.requestUpdate();
    }
  }

  _getCatalogId() {
    // Build catalog identifier from current view, media type, and optional genre
    const mediaTypeSuffix = this._mediaType === 'movie' ? 'movies' : 'series';
    
    // If genre is selected, use genre-based browsing
    if (this._selectedGenre) {
      const genrePrefix = this._mediaType === 'movie' ? 'movie_genres' : 'series_genres';
      return `${genrePrefix}/${this._selectedGenre}`;
    }
    
    // Otherwise use view-based browsing (popular/new)
    return `${this._viewMode}_${mediaTypeSuffix}`;
  }

  _handleGenreChange(e) {
    const genre = e.target.value;
    this._selectedGenre = genre === 'all' ? null : genre;
    this._loadCatalog();
  }

  _handleViewChange(view) {
    this._viewMode = view;
    this._loadCatalog();
  }

  _handleTypeChange(type) {
    this._mediaType = type;
    this._loadCatalog();
  }

  _handleItemClick(item) {
    this._selectedItem = item;
    
    // Fire event for external listeners
    this.dispatchEvent(
      new CustomEvent('stremio-catalog-item-selected', {
        bubbles: true,
        composed: true,
        detail: { 
          item,
          mediaId: item.media_content_id,
          title: item.title,
        },
      })
    );
  }

  _closeDetail() {
    this._selectedItem = null;
  }

  _openMediaBrowser(item) {
    // Navigate to media browser for this item
    if (!item || !item.media_content_id) {
      console.error('Stremio Browse Card: Invalid item or missing media_content_id', { 
        item: item ? { title: item.title, type: item.media_content_type } : null 
      });
      return;
    }

    if (!this._hass) {
      console.error('Stremio Browse Card: Unable to open media browser - hass instance is unavailable.');
      return;
    }

    const hass = this._hass;
    const contentId = item.media_content_id;

    // Try native HA navigation first (most compatible method)
    try {
      // Use Home Assistant's history API to navigate to media browser
      const mediaSourceId = `media-source://stremio/${contentId}`;
      
      // Fire a more-info event that HA can handle
      this.dispatchEvent(
        new CustomEvent('hass-more-info', {
          bubbles: true,
          composed: true,
          detail: {
            entityId: null, // No specific entity
          },
        })
      );

      // Try to open the media browser programmatically using HA's built-in methods
      if (window.history && window.location) {
        const currentPath = window.location.pathname;
        // Check if we can navigate within HA
        if (currentPath.includes('/lovelace/') || currentPath.includes('/config/')) {
          // Use native browser navigation to media-browser
          const encodedPath = `/media-browser/${encodeURIComponent(mediaSourceId)}`;
          window.history.pushState(null, '', encodedPath);
          
          // Dispatch a popstate event to notify HA of the navigation
          window.dispatchEvent(new PopStateEvent('popstate'));
          return;
        }
      }
    } catch (error) {
      console.warn('Stremio Browse Card: Native navigation failed:', error);
    }

    // Fallback 1: Try browser_mod if available
    const hasBrowserMod =
      hass.services &&
      hass.services.browser_mod &&
      hass.services.browser_mod.navigate;

    if (hasBrowserMod) {
      const encodedPath = `/media-browser/media-source%3A%2F%2Fstremio%2F${contentId}`;
      
      hass.callService('browser_mod', 'navigate', {
        path: encodedPath,
      }).catch((error) => {
        console.error('Stremio Browse Card: browser_mod navigation failed:', error);
        this._showNavigationFallback(item);
      });
      return;
    }

    // Fallback 2: Show enhanced detail dialog with more information
    this._showNavigationFallback(item);
  }

  _showNavigationFallback(item) {
    // Show notification with instructions
    if (this._hass && this._hass.services?.persistent_notification?.create) {
      const mediaSourceId = `media-source://stremio/${item.media_content_id}`;
      this._hass.callService('persistent_notification', 'create', {
        title: 'Stremio - View Details',
        message: `To view full details for "${item.title}", open the Media Browser from the sidebar and navigate to Stremio section.\n\nMedia ID: ${mediaSourceId}`,
        notification_id: `stremio_media_${item.media_content_id}`,
      }).catch(err => console.error('Failed to create notification:', err));
    }
    
    // Also log to console for debugging
    console.info('Stremio Browse Card: Media browser path:', `/media-browser/media-source://stremio/${item.media_content_id}`);
  }

  _addToLibrary(item) {
    const parts = item.media_content_id.split('/');
    const mediaType = parts[0];
    const mediaId = parts[1];

    if (mediaId && this._hass) {
      this._hass.callService('stremio', 'add_to_library', {
        media_id: mediaId,
        media_type: mediaType,
      });
    }
  }

  render() {
    return html`
      <ha-card>
        <div class="header">
          <div class="header-title">${this.config.title}</div>
          
          ${this.config.show_view_controls ? html`
            <div class="control-row">
              <button 
                class="control-button ${this._viewMode === 'popular' ? 'active' : ''}"
                aria-label="Show popular content"
                aria-pressed="${this._viewMode === 'popular'}"
                @click=${() => this._handleViewChange('popular')}
              >
                🔥 Popular
              </button>
              <button 
                class="control-button ${this._viewMode === 'new' ? 'active' : ''}"
                aria-label="Show new content"
                aria-pressed="${this._viewMode === 'new'}"
                @click=${() => this._handleViewChange('new')}
              >
                🆕 New
              </button>
            </div>
          ` : ''}

          ${this.config.show_type_controls ? html`
            <div class="control-row">
              <button 
                class="control-button ${this._mediaType === 'movie' ? 'active' : ''}"
                aria-label="Show movies"
                aria-pressed="${this._mediaType === 'movie'}"
                @click=${() => this._handleTypeChange('movie')}
              >
                🎬 Movies
              </button>
              <button 
                class="control-button ${this._mediaType === 'series' ? 'active' : ''}"
                aria-label="Show TV shows"
                aria-pressed="${this._mediaType === 'series'}"
                @click=${() => this._handleTypeChange('series')}
              >
                📺 TV Shows
              </button>
            </div>
          ` : ''}

          ${this.config.show_genre_filter ? html`
            <div class="control-row">
              <select 
                class="control-button"
                style="width: 100%; cursor: pointer;"
                aria-label="Filter by genre"
                @change=${this._handleGenreChange}
                .value=${this._selectedGenre || 'all'}
              >
                <option value="all">🎭 All Genres</option>
                ${this._genres.map(genre => html`
                  <option value="${genre}">${genre}</option>
                `)}
              </select>
            </div>
          ` : ''}
        </div>

        ${this._loading ? html`
          <div class="loading-spinner">
            <ha-circular-progress active></ha-circular-progress>
          </div>
        ` : this._catalogItems.length === 0 ? html`
          <div class="empty-state">
            No ${this._viewMode} ${this._mediaType === 'movie' ? 'movies' : 'TV shows'} found
          </div>
        ` : html`
          <div class="catalog-grid" style="grid-template-columns: repeat(auto-fill, minmax(${100 + (this.config.columns - 4) * 20}px, 1fr))">
            ${this._catalogItems.map(item => html`
              <div 
                class="catalog-item" 
                role="button"
                tabindex="0"
                aria-label="${item.title}"
                @click=${() => this._handleItemClick(item)}
                @keydown=${(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this._handleItemClick(item);
                  }
                }}
              >
                ${item.thumbnail ? html`
                  <img 
                    class="catalog-poster" 
                    src="${item.thumbnail}" 
                    alt="${item.title}"
                    loading="lazy"
                  />
                ` : html`
                  <div class="catalog-poster"></div>
                `}
                <div class="catalog-title">${item.title}</div>
              </div>
            `)}
          </div>
        `}

        ${this._selectedItem ? html`
          <div class="modal-overlay" @click=${this._closeDetail}>
            <div class="item-detail" @click=${(e) => e.stopPropagation()}>
              <button class="close-button" aria-label="Close" @click=${this._closeDetail}>✕</button>
              <div class="detail-header">
                ${this._selectedItem.thumbnail ? html`
                  <img class="detail-poster" src="${this._selectedItem.thumbnail}" alt="${this._selectedItem.title}" />
                ` : ''}
                <div class="detail-info">
                  <h3>${this._selectedItem.title}</h3>
                  <p>Type: ${this._selectedItem.media_content_type || 'Unknown'}</p>
                </div>
              </div>
              <div class="detail-actions">
                <button 
                  class="detail-button primary" 
                  aria-label="View details for ${this._selectedItem.title}"
                  @click=${() => this._openMediaBrowser(this._selectedItem)}
                >
                  View Details
                </button>
                <button 
                  class="detail-button secondary" 
                  aria-label="Add ${this._selectedItem.title} to library"
                  @click=${() => this._addToLibrary(this._selectedItem)}
                >
                  + Library
                </button>
              </div>
            </div>
          </div>
        ` : ''}
      </ha-card>
    `;
  }

  // For UI card editor support
  getCardSize() {
    return 3;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-browse-card')) {
  customElements.define('stremio-browse-card', StremioBrowseCard);
}

// Editor for Browse Card
class StremioBrowseCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
      _stremioEntities: { type: Array },
      _expandedSections: { type: Object },
    };
  }

  constructor() {
    super();
    this._stremioEntities = [];
    this._expandedSections = {
      account: true,
      display: false,
      layout: false,
      behavior: false,
      device: false,
    };
  }

  setConfig(config) {
    this._config = config;
  }

  updated(changedProps) {
    if (changedProps.has('hass') && this.hass) {
      this._updateEntities();
    }
  }

  _updateEntities() {
    // Find Stremio media player entities (represent each account)
    this._stremioEntities = Object.keys(this.hass.states)
      .filter(entityId => 
        entityId.startsWith('media_player.') && 
        entityId.toLowerCase().includes('stremio')
      )
      .map(entityId => ({
        entity_id: entityId,
        friendly_name: this.hass.states[entityId].attributes.friendly_name || entityId,
      }));
  }

  _selectEntity(entityId) {
    this._config = { ...this._config, entity: entityId };
    this.dispatchEvent(new CustomEvent('config-changed', {
      bubbles: true,
      composed: true,
      detail: { config: this._config },
    }));
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
        <!-- Stremio Account Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('account')}>
            <ha-icon icon="mdi:account"></ha-icon>
            <span>Stremio Account</span>
            <ha-icon class="expand-icon ${this._expandedSections.account ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.account ? html`
            <div class="section-content">
              ${this._stremioEntities?.length > 0 ? html`
                <div class="entity-buttons">
                  ${this._stremioEntities.map(entity => html`
                    <button 
                      class="entity-btn ${this._config.entity === entity.entity_id ? 'selected' : ''}"
                      @click=${() => this._selectEntity(entity.entity_id)}
                    >
                      <ha-icon icon="mdi:account-circle"></ha-icon>
                      <span>${entity.friendly_name}</span>
                    </button>
                  `)}
                </div>
              ` : html`
                <div class="no-entities">
                  <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
                  <span>No Stremio accounts found.</span>
                </div>
              `}
              
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this._config.entity || ''}
                .configValue=${'entity'}
                .includeDomains=${['media_player']}
                label="Or select manually"
                allow-custom-entity
                @value-changed=${this._valueChanged}
              ></ha-entity-picker>
              <p class="helper-text">Select a Stremio account to browse catalogs from that user's library.</p>
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
              <ha-textfield
                label="Card Title"
                .value=${this._config.title || 'Browse Stremio'}
                .configValue=${'title'}
                @input=${this._valueChanged}
              ></ha-textfield>

              <div class="toggle-group">
                <ha-formfield label="Show View Controls (Popular/New)">
                  <ha-switch
                    .checked=${this._config.show_view_controls !== false}
                    .configValue=${'show_view_controls'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Type Controls (Movie/Series)">
                  <ha-switch
                    .checked=${this._config.show_type_controls !== false}
                    .configValue=${'show_type_controls'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Genre Filter">
                  <ha-switch
                    .checked=${this._config.show_genre_filter !== false}
                    .configValue=${'show_genre_filter'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Title Below Poster">
                  <ha-switch
                    .checked=${this._config.show_title !== false}
                    .configValue=${'show_title'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Rating Badge">
                  <ha-switch
                    .checked=${this._config.show_rating !== false}
                    .configValue=${'show_rating'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Layout Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('layout')}>
            <ha-icon icon="mdi:view-grid"></ha-icon>
            <span>Layout</span>
            <ha-icon class="expand-icon ${this._expandedSections.layout ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.layout ? html`
            <div class="section-content">
              <div class="input-row">
                <ha-textfield
                  label="Columns"
                  .value=${this._config.columns || 4}
                  .configValue=${'columns'}
                  type="number"
                  min="2"
                  max="8"
                  @input=${this._valueChanged}
                ></ha-textfield>

                <ha-textfield
                  label="Max Items"
                  .value=${this._config.max_items || 50}
                  .configValue=${'max_items'}
                  type="number"
                  min="1"
                  max="100"
                  @input=${this._valueChanged}
                ></ha-textfield>
              </div>

              <div class="input-row">
                <ha-textfield
                  label="Card Height (px, 0 for auto)"
                  .value=${this._config.card_height || 0}
                  .configValue=${'card_height'}
                  type="number"
                  min="0"
                  max="1000"
                  @input=${this._valueChanged}
                ></ha-textfield>
              </div>

              <ha-select
                label="Poster Aspect Ratio"
                .value=${this._config.poster_aspect_ratio || '2/3'}
                .configValue=${'poster_aspect_ratio'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="2/3">2:3 (Movie Poster)</mwc-list-item>
                <mwc-list-item value="16/9">16:9 (Widescreen)</mwc-list-item>
                <mwc-list-item value="1/1">1:1 (Square)</mwc-list-item>
                <mwc-list-item value="4/3">4:3 (Classic)</mwc-list-item>
              </ha-select>

              <ha-formfield label="Horizontal Scroll Mode">
                <ha-switch
                  .checked=${this._config.horizontal_scroll === true}
                  .configValue=${'horizontal_scroll'}
                  @change=${this._valueChanged}
                ></ha-switch>
              </ha-formfield>
            </div>
          ` : ''}
        </div>

        <!-- Behavior Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('behavior')}>
            <ha-icon icon="mdi:gesture-tap"></ha-icon>
            <span>Behavior</span>
            <ha-icon class="expand-icon ${this._expandedSections.behavior ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.behavior ? html`
            <div class="section-content">
              <ha-select
                label="Default View"
                .value=${this._config.default_view || 'popular'}
                .configValue=${'default_view'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="popular">Popular</mwc-list-item>
                <mwc-list-item value="new">New</mwc-list-item>
              </ha-select>

              <ha-select
                label="Default Media Type"
                .value=${this._config.default_type || 'movie'}
                .configValue=${'default_type'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="movie">Movies</mwc-list-item>
                <mwc-list-item value="series">TV Series</mwc-list-item>
              </ha-select>

              <ha-select
                label="Tap Action"
                .value=${this._config.tap_action || 'details'}
                .configValue=${'tap_action'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="details">Show Details</mwc-list-item>
                <mwc-list-item value="play">Play Directly</mwc-list-item>
                <mwc-list-item value="streams">Get Streams</mwc-list-item>
              </ha-select>
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

  _selectChanged(ev) {
    const target = ev.target;
    if (target.configValue) {
      this._updateConfig(target.configValue, ev.detail.value || target.value);
    }
  }

  _valueChanged(ev) {
    if (!this._config || !this.hass) return;

    const target = ev.target;
    let value;
    
    if (target.configValue) {
      if (target.checked !== undefined) {
        value = target.checked;
      } else if (target.value !== undefined) {
        value = target.value;
        if (target.type === 'number') {
          value = Number(value);
        }
      }
      this._updateConfig(target.configValue, value);
    }
  }

  _updateConfig(key, value) {
    this._config = { ...this._config, [key]: value };
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
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

      .input-row {
        display: flex;
        gap: 12px;
      }

      .input-row > * {
        flex: 1;
      }

      .helper-text {
        color: var(--secondary-text-color);
        font-size: 0.9em;
        margin: 0;
      }

      ha-entity-picker,
      ha-textfield,
      ha-select {
        width: 100%;
      }

      .entity-buttons {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 12px;
      }

      .entity-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: var(--secondary-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        color: var(--primary-text-color);
        transition: all 0.2s ease;
      }

      .entity-btn:hover {
        background: var(--primary-background-color);
        border-color: var(--primary-color);
      }

      .entity-btn.selected {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color);
      }

      .entity-btn span {
        flex: 1;
        text-align: left;
      }

      .no-entities {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: var(--warning-color, #ffc107);
        border-radius: 8px;
        color: var(--primary-text-color);
        margin-bottom: 12px;
      }
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-browse-card-editor')) {
  customElements.define('stremio-browse-card-editor', StremioBrowseCardEditor);
}

// Note: Card registration with window.customCards is handled in stremio-card-bundle.js
// to prevent duplicate entries
