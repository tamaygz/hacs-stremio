# Apple TV Device ID Bug - Investigation Update

## Media Details Card - Detailed Analysis

### Current Implementation

The **Media Details Card** uses a **completely different approach** from other cards for stream handling:

**File**: `custom_components/stremio/frontend/stremio-media-details-card.js`

**Lines 867-893**: `_getStreams()` method
```javascript
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
    await this.hass.callService('stremio', 'get_streams', {
      media_id: this._media.media_id || this._media.stremio_id,
    });
  } catch (e) {
    console.warn('Stream service call failed:', e);
  }
}
```

### Key Findings

#### 1. **Event-Based Approach (Non-Functional)**
- Fires a custom event `stremio-open-stream-dialog`
- **PROBLEM**: No event listeners exist anywhere in the codebase for this event
- Search results: Only 1 occurrence - the dispatch itself
- **CONCLUSION**: This event is never caught, making it dead code

#### 2. **Service Call Issues**
- Calls `stremio.get_streams` service
- **PROBLEM**: Missing `media_type` parameter (required by service schema)
- **PROBLEM**: Missing `season`/`episode` for TV series
- The service call will **fail validation** for series content
- Even if it succeeds, the response is not handled - no `.then()` or `await` handling

#### 3. **No Stream Dialog Integration**
- Unlike other cards, this card does NOT:
  - Import or use `StremioStreamDialog.show()`
  - Create a fallback dialog element
  - Handle the service response to display streams
  - Pass `apple_tv_entity` anywhere

### Comparison with Working Cards

**Browse Card Pattern** (working):
```javascript
_fetchStreams(item, season, episode) {
  // Prepare service data
  const serviceData = {
    media_id: id,
    media_type: mediaType,
  };
  
  if (mediaType === 'series' && season && episode) {
    serviceData.season = season;
    serviceData.episode = episode;
  }

  // Call service and HANDLE response
  this._hass.callWS({
    type: 'call_service',
    domain: 'stremio',
    service: 'get_streams',
    service_data: serviceData,
    return_response: true,
  })
    .then((response) => {
      const streams = response?.response?.streams || response?.streams;
      if (streams && streams.length > 0) {
        // ✅ SHOW STREAM DIALOG with streams
        this._showStreamDialog(item, streams);
      }
    });
}

_showStreamDialog(item, streams) {
  if (window.StremioStreamDialog) {
    window.StremioStreamDialog.show(
      this._hass,
      mediaItem,
      streams,
      this.config.apple_tv_entity  // ✅ PASSES APPLE TV ENTITY
    );
  }
}
```

**Media Details Card** (broken):
```javascript
async _getStreams() {
  // ❌ Fires event that nothing listens to
  this.dispatchEvent(new CustomEvent('stremio-open-stream-dialog', { ... }));

  // ❌ Calls service without handling response
  // ❌ Missing media_type parameter
  // ❌ Missing season/episode for series
  try {
    await this.hass.callService('stremio', 'get_streams', {
      media_id: this._media.media_id || this._media.stremio_id,
    });
  } catch (e) {
    console.warn('Stream service call failed:', e);
  }
  // ❌ No .then() to handle response
  // ❌ No stream dialog shown
  // ❌ No apple_tv_entity passed
}
```

---

## Root Cause Summary

### Media Details Card Has Three Issues:

1. **Dead Event Code**: Fires `stremio-open-stream-dialog` event but no listeners exist
2. **Incomplete Service Call**: Missing required parameters and no response handling
3. **No Stream Dialog Integration**: Doesn't show streams to user or support handover

### This is NOT the same bug as other cards!

- **Continue Watching Card**: Has config, has dialog integration, just missing parameter pass
- **Recommendations Card**: Missing config + missing parameter pass
- **Media Details Card**: Missing ENTIRE stream workflow implementation

---

## Recommended Solutions

### Option 1: Implement Full Stream Workflow (Recommended)

Follow the Browse Card pattern:

