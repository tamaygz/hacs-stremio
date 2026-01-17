/**
 * Stremio Cards Bundle - Entry Point
 * 
 * This file bundles all Stremio custom Lovelace cards for Home Assistant.
 * Cards are auto-registered when the integration loads.
 * 
 * @author @tamaygz
 * @version 0.1.0
 */

// Import card components
import './stremio-player-card.js';
import './stremio-library-card.js';
import './stremio-stream-dialog.js';

// Card registration info
const CARD_VERSION = '0.1.0';

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
