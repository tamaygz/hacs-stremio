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
      // Note: entity is NOT defaulted here - _resolveEntity will auto-discover
      show_filters: true,
      max_items: 20,
      columns: 4,
      ...config,
    };
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Load initial data if this is the first time hass is set
    if (!oldHass && hass) {
      this._updateContinueWatchingItems();
      this.requestUpdate();
      return;
    }
    
    // Check if the resolved entity state changed (handles auto-discovered entities)
    const resolvedEntity = this._resolveEntity(this.config);
    const oldState = oldHass?.states?.[resolvedEntity];
    const newState = hass?.states?.[resolvedEntity];
    
    if (oldState !== newState) {
      this._updateContinueWatchingItems();
      this.requestUpdate();
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
      console.log('[Continue Watching Card] No hass instance');
      this._continueWatchingItems = [];
      return;
    }

    // Get continue watching data from sensor - resolve from device name if needed
    const sensorEntity = this._resolveEntity(this.config);
    const entity = this._hass.states[sensorEntity];
    
    console.log('[Continue Watching Card] Looking for entity:', sensorEntity);
    console.log('[Continue Watching Card] Entity found:', entity ? 'yes' : 'no');
    console.log('[Continue Watching Card] Entity state:', entity?.state);
    console.log('[Continue Watching Card] Items in attributes:', entity?.attributes?.items?.length || 0);

    if (!entity?.attributes?.items) {
      this._continueWatchingItems = [];
      console.log('[Continue Watching Card] No items found');
      return;
    }

    this._continueWatchingItems = entity.attributes.items || [];
    console.log('[Continue Watching Card] Items loaded:', this._continueWatchingItems.length);
  }

  _resolveEntity(config) {
    // Helper to resolve entity from config - supports both entity ID and device name
    // Also auto-discovers entities when default doesn't exist
    
    if (config.entity) {
      // If it starts with sensor., it's already an entity ID - check if it exists
      if (config.entity.startsWith('sensor.')) {
        if (this._hass?.states?.[config.entity]) {
          console.log('[Continue Watching Card] Using configured entity:', config.entity);
          return config.entity;
        }
        // Configured entity doesn't exist, fall through to auto-discovery
        console.log('[Continue Watching Card] Configured entity not found:', config.entity);
      } else {
        // Treat it as a device name and try to find matching entity
        if (this._hass) {
          const deviceName = config.entity.toLowerCase();
          for (const entityId in this._hass.states) {
            if (entityId.includes('continue_watching_count')) {
              const normalizedEntityId = entityId.toLowerCase().replace(/_/g, '');
              const normalizedDeviceName = deviceName.replace(/[^a-z0-9]/g, '');
              if (normalizedEntityId.includes(normalizedDeviceName)) {
                console.log('[Continue Watching Card] Resolved device name to entity:', deviceName, '->', entityId);
                return entityId;
              }
            }
          }
        }
      }
    }
    
    // Auto-discover: find ANY stremio continue_watching_count sensor in the system
    if (this._hass) {
      for (const entityId in this._hass.states) {
        if (entityId.startsWith('sensor.stremio') && entityId.endsWith('_continue_watching_count')) {
          console.log('[Continue Watching Card] Auto-discovered continue watching sensor:', entityId);
          return entityId;
        }
      }
      // Also check for sensors containing stremio and continue_watching_count (different naming patterns)
      for (const entityId in this._hass.states) {
        if (entityId.includes('stremio') && entityId.includes('continue_watching_count')) {
          console.log('[Continue Watching Card] Auto-discovered continue watching sensor (pattern match):', entityId);
          return entityId;
        }
      }
    }
    
    // Last resort fallback
    console.log('[Continue Watching Card] No continue watching sensor found, using default');
    return 'sensor.stremio_continue_watching_count';
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
    // For TV series, show episode picker first to select season/episode
    if (item.type === 'series') {
      console.log('[Continue Watching Card] TV Series clicked, showing episode picker first');
      this._showEpisodePicker(item, 'detail');
      return;
    }
    
    // For movies, go directly to detail view
    this._showDetailView(item);
  }
  
  _showDetailView(item) {
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
    
    // Validate ID format to prevent protocol injection
    // IMDb IDs should match pattern: tt followed by 7-8 digits
    if (id && typeof id === 'string') {
      // Basic sanitization: only allow alphanumeric and safe characters
      const sanitizedId = id.replace(/[^a-zA-Z0-9_-]/g, '');
      if (sanitizedId && sanitizedId.length > 0) {
        window.open(`stremio://detail/${type}/${sanitizedId}`, '_blank');
      } else {
        console.warn('Stremio Continue Watching Card: Invalid media ID format', id);
      }
    }
  }

  _getStreams(item) {
    const id = item.imdb_id || item.id;
    if (!id || !this._hass) {
      console.error('[Continue Watching Card] Cannot get streams: missing ID or hass');
      return;
    }

    // For series, show episode picker first (but pre-select current episode)
    if (item.type === 'series') {
      console.log('[Continue Watching Card] TV Show detected, opening episode picker');
      this._showEpisodePicker(item, 'streams');
      return;
    }

    // For movies, fetch streams directly
    this._fetchStreams(item, null, null);
  }

  _showEpisodePicker(item, mode = 'streams') {
    const onEpisodeSelected = (season, episode) => {
      console.log('[Continue Watching Card] Episode selected:', { season, episode, mode });
      if (mode === 'detail') {
        // Create a modified item with selected episode info and show detail
        const itemWithEpisode = {
          ...item,
          selectedSeason: season,
          selectedEpisode: episode,
        };
        this._showDetailView(itemWithEpisode);
      } else {
        // Default: fetch streams for the selected episode
        this._fetchStreams(item, season, episode);
      }
    };
    
    // Use the global helper if available
    if (window.StremioEpisodePicker) {
      window.StremioEpisodePicker.show(
        this._hass,
        {
          title: item.title || item.name,
          type: item.type,
          poster: item.poster,
          imdb_id: item.imdb_id || item.id,
          // Pre-select the episode they were watching
          lastWatchedSeason: item.season,
          lastWatchedEpisode: item.episode,
          total_seasons: item.total_seasons,
          watched_episodes: item.watched_episodes || [],
        },
        (selection) => {
          onEpisodeSelected(selection.season, selection.episode);
        }
      );
    } else {
      // Fallback: Use current season/episode directly
      onEpisodeSelected(item.season, item.episode);
    }
  }

  _fetchStreams(item, season, episode) {
    const id = item.imdb_id || item.id;
    console.log('[Continue Watching Card] Getting streams for:', id, item.type, season ? `S${season}E${episode}` : '');
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

    // Call service with return_response using WebSocket directly
    // The callService with returnResponse=true doesn't work reliably
    this._hass.callWS({
      type: 'call_service',
      domain: 'stremio',
      service: 'get_streams',
      service_data: serviceData,
      return_response: true,
    })
      .then((response) => {
        console.log('[Continue Watching Card] Streams response:', response);
        
        // Handle different response formats:
        // WebSocket response: { response: { streams: [...] } }
        // Or direct: { streams: [...] }
        let streams = null;
        
        if (response?.response?.streams) {
          // Format: { response: { streams: [...] } }
          streams = response.response.streams;
        } else if (response?.streams) {
          // Format: { streams: [...] } (direct)
          streams = response.streams;
        }
        
        if (streams && streams.length > 0) {
          console.log('[Continue Watching Card] Found', streams.length, 'streams');
          // Show the stream dialog
          const displayItem = { ...item };
          if (season && episode) {
            displayItem.title = `${item.title || item.name} - S${season}E${episode}`;
          }
          this._showStreamDialog(displayItem, streams);
        } else {
          console.log('[Continue Watching Card] No streams in response:', response);
          this._showToast('No streams found for this title');
        }
      })
      .catch((error) => {
        console.error('[Continue Watching Card] Failed to get streams:', error);
        this._showToast(`Failed to get streams: ${error.message}`, 'error');
      });
  }

  _showStreamDialog(item, streams) {
    console.log('[Continue Watching Card] Opening stream dialog with', streams.length, 'streams');
    
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
    console.log(`[Continue Watching Card] Toast: ${message}`);
  }

  render() {
    try {
      const filteredItems = this._getFilteredItems();

      // If an item is selected, show detail view instead of grid
      if (this._selectedItem) {
        return html`
          <ha-card>
            <div class="header">
              <button class="back-button" @click=${this._closeDetail} aria-label="Back to continue watching">
                <ha-icon icon="mdi:arrow-left"></ha-icon>
                Back to Continue Watching
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
    const progress = typeof item.progress_percent === 'number' ? item.progress_percent : 0;

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

  _renderDetailView() {
    const item = this._selectedItem;
    const title = item.title || 'Unknown';
    const progress = typeof item.progress_percent === 'number' ? item.progress_percent : 0;
    // For continue watching, use selectedSeason/Episode if changed, otherwise use original season/episode
    const displaySeason = item.selectedSeason || item.season;
    const displayEpisode = item.selectedEpisode || item.episode;
    const hasEpisodeInfo = item.type === 'series' && displaySeason && displayEpisode;
    const episodeLabel = hasEpisodeInfo 
      ? `S${String(displaySeason).padStart(2, '0')}E${String(displayEpisode).padStart(2, '0')}`
      : null;

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
            ${episodeLabel ? html`<p class="detail-episode">Episode: ${episodeLabel}</p>` : ''}
            ${item.year ? html`<p class="detail-meta">Year: ${item.year}</p>` : ''}
            ${progress > 0 ? html`
              <div class="detail-progress-container">
                <p class="detail-meta">Progress: ${progress.toFixed(0)}%</p>
                <div class="detail-progress-bar">
                  <div class="detail-progress-fill" style="width: ${progress}%"></div>
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        ${item.type === 'series' ? html`
          <div class="detail-actions">
            <button class="detail-button tertiary" @click=${() => this._showEpisodePicker(item, 'detail')}>
              <ha-icon icon="mdi:playlist-play"></ha-icon>
              Change Episode
            </button>
          </div>
        ` : ''}

        <div class="detail-actions">
          <button class="detail-button primary" @click=${() => this._resumeInStremio(item)}>
            <ha-icon icon="mdi:play"></ha-icon>
            Resume in Stremio
          </button>
          <button class="detail-button secondary" @click=${() => this._getStreamsForDetailItem(item)}>
            <ha-icon icon="mdi:format-list-bulleted"></ha-icon>
            Get Streams
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Get streams for the item shown in detail view.
   * For series, use the selected/current episode. Otherwise, prompt for episode.
   */
  _getStreamsForDetailItem(item) {
    if (item.type === 'series') {
      const season = item.selectedSeason || item.season;
      const episode = item.selectedEpisode || item.episode;
      if (season && episode) {
        // Episode already selected/known, fetch streams directly
        this._fetchStreams(item, season, episode);
      } else {
        // No episode info, show picker
        this._showEpisodePicker(item, 'streams');
      }
    } else {
      // Movie - fetch directly
      this._fetchStreams(item, null, null);
    }
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
    return document.createElement('stremio-continue-watching-card-editor');
  }

  static getStubConfig() {
    return {
      type: 'custom:stremio-continue-watching-card',
      title: 'Continue Watching',
      entity: 'sensor.stremio_continue_watching_count',
      show_filters: true,
      max_items: 20,
      columns: 4,
    };
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-continue-watching-card')) {
  customElements.define('stremio-continue-watching-card', StremioContinueWatchingCard);
}

// Editor for Continue Watching Card
class StremioContinueWatchingCardEditor extends LitElement {
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
    // Find all Stremio continue_watching sensors
    this._stremioEntities = Object.keys(this.hass.states)
      .filter(entityId => 
        entityId.includes('stremio') && 
        entityId.includes('continue_watching')
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
          <label class="section-label">Continue Watching Sensor</label>
          
          ${this._stremioEntities?.length > 0 ? html`
            <div class="entity-buttons">
              ${this._stremioEntities.map(entity => html`
                <button 
                  class="entity-btn ${this._config.entity === entity.entity_id ? 'selected' : ''}"
                  @click=${() => this._selectEntity(entity.entity_id)}
                >
                  <ha-icon icon="mdi:play-pause"></ha-icon>
                  <span>${entity.friendly_name}</span>
                </button>
              `)}
            </div>
          ` : html`
            <div class="no-entities">
              <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
              <span>No Stremio continue watching sensors found. Make sure the integration is configured.</span>
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
          .value=${this._config.title || 'Continue Watching'}
          .configValue=${'title'}
          @input=${this._valueChanged}
        ></ha-textfield>

        <ha-formfield label="Show Filters">
          <ha-switch
            .checked=${this._config.show_filters !== false}
            .configValue=${'show_filters'}
            @change=${this._valueChanged}
          ></ha-switch>
        </ha-formfield>

        <ha-textfield
          label="Max Items"
          .value=${this._config.max_items || 20}
          .configValue=${'max_items'}
          type="number"
          min="1"
          max="100"
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
if (!customElements.get('stremio-continue-watching-card')) {
  customElements.define('stremio-continue-watching-card', StremioContinueWatchingCard);
}

// Guard against duplicate registration
if (!customElements.get('stremio-continue-watching-card-editor')) {
  customElements.define('stremio-continue-watching-card-editor', StremioContinueWatchingCardEditor);
}

// Note: Card registration with window.customCards is handled in stremio-card-bundle.js
// to prevent duplicate entries
