# Investigation Summary: Apple TV Handover Device ID Bug

## Executive Summary

Completed comprehensive investigation of Apple TV device ID configuration bug across all Stremio HACS integration cards.

**Date**: 2026-01-26
**Commits**: fce8858 (initial), 0f15af1 (media details investigation)

---

## Cards Status Overview

| Card | Apple TV Config UI | Stream Dialog | Issue Type | Fix Complexity |
|------|-------------------|---------------|------------|----------------|
| Browse Card | ✅ Yes | ✅ Working | ✅ None | No fix needed |
| Library Card | ✅ Yes | ✅ Working | ✅ None | No fix needed |
| Player Card | ✅ Yes | N/A | ✅ N/A | Not applicable |
| Continue Watching | ✅ Yes | ⚠️ Missing param | ❌ Parameter pass | Simple (2 lines) |
| Recommendations | ❌ No | ⚠️ Missing param | ❌ Missing config + param | Medium (4 changes) |
| Media Details | ✅ Yes | ❌ Broken | ❌ Broken workflow | Complex (choose option) |

---

## Detailed Findings

### ✅ Working Correctly (No Action Needed)

**Browse Card** (`stremio-browse-card.js`)
- Has `apple_tv_entity` configuration with UI
- Properly passes parameter to `StremioStreamDialog.show()`
- Properly sets `dialog.appleTvEntity` in fallback
- Reference implementation for fixes

**Library Card** (`stremio-library-card.js`)
- Has `apple_tv_entity` configuration with UI
- Properly passes parameter to `StremioStreamDialog.show()`
- Properly sets `dialog.appleTvEntity` in fallback
- Reference implementation for fixes

**Player Card** (`stremio-player-card.js`)
- Has `apple_tv_entity` in config but doesn't use stream selection
- Not applicable to this bug (status display only)

---

### ❌ Broken - Simple Fixes

**Continue Watching Card** (`stremio-continue-watching-card.js`)

**Problem**: Has configuration UI but doesn't pass the value to stream dialog

**Missing**:
- Line 809: Add `, this.config.apple_tv_entity` as 4th parameter to `show()` call
- After line 823: Add `dialog.appleTvEntity = this.config.apple_tv_entity;`

**Impact**: User configuration is saved but completely ignored during handover

**Fix Effort**: 5 minutes (2 line additions)

---

### ❌ Broken - Medium Complexity

**Recommendations Card** (`stremio-recommendations-card.js`)

**Problem**: Missing configuration option entirely AND missing parameter pass

**Missing**:
1. Config default (line ~461): Add `apple_tv_entity: undefined,`
2. Configuration UI section: Add Apple TV device picker (similar to other cards)
3. Line 719: Add `, this.config.apple_tv_entity` as 4th parameter to `show()` call
4. After line 728: Add `dialog.appleTvEntity = this.config.apple_tv_entity;`

**Impact**: No way for users to configure Apple TV entity at all - most severe case

**Fix Effort**: 30 minutes (config + UI section + 2 line additions)

---

### ❌ Broken - Complex (Different Issue)

**Media Details Card** (`stremio-media-details-card.js`)

**Problem**: This is NOT just a missing parameter - the entire stream workflow is broken

**Three Issues Found**:

1. **Dead Event Code** (Line 874)
   - Fires `stremio-open-stream-dialog` custom event
   - No event listeners exist anywhere in codebase
   - This event is never caught - dead code

2. **Broken Service Call** (Line 887)
   - Missing required `media_type` parameter (will fail validation)
   - Missing `season`/`episode` for TV series
   - No response handling (no `.then()` or await handling)
   - Service response is ignored

3. **No Stream Dialog Integration**
   - Doesn't call `StremioStreamDialog.show()`
   - Doesn't create fallback dialog
   - Streams are never displayed to users
   - "Get Streams" button visible but non-functional

**Fix Options**:

**Option 1 (Recommended)**: Implement Full Stream Workflow
- Follow Browse Card pattern
- Add proper service call with all parameters
- Add response handling
- Add stream dialog integration
- Add episode picker for TV series
- Pass `apple_tv_entity` to dialog
- **Effort**: 1-2 hours (implementation + testing)
- **Benefits**: Feature parity with other cards, users can actually use the button

