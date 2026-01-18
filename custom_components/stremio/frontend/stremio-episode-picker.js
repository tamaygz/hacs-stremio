/**
 * Stremio Episode Picker Dialog
 * 
 * Modal dialog to select season and episode for TV shows before getting streams.
 * Highlights watched episodes and last watched position.
 * 
 * @customElement stremio-episode-picker
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

class StremioEpisodePicker extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      open: { type: Boolean },
      mediaItem: { type: Object },
      seasons: { type: Array },
      _selectedSeason: { type: Number },
      _loading: { type: Boolean },
      _episodes: { type: Array },
      _seriesMetadata: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      .overlay {
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
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
      }

      .overlay.open {
        opacity: 1;
        visibility: visible;
      }

      .dialog {
        background: var(--card-background-color);
        border-radius: 12px;
        max-width: 600px;
        width: 95%;
        max-height: 80vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        transform: scale(0.9);
        transition: transform 0.3s ease;
      }

      .overlay.open .dialog {
        transform: scale(1);
      }

      .dialog-header {
        padding: 16px 20px;
        border-bottom: 1px solid var(--divider-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .dialog-header h3 {
        margin: 0;
        font-size: 1.1em;
        color: var(--primary-text-color);
      }

      .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .close-btn:hover {
        background: var(--secondary-background-color);
      }

      .close-btn ha-icon {
        color: var(--secondary-text-color);
      }

      .dialog-content {
        padding: 16px 20px;
        overflow-y: auto;
        flex: 1;
      }

      .season-selector {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 16px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--divider-color);
      }

      .season-btn {
        padding: 8px 16px;
        border: 1px solid var(--divider-color);
        border-radius: 20px;
        background: transparent;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.9em;
        transition: all 0.2s ease;
      }

      .season-btn:hover {
        background: var(--secondary-background-color);
      }

      .season-btn.selected {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .season-btn.has-progress {
        border-color: var(--primary-color);
      }

      .episode-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .episode-item {
        display: flex;
        align-items: center;
        padding: 12px;
        background: var(--secondary-background-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        gap: 12px;
      }

      .episode-item:hover {
        background: var(--divider-color);
      }

      .episode-item.watched {
        opacity: 0.7;
      }

      .episode-item.last-watched {
        border: 2px solid var(--primary-color);
        background: rgba(var(--rgb-primary-color), 0.1);
      }

      .episode-number {
        font-weight: 600;
        color: var(--primary-text-color);
        min-width: 50px;
      }

      .episode-info {
        flex: 1;
        min-width: 0;
      }

      .episode-title {
        font-weight: 500;
        color: var(--primary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .episode-meta {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
      }

      .episode-progress {
        width: 100px;
        height: 4px;
        background: var(--divider-color);
        border-radius: 2px;
        overflow: hidden;
      }

      .episode-progress-fill {
        height: 100%;
        background: var(--primary-color);
      }

      .watched-badge {
        display: flex;
        align-items: center;
        gap: 4px;
        color: var(--success-color, #4caf50);
        font-size: 0.8em;
      }

      .watched-badge ha-icon {
        --mdc-icon-size: 14px;
      }

      .last-watched-badge {
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: 500;
      }

      .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        color: var(--secondary-text-color);
      }

      .loading ha-circular-progress {
        margin-bottom: 16px;
      }

      .empty {
        text-align: center;
        padding: 40px;
        color: var(--secondary-text-color);
      }

      .empty ha-icon {
        --mdc-icon-size: 48px;
        margin-bottom: 12px;
        opacity: 0.5;
      }
    `;
  }

  constructor() {
    super();
    this.open = false;
    this.seasons = [];
    this._selectedSeason = 1;
    this._loading = false;
    this._episodes = [];
    this._seriesMetadata = null;
    this._handleKeyDown = this._handleKeyDown.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    document.addEventListener('keydown', this._handleKeyDown);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('keydown', this._handleKeyDown);
  }

  _handleKeyDown(e) {
    if (this.open && e.key === 'Escape') {
      this._close();
    }
  }

  updated(changedProps) {
    if (changedProps.has('mediaItem') && this.mediaItem) {
      this._fetchSeriesMetadata();
    }
    if (changedProps.has('_selectedSeason') && !this._loading) {
      this._updateEpisodesForSeason();
    }
  }

  async _fetchSeriesMetadata() {
    const mediaId = this.mediaItem?.imdb_id;
    if (!mediaId || !this.hass) {
      console.warn('[Episode Picker] Cannot fetch metadata: missing mediaId or hass');
      this._loadFallbackData();
      return;
    }

    this._loading = true;
    console.log('[Episode Picker] Fetching series metadata for:', mediaId);

    try {
      // Call the get_series_metadata service via WebSocket
      const response = await this.hass.callWS({
        type: 'call_service',
        domain: 'stremio',
        service: 'get_series_metadata',
        service_data: { media_id: mediaId },
        return_response: true,
      });

      console.log('[Episode Picker] Metadata response:', response);

      // Extract metadata from response
      const metadata = response?.response?.metadata || response?.metadata;

      if (metadata && metadata.seasons && metadata.seasons.length > 0) {
        this._seriesMetadata = metadata;
        this.seasons = metadata.seasons.map(s => ({
          number: s.number,
          name: s.title || `Season ${s.number}`,
          episodes: s.episodes || [],
        }));

        // Set selected season to last watched or first available
        this._selectedSeason = this.mediaItem.lastWatchedSeason || this.seasons[0]?.number || 1;
        this._updateEpisodesForSeason();
        
        console.log('[Episode Picker] Loaded', this.seasons.length, 'seasons');
      } else {
        console.warn('[Episode Picker] No metadata returned, using fallback');
        this._loadFallbackData();
      }
    } catch (err) {
      console.error('[Episode Picker] Error fetching metadata:', err);
      this._loadFallbackData();
    } finally {
      this._loading = false;
    }
  }

  _updateEpisodesForSeason() {
    const seasonData = this.seasons.find(s => s.number === this._selectedSeason);
    
    if (seasonData && seasonData.episodes && seasonData.episodes.length > 0) {
      // Use real episode data from metadata
      this._episodes = seasonData.episodes.map(ep => {
        const isWatched = this._isEpisodeWatched(this._selectedSeason, ep.number);
        const isLastWatched = (
          this.mediaItem.lastWatchedSeason === this._selectedSeason &&
          this.mediaItem.lastWatchedEpisode === ep.number
        );
        
        return {
          number: ep.number,
          title: ep.title || `Episode ${ep.number}`,
          overview: ep.overview,
          thumbnail: ep.thumbnail,
          released: ep.released,
          watched: isWatched,
          progress: 0, // Could be enhanced with actual progress data
          isLastWatched: isLastWatched,
        };
      });
    } else {
      // Fallback to placeholder episodes
      this._episodes = Array.from({ length: 20 }, (_, i) => ({
        number: i + 1,
        title: `Episode ${i + 1}`,
        watched: false,
        progress: 0,
        isLastWatched: false,
      }));
    }
  }

  _isEpisodeWatched(season, episode) {
    const watched = this.mediaItem?.watched_episodes || [];
    return watched.some(w => w.season === season && w.episode === episode);
  }

  _loadFallbackData() {
    // Fallback when metadata fetch fails - use mediaItem data or defaults
    if (this.mediaItem?.seasons) {
      this.seasons = this.mediaItem.seasons;
      this._selectedSeason = this.mediaItem.lastWatchedSeason || 1;
    } else if (this.mediaItem?.total_seasons) {
      this.seasons = Array.from({ length: this.mediaItem.total_seasons }, (_, i) => ({
        number: i + 1,
        name: `Season ${i + 1}`,
        episodes: [],
      }));
      this._selectedSeason = this.mediaItem.lastWatchedSeason || 1;
    } else {
      // Minimal fallback - just show seasons 1-5
      this.seasons = Array.from({ length: 5 }, (_, i) => ({
        number: i + 1,
        name: `Season ${i + 1}`,
        episodes: [],
      }));
      this._selectedSeason = 1;
    }
    this._updateEpisodesForSeason();
  }

  _loadSeasons() {
    // This method is now replaced by _fetchSeriesMetadata
    // Kept for backwards compatibility
    this._fetchSeriesMetadata();
  }

  _loadEpisodes() {
    // This method is now replaced by _updateEpisodesForSeason
    // Kept for backwards compatibility
    this._updateEpisodesForSeason();
  }

  _selectSeason(seasonNum) {
    this._selectedSeason = seasonNum;
  }

  _selectEpisode(episode) {
    this._close();
    
    // Fire event with selected episode
    this.dispatchEvent(new CustomEvent('episode-selected', {
      bubbles: true,
      composed: true,
      detail: {
        mediaItem: this.mediaItem,
        season: this._selectedSeason,
        episode: episode.number,
        episodeTitle: episode.title,
      },
    }));
  }

  _close() {
    this.open = false;
    this.dispatchEvent(new CustomEvent('close'));
  }

  _handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      this._close();
    }
  }

  render() {
    return html`
      <div 
        class="overlay ${this.open ? 'open' : ''}" 
        @click=${this._handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="episode-picker-title"
        aria-hidden="${!this.open}"
      >
        <div class="dialog">
          <div class="dialog-header">
            <h3 id="episode-picker-title">
              ${this.mediaItem?.title || 'Select Episode'}
            </h3>
            <button 
              class="close-btn" 
              @click=${this._close}
              aria-label="Close dialog"
            >
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-content">
            ${this._loading ? this._renderLoading() : html`
              ${this._renderSeasonSelector()}
              ${this._renderEpisodeList()}
            `}
          </div>
        </div>
      </div>
    `;
  }

  _renderLoading() {
    return html`
      <div class="loading">
        <ha-circular-progress active></ha-circular-progress>
        <div>Loading episodes...</div>
      </div>
    `;
  }

  _renderSeasonSelector() {
    if (this.seasons.length <= 1) return '';

    return html`
      <div class="season-selector" role="tablist" aria-label="Select season">
        ${this.seasons.map(season => html`
          <button
            class="season-btn ${this._selectedSeason === season.number ? 'selected' : ''} ${season.hasProgress ? 'has-progress' : ''}"
            @click=${() => this._selectSeason(season.number)}
            role="tab"
            aria-selected="${this._selectedSeason === season.number}"
          >
            ${season.name || `Season ${season.number}`}
          </button>
        `)}
      </div>
    `;
  }

  _renderEpisodeList() {
    if (this._episodes.length === 0) {
      return html`
        <div class="empty">
          <ha-icon icon="mdi:television-off"></ha-icon>
          <div>No episodes available</div>
        </div>
      `;
    }

    return html`
      <div class="episode-list" role="list" aria-label="Episodes">
        ${this._episodes.map(episode => this._renderEpisodeItem(episode))}
      </div>
    `;
  }

  _renderEpisodeItem(episode) {
    const classes = [
      'episode-item',
      episode.watched ? 'watched' : '',
      episode.isLastWatched ? 'last-watched' : '',
    ].filter(Boolean).join(' ');

    return html`
      <div 
        class="${classes}"
        role="listitem"
        tabindex="0"
        @click=${() => this._selectEpisode(episode)}
        @keydown=${(e) => e.key === 'Enter' && this._selectEpisode(episode)}
      >
        <span class="episode-number">E${String(episode.number).padStart(2, '0')}</span>
        
        <div class="episode-info">
          <div class="episode-title">${episode.title}</div>
          <div class="episode-meta">
            ${episode.progress > 0 && episode.progress < 100 ? html`
              <div class="episode-progress">
                <div class="episode-progress-fill" style="width: ${episode.progress}%"></div>
              </div>
              <span>${Math.round(episode.progress)}%</span>
            ` : ''}
            ${episode.watched ? html`
              <span class="watched-badge">
                <ha-icon icon="mdi:check-circle"></ha-icon>
                Watched
              </span>
            ` : ''}
            ${episode.isLastWatched ? html`
              <span class="last-watched-badge">Continue</span>
            ` : ''}
          </div>
        </div>

        <ha-icon icon="mdi:play-circle-outline"></ha-icon>
      </div>
    `;
  }
}

// Guard against duplicate registration
if (!customElements.get('stremio-episode-picker')) {
  customElements.define('stremio-episode-picker', StremioEpisodePicker);
}

// Global helper to open the episode picker
window.StremioEpisodePicker = {
  show(hass, mediaItem, callback) {
    let picker = document.querySelector('stremio-episode-picker');
    if (!picker) {
      picker = document.createElement('stremio-episode-picker');
      document.body.appendChild(picker);
    }
    picker.hass = hass;
    picker.mediaItem = mediaItem;
    picker.open = true;
    
    // Set up callback for episode selection
    const handler = (e) => {
      picker.removeEventListener('episode-selected', handler);
      if (callback) callback(e.detail);
    };
    picker.addEventListener('episode-selected', handler);
    
    return picker;
  },

  hide() {
    const picker = document.querySelector('stremio-episode-picker');
    if (picker) {
      picker.open = false;
    }
  },
};