```javascript
async _getStreams() {
  if (!this._media.media_id && !this._media.stremio_id) {
    this._showNotification('No media ID available for stream lookup');
    return;
  }

  const mediaId = this._media.media_id || this._media.stremio_id;
  const mediaType = this._media.type || 'movie';
  
  // For series, show episode picker first
  if (mediaType === 'series') {
    this._showEpisodePicker(mediaId);
    return;
  }
  
  // For movies, fetch streams directly
  this._fetchStreams(mediaId, mediaType);
}

_fetchStreams(mediaId, mediaType, season, episode) {
  this._showNotification('Fetching streams...');
  
  const serviceData = {
    media_id: mediaId,
    media_type: mediaType,
  };
  
  if (mediaType === 'series' && season && episode) {
    serviceData.season = season;
    serviceData.episode = episode;
  }

  this.hass.callWS({
    type: 'call_service',
    domain: 'stremio',
    service: 'get_streams',
    service_data: serviceData,
    return_response: true,
  })
    .then((response) => {
      const streams = response?.response?.streams || response?.streams;
      if (streams && streams.length > 0) {
        this._showStreamDialog({
          title: this._media.title,
          type: mediaType,
          poster: this._media.poster,
          imdb_id: mediaId,
        }, streams);
      } else {
        this._showNotification('No streams found for this title');
      }
    })
    .catch((error) => {
      console.error('[Media Details Card] Failed to get streams:', error);
      this._showNotification(`Failed to get streams: ${error.message}`);
    });
}

_showStreamDialog(item, streams) {
  if (window.StremioStreamDialog) {
    window.StremioStreamDialog.show(
      this.hass,
      item,
      streams,
      this.config.apple_tv_entity  // ✅ Pass configured entity
    );
  } else {
    // Fallback: Create dialog directly
    let dialog = document.querySelector('stremio-stream-dialog');
    if (!dialog) {
      dialog = document.createElement('stremio-stream-dialog');
      document.body.appendChild(dialog);
    }
    dialog.hass = this.hass;
    dialog.mediaItem = item;
    dialog.streams = streams;
    dialog.appleTvEntity = this.config.apple_tv_entity;  // ✅ Pass configured entity
    dialog.open = true;
  }
}

_showEpisodePicker(mediaId) {
  // Implement episode picker integration like Browse Card
  // See stremio-browse-card.js lines 706-735
}
```

### Option 2: Remove Non-Functional Code (Quick Fix)

If stream viewing is not intended for this card:
1. Remove the "Get Streams" button
2. Remove the `_getStreams()` method
3. Keep only "Open in Stremio" functionality

---

## Testing Requirements

If implementing Option 1:

1. **Movie Testing**
   - Click "Get Streams" on a movie
   - Verify stream dialog appears
   - Select a stream
   - Click "Play on Apple TV"
   - Verify correct Apple TV entity is targeted (not default)

2. **TV Series Testing**
   - Click "Get Streams" on a TV series
   - Verify episode picker appears
   - Select season and episode
   - Verify stream dialog appears with episode info
   - Test Apple TV handover

3. **Configuration Testing**
   - Configure custom Apple TV entity in card settings
   - Verify configuration persists
   - Verify handover uses configured entity

---

## Updated Files Requiring Changes

### Critical Fixes (Same as before)
1. `stremio-continue-watching-card.js` - 2 line changes
2. `stremio-recommendations-card.js` - 4 changes (config + UI + parameters)

### Media Details Card (Choose one option)
3. `stremio-media-details-card.js` - Either:
   - **Option 1**: Implement full stream workflow (~100-150 lines, similar to Browse Card)
   - **Option 2**: Remove non-functional "Get Streams" button and code (~10 line removal)

---

## Effort Estimate Update

- Continue Watching Card: ~5 minutes ✓ (same)
- Recommendations Card: ~30 minutes ✓ (same)
- Media Details Card (Option 1): ~1-2 hours (full implementation + testing)
- Media Details Card (Option 2): ~5 minutes (removal)
- Testing all fixes: ~30-45 minutes

**Total (Option 1)**: ~2.5-3 hours
**Total (Option 2)**: ~1.5 hours

---

## Recommendation

**Implement Option 1** for Media Details Card to provide feature parity with other cards. The "Get Streams" button is currently visible in the UI but non-functional - this is confusing for users. Either make it work properly or remove it.

The Browse Card provides an excellent reference implementation that can be adapted for the Media Details Card.
