/**
 * Stremio Media Details Card
 * 
 * A Lovelace card that displays full media metadata including
 * description, cast, year, genres, and provides access to streams.
 * 
 * @customElement stremio-media-details-card
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

class StremioMediaDetailsCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _media: { type: Object },
      _loading: { type: Boolean },
      _showStreamDialog: { type: Boolean },
      _expanded: { type: Boolean },
      _fetchedMetadata: { type: Object },
      _metadataFetchId: { type: String },
    };
  }

  static get styles() {
    return css`
      :host {
        --card-background: var(--ha-card-background, var(--card-background-color, white));
        --text-primary: var(--primary-text-color, #212121);
        --text-secondary: var(--secondary-text-color, #727272);
        --primary: var(--primary-color, #03a9f4);
        --divider: var(--divider-color, rgba(0, 0, 0, 0.12));
        --stremio-purple: #8458b3;
        display: block;
        height: 100%;
      }

      ha-card {
        overflow: hidden;
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      .backdrop {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 200px;
        background-size: cover;
        background-position: center top;
        filter: blur(0px);
        opacity: 0.3;
        z-index: 0;
      }

      .backdrop::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 100px;
        background: linear-gradient(transparent, var(--card-background));
      }

      .content {
        position: relative;
        z-index: 1;
        padding: 16px;
        flex: 1;
        overflow-y: auto;
        min-height: 0;
      }

      .header {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }

      .poster-container {
        flex-shrink: 0;
        width: 130px;
        position: relative;
      }

      .poster {
        width: 130px;
        height: 195px;
        border-radius: 8px;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        background: var(--divider);
      }

      .no-poster {
        width: 130px;
        height: 195px;
        border-radius: 8px;
        background: var(--divider);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
      }

      .no-poster ha-icon {
        --mdc-icon-size: 48px;
        opacity: 0.5;
      }

      .progress-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 0 0 8px 8px;
        overflow: hidden;
      }

      .progress-bar {
        height: 100%;
        background: var(--stremio-purple);
        transition: width 0.3s ease;
      }

      .info {
        flex: 1;
        min-width: 0;
      }

      .title {
        font-size: 1.5em;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 4px 0;
        line-height: 1.2;
      }

      .subtitle {
        font-size: 0.95em;
        color: var(--text-secondary);
        margin: 0 0 8px 0;
      }

      .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
      }

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.85em;
        color: var(--text-secondary);
        background: rgba(0, 0, 0, 0.05);
        padding: 4px 8px;
        border-radius: 4px;
      }

      .meta-item ha-icon {
        --mdc-icon-size: 16px;
      }

      .rating {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #ffc107;
        font-weight: 500;
      }

      .rating ha-icon {
        --mdc-icon-size: 18px;
      }

      .genres {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 12px;
      }

      .genre-tag {
        font-size: 0.75em;
        padding: 3px 10px;
        background: var(--stremio-purple);
        color: white;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .description-section {
        margin-bottom: 16px;
      }

      .section-title {
        font-size: 0.9em;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .description {
        font-size: 0.9em;
        color: var(--text-secondary);
        line-height: 1.5;
        margin: 0;
      }

      .description.truncated {
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .expand-btn {
        background: none;
        border: none;
        color: var(--primary);
        cursor: pointer;
        padding: 4px 0;
        font-size: 0.85em;
        font-weight: 500;
      }

      .cast-section {
        margin-bottom: 16px;
      }

      .cast-list {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }

      .cast-member {
        font-size: 0.8em;
        padding: 4px 8px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
        color: var(--text-secondary);
      }

      .episode-section {
        margin-bottom: 16px;
        padding: 12px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 8px;
      }

      .episode-info {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .episode-badge {
        font-size: 0.75em;
        padding: 4px 10px;
        background: var(--primary);
        color: white;
        border-radius: 4px;
        font-weight: 600;
      }

      .episode-title {
        font-size: 0.95em;
        color: var(--text-primary);
        font-weight: 500;
      }

      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .action-btn {
        flex: 1;
        min-width: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px 16px;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
        font-size: 0.9em;
      }

      .action-btn.primary {
        background: var(--stremio-purple);
        color: white;
      }

      .action-btn.primary:hover {
        background: #6a4690;
        transform: translateY(-1px);
      }

      .action-btn.secondary {
        background: rgba(0, 0, 0, 0.05);
        color: var(--text-primary);
      }

      .action-btn.secondary:hover {
        background: rgba(0, 0, 0, 0.1);
      }

      .action-btn ha-icon {
        --mdc-icon-size: 20px;
      }

      .loading {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px;
        color: var(--text-secondary);
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        text-align: center;
        color: var(--text-secondary);
      }

      .empty-state ha-icon {
        --mdc-icon-size: 64px;
        opacity: 0.3;
        margin-bottom: 16px;
      }

      .empty-state p {
        margin: 0;
        font-size: 0.95em;
      }

      @media (max-width: 400px) {
        .header {
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .meta {
          justify-content: center;
        }

        .genres {
          justify-content: center;
        }
      }
    `;
  }

  constructor() {
    super();
    this._media = null;
    this._loading = false;
    this._showStreamDialog = false;
    this._expanded = false;
    this._fetchedMetadata = null;
    this._metadataFetchId = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define a media_player entity');
    }
    this.config = {
      // Display options
      show_backdrop: true,
      show_cast: true,
      show_genres: true,
      show_description: true,
      show_progress: true,
      expand_description: false, // Start with description expanded
      
      // Content limits
      max_cast: 8,
      max_description_lines: 3, // When collapsed
      
      // Device integration
      apple_tv_entity: undefined, // For Apple TV handover
      
      ...config,
    };
  }

  getCardSize() {
    return 6;
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
    return document.createElement('stremio-media-details-card-editor');
  }

  static getStubConfig() {
    return {
      entity: '',
      show_backdrop: true,
      show_cast: true,
      show_genres: true,
      show_description: true,
      show_progress: true,
      expand_description: false,
      max_cast: 8,
      max_description_lines: 3,
    };
  }

  // Optimize re-renders
  shouldUpdate(changedProps) {
    if (changedProps.has('config')) return true;
    if (changedProps.has('_media')) return true;
    if (changedProps.has('_loading')) return true;
    if (changedProps.has('_showStreamDialog')) return true;
    if (changedProps.has('_expanded')) return true;
    
    // For hass, only update if relevant entity changed
    if (changedProps.has('hass') && this.config?.entity) {
      const oldHass = changedProps.get('hass');
      const oldState = oldHass?.states?.[this.config.entity];
      const newState = this.hass?.states?.[this.config.entity];
      return oldState !== newState;
    }
    
    return false;
  }

  updated(changedProps) {
    super.updated(changedProps);
    if (changedProps.has('hass') || changedProps.has('config')) {
      this._updateMedia();
    }
  }

  _updateMedia() {
    if (!this.hass || !this.config.entity) return;

    const entity = this.hass.states[this.config.entity];
    if (!entity) {
      this._media = null;
      return;
    }

    const attributes = entity.attributes || {};
    const imdbId = attributes.imdb_id;
    const mediaType = attributes.type || attributes.media_content_type || 'movie';
    
    // Build media object from entity attributes
    this._media = {
      title: attributes.media_title || entity.state,
      type: mediaType,
      poster: attributes.entity_picture || attributes.media_image_url || attributes.poster,
      backdrop: attributes.backdrop_url,
      year: attributes.year,
      runtime: attributes.runtime || attributes.media_duration,
      rating: attributes.rating,
      description: attributes.description || attributes.overview,
      genres: attributes.genres || [],
      cast: attributes.cast || [],
      director: attributes.director,
      // Series-specific
      season: attributes.season,
      episode: attributes.episode,
      episode_title: attributes.episode_title,
      series_title: attributes.series_title,
      // Progress
      progress: attributes.media_position || 0,
      duration: attributes.media_duration || 0,
      // IDs for actions
      media_id: attributes.media_id || imdbId,
      stremio_id: attributes.stremio_id || imdbId,
      imdb_id: imdbId,
    };
    
    // If we have an imdb_id but missing detailed metadata, fetch it
    const needsMetadata = imdbId && (
      !this._media.description || 
      (this._media.genres?.length === 0) ||
      (this._media.cast?.length === 0)
    );
    
    // Only fetch if we haven't already fetched for this ID
    if (needsMetadata && this._metadataFetchId !== imdbId) {
      this._fetchMetadata(imdbId, mediaType);
    }
    
    // Apply any previously fetched metadata
    if (this._fetchedMetadata && this._metadataFetchId === imdbId) {
      this._applyFetchedMetadata();
    }
  }
  
  async _fetchMetadata(imdbId, mediaType) {
    if (!imdbId || !this.hass) return;
    
    // Mark that we're fetching for this ID
    this._metadataFetchId = imdbId;
    
    try {
      console.log('[Media Details] Fetching metadata for:', imdbId, mediaType);
      
      // Use the get_series_metadata service for series, or search for movies
      if (mediaType === 'series' || mediaType === 'episode') {
        const response = await this.hass.callWS({
          type: 'call_service',
          domain: 'stremio',
          service: 'get_series_metadata',
          service_data: { media_id: imdbId },
          return_response: true,
        });
        
        if (response?.response?.metadata) {
          this._fetchedMetadata = response.response.metadata;
          this._applyFetchedMetadata();
        }
      } else {
        // For movies, use search to get metadata
        const response = await this.hass.callWS({
          type: 'call_service',
          domain: 'stremio',
          service: 'search',
          service_data: { query: this._media.title, limit: 1 },
          return_response: true,
        });
        
        if (response?.response?.results?.[0]) {
          this._fetchedMetadata = response.response.results[0];
          this._applyFetchedMetadata();
        }
      }
    } catch (err) {
      console.warn('[Media Details] Failed to fetch metadata:', err);
    }
  }
  
  _applyFetchedMetadata() {
    if (!this._fetchedMetadata || !this._media) return;
    
    const meta = this._fetchedMetadata;
    
    // Only apply if we don't already have the data
    if (!this._media.description && meta.description) {
      this._media.description = meta.description;
    }
    if ((!this._media.genres || this._media.genres.length === 0) && meta.genres?.length > 0) {
      this._media.genres = meta.genres;
    }
    if ((!this._media.cast || this._media.cast.length === 0) && meta.cast?.length > 0) {
      this._media.cast = meta.cast;
    }
    if (!this._media.backdrop && meta.background) {
      this._media.backdrop = meta.background;
    }
    if (!this._media.rating && meta.imdbRating) {
      this._media.rating = meta.imdbRating;
    }
    if (!this._media.director && meta.director?.length > 0) {
      this._media.director = meta.director.join(', ');
    }
    if (!this._media.year && meta.year) {
      this._media.year = meta.year;
    }
    if (!this._media.runtime && meta.runtime) {
      this._media.runtime = meta.runtime;
    }
    
    // Trigger re-render
    this.requestUpdate();
  }

  render() {
    if (!this.hass || !this.config.entity) {
      return html`
        <ha-card>
          <div class="empty-state">
            <ha-icon icon="mdi:movie-search-outline"></ha-icon>
            <p>No entity configured</p>
          </div>
        </ha-card>
      `;
    }

    const entity = this.hass.states[this.config.entity];
    if (!entity) {
      return html`
        <ha-card>
          <div class="empty-state">
            <ha-icon icon="mdi:movie-search-outline"></ha-icon>
            <p>Entity not found: ${this.config.entity}</p>
          </div>
        </ha-card>
      `;
    }

    if (!this._media || entity.state === 'idle' || entity.state === 'off') {
      return html`
        <ha-card>
          <div class="empty-state">
            <ha-icon icon="mdi:filmstrip-off"></ha-icon>
            <p>No media currently playing</p>
          </div>
        </ha-card>
      `;
    }

    if (this._loading) {
      return html`
        <ha-card>
          <div class="loading">
            <ha-circular-progress indeterminate></ha-circular-progress>
          </div>
        </ha-card>
      `;
    }

    return html`
      <ha-card>
        ${this.config.show_backdrop && this._media.backdrop ? html`
          <div class="backdrop" style="background-image: url('${this._media.backdrop}')"></div>
        ` : ''}
        
        <div class="content">
          ${this._renderHeader()}
          ${this._renderEpisodeInfo()}
          ${this._renderDescription()}
          ${this._renderCast()}
          ${this._renderActions()}
        </div>
      </ha-card>
    `;
  }

  _renderHeader() {
    const progressPercent = this._media.duration > 0 
      ? (this._media.progress / this._media.duration) * 100 
      : 0;

    return html`
      <div class="header">
        <div class="poster-container">
          ${this._media.poster ? html`
            <img class="poster" src="${this._media.poster}" alt="${this._media.title}">
          ` : html`
            <div class="no-poster">
              <ha-icon icon="mdi:movie-outline"></ha-icon>
            </div>
          `}
          ${this.config.show_progress !== false && progressPercent > 0 ? html`
            <div class="progress-overlay">
              <div class="progress-bar" style="width: ${progressPercent}%"></div>
            </div>
          ` : ''}
        </div>
        
        <div class="info">
          <h2 class="title">${this._media.series_title || this._media.title}</h2>
          
          ${this._media.series_title && this._media.title !== this._media.series_title ? html`
            <p class="subtitle">${this._media.title}</p>
          ` : ''}
          
          <div class="meta">
            ${this._media.year ? html`
              <span class="meta-item">
                <ha-icon icon="mdi:calendar"></ha-icon>
                ${this._media.year}
              </span>
            ` : ''}
            
            ${this._media.runtime ? html`
              <span class="meta-item">
                <ha-icon icon="mdi:clock-outline"></ha-icon>
                ${this._formatRuntime(this._media.runtime)}
              </span>
            ` : ''}
            
            ${this._media.rating ? html`
              <span class="rating">
                <ha-icon icon="mdi:star"></ha-icon>
                ${this._media.rating}
              </span>
            ` : ''}
            
            <span class="meta-item">
              <ha-icon icon="${this._getTypeIcon(this._media.type)}"></ha-icon>
              ${this._formatType(this._media.type)}
            </span>
          </div>
          
          ${this.config.show_genres && this._media.genres?.length > 0 ? html`
            <div class="genres">
              ${this._media.genres.slice(0, 5).map(genre => html`
                <span class="genre-tag">${genre}</span>
              `)}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  _renderEpisodeInfo() {
    if (!this._media.season && !this._media.episode) return '';

    return html`
      <div class="episode-section">
        <div class="episode-info">
          ${this._media.season ? html`
            <span class="episode-badge">S${this._media.season}</span>
          ` : ''}
          ${this._media.episode ? html`
            <span class="episode-badge">E${this._media.episode}</span>
          ` : ''}
          ${this._media.episode_title ? html`
            <span class="episode-title">${this._media.episode_title}</span>
          ` : ''}
        </div>
      </div>
    `;
  }

  _renderDescription() {
    if (this.config.show_description === false || !this._media.description) return '';

    return html`
      <div class="description-section">
        <h3 class="section-title">Overview</h3>
        <p class="description ${this._expanded ? '' : 'truncated'}">
          ${this._media.description}
        </p>
        ${this._media.description.length > 200 ? html`
          <button class="expand-btn" @click=${this._toggleExpanded}>
            ${this._expanded ? 'Show less' : 'Show more'}
          </button>
        ` : ''}
      </div>
    `;
  }

  _renderCast() {
    if (!this.config.show_cast || !this._media.cast?.length) return '';

    return html`
      <div class="cast-section">
        <h3 class="section-title">
          ${this._media.director ? `Director: ${this._media.director}` : 'Cast'}
        </h3>
        <div class="cast-list">
          ${this._media.cast.slice(0, this.config.max_cast).map(member => html`
            <span class="cast-member">${member}</span>
          `)}
        </div>
      </div>
    `;
  }

  _renderActions() {
    return html`
      <div class="actions">
        <button class="action-btn primary" @click=${this._getStreams}>
          <ha-icon icon="mdi:play-circle"></ha-icon>
          Get Streams
        </button>
        
        <button class="action-btn secondary" @click=${this._openInStremio}>
          <ha-icon icon="mdi:open-in-app"></ha-icon>
          Open in Stremio
        </button>
      </div>
    `;
  }

  _toggleExpanded() {
    this._expanded = !this._expanded;
  }

  _formatRuntime(seconds) {
    if (typeof seconds === 'number') {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    }
    return seconds;
  }

  _formatType(type) {
    const types = {
      'movie': 'Movie',
      'episode': 'TV Episode',
      'series': 'TV Series',
      'tvshow': 'TV Show',
    };
    return types[type?.toLowerCase()] || type || 'Unknown';
  }

  _getTypeIcon(type) {
    const icons = {
      'movie': 'mdi:movie',
      'episode': 'mdi:television-classic',
      'series': 'mdi:television',
      'tvshow': 'mdi:television',
    };
    return icons[type?.toLowerCase()] || 'mdi:filmstrip';
  }

  async _getStreams() {
    if (!this._media.media_id && !this._media.stremio_id) {
      this._showNotification('No media ID available for stream lookup');
      return;
    }

    // Fire custom event for stream dialog
    this.dispatchEvent(new CustomEvent('stremio-open-stream-dialog', {
      bubbles: true,
      composed: true,
      detail: {
        mediaId: this._media.media_id || this._media.stremio_id,
        title: this._media.title,
        type: this._media.type,
        poster: this._media.poster,
      }
    }));

    // Also call the service if available
    try {
      await this.hass.callService('stremio', 'get_stream_url', {
        media_id: this._media.media_id || this._media.stremio_id,
      });
    } catch (e) {
      console.warn('Stream service call failed:', e);
    }
  }

  _openInStremio() {
    const id = this._media.stremio_id || this._media.media_id;
    const type = this._media.type || 'movie';
    
    if (id) {
      // Stremio deep link format
      let deepLink;
      if (type === 'episode' || type === 'series') {
        const seasonEp = this._media.season && this._media.episode 
          ? `:${this._media.season}:${this._media.episode}` 
          : '';
        deepLink = `stremio://detail/series/${id}${seasonEp}`;
      } else {
        deepLink = `stremio://detail/movie/${id}`;
      }
      
      window.open(deepLink, '_blank');
    } else {
      // Fallback: search by title
      const searchUrl = `stremio://search?search=${encodeURIComponent(this._media.title)}`;
      window.open(searchUrl, '_blank');
    }
  }

  _showNotification(message) {
    this.dispatchEvent(new CustomEvent('hass-notification', {
      bubbles: true,
      composed: true,
      detail: { message }
    }));
  }
}

// Card Editor
class StremioMediaDetailsCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
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
      content: false,
      device: false,
    };
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
      ha-textfield {
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

  setConfig(config) {
    this.config = config;
  }

  updated(changedProps) {
    if (changedProps.has('hass') && this.hass) {
      this._updateEntities();
    }
  }

  _updateEntities() {
    // Find Stremio media player entities
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
    this.config = { ...this.config, entity: entityId };
    this.dispatchEvent(new CustomEvent('config-changed', {
      bubbles: true,
      composed: true,
      detail: { config: this.config },
    }));
  }

  _selectAppleTv(entityId) {
    this.config = { ...this.config, apple_tv_entity: entityId || undefined };
    this.dispatchEvent(new CustomEvent('config-changed', {
      bubbles: true,
      composed: true,
      detail: { config: this.config },
    }));
  }

  _toggleSection(section) {
    this._expandedSections = {
      ...this._expandedSections,
      [section]: !this._expandedSections[section],
    };
  }

  render() {
    if (!this.hass || !this.config) {
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
                      class="entity-btn ${this.config.entity === entity.entity_id ? 'selected' : ''}"
                      @click=${() => this._selectEntity(entity.entity_id)}
                    >
                      <ha-icon icon="mdi:movie-outline"></ha-icon>
                      <span>${entity.friendly_name}</span>
                    </button>
                  `)}
                </div>
              ` : html`
                <div class="no-entities">
                  <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
                  <span>No Stremio media players found.</span>
                </div>
              `}
              
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this.config.entity || ''}
                .configValue=${'entity'}
                label="Or select manually"
                .includeDomains=${['media_player']}
                @value-changed=${this._valueChanged}
                allow-custom-entity
              ></ha-entity-picker>
            </div>
          ` : ''}}
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
                <ha-formfield label="Show Backdrop Image">
                  <ha-switch
                    .checked=${this.config.show_backdrop !== false}
                    .configValue=${'show_backdrop'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Progress Bar">
                  <ha-switch
                    .checked=${this.config.show_progress !== false}
                    .configValue=${'show_progress'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Content Section -->
        <div class="config-section">
          <div class="section-header" @click=${() => this._toggleSection('content')}>
            <ha-icon icon="mdi:text"></ha-icon>
            <span>Content Options</span>
            <ha-icon class="expand-icon ${this._expandedSections.content ? 'expanded' : ''}" icon="mdi:chevron-down"></ha-icon>
          </div>
          ${this._expandedSections.content ? html`
            <div class="section-content">
              <div class="toggle-group">
                <ha-formfield label="Show Description">
                  <ha-switch
                    .checked=${this.config.show_description !== false}
                    .configValue=${'show_description'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Cast">
                  <ha-switch
                    .checked=${this.config.show_cast !== false}
                    .configValue=${'show_cast'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Show Genres">
                  <ha-switch
                    .checked=${this.config.show_genres !== false}
                    .configValue=${'show_genres'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>

                <ha-formfield label="Expand Description by Default">
                  <ha-switch
                    .checked=${this.config.expand_description === true}
                    .configValue=${'expand_description'}
                    @change=${this._valueChanged}
                  ></ha-switch>
                </ha-formfield>
              </div>

              <div class="input-row">
                <ha-textfield
                  label="Max Cast Members"
                  .value=${this.config.max_cast || 8}
                  .configValue=${'max_cast'}
                  type="number"
                  min="1"
                  max="20"
                  @input=${this._valueChanged}
                ></ha-textfield>

                <ha-textfield
                  label="Description Lines (collapsed)"
                  .value=${this.config.max_description_lines || 3}
                  .configValue=${'max_description_lines'}
                  type="number"
                  min="1"
                  max="10"
                  @input=${this._valueChanged}
                ></ha-textfield>
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
              
              ${this._appleTvEntities?.length > 0 ? html`
                <div class="entity-buttons">
                  ${this._appleTvEntities.map(entity => html`
                    <button 
                      class="entity-btn ${this.config.apple_tv_entity === entity.entity_id ? 'selected' : ''}"
                      @click=${() => this._selectAppleTv(entity.entity_id)}
                    >
                      <ha-icon icon="mdi:apple"></ha-icon>
                      <span>${entity.friendly_name}</span>
                    </button>
                  `)}
                  <button 
                    class="entity-btn ${!this.config.apple_tv_entity ? 'selected' : ''}"
                    @click=${() => this._selectAppleTv('')}
                  >
                    <ha-icon icon="mdi:close"></ha-icon>
                    <span>None</span>
                  </button>
                </div>
              ` : ''}

              <ha-entity-picker
                .hass=${this.hass}
                .value=${this.config.apple_tv_entity || ''}
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
    if (!this.config || !this.hass) return;
    
    const target = ev.target;
    const configValue = target.configValue;
    let value = target.checked !== undefined ? target.checked : ev.detail?.value;
    
    // Convert to number for numeric fields
    if (target.type === 'number') {
      value = Number(value);
    }
    
    if (this.config[configValue] === value) return;
    
    const newConfig = {
      ...this.config,
      [configValue]: value,
    };
    
    this.dispatchEvent(new CustomEvent('config-changed', {
      bubbles: true,
      composed: true,
      detail: { config: newConfig },
    }));
  }
}

// Register elements (guard against duplicate registration)
if (!customElements.get('stremio-media-details-card')) {
  customElements.define('stremio-media-details-card', StremioMediaDetailsCard);
}
if (!customElements.get('stremio-media-details-card-editor')) {
  customElements.define('stremio-media-details-card-editor', StremioMediaDetailsCardEditor);
}

// Note: Card info is registered in stremio-card-bundle.js to avoid duplicates
