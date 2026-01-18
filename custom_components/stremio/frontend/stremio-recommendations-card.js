/**
 * Stremio Recommendations Card
 * 
 * Display personalized content recommendations based on your Stremio library preferences.
 * 
 * @customElement stremio-recommendations-card
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

class StremioRecommendationsCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _recommendations: { type: Array },
      _selectedItem: { type: Object },
      _filterType: { type: String },
      _loading: { type: Boolean },
      _error: { type: String },
      _lastFetchTime: { type: Number },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        height: 100%;
      }

      ha-card {
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      .header {
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
        flex-shrink: 0;
      }

      .header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .header-title {
        font-size: 1.2em;
        font-weight: 500;
        margin: 0;
        color: var(--primary-text-color);
      }

      .refresh-btn {
        background: transparent;
        border: none;
        color: var(--primary-color);
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        transition: background-color 0.2s;
      }

      .refresh-btn:hover {
        background: var(--secondary-background-color);
      }

      .refresh-btn.loading {
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }

      .filter-row {
        display: flex;
        gap: 8px;
      }

      .filter-btn {
        padding: 6px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 16px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.85em;
        transition: all 0.2s;
      }

      .filter-btn:hover {
        border-color: var(--primary-color);
      }

      .filter-btn.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .items-grid {
        display: grid;
        grid-template-columns: repeat(var(--grid-columns, 4), 1fr);
        gap: 12px;
        padding: 16px;
        overflow-y: auto;
        flex: 1;
        min-height: 0;
      }

      .items-grid.horizontal {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: hidden;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
      }

      .items-grid.horizontal .item {
        flex: 0 0 auto;
        width: calc(100% / var(--grid-columns, 4) - 10px);
        min-width: 100px;
        scroll-snap-align: start;
      }

      @media (max-width: 768px) {
        .items-grid {
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 8px;
          padding: 12px;
        }
      }

      .item {
        cursor: pointer;
        transition: transform 0.2s ease;
        position: relative;
      }

      .item:hover {
        transform: scale(1.05);
      }

      .item:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
        transform: scale(1.05);
      }

      .item-poster {
        width: 100%;
        aspect-ratio: var(--poster-aspect-ratio, 2/3);
        object-fit: cover;
        border-radius: 6px;
        background: var(--secondary-background-color);
      }

      .item-poster-placeholder {
        width: 100%;
        aspect-ratio: var(--poster-aspect-ratio, 2/3);
        border-radius: 6px;
        background: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .item-poster-placeholder ha-icon {
        --mdc-icon-size: 32px;
        color: var(--secondary-text-color);
      }

      .media-type-badge {
        position: absolute;
        top: 6px;
        left: 6px;
        background: rgba(0, 0, 0, 0.7);
        color: #fff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.65em;
        text-transform: uppercase;
        font-weight: 600;
      }

      .recommendation-reason {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, rgba(0,0,0,0.8));
        color: #fff;
        padding: 24px 6px 6px;
        border-radius: 0 0 6px 6px;
        font-size: 0.65em;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .item-title {
        font-size: 0.8em;
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--primary-text-color);
      }

      .loading-state,
      .empty-state,
      .error-state {
        padding: 40px;
        text-align: center;
        color: var(--secondary-text-color);
      }

      .loading-state ha-icon,
      .empty-state ha-icon,
      .error-state ha-icon {
        --mdc-icon-size: 48px;
        margin-bottom: 8px;
        opacity: 0.5;
      }

      .error-state {
        color: var(--error-color);
      }

      .retry-btn {
        margin-top: 12px;
        padding: 8px 16px;
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }

      .count-badge {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        margin-left: 8px;
      }

      /* Back button */
      .back-button {
        background: transparent;
        border: none;
        color: var(--primary-color);
        cursor: pointer;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.95em;
        font-weight: 500;
        transition: background-color 0.2s;
      }

      .back-button:hover {
        background-color: var(--secondary-background-color);
      }

      /* Inline detail view */
      .item-detail-view {
        padding: 16px;
      }

      .detail-header {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }

      .detail-poster {
        width: 120px;
        height: 180px;
        object-fit: cover;
        border-radius: 8px;
        flex-shrink: 0;
      }

      .detail-poster-placeholder {
        width: 120px;
        height: 180px;
        background: var(--secondary-background-color);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .detail-poster-placeholder ha-icon {
        width: 48px;
        height: 48px;
        color: var(--disabled-text-color);
      }

      .detail-info {
        flex: 1;
      }

      .detail-info h3 {
        margin: 0 0 8px 0;
        color: var(--primary-text-color);
        font-size: 1.3em;
      }

      .detail-type {
        margin: 4px 0;
        font-size: 0.95em;
        color: var(--primary-color);
        font-weight: 500;
      }

      .detail-meta {
        margin: 4px 0;
        font-size: 0.9em;
        color: var(--secondary-text-color);
      }

      .detail-reason {
        margin-top: 8px;
        padding: 8px;
        background: var(--secondary-background-color);
        border-radius: 4px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }

      .detail-reason ha-icon {
        --mdc-icon-size: 16px;
        margin-right: 4px;
        color: var(--primary-color);
      }

      .detail-actions {
        display: flex;
        gap: 8px;
        margin-top: 16px;
      }

      .detail-button {
        flex: 1;
        padding: 12px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        transition: opacity 0.2s;
      }

      .detail-button:hover {
        opacity: 0.9;
      }

      .detail-button.primary {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .detail-button.secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
      }

      .detail-button.tertiary {
        background: transparent;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
      }

      .detail-button.tertiary:hover {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
    `;
  }

  constructor() {
    super();
    this._recommendations = [];
    this._selectedItem = null;
    this._filterType = 'all';
    this._loading = false;
    this._error = null;
    this._lastFetchTime = 0;
    
    // Bind methods that are used as event handlers
    this._closeDetail = this._closeDetail.bind(this);
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = {
      // Display options
      title: 'Recommended For You',
      show_filters: true,
      show_title: true, // Show title below poster
      show_reason: true, // Show recommendation reason
      show_media_type_badge: false, // Show Movie/TV badge on poster
      
      // Layout options
      max_items: 20,
      columns: 4,
      card_height: 0, // 0 for auto
      poster_aspect_ratio: '2/3', // 2/3, 16/9, 1/1, 4/3
      horizontal_scroll: false, // Horizontal carousel mode
      
      // Behavior options
      tap_action: 'details', // details, open_stremio, streams
      auto_refresh: false, // Auto-refresh on load
      refresh_interval: 3600, // Seconds between auto-refreshes (default 1 hour)
      
      // Filter defaults
      default_filter: 'all', // all, movie, series
      
      ...config,
    };
    
    this._filterType = this.config.default_filter;
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Fetch recommendations on first hass set
    if (!oldHass && hass) {
      this._fetchRecommendations();
    }
  }

  get hass() {
    return this._hass;
  }

  // Optimize re-renders
  shouldUpdate(changedProps) {
    if (changedProps.has('config')) return true;
    if (changedProps.has('_recommendations')) return true;
    if (changedProps.has('_selectedItem')) return true;
    if (changedProps.has('_filterType')) return true;
    if (changedProps.has('_loading')) return true;
    if (changedProps.has('_error')) return true;
    return false;
  }

  async _fetchRecommendations() {
    if (!this._hass) {
      console.log('[Recommendations Card] No hass instance');
      return;
    }

    // Check refresh interval (avoid fetching too frequently)
    const now = Date.now();
    const minInterval = (this.config.refresh_interval || 3600) * 1000;
    if (this._lastFetchTime && (now - this._lastFetchTime) < minInterval && this._recommendations.length > 0) {
      console.log('[Recommendations Card] Skipping fetch, data is still fresh');
      return;
    }

    this._loading = true;
    this._error = null;

    try {
      const response = await this._hass.callWS({
        type: 'call_service',
        domain: 'stremio',
        service: 'get_recommendations',
        service_data: {
          limit: this.config.max_items || 20,
        },
        return_response: true,
      });

      console.log('[Recommendations Card] Response:', response);

      let recommendations = null;
      if (response?.response?.recommendations) {
        recommendations = response.response.recommendations;
      } else if (response?.recommendations) {
        recommendations = response.recommendations;
      }

      if (recommendations) {
        this._recommendations = recommendations;
        this._lastFetchTime = now;
        console.log('[Recommendations Card] Loaded', recommendations.length, 'recommendations');
      } else {
        this._recommendations = [];
      }
    } catch (error) {
      console.error('[Recommendations Card] Failed to fetch recommendations:', error);
      this._error = error.message || 'Failed to load recommendations';
    } finally {
      this._loading = false;
    }
  }

  _getFilteredItems() {
    let items = [...this._recommendations];

    // Apply type filter
    if (this._filterType !== 'all') {
      items = items.filter(item => item.type === this._filterType);
    }

    return items.slice(0, this.config.max_items);
  }

  _handleFilterChange(filter) {
    this._filterType = filter;
  }

  _handleRefresh() {
    this._lastFetchTime = 0; // Force refresh
    this._fetchRecommendations();
  }

  _handleItemClick(item) {
    this._selectedItem = item;
    
    // Fire event for external listeners
    this.dispatchEvent(
      new CustomEvent('stremio-item-selected', {
        bubbles: true,
        composed: true,
        detail: { 
          item,
          mediaId: item.imdb_id || item.id,
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
          recommendation_reason: item.recommendation_reason,
        },
      })
    );
  }

  _closeDetail() {
    this._selectedItem = null;
    
    this.dispatchEvent(
      new CustomEvent('stremio-detail-closed', {
        bubbles: true,
        composed: true,
      })
    );
  }

  _openInStremio(item) {
    const type = item.type === 'series' ? 'series' : 'movie';
    const id = item.imdb_id || item.id;
    
    if (id && typeof id === 'string') {
      const sanitizedId = id.replace(/[^a-zA-Z0-9_-]/g, '');
      if (sanitizedId && sanitizedId.length > 0) {
        window.open(`stremio://detail/${type}/${sanitizedId}`, '_blank');
      }
    }
  }

  _addToLibrary(item) {
    const id = item.imdb_id || item.id;
    if (!id || !this._hass) return;

    this._showToast('Adding to library...');

    this._hass.callService('stremio', 'add_to_library', {
      media_id: id,
      media_type: item.type || 'movie',
    })
      .then(() => {
        this._showToast(`Added "${item.title || item.name}" to library`);
      })
      .catch((error) => {
        console.error('[Recommendations Card] Failed to add to library:', error);
        this._showToast(`Failed to add: ${error.message}`, 'error');
      });
  }

  _getStreams(item) {
    const id = item.imdb_id || item.id;
    if (!id || !this._hass) return;

    // For series, show episode picker
    if (item.type === 'series') {
      this._showEpisodePicker(item);
      return;
    }

    this._fetchStreams(item, null, null);
  }

  _showEpisodePicker(item) {
    if (window.StremioEpisodePicker) {
      window.StremioEpisodePicker.show(
        this._hass,
        {
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
          imdb_id: item.imdb_id || item.id,
        },
        (selection) => {
          this._fetchStreams(item, selection.season, selection.episode);
        }
      );
    } else {
      this._showToast('Episode picker not available');
    }
  }

  _fetchStreams(item, season, episode) {
    const id = item.imdb_id || item.id;
    this._showToast('Fetching streams...');
    
    const serviceData = {
      media_id: id,
      media_type: item.type || 'movie',
    };
    
    if (item.type === 'series' && season && episode) {
      serviceData.season = season;
      serviceData.episode = episode;
    }

    this._hass.callWS({
      type: 'call_service',
      domain: 'stremio',
      service: 'get_streams',
      service_data: serviceData,
      return_response: true,
    })
      .then((response) => {
        let streams = response?.response?.streams || response?.streams;
        
        if (streams && streams.length > 0) {
          this._showStreamDialog(item, streams);
        } else {
          this._showToast('No streams found');
        }
      })
      .catch((error) => {
        console.error('[Recommendations Card] Failed to get streams:', error);
        this._showToast(`Failed to get streams: ${error.message}`, 'error');
      });
  }

  _showStreamDialog(item, streams) {
    if (window.StremioStreamDialog) {
      window.StremioStreamDialog.show(
        this._hass,
        {
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
          imdb_id: item.imdb_id || item.id,
        },
        streams
      );
    } else {
      let dialog = document.querySelector('stremio-stream-dialog');
      if (!dialog) {
        dialog = document.createElement('stremio-stream-dialog');
        document.body.appendChild(dialog);
      }
      dialog.hass = this._hass;
      dialog.mediaItem = item;
      dialog.streams = streams;
      dialog.open = true;
    }
  }

  _showToast(message, type = 'info') {
    const event = new CustomEvent('hass-notification', {
      detail: { message: message },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
    console.log(`[Recommendations Card] Toast: ${message}`);
  }

  render() {
    try {
      const columns = Number(this.config.columns || 4);
      const posterAspectRatio = this.config.poster_aspect_ratio || '2/3';
      const cardHeight = this.config.card_height > 0 ? `${this.config.card_height}px` : 'none';
      const gridStyle = `--card-max-height: ${cardHeight}; --grid-columns: ${columns}; --poster-aspect-ratio: ${posterAspectRatio};`;

      // If an item is selected, show detail view
      if (this._selectedItem) {
        return html`
          <ha-card>
            <div class="header">
              <button class="back-button" @click=${this._closeDetail} aria-label="Back to recommendations">
                <ha-icon icon="mdi:arrow-left"></ha-icon>
                Back to Recommendations
              </button>
            </div>
            ${this._renderDetailView()}
          </ha-card>
        `;
      }

      const filteredItems = this._getFilteredItems();

      return html`
        <ha-card>
          <div class="header">
            <div class="header-row">
              <h2 class="header-title">
                ${this.config.title}
                <span class="count-badge">(${filteredItems.length})</span>
              </h2>
              <button 
                class="refresh-btn ${this._loading ? 'loading' : ''}" 
                @click=${this._handleRefresh}
                aria-label="Refresh recommendations"
                ?disabled=${this._loading}
              >
                <ha-icon icon="mdi:refresh"></ha-icon>
              </button>
            </div>

            ${this.config.show_filters ? html`
              <div class="filter-row">
                <button 
                  class="filter-btn ${this._filterType === 'all' ? 'active' : ''}"
                  @click=${() => this._handleFilterChange('all')}
                >
                  All
                </button>
                <button 
                  class="filter-btn ${this._filterType === 'movie' ? 'active' : ''}"
                  @click=${() => this._handleFilterChange('movie')}
                >
                  Movies
                </button>
                <button 
                  class="filter-btn ${this._filterType === 'series' ? 'active' : ''}"
                  @click=${() => this._handleFilterChange('series')}
                >
                  TV Series
                </button>
              </div>
            ` : ''}
          </div>

          ${this._loading ? html`
            <div class="loading-state">
              <ha-icon icon="mdi:loading"></ha-icon>
              <div>Loading recommendations...</div>
            </div>
          ` : this._error ? html`
            <div class="error-state">
              <ha-icon icon="mdi:alert-circle"></ha-icon>
              <div>${this._error}</div>
              <button class="retry-btn" @click=${this._handleRefresh}>Retry</button>
            </div>
          ` : filteredItems.length > 0 ? html`
            <div 
              class="items-grid ${this.config.horizontal_scroll ? 'horizontal' : ''}" 
              role="list" 
              aria-label="Recommended items"
              style="${gridStyle}"
            >
              ${filteredItems.map(item => this._renderItem(item))}
            </div>
          ` : html`
            <div class="empty-state" role="status">
              <ha-icon icon="mdi:lightbulb-outline"></ha-icon>
              <div>No recommendations available</div>
              <p>Add more items to your library to get personalized recommendations.</p>
            </div>
          `}
        </ha-card>
      `;
    } catch (error) {
      console.error('Stremio Recommendations Card render error:', error);
      return html`
        <ha-card>
          <div class="card-content" style="padding: 16px; color: var(--error-color);">
            <ha-icon icon="mdi:alert"></ha-icon>
            Error rendering card: ${error.message}
          </div>
        </ha-card>
      `;
    }
  }

  _renderItem(item) {
    const title = item.title || item.name || 'Unknown';
    const reason = item.recommendation_reason;

    return html`
      <div 
        class="item" 
        role="listitem"
        tabindex="0"
        @click=${() => this._handleItemClick(item)}
        @keydown=${(e) => e.key === 'Enter' && this._handleItemClick(item)}
        aria-label="${title}${reason ? ` - ${reason}` : ''}"
      >
        <div style="position: relative;">
          ${item.poster ? html`
            <img class="item-poster" src="${item.poster}" alt="" loading="lazy" />
          ` : html`
            <div class="item-poster-placeholder">
              <ha-icon icon="mdi:${item.type === 'series' ? 'television' : 'movie'}"></ha-icon>
            </div>
          `}
          ${this.config.show_media_type_badge && item.type ? html`
            <span class="media-type-badge">${item.type === 'series' ? 'TV' : 'Movie'}</span>
          ` : ''}
          ${this.config.show_reason && reason ? html`
            <div class="recommendation-reason">${reason}</div>
          ` : ''}
        </div>
        ${this.config.show_title !== false ? html`
          <div class="item-title" title="${title}">${title}</div>
        ` : ''}
      </div>
    `;
  }

  _renderDetailView() {
    const item = this._selectedItem;
    const title = item.title || item.name || 'Unknown';
    const reason = item.recommendation_reason;

    return html`
      <div class="item-detail-view">
        <div class="detail-header">
          ${item.poster ? html`
            <img class="detail-poster" src="${item.poster}" alt="${title}" />
          ` : html`
            <div class="detail-poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
          <div class="detail-info">
            <h3>${title}</h3>
            <p class="detail-type">${item.type === 'series' ? 'TV Series' : 'Movie'}</p>
            ${item.year ? html`<p class="detail-meta">Year: ${item.year}</p>` : ''}
            ${item.genres && item.genres.length > 0 ? html`
              <p class="detail-meta">Genres: ${item.genres.join(', ')}</p>
            ` : ''}
            ${reason ? html`
              <div class="detail-reason">
                <ha-icon icon="mdi:lightbulb"></ha-icon>
                ${reason}
              </div>
            ` : ''}
          </div>
        </div>

        <div class="detail-actions">
          <button class="detail-button primary" @click=${() => this._openInStremio(item)}>
            <ha-icon icon="mdi:play"></ha-icon>
            Open in Stremio
          </button>
          <button class="detail-button secondary" @click=${() => this._addToLibrary(item)}>
            <ha-icon icon="mdi:plus"></ha-icon>
            Add to Library
          </button>
        </div>

        <div class="detail-actions">
          <button class="detail-button tertiary" @click=${() => this._getStreams(item)}>
            <ha-icon icon="mdi:format-list-bulleted"></ha-icon>
            Get Streams
          </button>
        </div>
      </div>
    `;
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    const defaults = {
      rows: 6,
      columns: 6,
      min_rows: 4,
      min_columns: 3,
    };

    if (this.config?.layout && typeof this.config.layout === 'object') {
      return { ...defaults, ...this.config.layout };
    }

    return defaults;
  }

  static getConfigElement() {
    return document.createElement('stremio-recommendations-card-editor');
  }

  static getStubConfig() {
    return {
      type: 'custom:stremio-recommendations-card',
      title: 'Recommended For You',
      show_filters: true,
      show_title: true,
      show_reason: true,
      show_media_type_badge: false,
      max_items: 20,
      columns: 4,
      card_height: 0,
      poster_aspect_ratio: '2/3',
      horizontal_scroll: false,
      tap_action: 'details',
      default_filter: 'all',
    };
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-recommendations-card')) {
  customElements.define('stremio-recommendations-card', StremioRecommendationsCard);
}

// Editor for Recommendations Card
class StremioRecommendationsCardEditor extends LitElement {
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
      display: true,
      layout: false,
      behavior: false,
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
                .value=${this._config.title || 'Recommended For You'}
                .configValue=${'title'}
                @input=${this._valueChanged}
              ></ha-textfield>

              <div class="toggle-group">
                <ha-formfield label="Show Type Filters">
                  <ha-switch
                    .checked=${this._config.show_filters !== false}
                    .configValue=${'show_filters'}
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

                <ha-formfield label="Show Recommendation Reason">
                  <ha-switch
                    .checked=${this._config.show_reason !== false}
                    .configValue=${'show_reason'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Media Type Badge">
                  <ha-switch
                    .checked=${this._config.show_media_type_badge === true}
                    .configValue=${'show_media_type_badge'}
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
                  .value=${this._config.max_items || 20}
                  .configValue=${'max_items'}
                  type="number"
                  min="1"
                  max="50"
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
                label="Tap Action"
                .value=${this._config.tap_action || 'details'}
                .configValue=${'tap_action'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="details">Show Details</mwc-list-item>
                <mwc-list-item value="open_stremio">Open in Stremio</mwc-list-item>
                <mwc-list-item value="streams">Get Streams</mwc-list-item>
              </ha-select>

              <ha-select
                label="Default Filter"
                .value=${this._config.default_filter || 'all'}
                .configValue=${'default_filter'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="all">All</mwc-list-item>
                <mwc-list-item value="movie">Movies Only</mwc-list-item>
                <mwc-list-item value="series">TV Series Only</mwc-list-item>
              </ha-select>

              <ha-textfield
                label="Refresh Interval (seconds)"
                .value=${this._config.refresh_interval || 3600}
                .configValue=${'refresh_interval'}
                type="number"
                min="300"
                max="86400"
                @input=${this._valueChanged}
              ></ha-textfield>
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

      ha-textfield,
      ha-select {
        width: 100%;
      }
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-recommendations-card-editor')) {
  customElements.define('stremio-recommendations-card-editor', StremioRecommendationsCardEditor);
}

// Note: Card registration with window.customCards is handled in stremio-card-bundle.js

