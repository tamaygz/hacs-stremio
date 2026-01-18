/**
 * Stremio Continue Watching Card
 * 
 * Display and resume content from your Stremio "Continue Watching" list with progress indicators.
 * 
 * @customElement stremio-continue-watching-card
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

class StremioContinueWatchingCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _continueWatchingItems: { type: Array },
      _selectedItem: { type: Object },
      _filterType: { type: String },
      _sortBy: { type: String },
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

      .filter-row {
        display: flex;
        gap: 8px;
      }

      .filter-select {
        padding: 6px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 0.85em;
      }

      .items-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 12px;
        padding: 16px;
        max-height: 500px;
        overflow-y: auto;
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
        aspect-ratio: 2/3;
        object-fit: cover;
        border-radius: 6px;
        background: var(--secondary-background-color);
      }

      .item-poster-placeholder {
        width: 100%;
        aspect-ratio: 2/3;
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

      .item-title {
        font-size: 0.8em;
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--primary-text-color);
      }

      .item-progress {
        height: 4px;
        background: var(--secondary-background-color);
        border-radius: 2px;
        margin-top: 4px;
        overflow: hidden;
        position: relative;
      }

      .item-progress-fill {
        height: 100%;
        background: var(--primary-color);
        transition: width 0.3s ease;
      }

      .item-progress-text {
        font-size: 0.7em;
        color: var(--secondary-text-color);
        margin-top: 2px;
        text-align: center;
      }

      .empty-state {
        padding: 40px;
        text-align: center;
        color: var(--secondary-text-color);
      }

      .empty-state ha-icon {
        --mdc-icon-size: 48px;
        margin-bottom: 8px;
        opacity: 0.5;
      }

      .count-badge {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        margin-left: 8px;
      }

      /* Item detail overlay */
      .item-detail-overlay {
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
    this._continueWatchingItems = [];
    this._selectedItem = null;
    this._filterType = 'all';
    this._sortBy = 'progress';
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = {
      title: 'Continue Watching',
      entity: 'sensor.stremio_continue_watching_count',
      show_filters: true,
      max_items: 20,
      columns: 4,
      ...config,
    };
  }

  // Define card type for UI editor
  static getStubConfig() {
    return {
      type: 'custom:stremio-continue-watching-card',
      title: 'Continue Watching',
      entity: 'sensor.stremio_continue_watching_count',
      show_filters: true,
    };
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Only update if relevant entity state changed
    if (this.config?.entity) {
      const oldState = oldHass?.states?.[this.config.entity];
      const newState = hass?.states?.[this.config.entity];
      
      if (oldState !== newState) {
        this._updateContinueWatchingItems();
        this.requestUpdate();
      }
    }
  }

  get hass() {
    return this._hass;
  }

  // Optimize re-renders
  shouldUpdate(changedProps) {
    if (changedProps.has('config')) return true;
    if (changedProps.has('_continueWatchingItems')) return true;
    if (changedProps.has('_selectedItem')) return true;
    if (changedProps.has('_filterType')) return true;
    if (changedProps.has('_sortBy')) return true;
    return false;
  }

  _updateContinueWatchingItems() {
    if (!this._hass) {
      this._continueWatchingItems = [];
      return;
    }

    // Get continue watching data from sensor
    const entity = this._hass.states[this.config.entity];

    if (!entity?.attributes?.items) {
      this._continueWatchingItems = [];
      return;
    }

    this._continueWatchingItems = entity.attributes.items || [];
  }

  _getFilteredItems() {
    let items = [...this._continueWatchingItems];

    // Apply type filter
    if (this._filterType !== 'all') {
      items = items.filter(item => item.type === this._filterType);
    }

    // Apply sorting
    switch (this._sortBy) {
      case 'title':
        items.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
        break;
      case 'progress':
        // Sort by progress descending (most progress first)
        items.sort((a, b) => (b.progress_percent || 0) - (a.progress_percent || 0));
        break;
      case 'recent':
      default:
        // Keep original order (usually most recently watched)
        break;
    }

    return items.slice(0, this.config.max_items);
  }

  _handleFilterChange(e) {
    this._filterType = e.target.value;
  }

  _handleSortChange(e) {
    this._sortBy = e.target.value;
  }

  _handleItemClick(item) {
    this._selectedItem = item;
    
    // Fire event for external listeners (media details card integration)
    this.dispatchEvent(
      new CustomEvent('stremio-item-selected', {
        bubbles: true,
        composed: true,
        detail: { 
          item,
          mediaId: item.imdb_id || item.id,
          title: item.title,
          type: item.type,
          poster: item.poster,
          progress: item.progress_percent,
        },
      })
    );
  }

  _closeDetail() {
    this._selectedItem = null;
    
    // Fire event for external listeners
    this.dispatchEvent(
      new CustomEvent('stremio-detail-closed', {
        bubbles: true,
        composed: true,
      })
    );
  }

  _resumeInStremio(item) {
    const type = item.type === 'series' ? 'series' : 'movie';
    const id = item.imdb_id || item.id;
    if (id) {
      window.open(`stremio://detail/${type}/${id}`, '_blank');
    }
  }

  _openFullDetails(item) {
    // Fire event to open in stremio-media-details-card or browser_mod popup
    this.dispatchEvent(
      new CustomEvent('stremio-open-media-details', {
        bubbles: true,
        composed: true,
        detail: { 
          item,
          mediaId: item.imdb_id || item.id,
          title: item.title,
          type: item.type,
          poster: item.poster,
          year: item.year,
          progress: item.progress_percent,
        },
      })
    );
  }

  _getStreams(item) {
    const id = item.imdb_id || item.id;
    if (!id || !this._hass) return;

    this._hass.callService('stremio', 'get_streams', {
      media_id: id,
      media_type: item.type || 'movie',
    });

    // Fire custom event to show stream dialog
    this.dispatchEvent(
      new CustomEvent('stremio-open-stream-dialog', {
        bubbles: true,
        composed: true,
        detail: { 
          item,
          mediaId: id,
          title: item.title,
          type: item.type,
          poster: item.poster,
        },
      })
    );
  }

  render() {
    try {
      const filteredItems = this._getFilteredItems();

      return html`
        <ha-card>
          <div class="header">
            <h2 class="header-title">
              ${this.config.title}
              <span class="count-badge" aria-label="${filteredItems.length} items">(${filteredItems.length})</span>
            </h2>

            ${this.config.show_filters ? html`
              <div class="filter-row" role="group" aria-label="Filter options">
                <select 
                  class="filter-select" 
                  @change=${this._handleFilterChange}
                  aria-label="Filter by type"
                >
                  <option value="all">All Types</option>
                  <option value="movie">Movies</option>
                  <option value="series">TV Series</option>
                </select>
                <select 
                  class="filter-select" 
                  @change=${this._handleSortChange}
                  aria-label="Sort by"
                >
                  <option value="recent">Most Recent</option>
                  <option value="progress">By Progress</option>
                  <option value="title">Title A-Z</option>
                </select>
              </div>
            ` : ''}
          </div>

          ${filteredItems.length > 0 ? html`
            <div class="items-grid" role="list" aria-label="Continue watching items">
              ${filteredItems.map(item => this._renderItem(item))}
            </div>
          ` : html`
            <div class="empty-state" role="status">
              <ha-icon icon="mdi:play-pause"></ha-icon>
              <div>No items to continue watching</div>
            </div>
          `}

          ${this._selectedItem ? this._renderDetailOverlay() : ''}
        </ha-card>
      `;
    } catch (error) {
      console.error('Stremio Continue Watching Card render error:', error);
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
    const title = item.title || 'Unknown';
    const progress = item.progress_percent || 0;

    return html`
      <div 
        class="item" 
        role="listitem"
        tabindex="0"
        @click=${() => this._handleItemClick(item)}
        @keydown=${(e) => e.key === 'Enter' && this._handleItemClick(item)}
        aria-label="${title}, ${progress.toFixed(0)}% watched"
      >
        ${item.poster ? html`
          <img class="item-poster" src="${item.poster}" alt="" loading="lazy" />
        ` : html`
          <div class="item-poster-placeholder">
            <ha-icon icon="mdi:${item.type === 'series' ? 'television' : 'movie'}"></ha-icon>
          </div>
        `}
        <div class="item-title" title="${title}">${title}</div>
        ${progress > 0 ? html`
          <div class="item-progress" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
            <div class="item-progress-fill" style="width: ${progress}%"></div>
          </div>
          <div class="item-progress-text">${progress.toFixed(0)}% watched</div>
        ` : ''}
      </div>
    `;
  }

  _renderDetailOverlay() {
    const item = this._selectedItem;
    const title = item.title || 'Unknown';

    return html`
      <div class="item-detail-overlay" @click=${this._closeDetail}>
        <div class="item-detail" @click=${e => e.stopPropagation()}>
          <button class="close-button" aria-label="Close" @click=${this._closeDetail}>✕</button>
          <div class="detail-header">
            ${item.poster ? html`
              <img class="detail-poster" src="${item.poster}" alt="${title}" />
            ` : ''}
            <div class="detail-info">
              <h3>${title}</h3>
              <p>${item.type === 'series' ? 'TV Series' : 'Movie'}</p>
              ${item.year ? html`<p>Year: ${item.year}</p>` : ''}
              ${item.progress_percent ? html`<p>Progress: ${item.progress_percent.toFixed(0)}%</p>` : ''}
            </div>
          </div>

          <div class="detail-actions">
            <button class="detail-button primary" @click=${() => this._resumeInStremio(item)}>
              <ha-icon icon="mdi:play"></ha-icon>
              Resume in Stremio
            </button>
            <button class="detail-button secondary" @click=${() => this._getStreams(item)}>
              <ha-icon icon="mdi:format-list-bulleted"></ha-icon>
              Get Streams
            </button>
          </div>

          <div class="detail-actions">
            <button class="detail-button secondary" @click=${() => this._openFullDetails(item)}>
              <ha-icon icon="mdi:information-outline"></ha-icon>
              Full Details
            </button>
            <button class="detail-button secondary" @click=${this._closeDetail}>
              Close
            </button>
          </div>
        </div>
      </div>
    `;
  }

  getCardSize() {
    return 4;
  }

  // Grid sizing for sections view (HA 2024.8+)
  getGridOptions() {
    return {
      rows: 6,
      columns: 6,
      min_rows: 4,
      min_columns: 3,
    };
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-continue-watching-card')) {
  customElements.define('stremio-continue-watching-card', StremioContinueWatchingCard);
}

// Note: Card registration with window.customCards is handled in stremio-card-bundle.js
// to prevent duplicate entries
