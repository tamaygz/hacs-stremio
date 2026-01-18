/**
 * Stremio Media Details Card
 * 
 * A Lovelace card that displays full media metadata including
 * description, cast, year, genres, and provides access to streams.
 * 
 * @customElement stremio-media-details-card
 * @version 1.0.0
 */

const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class StremioMediaDetailsCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _media: { type: Object },
      _loading: { type: Boolean },
      _showStreamDialog: { type: Boolean },
      _expanded: { type: Boolean },
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
      }

      ha-card {
        overflow: hidden;
        position: relative;
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
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define a media_player entity');
    }
    this.config = {
      show_backdrop: true,
      show_cast: true,
      show_genres: true,
      max_cast: 8,
      ...config,
    };
  }

  getCardSize() {
    return 6;
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
    };
  }

  updated(changedProps) {
    super.updated(changedProps);
    if (changedProps.has('hass')) {
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
    
    // Build media object from entity attributes
    this._media = {
      title: attributes.media_title || entity.state,
      type: attributes.media_content_type || 'unknown',
      poster: attributes.entity_picture || attributes.media_image_url,
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
      media_id: attributes.media_id,
      stremio_id: attributes.stremio_id,
    };
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
          ${progressPercent > 0 ? html`
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
    if (!this._media.description) return '';

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
    };
  }

  static get styles() {
    return css`
      .form {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      ha-textfield, ha-switch {
        width: 100%;
      }
      .switch-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
    `;
  }

  setConfig(config) {
    this.config = config;
  }

  render() {
    if (!this.hass || !this.config) {
      return html``;
    }

    return html`
      <div class="form">
        <ha-entity-picker
          .hass=${this.hass}
          .value=${this.config.entity}
          .configValue=${'entity'}
          label="Media Player Entity"
          .includeDomains=${['media_player']}
          @value-changed=${this._valueChanged}
        ></ha-entity-picker>
        
        <div class="switch-row">
          <span>Show Backdrop</span>
          <ha-switch
            .checked=${this.config.show_backdrop !== false}
            .configValue=${'show_backdrop'}
            @change=${this._valueChanged}
          ></ha-switch>
        </div>
        
        <div class="switch-row">
          <span>Show Cast</span>
          <ha-switch
            .checked=${this.config.show_cast !== false}
            .configValue=${'show_cast'}
            @change=${this._valueChanged}
          ></ha-switch>
        </div>
        
        <div class="switch-row">
          <span>Show Genres</span>
          <ha-switch
            .checked=${this.config.show_genres !== false}
            .configValue=${'show_genres'}
            @change=${this._valueChanged}
          ></ha-switch>
        </div>
      </div>
    `;
  }

  _valueChanged(ev) {
    if (!this.config || !this.hass) return;
    
    const target = ev.target;
    const configValue = target.configValue;
    const value = target.checked !== undefined ? target.checked : ev.detail?.value;
    
    if (this.config[configValue] === value) return;
    
    const newConfig = {
      ...this.config,
      [configValue]: value,
    };
    
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: newConfig }
    }));
  }
}

// Register elements
customElements.define('stremio-media-details-card', StremioMediaDetailsCard);
customElements.define('stremio-media-details-card-editor', StremioMediaDetailsCardEditor);

// Register card info
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'stremio-media-details-card',
  name: 'Stremio Media Details',
  description: 'Display full media metadata with actions',
  preview: true,
  documentationURL: 'https://github.com/yourusername/hacs-stremio/blob/main/docs/ui.md',
});

console.info(
  '%c STREMIO-MEDIA-DETAILS-CARD %c v1.0.0 ',
  'color: white; background: #8458b3; font-weight: bold;',
  'color: #8458b3; background: white; font-weight: bold;'
);
