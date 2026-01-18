/**
 * Stremio Cards Bundle - Entry Point
 * 
 * This file bundles all Stremio custom Lovelace cards for Home Assistant.
 * Cards are auto-registered when the integration loads.
 * 
 * @author @tamaygz
 * @version 0.3.2
 * @cacheBust 20260118b
 */

// Import card components (relative paths - all in frontend/ folder)
// Cache busting is handled via version query param on the bundle URL
import './stremio-browse-card.js';
import './stremio-continue-watching-card.js';
import './stremio-library-card.js';
import './stremio-media-details-card.js';
import './stremio-player-card.js';
import './stremio-stream-dialog.js';

// Card registration info - should match manifest.json version
const CARD_VERSION = '0.3.1';

console.info(
  `%c STREMIO CARDS %c ${CARD_VERSION} `,
  'color: white; background: #7b68ee; font-weight: bold;',
  'color: #7b68ee; background: white; font-weight: bold;'
);

// Register cards with Lovelace
window.customCards = window.customCards || [];

window.customCards.push({
  type: 'stremio-player-card',
  name: 'Stremio Player Card',
  description: 'Display current Stremio playback with media info and controls',
  preview: true,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});

window.customCards.push({
  type: 'stremio-library-card',
  name: 'Stremio Library Card',
  description: 'Browse and search your Stremio library',
  preview: true,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});

window.customCards.push({
  type: 'stremio-media-details-card',
  name: 'Stremio Media Details Card',
  description: 'Display full media metadata with description, cast, and actions',
  preview: true,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});

window.customCards.push({
  type: 'stremio-stream-dialog',
  name: 'Stremio Stream Dialog',
  description: 'Stream selector dialog for choosing playback sources',
  preview: false,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});

window.customCards.push({
  type: 'stremio-browse-card',
  name: 'Stremio Browse Card',
  description: 'Browse popular movies, TV shows, and new content from Stremio catalogs',
  preview: true,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});

window.customCards.push({
  type: 'stremio-continue-watching-card',
  name: 'Stremio Continue Watching Card',
  description: 'Display and resume content from your Continue Watching list with progress indicators',
  preview: true,
  documentationURL: 'https://github.com/tamaygz/hacs-stremio/blob/main/docs/ui.md',
});
