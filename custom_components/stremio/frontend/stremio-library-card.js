/**
 * Stremio Library Card
 * 
 * Browse and search your Stremio library with filtering and sorting.
 * 
 * @customElement stremio-library-card
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

class StremioLibraryCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _searchQuery: { type: String },
      _filterType: { type: String },
      _sortBy: { type: String },
      _libraryItems: { type: Array },
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

      .search-row {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
      }

      .search-input {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 0.95em;
      }

      .search-input:focus {
        outline: none;
        border-color: var(--primary-color);
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

      .library-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 12px;
        padding: 16px;
        max-height: 400px;
        overflow-y: auto;
      }

      .library-item {
        cursor: pointer;
        transition: transform 0.2s ease;
      }

      .library-item:hover {
        transform: scale(1.05);
      }

      .library-item:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
        transform: scale(1.05);
      }

      .library-item:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
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
        height: 3px;
        background: var(--secondary-background-color);
        border-radius: 2px;
        margin-top: 4px;
        overflow: hidden;
      }

      .item-progress-fill {
        height: 100%;
        background: var(--primary-color);
      }

      .empty-state {
        padding: 32px;
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

      .detail-progress-container {
        margin-top: 12px;
      }

      .detail-progress-bar {
        width: 100%;
        height: 6px;
        background: var(--divider-color);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 4px;
      }

      .detail-progress-fill {
        height: 100%;
        background: var(--primary-color);
        transition: width 0.3s ease;
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
    `;
  }

  constructor() {
    super();
    this._searchQuery = '';
    this._filterType = 'all';
    this._sortBy = 'recent';
    this._libraryItems = [];
    this._selectedItem = null;
    this._viewMode = 'library'; // 'library' or 'catalog'
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = {
      title: 'Stremio Library',
      show_search: true,
      show_filters: true,
      show_view_toggle: true,
      default_view: 'library',
      columns: 4,
      max_items: 50,
      ...config,
    };
    this._viewMode = this.config.default_view;
  }

  // Define card type for UI editor
  static getConfigElement() {
    return document.createElement('stremio-library-card-editor');
  }

  static getStubConfig() {
    return {
      type: 'custom:stremio-library-card',
      title: 'Stremio Library',
      show_view_toggle: true,
      default_view: 'library',
    };
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Load initial data if this is the first time hass is set
    if (!oldHass && hass) {
      this._updateLibraryItems();
      this.requestUpdate();
      return;
    }
    
    // Check if any stremio sensor state changed (to handle auto-discovered entities)
    // Also check the resolved entity specifically
    const resolvedEntity = this._resolveEntity(this.config);
    const oldState = oldHass?.states?.[resolvedEntity];
    const newState = hass?.states?.[resolvedEntity];
    
    if (oldState !== newState) {
      this._updateLibraryItems();
      this.requestUpdate();
    }
  }

  get hass() {
    return this._hass;
  }

  // Optimize re-renders
  shouldUpdate(changedProps) {
    if (changedProps.has('config')) return true;
    if (changedProps.has('_searchQuery')) return true;
    if (changedProps.has('_filterType')) return true;
    if (changedProps.has('_sortBy')) return true;
    if (changedProps.has('_libraryItems')) return true;
    if (changedProps.has('_selectedItem')) return true;
    return false;
  }

  _resolveEntity(config) {
    // Helper to resolve entity from config - supports both entity ID and device name
    // Also auto-discovers entities when default doesn't exist
    
    if (config.entity) {
      // If it starts with sensor., it's already an entity ID - check if it exists
      if (config.entity.startsWith('sensor.')) {
        if (this._hass?.states?.[config.entity]) {
          console.log('[Library Card] Using configured entity:', config.entity);
          return config.entity;
        }
        // Configured entity doesn't exist, fall through to auto-discovery
        console.log('[Library Card] Configured entity not found:', config.entity);
      } else {
        // Treat it as a device name and try to find matching entity
        if (this._hass) {
          const deviceName = config.entity.toLowerCase();
          for (const entityId in this._hass.states) {
            if (entityId.includes('library_count')) {
              const normalizedEntityId = entityId.toLowerCase().replace(/_/g, '');
              const normalizedDeviceName = deviceName.replace(/[^a-z0-9]/g, '');
              if (normalizedEntityId.includes(normalizedDeviceName)) {
                console.log('[Library Card] Resolved device name to entity:', deviceName, '->', entityId);
                return entityId;
              }
            }
          }
        }
      }
    }
    
    // Auto-discover: find ANY stremio library_count sensor in the system
    if (this._hass) {
      for (const entityId in this._hass.states) {
        if (entityId.startsWith('sensor.stremio') && entityId.endsWith('_library_count')) {
          console.log('[Library Card] Auto-discovered library sensor:', entityId);
          return entityId;
        }
      }
      // Also check for sensors containing stremio and library_count (different naming patterns)
      for (const entityId in this._hass.states) {
        if (entityId.includes('stremio') && entityId.includes('library_count')) {
          console.log('[Library Card] Auto-discovered library sensor (pattern match):', entityId);
          return entityId;
        }
      }
    }
    
    // Last resort fallback
    console.log('[Library Card] No library sensor found, using default');
    return 'sensor.stremio_library_count';
  }

  _updateLibraryItems() {
    if (!this._hass) {
      console.log('[Library Card] No hass instance');
      this._libraryItems = [];
      return;
    }

    // Get library data from sensor - resolve from device name if needed
    const sensorEntity = this._resolveEntity(this.config);
    const entity = this._hass.states[sensorEntity];
    
    console.log('[Library Card] Looking for entity:', sensorEntity);
    console.log('[Library Card] Entity found:', entity ? 'yes' : 'no');
    console.log('[Library Card] Entity state:', entity?.state);
    console.log('[Library Card] Items in attributes:', entity?.attributes?.items?.length || 0);

    if (!entity?.attributes?.items) {
      console.log('[Library Card] No items in library sensor');
      this._libraryItems = [];
      return;
    }

    this._libraryItems = entity.attributes.items || [];
    console.log('[Library Card] Library items loaded:', this._libraryItems.length);
  }

  _getFilteredItems() {
    let items = [...this._libraryItems];

    // Apply search filter
    if (this._searchQuery) {
      const query = this._searchQuery.toLowerCase();
      items = items.filter(item => 
        item.title?.toLowerCase().includes(query) ||
        item.name?.toLowerCase().includes(query)
      );
    }

    // Apply type filter
    if (this._filterType !== 'all') {
      items = items.filter(item => item.type === this._filterType);
    }

    // Apply sorting
    switch (this._sortBy) {
      case 'title':
        items.sort((a, b) => (a.title || a.name || '').localeCompare(b.title || b.name || ''));
        break;
      case 'progress':
        items.sort((a, b) => (b.progress_percent || 0) - (a.progress_percent || 0));
        break;
      case 'recent':
      default:
        // Keep original order (usually most recent first)
        break;
    }

    return items.slice(0, this.config.max_items);
  }

  _handleSearch(e) {
    this._searchQuery = e.target.value;
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
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
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

  _openInStremio(item) {
    const type = item.type === 'series' ? 'series' : 'movie';
    const id = item.imdb_id || item.id;
    
    // Validate ID format to prevent protocol injection
    // IMDb IDs should match pattern: tt followed by 7-8 digits
    if (id && typeof id === 'string') {
      // Basic sanitization: only allow alphanumeric and safe characters
      const sanitizedId = id.replace(/[^a-zA-Z0-9_-]/g, '');
      if (sanitizedId && sanitizedId.length > 0) {
        window.open(`stremio://detail/${type}/${sanitizedId}`, '_blank');
      } else {
        console.warn('Stremio Library Card: Invalid media ID format', id);
      }
    }
  }

  _getStreams(item) {
    const id = item.imdb_id || item.id;
    if (!id || !this._hass) {
      console.error('[Library Card] Cannot get streams: missing ID or hass');
      return;
    }

    // For series, show episode picker first
    if (item.type === 'series') {
      console.log('[Library Card] TV Show detected, opening episode picker');
      this._showEpisodePicker(item);
      return;
    }

    // For movies, fetch streams directly
    this._fetchStreams(item, null, null);
  }

  _showEpisodePicker(item) {
    // Use the global helper if available
    if (window.StremioEpisodePicker) {
      window.StremioEpisodePicker.show(
        this._hass,
        {
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
          imdb_id: item.imdb_id || item.id,
          // Pass watch progress info for highlighting
          lastWatchedSeason: item.last_season || item.season,
          lastWatchedEpisode: item.last_episode || item.episode,
          total_seasons: item.total_seasons,
          watched_episodes: item.watched_episodes || [],
        },
        (selection) => {
          console.log('[Library Card] Episode selected:', selection);
          this._fetchStreams(item, selection.season, selection.episode);
        }
      );
    } else {
      // Fallback: Create picker directly
      let picker = document.querySelector('stremio-episode-picker');
      if (!picker) {
        picker = document.createElement('stremio-episode-picker');
        document.body.appendChild(picker);
      }
      picker.hass = this._hass;
      picker.mediaItem = {
        title: item.title || item.name,
        type: item.type,
        imdb_id: item.imdb_id || item.id,
        lastWatchedSeason: item.last_season || item.season,
        lastWatchedEpisode: item.last_episode || item.episode,
        total_seasons: item.total_seasons,
      };
      picker.open = true;
      
      // Listen for selection
      const handler = (e) => {
        picker.removeEventListener('episode-selected', handler);
        this._fetchStreams(item, e.detail.season, e.detail.episode);
      };
      picker.addEventListener('episode-selected', handler);
    }
  }

  _fetchStreams(item, season, episode) {
    const id = item.imdb_id || item.id;
    console.log('[Library Card] Getting streams for:', id, item.type, season ? `S${season}E${episode}` : '');
    this._showToast('Fetching streams...');
    
    const serviceData = {
      media_id: id,
      media_type: item.type || 'movie',
    };
    
    // Add season/episode for series
    if (item.type === 'series' && season && episode) {
      serviceData.season = season;
      serviceData.episode = episode;
    }

    // Call service with return_response to get streams back
    this._hass.callService('stremio', 'get_streams', serviceData, undefined, true, true)
      .then((response) => {
        console.log('[Library Card] Streams response:', response);
        
        // Handle different response formats:
        // HA 2024+: { context: {...}, response: { streams: [...] } }
        // Some versions: { context: {...}, streams: [...] }
        // Direct return: { streams: [...] }
        let streams = null;
        
        if (response?.response?.streams) {
          // Format: { response: { streams: [...] } }
          streams = response.response.streams;
        } else if (response?.streams) {
          // Format: { streams: [...] } (direct)
          streams = response.streams;
        }
        
        if (streams && streams.length > 0) {
          console.log('[Library Card] Found', streams.length, 'streams');
          // Show the stream dialog
          const displayItem = { ...item };
          if (season && episode) {
            displayItem.title = `${item.title || item.name} - S${season}E${episode}`;
          }
          this._showStreamDialog(displayItem, streams);
        } else {
          console.log('[Library Card] No streams in response:', response);
          this._showToast('No streams found for this title');
        }
      })
      .catch((error) => {
        console.error('[Library Card] Failed to get streams:', error);
        this._showToast(`Failed to get streams: ${error.message}`, 'error');
      });
  }

  _showStreamDialog(item, streams) {
    console.log('[Library Card] Opening stream dialog with', streams.length, 'streams');
    
    // Use the global helper if available
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
      // Fallback: Create dialog directly
      let dialog = document.querySelector('stremio-stream-dialog');
      if (!dialog) {
        dialog = document.createElement('stremio-stream-dialog');
        document.body.appendChild(dialog);
      }
      dialog.hass = this._hass;
      dialog.mediaItem = {
        title: item.title || item.name,
        type: item.type,
        poster: item.poster,
      };
      dialog.streams = streams;
      dialog.open = true;
    }
  }

  _showToast(message, type = 'info') {
    // Show HA toast notification using the fire event method
    const event = new CustomEvent('hass-notification', {
      detail: { message: message },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
    
    // Also log to console for debugging
    console.log(`[Library Card] Toast: ${message}`);
  }

  render() {
    try {
      const filteredItems = this._getFilteredItems();

      // If an item is selected, show detail view instead of grid
      if (this._selectedItem) {
        return html`
          <ha-card>
            <div class="header">
              <button class="back-button" @click=${this._closeDetail} aria-label="Back to library">
                <ha-icon icon="mdi:arrow-left"></ha-icon>
                Back to Library
              </button>
            </div>
            ${this._renderDetailView()}
          </ha-card>
        `;
      }

      // Normal grid view
      return html`
        <ha-card>
          <div class="header">
            <h2 class="header-title">
              ${this.config.title}
              <span class="count-badge" aria-label="${filteredItems.length} items">(${filteredItems.length})</span>
            </h2>

            ${this.config.show_search ? html`
              <div class="search-row">
                <input
                  type="search"
                  class="search-input"
                  placeholder="Search library..."
                  .value=${this._searchQuery}
                  @input=${this._handleSearch}
                  aria-label="Search library"
                />
              </div>
            ` : ''}

            ${this.config.show_filters ? html`
              <div class="filter-row" role="group" aria-label="Filter options">
                <select 
                  class="filter-select" 
                  @change=${this._handleFilterChange}
                  aria-label="Filter by type"
                >
                  <option value="all">All Types</option>
                  <option value="movie">Movies</option>
                  <option value="series">Series</option>
                </select>
                <select 
                  class="filter-select" 
                  @change=${this._handleSortChange}
                  aria-label="Sort by"
                >
                  <option value="recent">Most Recent</option>
                  <option value="title">Title A-Z</option>
                  <option value="progress">Progress</option>
                </select>
              </div>
            ` : ''}
          </div>

          ${filteredItems.length > 0 ? html`
            <div class="library-grid" role="list" aria-label="Library items">
              ${filteredItems.map(item => this._renderItem(item))}
            </div>
          ` : html`
            <div class="empty-state" role="status">
              <ha-icon icon="mdi:movie-open-outline"></ha-icon>
              <div>No items found</div>
            </div>
          `}
        </ha-card>
      `;
    } catch (error) {
      console.error('Stremio Library Card render error:', error);
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

  _renderDetailView() {
    const item = this._selectedItem;
    const title = item.title || item.name || 'Unknown';

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
            ${item.progress_percent ? html`
              <div class="detail-progress-container">
                <p class="detail-meta">Progress: ${item.progress_percent.toFixed(0)}%</p>
                <div class="detail-progress-bar">
                  <div class="detail-progress-fill" style="width: ${item.progress_percent}%"></div>
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        <div class="detail-actions">
          <button class="detail-button primary" @click=${() => this._openInStremio(item)}>
            <ha-icon icon="mdi:play"></ha-icon>
            Open in Stremio
          </button>
          <button class="detail-button secondary" @click=${() => this._getStreams(item)}>
            <ha-icon icon="mdi:format-list-bulleted"></ha-icon>
            Get Streams
          </button>
        </div>
      </div>
    `;
  }

  _renderItem(item) {
    const title = item.title || item.name || 'Unknown';
    const progress = item.progress_percent || 0;

    return html`
      <div 
        class="library-item" 
        role="listitem"
        tabindex="0"
        @click=${() => this._handleItemClick(item)}
        @keydown=${(e) => e.key === 'Enter' && this._handleItemClick(item)}
        aria-label="${title}${progress > 0 ? `, ${progress.toFixed(0)}% watched` : ''}"
      >
        ${item.poster ? html`
          <img class="item-poster" src="${item.poster}" alt="" loading="lazy" />
        ` : html`
          <div class="item-poster-placeholder">
            <ha-icon icon="mdi:movie-outline"></ha-icon>
          </div>
        `}
        <div class="item-title" title="${title}">${title}</div>
        ${progress > 0 ? html`
          <div class="item-progress" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
            <div class="item-progress-fill" style="width: ${progress}%"></div>
          </div>
        ` : ''}
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

  static getConfigElement() {
    return document.createElement('stremio-library-card-editor');
  }

  static getStubConfig() {
    return {
      title: 'Stremio Library',
      show_search: true,
      show_filters: true,
      max_items: 50,
    };
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-library-card')) {
  customElements.define('stremio-library-card', StremioLibraryCard);
}

// Editor
class StremioLibraryCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      _config: { type: Object },
      _stremioEntities: { type: Array },
    };
  }

  setConfig(config) {
    this._config = config;
  }

  updated(changedProps) {
    if (changedProps.has('hass') && this.hass) {
      this._updateStremioEntities();
    }
  }

  _updateStremioEntities() {
    // Find all Stremio library sensors
    this._stremioEntities = Object.keys(this.hass.states)
      .filter(entityId => 
        entityId.includes('stremio') && 
        entityId.includes('library_count')
      )
      .map(entityId => ({
        entity_id: entityId,
        friendly_name: this.hass.states[entityId].attributes.friendly_name || entityId,
      }));
  }

  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      <div class="card-config">
        <div class="entity-section">
          <label class="section-label">Library Sensor</label>
          
          ${this._stremioEntities?.length > 0 ? html`
            <div class="entity-buttons">
              ${this._stremioEntities.map(entity => html`
                <button 
                  class="entity-btn ${this._config.entity === entity.entity_id ? 'selected' : ''}"
                  @click=${() => this._selectEntity(entity.entity_id)}
                >
                  <ha-icon icon="mdi:movie"></ha-icon>
                  <span>${entity.friendly_name}</span>
                </button>
              `)}
            </div>
          ` : html`
            <div class="no-entities">
              <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
              <span>No Stremio library sensors found. Make sure the integration is configured.</span>
            </div>
          `}
          
          <ha-entity-picker
            .hass=${this.hass}
            .value=${this._config.entity || ''}
            .configValue=${'entity'}
            .includeDomains=${['sensor']}
            .includeEntities=${this._stremioEntities?.map(e => e.entity_id) || []}
            label="Or select manually"
            allow-custom-entity
            @value-changed=${this._valueChanged}
          ></ha-entity-picker>
        </div>

        <ha-textfield
          label="Title"
          .value=${this._config.title || 'Stremio Library'}
          .configValue=${'title'}
          @input=${this._valueChanged}
        ></ha-textfield>

        <ha-formfield label="Show Search">
          <ha-switch
            .checked=${this._config.show_search !== false}
            .configValue=${'show_search'}
            @change=${this._valueChanged}
          ></ha-switch>
        </ha-formfield>

        <ha-formfield label="Show Filters">
          <ha-switch
            .checked=${this._config.show_filters !== false}
            .configValue=${'show_filters'}
            @change=${this._valueChanged}
          ></ha-switch>
        </ha-formfield>

        <ha-textfield
          label="Max Items"
          .value=${this._config.max_items || 50}
          .configValue=${'max_items'}
          type="number"
          min="1"
          max="200"
          @input=${this._valueChanged}
        ></ha-textfield>

        <ha-textfield
          label="Columns"
          .value=${this._config.columns || 4}
          .configValue=${'columns'}
          type="number"
          min="2"
          max="8"
          @input=${this._valueChanged}
        ></ha-textfield>
      </div>
    `;
  }

  _selectEntity(entityId) {
    this._config = { ...this._config, entity: entityId };
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
  }

  _valueChanged(ev) {
    if (!this._config || !this.hass) {
      return;
    }

    const target = ev.target;
    let value;
    
    if (target.configValue) {
      if (target.checked !== undefined) {
        value = target.checked;
      } else if (target.value !== undefined) {
        value = target.value;
        // Convert to number for numeric fields
        if (target.type === 'number') {
          value = Number(value);
        }
      }

      this._config = { ...this._config, [target.configValue]: value };
      
      const event = new CustomEvent('config-changed', {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      });
      this.dispatchEvent(event);
    }
  }

  static get styles() {
    return css`
      .card-config {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 16px;
      }

      .entity-section {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .section-label {
        font-weight: 500;
        color: var(--primary-text-color);
        font-size: 0.9em;
      }

      .entity-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .entity-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.9em;
        transition: all 0.2s ease;
      }

      .entity-btn:hover {
        background: var(--secondary-background-color);
        border-color: var(--primary-color);
      }

      .entity-btn.selected {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .entity-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .no-entities {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: var(--warning-color, #ff9800);
        color: white;
        border-radius: 8px;
        font-size: 0.9em;
      }

      .no-entities ha-icon {
        --mdc-icon-size: 20px;
      }

      ha-entity-picker {
        width: 100%;
      }

      ha-textfield {
        width: 100%;
      }
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-library-card-editor')) {
  customElements.define('stremio-library-card-editor', StremioLibraryCardEditor);
}
