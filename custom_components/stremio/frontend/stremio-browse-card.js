/**
 * Stremio Browse Card
 * 
 * Browse popular movies, TV shows, and new content from Stremio catalogs.
 * Features inline detail view (like library cards) and episode selection for TV shows.
 * 
 * @customElement stremio-browse-card
 * @extends LitElement
 * @version 0.4.0
 * @cacheBust 20260118c
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
        overflow-y: auto;
        align-items: start;
        flex: 1;
        min-height: 0;
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
        display: flex;
        flex-direction: column;
        align-self: start;
      }

      .catalog-item:hover {
        transform: scale(1.05);
      }

      .catalog-item:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
        transform: scale(1.05);
      }

      .catalog-poster-container {
        width: 100%;
        aspect-ratio: var(--poster-aspect-ratio, 2/3);
        position: relative;
        overflow: hidden;
        border-radius: 8px 8px 0 0;
        background: var(--secondary-background-color);
        flex-shrink: 0;
      }

      .catalog-poster {
        width: 100%;
        height: 100%;
        object-fit: cover;
        position: absolute;
        top: 0;
        left: 0;
      }

      .catalog-poster-placeholder {
        width: 100%;
        height: 100%;
        position: absolute;
        top: 0;
        left: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--secondary-background-color);
      }

      .catalog-poster-placeholder ha-icon {
        --mdc-icon-size: 32px;
        color: var(--secondary-text-color);
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

      .item-title {
        padding: 8px 8px 2px;
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

      .item-year {
        padding: 0 8px 8px;
        font-size: 0.75em;
        color: var(--secondary-text-color);
        text-align: center;
        background: var(--card-background-color);
      }

      .item-poster-container {
        width: 100%;
        aspect-ratio: var(--poster-aspect-ratio, 2/3);
        position: relative;
        overflow: hidden;
        border-radius: 8px 8px 0 0;
        background: var(--secondary-background-color);
        flex-shrink: 0;
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
        background: var(--secondary-background-color);
      }

      .item-poster-placeholder ha-icon {
        --mdc-icon-size: 32px;
        color: var(--secondary-text-color);
      }

      .count-badge {
        font-size: 0.7em;
        font-weight: normal;
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
        flex: 1;
        overflow-y: auto;
        min-height: 0;
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

      .detail-episode {
        color: var(--primary-color);
        font-weight: 500;
        font-size: 0.95em;
        margin: 4px 0;
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
    this._viewMode = 'popular';
    this._mediaType = 'movie';
    this._selectedGenre = null;
    this._catalogItems = [];
    this._loading = false;
    this._selectedItem = null;
    this._similarItems = null;
    this._similarSourceItem = null;
    this._loadingSimilar = false;
    this._genres = [
      'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
      'Documentary', 'Drama', 'Family', 'Fantasy', 'History', 'Horror',
      'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western'
    ];
    
    // Bind methods that are used as event handlers
    this._closeSimilarView = this._closeSimilarView.bind(this);
    this._closeDetail = this._closeDetail.bind(this);
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
      show_media_type_badge: false, // Show movie/series badge on poster
      show_similar_button: true, // Show "Find Similar" button in detail view
      
      // Layout options
      columns: 4,
      max_items: 50,
      card_height: 500, // Max height in pixels (0 for auto)
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
      show_media_type_badge: false,
      show_similar_button: true,
      columns: 4,
      max_items: 50,
      card_height: 500,
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
    // Extract media type from content ID or use current media type filter
    const mediaType = this._getItemMediaType(item);
    
    // For TV series, show episode picker first
    if (mediaType === 'series') {
      console.log('[Browse Card] TV Series clicked, showing episode picker first');
      this._showEpisodePicker(item, 'detail');
      return;
    }
    
    // For movies, go directly to detail view
    this._showDetailView(item);
  }

  _getItemMediaType(item) {
    // Try to determine media type from item or content ID
    // Check direct type property first (from similar content API)
    if (item.type) {
      return item.type === 'tvshow' ? 'series' : item.type;
    }
    if (item.media_content_type) {
      // Handle Home Assistant MediaType values (e.g., "video/movie", "video/tvshow")
      if (item.media_content_type.includes('movie')) {
        return 'movie';
      }
      if (item.media_content_type.includes('tvshow') || item.media_content_type.includes('series')) {
        return 'series';
      }
      return item.media_content_type === 'tvshow' ? 'series' : item.media_content_type;
    }
    if (item.media_content_id) {
      // Handle media-source:// URLs
      let path = item.media_content_id;
      if (path.includes('media-source://stremio/')) {
        path = path.replace('media-source://stremio/', '');
      }
      const parts = path.split('/');
      if (parts.length > 0) {
        const typeFromId = parts[0];
        if (typeFromId === 'series' || typeFromId === 'movie') {
          return typeFromId;
        }
      }
    }
    // Fallback to current filter
    return this._mediaType;
  }

  _showDetailView(item) {
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
          type: this._getItemMediaType(item),
        },
      })
    );
  }

  _closeDetail() {
    this._selectedItem = null;
    this.requestUpdate();
    
    // Fire event for external listeners
    this.dispatchEvent(
      new CustomEvent('stremio-detail-closed', {
        bubbles: true,
        composed: true,
      })
    );
  }

  _showEpisodePicker(item, mode = 'streams') {
    const onEpisodeSelected = (season, episode) => {
      console.log('[Browse Card] Episode selected:', { season, episode, mode });
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
    
    // Extract media ID from item
    const mediaId = this._extractMediaId(item);
    
    // Use the global helper if available
    if (window.StremioEpisodePicker) {
      window.StremioEpisodePicker.show(
        this._hass,
        {
          title: item.title,
          type: 'series',
          poster: item.thumbnail,
          imdb_id: mediaId,
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
        title: item.title,
        type: 'series',
        imdb_id: mediaId,
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

  _extractMediaId(item) {
    console.log('[Browse Card] _extractMediaId called with item:', item);
    // Extract IMDb ID from item - check direct properties first (from similar content API)
    if (item.imdb_id) {
      console.log('[Browse Card] Found imdb_id:', item.imdb_id);
      return item.imdb_id;
    }
    if (item.id && item.id.startsWith('tt')) {
      console.log('[Browse Card] Found id starting with tt:', item.id);
      return item.id;
    }
    // Try to extract from media_content_id
    // Format can be:
    // - "media-source://stremio/movie/tt1234567" (from browse_media)
    // - "movie/tt1234567" (simple format)
    if (item.media_content_id) {
      console.log('[Browse Card] Processing media_content_id:', item.media_content_id);
      // Handle media-source:// URLs
      if (item.media_content_id.includes('media-source://stremio/')) {
        const path = item.media_content_id.replace('media-source://stremio/', '');
        const parts = path.split('/');
        // Path is now "movie/tt1234567" or "series/tt1234567"
        if (parts.length > 1) {
          console.log('[Browse Card] Extracted ID from media-source URL:', parts[1]);
          return parts[1]; // Return the IMDB ID
        }
        return parts[0];
      }
      // Simple format: "type/id"
      const parts = item.media_content_id.split('/');
      if (parts.length > 1) {
        console.log('[Browse Card] Extracted ID from simple format:', parts[1]);
        return parts[1];
      }
      return parts[0];
    }
    console.log('[Browse Card] Falling back to item.id:', item.id);
    return item.id;
  }

  _openInStremio(item) {
    const type = this._getItemMediaType(item);
    const id = this._extractMediaId(item);
    
    // Validate ID format to prevent protocol injection
    if (id && typeof id === 'string') {
      const sanitizedId = id.replace(/[^a-zA-Z0-9_-]/g, '');
      if (sanitizedId && sanitizedId.length > 0) {
        window.open(`stremio://detail/${type}/${sanitizedId}`, '_blank');
      } else {
        console.warn('Stremio Browse Card: Invalid media ID format', id);
      }
    }
  }

  _getStreams(item) {
    const mediaType = this._getItemMediaType(item);
    
    // For series, show episode picker first
    if (mediaType === 'series') {
      console.log('[Browse Card] TV Show detected, opening episode picker');
      this._showEpisodePicker(item, 'streams');
      return;
    }

    // For movies, fetch streams directly
    this._fetchStreams(item, null, null);
  }

  _fetchStreams(item, season, episode) {
    const id = this._extractMediaId(item);
    const mediaType = this._getItemMediaType(item);
    
    console.log('[Browse Card] Getting streams for:', id, mediaType, season ? `S${season}E${episode}` : '');
    this._showToast('Fetching streams...');
    
    const serviceData = {
      media_id: id,
      media_type: mediaType,
    };
    
    // Add season/episode for series
    if (mediaType === 'series' && season && episode) {
      serviceData.season = season;
      serviceData.episode = episode;
    }

    // Call service with return_response using WebSocket directly
    this._hass.callWS({
      type: 'call_service',
      domain: 'stremio',
      service: 'get_streams',
      service_data: serviceData,
      return_response: true,
    })
      .then((response) => {
        console.log('[Browse Card] Streams response:', response);
        
        let streams = null;
        if (response?.response?.streams) {
          streams = response.response.streams;
        } else if (response?.streams) {
          streams = response.streams;
        }
        
        if (streams && streams.length > 0) {
          console.log('[Browse Card] Found', streams.length, 'streams');
          const displayItem = { ...item };
          if (season && episode) {
            displayItem.title = `${item.title} - S${season}E${episode}`;
          }
          this._showStreamDialog(displayItem, streams);
        } else {
          console.log('[Browse Card] No streams in response:', response);
          this._showToast('No streams found for this title');
        }
      })
      .catch((error) => {
        console.error('[Browse Card] Failed to get streams:', error);
        this._showToast(`Failed to get streams: ${error.message}`, 'error');
      });
  }

  _showStreamDialog(item, streams) {
    console.log('[Browse Card] Opening stream dialog with', streams.length, 'streams');
    
    // Use the global helper if available
    if (window.StremioStreamDialog) {
      window.StremioStreamDialog.show(
        this._hass,
        {
          title: item.title,
          type: this._getItemMediaType(item),
          poster: item.thumbnail,
          imdb_id: this._extractMediaId(item),
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
        title: item.title,
        type: this._getItemMediaType(item),
        poster: item.thumbnail,
      };
      dialog.streams = streams;
      dialog.appleTvEntity = this.config.apple_tv_entity;
      dialog.open = true;
    }
  }

  _addToLibrary(item) {
    const mediaType = this._getItemMediaType(item);
    const mediaId = this._extractMediaId(item);

    if (mediaId && this._hass) {
      this._hass.callService('stremio', 'add_to_library', {
        media_id: mediaId,
        media_type: mediaType,
      }).then(() => {
        this._showToast(`Added "${item.title}" to library`);
      }).catch((error) => {
        console.error('[Browse Card] Failed to add to library:', error);
        this._showToast(`Failed to add to library: ${error.message}`, 'error');
      });
    }
  }

  _getSimilarContent(item) {
    const mediaId = this._extractMediaId(item);
    if (!mediaId || !this._hass) {
      console.error('[Browse Card] Cannot get similar: missing ID or hass');
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
        console.log('[Browse Card] Similar content response:', response);
        this._loadingSimilar = false;
        
        let similarItems = null;
        if (response?.response?.similar) {
          similarItems = response.response.similar;
        } else if (response?.similar) {
          similarItems = response.similar;
        }
        
        if (similarItems && similarItems.length > 0) {
          console.log('[Browse Card] Found', similarItems.length, 'similar items');
          this._similarSourceItem = item;
          this._similarItems = similarItems;
          this._selectedItem = null; // Close detail view to show similar grid
        } else {
          console.log('[Browse Card] No similar content found');
          this._showToast('No similar content found');
        }
      })
      .catch((error) => {
        console.error('[Browse Card] Failed to get similar content:', error);
        this._loadingSimilar = false;
        this._showToast(`Failed to get similar content: ${error.message}`, 'error');
      });
  }

  /**
   * Close the similar items view and return to the catalog.
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
    // Similar items have poster/name/type/imdb_id, catalog items have thumbnail/title/media_content_id
    const normalizedItem = {
      ...item,
      title: item.title || item.name,
      thumbnail: item.thumbnail || item.poster,
      // Ensure media_content_id is set if not present (for _extractMediaId fallback)
      media_content_id: item.media_content_id || `${item.type || 'movie'}/${item.imdb_id || item.id}`,
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
        class="catalog-item" 
        role="listitem"
        tabindex="0"
        @click=${() => this._handleSimilarItemClick(item)}
        @keydown=${(e) => e.key === 'Enter' && this._handleSimilarItemClick(item)}
        aria-label="${title}${year ? ` (${year})` : ''}"
        style="--poster-aspect-ratio: ${this.config.poster_aspect_ratio || '2/3'}"
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

  /**
   * Get streams for the item shown in detail view.
   * For series with a selected episode, use that. Otherwise, prompt for episode.
   */
  _getStreamsForDetailItem(item) {
    const mediaType = this._getItemMediaType(item);
    
    if (mediaType === 'series') {
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

  _showToast(message, type = 'info') {
    const event = new CustomEvent('hass-notification', {
      detail: { message: message },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
    console.log(`[Browse Card] Toast: ${message}`);
  }

  render() {
    const columns = Number(this.config.columns || 5);
    const posterAspectRatio = this.config.poster_aspect_ratio || '2/3';
    const cardHeight = this.config.card_height > 0 ? `${this.config.card_height}px` : 'none';
    const gridStyle = `--card-max-height: ${cardHeight}; --grid-columns: ${columns}; --poster-aspect-ratio: ${posterAspectRatio};`;

    // If showing similar items, show that view
    if (this._similarItems && this._similarItems.length > 0) {
      const sourceTitle = this._similarSourceItem?.title || this._similarSourceItem?.name || 'Unknown';
      return html`
        <ha-card>
          <div class="header">
            <button class="back-button" @click=${this._closeSimilarView} aria-label="Back to browse">
              <ha-icon icon="mdi:arrow-left"></ha-icon>
              Back to Browse
            </button>
            <h2 class="header-title" style="margin-top: 12px;">
              Similar to "${sourceTitle}"
              <span class="count-badge">(${this._similarItems.length})</span>
            </h2>
          </div>
          <div 
            class="catalog-grid ${this.config.horizontal_scroll ? 'horizontal' : ''}" 
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
            <button class="back-button" @click=${this._closeDetail} aria-label="Back to browse">
              <ha-icon icon="mdi:arrow-left"></ha-icon>
              Back to Browse
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
          <div 
            class="catalog-grid" 
            role="list"
            aria-label="Catalog items"
            style="${gridStyle} grid-template-columns: repeat(auto-fill, minmax(${100 + (columns - 4) * 20}px, 1fr));"
          >
            ${this._catalogItems.map(item => this._renderCatalogItem(item))}
          </div>
        `}
      </ha-card>
    `;
  }

  _renderCatalogItem(item) {
    const mediaType = this._getItemMediaType(item);
    
    return html`
      <div 
        class="catalog-item" 
        role="listitem"
        tabindex="0"
        aria-label="${item.title}"
        style="--poster-aspect-ratio: ${this.config.poster_aspect_ratio || '2/3'}"
        @click=${() => this._handleItemClick(item)}
        @keydown=${(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this._handleItemClick(item);
          }
        }}
      >
        <div class="catalog-poster-container">
          ${item.thumbnail ? html`
            <img 
              class="catalog-poster" 
              src="${item.thumbnail}" 
              alt=""
              loading="lazy"
            />
          ` : html`
            <div class="catalog-poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
        </div>
        ${this.config.show_media_type_badge ? html`
          <span class="media-type-badge ${mediaType}">${mediaType === 'series' ? 'TV' : 'Movie'}</span>
        ` : ''}
        ${this.config.show_title !== false ? html`
          <div class="catalog-title">${item.title}</div>
        ` : ''}
      </div>
    `;
  }

  _renderDetailView() {
    const item = this._selectedItem;
    const title = item.title || 'Unknown';
    const mediaType = this._getItemMediaType(item);
    const hasSelectedEpisode = mediaType === 'series' && item.selectedSeason && item.selectedEpisode;
    const episodeLabel = hasSelectedEpisode 
      ? `S${String(item.selectedSeason).padStart(2, '0')}E${String(item.selectedEpisode).padStart(2, '0')}`
      : null;

    return html`
      <div class="item-detail-view">
        <div class="detail-header">
          ${item.thumbnail ? html`
            <img class="detail-poster" src="${item.thumbnail}" alt="${title}" />
          ` : html`
            <div class="detail-poster-placeholder">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
          <div class="detail-info">
            <h3>${title}</h3>
            <p class="detail-type">${mediaType === 'series' ? 'TV Series' : 'Movie'}</p>
            ${episodeLabel ? html`<p class="detail-episode">Episode: ${episodeLabel}</p>` : ''}
            ${item.year ? html`<p class="detail-meta">Year: ${item.year}</p>` : ''}
          </div>
        </div>

        <div class="detail-actions">
          ${mediaType === 'series' ? html`
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
          <button class="detail-button tertiary" @click=${() => this._addToLibrary(item)}>
            <ha-icon icon="mdi:plus"></ha-icon>
            Add to Library
          </button>
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

  // For UI card editor support
  getCardSize() {
    return 3;
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
      _appleTvEntities: { type: Array },
      _expandedSections: { type: Object },
    };
  }

  constructor() {
    super();
    this._stremioEntities = [];
    this._appleTvEntities = [];
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

    // Find Apple TV media_player entities
    this._appleTvEntities = Object.keys(this.hass.states)
      .filter(entityId => {
        if (!entityId.startsWith('media_player.')) return false;
        const state = this.hass.states[entityId];
        const friendlyName = (state.attributes.friendly_name || '').toLowerCase();
        const entityLower = entityId.toLowerCase();
        // Match Apple TV by entity ID or friendly name
        return entityLower.includes('apple_tv') ||
               entityLower.includes('appletv') ||
               friendlyName.includes('apple tv') ||
               friendlyName.includes('appletv');
      })
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

  _selectAppleTv(entityId) {
    this._config = { ...this._config, apple_tv_entity: entityId || undefined };
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
          </div>
        ` : ''}
      </ha-card>
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