**Option 2 (Quick Fix)**: Remove Non-Functional Code
- Remove "Get Streams" button from UI
- Remove `_getStreams()` method
- Keep only "Open in Stremio" functionality
- **Effort**: 5 minutes (code removal)
- **Benefits**: Removes confusing non-functional UI element

---

## Root Cause Analysis

### Continue Watching & Recommendations Cards
**Root Cause**: Developer oversight - forgot to pass the 4th parameter when calling `StremioStreamDialog.show()` and forgot to set the property in fallback path.

**Evidence**: Browse and Library cards have identical patterns but correctly pass the parameter.

### Media Details Card
**Root Cause**: Incomplete implementation - appears to be work-in-progress or refactored code that was never finished.

**Evidence**: 
- Event system used instead of direct dialog calls
- No event handlers implemented
- Service call missing required parameters
- No response handling code
- Button visible in UI but doesn't work

---

## Testing Plan

After fixes are implemented, each card needs:

### Functional Testing
1. **Configuration Persistence**
   - Configure custom Apple TV entity in card settings
   - Save and reload page
   - Verify configuration persists

2. **Stream Dialog Handover**
   - Select media and get streams
   - Click "Play on Apple TV"
   - Verify service call targets configured entity (not default)
   - Check service call parameters in Developer Tools

3. **TV Series Handling** (where applicable)
   - Select TV series
   - Verify episode picker appears
   - Select episode
   - Verify handover works with season/episode data

### Regression Testing
- Verify cards with no apple_tv_entity configured still work (use default)
- Verify no JavaScript console errors
- Verify all existing functionality still works

---

## Files Requiring Changes

1. **Continue Watching Card**
   - File: `custom_components/stremio/frontend/stremio-continue-watching-card.js`
   - Changes: 2 line additions
   - Lines: 809, 824 (after 823)

2. **Recommendations Card**
   - File: `custom_components/stremio/frontend/stremio-recommendations-card.js`
   - Changes: Config definition + UI section + 2 line additions
   - Locations: ~line 461, add UI section similar to other cards, line 719, line 729 (after 728)

3. **Media Details Card** (Choose Option 1 or 2)
   - File: `custom_components/stremio/frontend/stremio-media-details-card.js`
   - Option 1: ~100-150 lines (new methods + integration)
   - Option 2: ~10 line removal (button + method)

---

## Documentation Created

1. **Initial Analysis**: `/tmp/apple_tv_bug_analysis.md` (created but not in repo)
2. **Updated Investigation**: `INVESTIGATION_UPDATE.md` (in repo)
3. **This Summary**: `INVESTIGATION_SUMMARY.md` (this file)

---

## Recommendations

1. **Immediate Fixes** (Critical Priority)
   - Fix Continue Watching Card (5 minutes)
   - Fix Recommendations Card (30 minutes)

2. **Media Details Card Decision** (High Priority)
   - **Recommended**: Implement Option 1 (full workflow)
   - **Reason**: Button is visible in UI - either make it work or remove it
   - **If time-constrained**: Use Option 2 temporarily, plan Option 1 for next sprint

3. **Testing** (Required)
   - Test all three cards with actual Apple TV integration
   - Verify handover works end-to-end
   - Document any edge cases found

---

## Effort Estimates

| Task | Effort | Priority |
|------|--------|----------|
| Continue Watching Card fix | 5 min | Critical |
| Recommendations Card fix | 30 min | Critical |
| Media Details Card (Option 1) | 1-2 hours | High |
| Media Details Card (Option 2) | 5 min | High |
| Testing all fixes | 30-45 min | Required |
| **Total (Option 1)** | **2.5-3 hours** | - |
| **Total (Option 2)** | **1.5 hours** | - |

---

## Next Steps

Awaiting decision on:
1. Proceed with fixes for Continue Watching and Recommendations cards?
2. Which option for Media Details Card (Option 1 or Option 2)?
3. Any other areas that need investigation?

Once approved, can begin implementation phase.
