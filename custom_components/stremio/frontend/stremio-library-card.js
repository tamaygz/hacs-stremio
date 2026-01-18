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
      _similarItems: { type: Array },
      _similarSourceItem: { type: Object },
      _loadingSimilar: { type: Boolean },
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
        grid-template-columns: repeat(var(--grid-columns, 4), 1fr);
        gap: 12px;
        padding: 16px;
        overflow-y: auto;
        flex: 1;
        min-height: 0;
      }

      .library-grid.horizontal {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: hidden;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
      }

      .library-grid.horizontal .library-item {
        flex: 0 0 auto;
        width: calc(100% / var(--grid-columns, 4) - 10px);
        min-width: 100px;
        scroll-snap-align: start;
      }

      .library-item {
        cursor: pointer;
        transition: transform 0.2s ease;
        position: relative;
        display: flex;
        flex-direction: column;
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

      .item-poster-container {
        width: 100%;
        /* Use padding-bottom technique for consistent aspect ratio across all browsers */
        /* --poster-height-ratio is height/width as percentage, e.g., 150 for 2:3 */
        padding-bottom: calc(var(--poster-height-ratio, 150) * 1%);
        position: relative;
        overflow: hidden;
        border-radius: 6px;
        background: var(--secondary-background-color);
        flex-shrink: 0;
        height: 0; /* Required for padding-bottom technique to work */
      }

      .item-poster {
        width: 100%;
        height: 100%;
        object-fit: cover;
        position: absolute;
        top: 0;
        left: 0;
      }

      .item-poster-placeholder {
        width: 100%;
        height: 100%;
        position: absolute;
        top: 0;
        left: 0;
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

      .item-year {
        font-size: 0.7em;
        color: var(--secondary-text-color);
        margin-top: 2px;
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

      .detail-button.tertiary {
        background: transparent;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
      }

      .detail-button.tertiary:hover {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .detail-episode {
        color: var(--primary-color);
        font-weight: 500;
        font-size: 0.95em;
        margin: 4px 0;
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
    this._similarItems = null;
    this._similarSourceItem = null;
    this._loadingSimilar = false;
    this._viewMode = 'library'; // 'library' or 'catalog'
    
    // Bind methods that are used as event handlers
    this._closeSimilarView = this._closeSimilarView.bind(this);
    this._closeDetail = this._closeDetail.bind(this);
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = {
      // Basic
      title: 'Stremio Library',
      entity: '', // Auto-discovered if empty
      
      // Display toggles
      show_search: true,
      show_filters: true,
      show_view_toggle: true,
      show_title: true, // Show title below poster
      show_media_type_badge: false, // Show movie/series badge
      show_similar_button: true, // Show "Find Similar" button in detail view
      
      // Layout
      default_view: 'library',
      columns: 4,
      max_items: 50,
      card_height: 400, // Max height in pixels (0 = no limit)
      poster_aspect_ratio: '2/3', // 2/3, 16/9, 1/1, 4/3
      horizontal_scroll: false, // Use horizontal scroll instead of grid
      
      // Behavior
      tap_action: 'show_detail', // show_detail, get_streams, open_stremio
      default_sort: 'recent', // recent, alphabetical, year
      
      // Device
      apple_tv_entity: '', // For handover functionality
      
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
      show_title: true,
      show_similar_button: true,
      default_view: 'library',
      columns: 4,
      max_items: 50,
      card_height: 400,
      poster_aspect_ratio: '2/3',
      tap_action: 'show_detail',
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
    if (changedProps.has('_similarItems')) return true;
    if (changedProps.has('_similarSourceItem')) return true;
    if (changedProps.has('_loadingSimilar')) return true;
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
    // For TV series, show episode picker first to select season/episode
    if (item.type === 'series') {
      console.log('[Library Card] TV Series clicked, showing episode picker first');
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
      this._showEpisodePicker(item, 'streams');
      return;
    }

    // For movies, fetch streams directly
    this._fetchStreams(item, null, null);
  }

  _showEpisodePicker(item, mode = 'streams') {
    const onEpisodeSelected = (season, episode) => {
      console.log('[Library Card] Episode selected:', { season, episode, mode });
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
          // Pass watch progress info for highlighting
          lastWatchedSeason: item.last_season || item.season,
          lastWatchedEpisode: item.last_episode || item.episode,
          total_seasons: item.total_seasons,
          watched_episodes: item.watched_episodes || [],
        },
        (selection) => {
          onEpisodeSelected(selection.season, selection.episode);
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
        onEpisodeSelected(e.detail.season, e.detail.episode);
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
        console.log('[Library Card] Streams response:', response);
        
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
        streams,
        this.config.apple_tv_entity
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
      dialog.appleTvEntity = this.config.apple_tv_entity;
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
      const columns = Number(this.config.columns || 4);
      const posterAspectRatio = this.config.poster_aspect_ratio || '2/3';
      const cardHeight = this.config.card_height > 0 ? `${this.config.card_height}px` : 'none';
      
      // Calculate height ratio for padding-bottom technique
      // For aspect ratio "w/h" (width/height), padding-bottom needs height/width * 100
      // e.g., "2/3" -> height/width = 3/2 = 1.5 -> 150%
      let posterHeightRatio = 150; // default 2:3 -> 150%
      if (posterAspectRatio.includes('/')) {
        const [w, h] = posterAspectRatio.split('/').map(Number);
        if (w > 0 && h > 0) {
          posterHeightRatio = (h / w) * 100;
        }
      }
      
      const gridStyle = `--card-max-height: ${cardHeight}; --grid-columns: ${columns}; --poster-height-ratio: ${posterHeightRatio};`;

      const filteredItems = this._getFilteredItems();

      // If showing similar items, show that view
      if (this._similarItems && this._similarItems.length > 0) {
        const sourceTitle = this._similarSourceItem?.title || this._similarSourceItem?.name || 'Unknown';
        return html`
          <ha-card>
            <div class="header">
              <button class="back-button" @click=${this._closeSimilarView} aria-label="Back to library">
                <ha-icon icon="mdi:arrow-left"></ha-icon>
                Back to Library
              </button>
              <h2 class="header-title" style="margin-top: 12px;">
                Similar to "${sourceTitle}"
                <span class="count-badge" aria-label="${this._similarItems.length} items">(${this._similarItems.length})</span>
              </h2>
            </div>
            <div 
              class="library-grid ${this.config.horizontal_scroll ? 'horizontal' : ''}" 
              role="list" 
              aria-label="Similar items"
              style="${gridStyle}"
            >
              ${this._similarItems.map(item => this._renderSimilarItem(item))}
            </div>
          </ha-card>
        `;
      }

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
            <div 
              class="library-grid ${this.config.horizontal_scroll ? 'horizontal' : ''}" 
              role="list" 
              aria-label="Library items"
              style="${gridStyle}"
            >
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
    const hasSelectedEpisode = item.type === 'series' && item.selectedSeason && item.selectedEpisode;
    const episodeLabel = hasSelectedEpisode 
      ? `S${String(item.selectedSeason).padStart(2, '0')}E${String(item.selectedEpisode).padStart(2, '0')}`
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
          ${item.type === 'series' ? html`
            <button class="detail-button tertiary" @click=${() => this._showEpisodePicker(item, 'detail')}>
              <ha-icon icon="mdi:playlist-play"></ha-icon>
              ${hasSelectedEpisode ? 'Change Episode' : 'Select Episode'}
            </button>
          ` : ''}
          ${this.config.show_similar_button !== false ? html`
            <button class="detail-button tertiary" @click=${() => this._getSimilarContent(item)} ?disabled=${this._loadingSimilar}>
              <ha-icon icon="mdi:movie-search"></ha-icon>
              ${this._loadingSimilar ? 'Loading...' : 'Find Similar'}
            </button>
          ` : ''}
        </div>

        <div class="detail-actions">
          <button class="detail-button primary" @click=${() => this._openInStremio(item)}>
            <ha-icon icon="mdi:play"></ha-icon>
            Open in Stremio
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
   * For series with a selected episode, use that. Otherwise, prompt for episode.
   */
  _getStreamsForDetailItem(item) {
    if (item.type === 'series') {
      if (item.selectedSeason && item.selectedEpisode) {
        // Episode already selected, fetch streams directly
        this._fetchStreams(item, item.selectedSeason, item.selectedEpisode);
      } else {
        // No episode selected, show picker
        this._showEpisodePicker(item, 'streams');
      }
    } else {
      // Movie - fetch directly
      this._fetchStreams(item, null, null);
    }
  }

  /**
   * Get similar content for the item and display in the card.
   */
  _getSimilarContent(item) {
    const mediaId = item.imdb_id || item.id;
    if (!mediaId || !this._hass) {
      console.error('[Library Card] Cannot get similar: missing ID or hass');
      return;
    }

    this._loadingSimilar = true;

    this._hass.callWS({
      type: 'call_service',
      domain: 'stremio',
      service: 'get_similar_content',
      service_data: {
        media_id: mediaId,
        limit: 20,
      },
      return_response: true,
    })
      .then((response) => {
        console.log('[Library Card] Similar content response:', response);
        this._loadingSimilar = false;
        
        let similarItems = null;
        if (response?.response?.similar) {
          similarItems = response.response.similar;
        } else if (response?.similar) {
          similarItems = response.similar;
        }
        
        if (similarItems && similarItems.length > 0) {
          console.log('[Library Card] Found', similarItems.length, 'similar items');
          this._similarSourceItem = item;
          this._similarItems = similarItems;
          this._selectedItem = null; // Close detail view to show similar grid
        } else {
          console.log('[Library Card] No similar content found');
          this._showToast('No similar content found');
        }
      })
      .catch((error) => {
        console.error('[Library Card] Failed to get similar content:', error);
        this._loadingSimilar = false;
        this._showToast(`Failed to get similar content: ${error.message}`, 'error');
      });
  }

  /**
   * Close the similar items view and return to the library.
   */
  _closeSimilarView() {
    this._similarItems = null;
    this._similarSourceItem = null;
    this.requestUpdate();
  }

  /**
   * Handle click on a similar item - show its detail view.
   */
  _handleSimilarItemClick(item) {
    // Clear similar view and show detail for this item
    this._similarItems = null;
    this._similarSourceItem = null;
    
    // Normalize item properties for consistent handling
    // Similar items from API have poster/name/type/imdb_id directly
    const normalizedItem = {
      ...item,
      title: item.title || item.name,
      name: item.name || item.title,
      poster: item.poster || item.thumbnail,
      imdb_id: item.imdb_id || item.id,
    };
    
    this._selectedItem = normalizedItem;
  }

  /**
   * Render a similar item in the grid.
   */
  _renderSimilarItem(item) {
    const title = item.title || item.name || 'Unknown';
    const year = item.year || item.releaseInfo || '';

    return html`
      <div 
        class="library-item" 
        role="listitem"
        tabindex="0"
        @click=${() => this._handleSimilarItemClick(item)}
        @keydown=${(e) => e.key === 'Enter' && this._handleSimilarItemClick(item)}
        aria-label="${title}${year ? ` (${year})` : ''}"
      >
        <div class="item-poster-container">
          ${item.poster ? html`
            <img class="item-poster" src="${item.poster}" alt="" loading="lazy" />
          ` : html`
            <div class="item-poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
        </div>
        ${item.type ? html`
          <span class="media-type-badge ${item.type}">${item.type === 'series' ? 'TV' : 'Movie'}</span>
        ` : ''}
        ${this.config.show_title !== false ? html`
          <div class="item-title" title="${title}">${title}</div>
        ` : ''}
        ${year ? html`
          <div class="item-year">${year}</div>
        ` : ''}
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
        <div class="item-poster-container">
          ${item.poster ? html`
            <img class="item-poster" src="${item.poster}" alt="" loading="lazy" />
          ` : html`
            <div class="item-poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
        </div>
        ${this.config.show_media_type_badge && item.type ? html`
          <span class="media-type-badge ${item.type}">${item.type === 'series' ? 'TV' : 'Movie'}</span>
        ` : ''}
        ${this.config.show_title !== false ? html`
          <div class="item-title" title="${title}">${title}</div>
        ` : ''}
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
    return document.createElement('stremio-library-card-editor');
  }

  static getStubConfig() {
    return {
      title: 'Stremio Library',
      show_search: true,
      show_filters: true,
      show_title: true,
      max_items: 50,
      columns: 4,
      card_height: 400,
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
      _appleTvEntities: { type: Array },
      _expandedSections: { type: Object },
    };
  }

  constructor() {
    super();
    this._stremioEntities = [];
    this._appleTvEntities = [];
    this._expandedSections = {
      entity: true,
      display: false,
      layout: false,
      behavior: false,
      device: false,
    };
  }

  setConfig(config) {
    this._config = config;
    // Refresh entity caches if hass is already available so the editor renders immediately
    if (this.hass) {
      this._updateEntities();
    }
  }

  updated(changedProps) {
    if (changedProps.has('hass') && this.hass) {
      this._updateEntities();
    }
  }

  _updateEntities() {
    // Find Stremio library sensors
    this._stremioEntities = Object.keys(this.hass.states)
      .filter(entityId => 
        entityId.includes('stremio') && 
        entityId.includes('library_count')
      )
      .map(entityId => ({
        entity_id: entityId,
        friendly_name: this.hass.states[entityId].attributes.friendly_name || entityId,
      }));

    // Find Apple TV media_player entities
    this._appleTvEntities = Object.keys(this.hass.states)
      .filter(entityId => {
        const state = this.hass.states[entityId];
        if (!entityId.startsWith('media_player.')) return false;

        const id = entityId.toLowerCase();
        const name = (state.attributes.friendly_name || '').toLowerCase();
        const app = (state.attributes.app_name || '').toLowerCase();
        const manufacturer = (state.attributes.manufacturer || '').toLowerCase();
        const model = (state.attributes.model || '').toLowerCase();

        return id.includes('apple_tv') || id.includes('appletv') ||
          name.includes('apple tv') || app.includes('apple tv') ||
          manufacturer.includes('apple') || model.includes('apple tv');
      })
      .map(entityId => ({
        entity_id: entityId,
        friendly_name: this.hass.states[entityId].attributes.friendly_name || entityId,
      }))
      .sort((a, b) => a.friendly_name.localeCompare(b.friendly_name));
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
                  <span>No Stremio library sensors found.</span>
                </div>
              `}
              
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this._config.entity || ''}
                .configValue=${'entity'}
                .includeDomains=${['sensor']}
                label="Or select manually"
                allow-custom-entity
                @value-changed=${this._valueChanged}
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
              <ha-textfield
                label="Card Title"
                .value=${this._config.title || 'Stremio Library'}
                .configValue=${'title'}
                @input=${this._valueChanged}
              ></ha-textfield>

              <div class="toggle-group">
                <ha-formfield label="Show Search Bar">
                  <ha-switch
                    .checked=${this._config.show_search !== false}
                    .configValue=${'show_search'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

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

                <ha-formfield label="Show Media Type Badge">
                  <ha-switch
                    .checked=${this._config.show_media_type_badge === true}
                    .configValue=${'show_media_type_badge'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Find Similar Button">
                  <ha-switch
                    .checked=${this._config.show_similar_button !== false}
                    .configValue=${'show_similar_button'}
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
                  max="200"
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
                <mwc-list-item value="play">Play Directly</mwc-list-item>
                <mwc-list-item value="streams">Get Streams</mwc-list-item>
              </ha-select>

              <ha-select
                label="Default Sort"
                .value=${this._config.default_sort || 'recent'}
                .configValue=${'default_sort'}
                @selected=${this._selectChanged}
                @closed=${(e) => e.stopPropagation()}
              >
                <mwc-list-item value="recent">Most Recent</mwc-list-item>
                <mwc-list-item value="title">Title A-Z</mwc-list-item>
                <mwc-list-item value="progress">Progress</mwc-list-item>
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

              ${(!this._appleTvEntities || this._appleTvEntities.length === 0) ? html`
                <p class="helper-text warning">No Apple TV media players detected. You can still pick any media_player below.</p>
              ` : ''}
              
              ${this._appleTvEntities?.length > 0 ? html`
                <div class="entity-buttons">
                  ${this._appleTvEntities.map(entity => html`
                    <button 
                      class="entity-btn ${this._config.apple_tv_entity === entity.entity_id ? 'selected' : ''}"
                      @click=${() => this._selectAppleTv(entity.entity_id)}
                    >
                      <ha-icon icon="mdi:apple"></ha-icon>
                      <span>${entity.friendly_name}</span>
                    </button>
                  `)}
                  <button 
                    class="entity-btn ${!this._config.apple_tv_entity ? 'selected' : ''}"
                    @click=${() => this._selectAppleTv('')}
                  >
                    <ha-icon icon="mdi:close"></ha-icon>
                    <span>None</span>
                  </button>
                </div>
              ` : ''}

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

  _selectEntity(entityId) {
    this._updateConfig('entity', entityId);
  }

  _selectAppleTv(entityId) {
    this._updateConfig('apple_tv_entity', entityId || undefined);
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
      } else if (ev.detail && ev.detail.value !== undefined) {
        // Fallback for components that emit value in the detail (e.g., ha-entity-picker)
        value = ev.detail.value;
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

      .helper-text {
        color: var(--secondary-text-color);
        font-size: 0.9em;
        margin: 0;
      }

      .helper-text.warning {
        color: var(--warning-color, #ff9800);
      }

      ha-entity-picker,
      ha-textfield,
      ha-select {
        width: 100%;
      }
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-library-card-editor')) {
  customElements.define('stremio-library-card-editor', StremioLibraryCardEditor);
}
