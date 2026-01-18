/**
 * Stremio Browse Card
 * 
 * Browse popular movies, TV shows, and new content from Stremio catalogs.
 * 
 * @customElement stremio-browse-card
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
      title: 'Browse Stremio',
      default_view: 'popular',
      default_type: 'movie',
      show_view_controls: true,
      show_type_controls: true,
      show_genre_filter: true,
      columns: 4,
      max_items: 50,
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
      title: 'Browse Stremio',
      default_view: 'popular',
      default_type: 'movie',
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
      console.error('Stremio Browse Card: Invalid item or missing media_content_id');
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

// Note: Card registration with window.customCards is handled in stremio-card-bundle.js
// to prevent duplicate entries
