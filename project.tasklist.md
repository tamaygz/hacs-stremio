# Stremio HACS Integration - Implementation Task List

> **Last Updated**: 2026-01-17
> **Status**: Phase 1 Complete - Starting Phase 2
> **Version**: 0.1.0

---

## Overview

This document tracks the implementation progress of the Stremio HACS integration for Home Assistant. Tasks are organized into phases with clear dependencies, status tracking, and best-practice references.

### Status Legend
- ⬜ **Not Started**: Task not yet begun
- 🟦 **In Progress**: Currently being worked on
- ✅ **Completed**: Task finished and verified
- ⏸️ **Blocked**: Waiting on dependencies or external factors
- 🔄 **Review**: Ready for code review or testing
- ❌ **Deferred**: Postponed to future release

---

## Phase 1: Project Foundation & Setup
**Goal**: Establish project structure, development environment, and basic scaffolding  
**Duration**: 1-2 days

### 1.1 Project Structure & Configuration
- [x] ✅ **Task 1.1.1**: Initialize HACS integration folder structure (Completed: 2026-01-17)
  - Create `custom_components/stremio/` directory
  - Add required files: `__init__.py`, `manifest.json`, `const.py`
  - Set up version.py for version tracking
  - **Best Practice**: Follow [HACS integration blueprint](https://github.com/jpawlowski/hacs.integration_blueprint)
  - **Dependencies**: None
  - **Output**: Basic folder structure ready ✓

- [x] ✅ **Task 1.1.2**: Configure manifest.json (Completed: 2026-01-17)
  - Define domain, name, version, requirements
  - Add `stremio-api` as requirement
  - Set config_flow: true
  - Define codeowners, documentation URL
  - **Best Practice**: Follow [manifest.json schema](https://developers.home-assistant.io/docs/creating_integration_manifest/)
  - **Dependencies**: Task 1.1.1
  - **Output**: Valid manifest.json ✓

- [x] ✅ **Task 1.1.3**: Create constants file (const.py) (Completed: 2026-01-17)
  - Define DOMAIN = "stremio"
  - Add update intervals (30s for player state, 5min for library)
  - Define sensor types, attributes, icons
  - Add event types and service names
  - **Best Practice**: Centralize all constants for maintainability
  - **Dependencies**: Task 1.1.1
  - **Output**: Complete const.py with all constants ✓

- [x] ✅ **Task 1.1.4**: Set up development environment (Completed: 2026-01-17)
  - Create `requirements_dev.txt` with pytest-homeassistant-custom-component
  - Add pre-commit hooks for code quality (black, flake8, pylint)
  - Configure .gitignore for Python/HA
  - Set up virtual environment
  - **Best Practice**: Use [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) for testing
  - **Dependencies**: None
  - **Output**: Dev environment ready ✓

- [x] ✅ **Task 1.1.5**: Create documentation structure (Completed: 2026-01-17)
  - Initialize `/docs/` folder
  - Create `/docs/setup.md` (user setup guide)
  - Create `/docs/configuration.md` (config options)
  - Create `/docs/services.md` (service documentation)
  - Create `/docs/api.md` (API reference)
  - Create `/docs/development.md` (developer guide)
  - Create `/docs/troubleshooting.md` (common issues)
  - Update README.md with overview and links
  - **Best Practice**: Comprehensive docs improve user experience
  - **Dependencies**: None
  - **Output**: Documentation structure in place ✓

---

## Phase 2: Core Integration Components
**Goal**: Implement config flow, coordinator, and basic HA integration  
**Duration**: 3-5 days

### 2.1 Configuration Flow
- [x] ✅ **Task 2.1.1**: Implement config_flow.py (Completed: 2026-01-17)
  - Create ConfigFlow class extending ConfigFlow
  - Implement async_step_user for initial setup
  - Add form for Stremio email/password input
  - Validate credentials using stremio-api
  - Handle authentication errors gracefully
  - **Best Practice**: [Config flow UI setup](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
  - **Dependencies**: Task 1.1.1, 1.1.3
  - **Output**: Working config flow ✓

- [x] ✅ **Task 2.1.2**: Implement options flow (Completed: 2026-01-17)
  - Create OptionsFlowHandler class
  - Add options for update intervals (player state, library sync)
  - Add toggle for Apple TV handover feature
  - Add selection for handover method (AirPlay/VLC/Auto)
  - Implement async_step_init and save options
  - **Best Practice**: Allow users to customize polling intervals
  - **Dependencies**: Task 2.1.1
  - **Output**: Options flow working ✓

- [x] ✅ **Task 2.1.3**: Add translations (strings.json) (Completed: 2026-01-17)
  - Create `translations/en.json`
  - Add config flow strings (title, description, errors)
  - Add options flow strings
  - Add entity state translations
  - **Best Practice**: Localization from the start
  - **Dependencies**: Task 2.1.1, 2.1.2
  - **Output**: English translations complete ✓

### 2.2 API Client & Coordinator
- [x] ✅ **Task 2.2.1**: Create Stremio API client wrapper (stremio_client.py) (Completed: 2026-01-17)
  - Wrap stremio-api library methods
  - Implement async login/authentication
  - Add methods: get_library(), get_continue_watching(), get_streams()
  - Add player state polling method (check last watched item)
  - Implement error handling and retries
  - **Best Practice**: Abstract external API for easier testing/mocking
  - **Dependencies**: Task 1.1.3
  - **Output**: StremioClient class ready ✓

- [x] ✅ **Task 2.2.2**: Implement DataUpdateCoordinator (coordinator.py) (Completed: 2026-01-17)
  - Create StremioDataUpdateCoordinator extending DataUpdateCoordinator
  - Implement _async_update_data() method
  - Poll player state every 30s
  - Poll library data every 5min
  - Handle API errors and rate limiting
  - Store last successful data
  - **Best Practice**: [DataUpdateCoordinator pattern](https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities) ✓
  - **Dependencies**: Task 2.2.1
  - **Output**: Working coordinator

- [x] ✅ **Task 2.2.3**: Implement __init__.py (integration setup) (Completed: 2026-01-17)
  - Create async_setup_entry function
  - Initialize StremioClient with credentials
  - Create and start StremioDataUpdateCoordinator
  - Store coordinator in hass.data[DOMAIN]
  - Forward setup to platforms (sensor, binary_sensor, media_player)
  - Implement async_unload_entry for cleanup
  - **Best Practice**: Clean entry point with proper lifecycle management
  - **Dependencies**: Task 2.2.1, 2.2.2
  - **Output**: Integration loads successfully ✓

---

## Phase 3: Entity Implementations
**Goal**: Create sensors, binary sensors, and media player entity  
**Duration**: 4-6 days

### 3.1 Sensor Platform
- [ ] ⬜ **Task 3.1.1**: Create sensor.py base structure
  - Implement async_setup_entry function
  - Create StremioSensorEntity base class
  - Inherit from CoordinatorEntity for automatic updates
  - Implement common properties (device_info, unique_id)
  - **Best Practice**: Use CoordinatorEntity for efficient updates
  - **Dependencies**: Task 2.2.2
  - **Output**: Base sensor class ready

- [ ] ⬜ **Task 3.1.2**: Implement player state sensors
  - Create CurrentMediaSensor (shows current playing media)
  - Create LastWatchedSensor (last media watched)
  - Create CurrentPositionSensor (playback position in seconds)
  - Create CurrentDurationSensor (total media duration)
  - Add proper icons and device classes
  - **Best Practice**: Use device_class and state_class for proper categorization
  - **Dependencies**: Task 3.1.1
  - **Output**: Player state sensors working

- [ ] ⬜ **Task 3.1.3**: Implement library sensors
  - Create LibraryCountSensor (total library items)
  - Create ContinueWatchingSensor (shows continue watching list as attributes)
  - Add proper JSON serialization for complex attributes
  - **Best Practice**: Use extra_state_attributes for rich data
  - **Dependencies**: Task 3.1.1
  - **Output**: Library sensors working

- [ ] ⬜ **Task 3.1.4**: Implement stats sensors
  - Create TotalWatchTimeSensor (total watch time)
  - Create FavoriteGenreSensor (most watched genre)
  - Create WatchStreakSensor (days of consecutive watching)
  - Calculate stats from library data
  - **Best Practice**: Derive stats from existing data, don't poll separately
  - **Dependencies**: Task 3.1.1
  - **Output**: Stats sensors working

### 3.2 Binary Sensor Platform
- [ ] ⬜ **Task 3.2.1**: Create binary_sensor.py
  - Implement async_setup_entry function
  - Create StreamioBinarySensor base class
  - Inherit from CoordinatorEntity and BinarySensorEntity
  - **Best Practice**: Proper binary sensor device classes
  - **Dependencies**: Task 2.2.2
  - **Output**: Base binary sensor ready

- [ ] ⬜ **Task 3.2.2**: Implement binary sensors
  - Create IsPlayingBinarySensor (is_on when media is playing)
  - Create HasNewContentBinarySensor (is_on when new library items detected)
  - Add proper device_class (occupancy for playing, update for new content)
  - **Best Practice**: Use appropriate device classes for automations
  - **Dependencies**: Task 3.2.1
  - **Output**: Binary sensors working

### 3.3 Media Player Platform
- [ ] ⬜ **Task 3.3.1**: Create media_player.py
  - Create StremioMediaPlayer extending MediaPlayerEntity
  - Implement state property (playing/paused/idle)
  - Add read-only properties: media_title, media_duration, media_position
  - Add media_content_type (movie/episode)
  - Add media_image_url (poster)
  - **Best Practice**: [Media player entity](https://developers.home-assistant.io/docs/core/entity/media-player/)
  - **Dependencies**: Task 2.2.2
  - **Output**: Read-only media player entity

- [ ] ⬜ **Task 3.3.2**: Add media player features
  - Implement supported_features (limited to PLAY_MEDIA)
  - Add async_play_media for deep link generation
  - Generate Stremio deep links (stremio://...)
  - Add metadata to extra_state_attributes
  - **Best Practice**: Document that playback control is external
  - **Dependencies**: Task 3.3.1
  - **Output**: Media player with deep link support

---

## Phase 4: Services & Events
**Goal**: Implement custom services and event firing  
**Duration**: 2-3 days

### 4.1 Services
- [ ] ⬜ **Task 4.1.1**: Create services.yaml
  - Define service schemas for all 5 services
  - Add descriptions and field validators
  - Document required/optional parameters
  - **Best Practice**: Clear service documentation for UI
  - **Dependencies**: Task 1.1.3
  - **Output**: services.yaml complete

- [ ] ⬜ **Task 4.1.2**: Implement search service
  - Create async_search_library service
  - Accept query parameter
  - Search library by title, genre, cast
  - Return results as service response
  - **Best Practice**: Use service response for query results
  - **Dependencies**: Task 2.2.2
  - **Output**: Search service working

- [ ] ⬜ **Task 4.1.3**: Implement stream URL service
  - Create async_get_stream_url service
  - Accept media_id and stream_quality parameters
  - Call stremio-api to get stream URL
  - Return URL as service response
  - **Best Practice**: Validate media_id before API call
  - **Dependencies**: Task 2.2.1
  - **Output**: Stream URL service working

- [ ] ⬜ **Task 4.1.4**: Implement library management services
  - Create async_add_to_library service
  - Create async_remove_from_library service
  - Create async_refresh_library service
  - Update coordinator data after modifications
  - Fire events on library changes
  - **Best Practice**: Refresh coordinator after state-changing operations
  - **Dependencies**: Task 2.2.2, Task 4.1.2
  - **Output**: Library management services working

### 4.2 Events
- [ ] ⬜ **Task 4.2.1**: Implement event firing logic
  - Add event firing to coordinator update method
  - Fire stremio_playback_started event
  - Fire stremio_playback_stopped event
  - Fire stremio_new_content event (library changes)
  - Include relevant data in event payload
  - **Best Practice**: Events enable powerful automations
  - **Dependencies**: Task 2.2.2
  - **Output**: Events fire correctly

- [ ] ⬜ **Task 4.2.2**: Document events in docs/events.md
  - Create /docs/events.md file
  - Document each event type, trigger, and payload
  - Provide automation examples using events
  - **Best Practice**: Clear event documentation
  - **Dependencies**: Task 4.2.1, Task 1.1.5
  - **Output**: Event documentation complete

---

## Phase 5: Apple TV Handover Feature
**Goal**: Implement AirPlay and VLC handover for Apple TV  
**Duration**: 3-4 days

### 5.1 Handover Service Core
- [ ] ⬜ **Task 5.1.1**: Create apple_tv_handover.py module
  - Create HandoverManager class
  - Implement format detection (HLS/MP4/MKV)
  - Add method to discover Apple TV devices (pyatv)
  - Add method to generate VLC deep links
  - **Best Practice**: Modular design for testability
  - **Dependencies**: Task 4.1.3
  - **Output**: HandoverManager class ready

- [ ] ⬜ **Task 5.1.2**: Implement AirPlay handover
  - Use pyatv library for AirPlay protocol
  - Discover Apple TV devices on network
  - Send stream URL via AirPlay
  - Handle connection errors gracefully
  - **Best Practice**: [pyatv library](https://pyatv.dev/)
  - **Dependencies**: Task 5.1.1
  - **Output**: AirPlay handover working for HLS

- [ ] ⬜ **Task 5.1.3**: Implement VLC handover fallback
  - Generate VLC deep links (vlc-x-callback://)
  - Encode stream URL properly
  - Add subtitle parameter if available
  - **Best Practice**: VLC fallback for non-HLS formats
  - **Dependencies**: Task 5.1.1
  - **Output**: VLC deep links working

- [ ] ⬜ **Task 5.1.4**: Create handover service
  - Add async_handover_to_apple_tv service
  - Accept media_id, device_name, method parameters
  - Call HandoverManager with appropriate method
  - Return success/error status
  - **Best Practice**: User choice of handover method
  - **Dependencies**: Task 5.1.1, 5.1.2, 5.1.3
  - **Output**: Handover service complete

- [ ] ⬜ **Task 5.1.5**: Add handover options to config flow
  - Add toggle for Apple TV handover in options flow
  - Add dropdown for default handover method
  - Store options in config entry
  - **Best Practice**: Optional feature, disabled by default
  - **Dependencies**: Task 2.1.2, Task 5.1.4
  - **Output**: Handover options configurable

---

## Phase 6: Frontend & Custom Cards
**Goal**: Create custom Lovelace cards for rich UI  
**Duration**: 5-7 days

### 6.1 Card Infrastructure
- [ ] ⬜ **Task 6.1.1**: Set up frontend structure
  - Create `www/` folder for card resources
  - Create `stremio-card-bundle.js` entry point
  - Set up build system (Rollup/Webpack) for card bundling
  - Configure lit-element for web components
  - **Best Practice**: [Embedded cards in integration](https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909)
  - **Dependencies**: Task 1.1.1
  - **Output**: Card build system ready

- [ ] ⬜ **Task 6.1.2**: Register cards in integration
  - Implement __init__.py lovelace resource registration
  - Auto-register cards on integration load
  - Add version hash for cache busting
  - **Best Practice**: No manual resource addition needed
  - **Dependencies**: Task 6.1.1, Task 2.2.3
  - **Output**: Cards auto-register in Lovelace

### 6.2 Stremio Player Card
- [ ] ⬜ **Task 6.2.1**: Create stremio-player-card.js
  - Extend LitElement for web component
  - Implement setConfig and hass property
  - Display current media (poster, title, progress bar)
  - Show play/pause/stop state
  - Add "Open in Stremio" button (deep link)
  - **Best Practice**: Follow [mini-media-player card](https://github.com/kalkih/mini-media-player) pattern
  - **Dependencies**: Task 6.1.1
  - **Output**: Player card working

- [ ] ⬜ **Task 6.2.2**: Style player card
  - Use HA theme variables (var(--primary-color), etc.)
  - Add responsive design (mobile/desktop)
  - Add hover effects and animations
  - Match HA design language
  - **Best Practice**: Consistent with HA UI/UX
  - **Dependencies**: Task 6.2.1
  - **Output**: Player card styled

### 6.3 Library Browser Card
- [ ] ⬜ **Task 6.3.1**: Create stremio-library-card.js
  - Display library items in grid layout
  - Show poster images, titles, progress
  - Add filter/sort options (genre, type, progress)
  - Implement lazy loading for large libraries
  - **Best Practice**: Virtualized list for performance
  - **Dependencies**: Task 6.1.1
  - **Output**: Library browser card working

- [ ] ⬜ **Task 6.3.2**: Add search and actions to library card
  - Add search box at top of card
  - Filter library items as user types
  - Add click action to open media details dialog
  - Add "Play in Stremio" action button
  - **Best Practice**: Intuitive search and navigation
  - **Dependencies**: Task 6.3.1
  - **Output**: Search and actions working

### 6.4 Stream Selector Dialog
- [ ] ⬜ **Task 6.4.1**: Create stremio-stream-dialog.js
  - Create modal dialog component
  - List available streams for selected media
  - Show quality, size, seeds (if torrent)
  - Add "Copy URL" button for each stream
  - Implement clipboard copy (navigator.clipboard.writeText)
  - **Best Practice**: Use browser_mod or native dialog
  - **Dependencies**: Task 6.1.1, Task 4.1.3
  - **Output**: Stream selector dialog working

- [ ] ⬜ **Task 6.4.2**: Add fallback clipboard methods
  - Implement fallback 1: fire HA event with URL
  - Implement fallback 2: create input_text entity with URL
  - Implement fallback 3: notification with URL
  - **Best Practice**: Multiple fallbacks for clipboard
  - **Dependencies**: Task 6.4.1
  - **Output**: Clipboard always works

### 6.5 Media Details Card
- [ ] ⬜ **Task 6.5.1**: Create stremio-media-details-card.js
  - Display full media metadata (description, cast, year)
  - Show large poster image
  - Display available addons (subtitles, etc.)
  - Add "Get Streams" button to open stream dialog
  - **Best Practice**: Rich media presentation
  - **Dependencies**: Task 6.1.1, Task 6.4.1
  - **Output**: Media details card working

- [ ] ⬜ **Task 6.5.2**: Integrate with library card
  - Open media details card when library item clicked
  - Pass media_id to details card
  - Use browser_mod for popup or inline display
  - **Best Practice**: Seamless navigation flow
  - **Dependencies**: Task 6.3.2, Task 6.5.1
  - **Output**: Library to details flow working

---

## Phase 7: Media Source Integration
**Goal**: Integrate with HA Media Browser  
**Duration**: 2-3 days

### 7.1 Media Source Implementation
- [ ] ⬜ **Task 7.1.1**: Create media_source.py
  - Implement StremioMediaSource class
  - Register as media source provider
  - Implement async_browse_media for library browsing
  - Return BrowseMedia objects with proper structure
  - **Best Practice**: [Media source integration](https://developers.home-assistant.io/docs/core/platform/media_source/)
  - **Dependencies**: Task 2.2.2
  - **Output**: Media source registered

- [ ] ⬜ **Task 7.1.2**: Implement browsing hierarchy
  - Root level: Library, Continue Watching, Search
  - Library level: Movies, Series, Anime
  - Item level: Individual media with metadata
  - Add proper thumbnails and titles
  - **Best Practice**: Intuitive hierarchy
  - **Dependencies**: Task 7.1.1
  - **Output**: Browsing hierarchy working

- [ ] ⬜ **Task 7.1.3**: Implement media playback
  - Implement async_resolve_media for stream URLs
  - Call get_stream_url service internally
  - Return playable URL with MIME type
  - **Best Practice**: Integration with HA media players
  - **Dependencies**: Task 7.1.1, Task 4.1.3
  - **Output**: Media playback from browser working

---

## Phase 8: Testing & Quality Assurance
**Goal**: Comprehensive testing and code quality  
**Duration**: 4-5 days

### 8.1 Unit Tests
- [ ] ⬜ **Task 8.1.1**: Set up test infrastructure
  - Create `tests/` folder structure
  - Add `conftest.py` with fixtures
  - Create mock Stremio API responses
  - Configure pytest.ini
  - **Best Practice**: [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
  - **Dependencies**: Task 1.1.4
  - **Output**: Test infrastructure ready

- [ ] ⬜ **Task 8.1.2**: Test config flow
  - Test successful authentication
  - Test invalid credentials error
  - Test network error handling
  - Test options flow changes
  - **Best Practice**: Test all user paths
  - **Dependencies**: Task 8.1.1, Task 2.1.1
  - **Output**: Config flow tests passing

- [ ] ⬜ **Task 8.1.3**: Test coordinator
  - Test successful data fetch
  - Test API error handling
  - Test rate limiting
  - Test data caching
  - **Best Practice**: Mock API calls
  - **Dependencies**: Task 8.1.1, Task 2.2.2
  - **Output**: Coordinator tests passing

- [ ] ⬜ **Task 8.1.4**: Test entities
  - Test sensor state updates
  - Test binary sensor state changes
  - Test media player properties
  - Test attribute formatting
  - **Best Practice**: Test state and attributes separately
  - **Dependencies**: Task 8.1.1, Phase 3
  - **Output**: Entity tests passing

- [ ] ⬜ **Task 8.1.5**: Test services
  - Test each service with valid inputs
  - Test error handling for invalid inputs
  - Test service responses
  - Mock coordinator updates
  - **Best Practice**: Test service schemas
  - **Dependencies**: Task 8.1.1, Phase 4
  - **Output**: Service tests passing

### 8.2 Integration Tests
- [ ] ⬜ **Task 8.2.1**: Test full integration setup
  - Test async_setup_entry
  - Test platform loading
  - Test async_unload_entry
  - Test reload behavior
  - **Best Practice**: Test complete lifecycle
  - **Dependencies**: Task 8.1.1, Task 2.2.3
  - **Output**: Integration tests passing

- [ ] ⬜ **Task 8.2.2**: Test coordinator updates
  - Test periodic updates trigger entity changes
  - Test event firing on state changes
  - Test library sync behavior
  - **Best Practice**: Test timing and scheduling
  - **Dependencies**: Task 8.2.1
  - **Output**: Update tests passing

### 8.3 Code Quality
- [ ] ⬜ **Task 8.3.1**: Run linters and formatters
  - Run black for code formatting
  - Run flake8 for style checking
  - Run pylint for code analysis
  - Fix all issues
  - **Best Practice**: Zero linter warnings
  - **Dependencies**: Task 1.1.4
  - **Output**: Clean linter output

- [ ] ⬜ **Task 8.3.2**: Add type hints
  - Add type hints to all functions
  - Run mypy for type checking
  - Fix type errors
  - **Best Practice**: Strong typing for maintainability
  - **Dependencies**: All implementation phases
  - **Output**: mypy passing

- [ ] ⬜ **Task 8.3.3**: Add docstrings
  - Add docstrings to all classes and methods
  - Follow Google or NumPy docstring format
  - Document parameters and return values
  - **Best Practice**: Self-documenting code
  - **Dependencies**: All implementation phases
  - **Output**: Complete documentation strings

---

## Phase 9: Documentation & Examples
**Goal**: Complete user and developer documentation  
**Duration**: 2-3 days

### 9.1 User Documentation
- [ ] ⬜ **Task 9.1.1**: Write setup guide (docs/setup.md)
  - Installation via HACS
  - Initial configuration steps
  - Credential setup
  - Troubleshooting common setup issues
  - **Best Practice**: Step-by-step with screenshots
  - **Dependencies**: Phase 2, Phase 8
  - **Output**: Complete setup guide

- [ ] ⬜ **Task 9.1.2**: Write configuration guide (docs/configuration.md)
  - Document all configuration options
  - Explain update intervals
  - Document Apple TV handover options
  - Provide YAML examples for automations
  - **Best Practice**: Comprehensive option reference
  - **Dependencies**: Phase 2, Phase 5
  - **Output**: Complete configuration guide

- [ ] ⬜ **Task 9.1.3**: Write services guide (docs/services.md)
  - Document each service with examples
  - Show YAML and UI usage
  - Provide automation examples
  - **Best Practice**: Real-world use cases
  - **Dependencies**: Phase 4
  - **Output**: Complete services guide

- [ ] ⬜ **Task 9.1.4**: Write UI/cards guide (docs/ui.md)
  - Document each custom card
  - Show configuration examples
  - Provide dashboard layouts
  - Add screenshots of cards
  - **Best Practice**: Visual examples help users
  - **Dependencies**: Phase 6
  - **Output**: Complete UI guide

### 9.2 Developer Documentation
- [ ] ⬜ **Task 9.2.1**: Write development guide (docs/development.md)
  - Setting up development environment
  - Running tests
  - Code structure overview
  - Contributing guidelines
  - **Best Practice**: Lower barrier for contributors
  - **Dependencies**: Phase 8
  - **Output**: Complete development guide

- [ ] ⬜ **Task 9.2.2**: Write API reference (docs/api.md)
  - Document StremioClient class
  - Document coordinator methods
  - Document internal APIs
  - **Best Practice**: Auto-generate from docstrings if possible
  - **Dependencies**: All implementation phases
  - **Output**: Complete API reference

- [ ] ⬜ **Task 9.2.3**: Create architecture diagram
  - Create visual diagram of component structure
  - Show data flow between components
  - Illustrate coordinator pattern
  - **Best Practice**: Visual aids for understanding
  - **Dependencies**: All implementation phases
  - **Output**: Architecture diagram

### 9.3 README & Examples
- [ ] ⬜ **Task 9.3.1**: Update README.md
  - Add badges (version, build status, coverage)
  - Write feature overview with screenshots
  - Add quick start guide
  - Link to full documentation
  - **Best Practice**: README is the front door
  - **Dependencies**: Phase 9.1, Phase 9.2
  - **Output**: Professional README

- [ ] ⬜ **Task 9.3.2**: Create example automations
  - Create `examples/` folder
  - Add automation YAML files
  - Example: Notification on new content
  - Example: Play media on voice command
  - Example: Library backup automation
  - **Best Practice**: Copy-paste ready examples
  - **Dependencies**: Phase 4
  - **Output**: Example automation files

---

## Phase 10: Release & Distribution
**Goal**: Prepare for HACS release and ongoing maintenance  
**Duration**: 2-3 days

### 10.1 HACS Preparation
- [ ] ⬜ **Task 10.1.1**: Create hacs.json
  - Define name, description, version
  - Set render_readme: true
  - Add homeassistant version requirement
  - **Best Practice**: [HACS documentation](https://hacs.xyz/docs/publish/integration)
  - **Dependencies**: All phases complete
  - **Output**: Valid hacs.json

- [ ] ⬜ **Task 10.1.2**: Add releases workflow
  - Create `.github/workflows/release.yml`
  - Automate version bumping
  - Generate changelog from commits
  - Create GitHub release on tag push
  - **Best Practice**: Automated releases
  - **Dependencies**: Task 10.1.1
  - **Output**: Release workflow ready

- [ ] ⬜ **Task 10.1.3**: Create CHANGELOG.md
  - Document all features in v1.0.0
  - Use Keep a Changelog format
  - Link to GitHub issues/PRs
  - **Best Practice**: Transparent change tracking
  - **Dependencies**: All implementation complete
  - **Output**: CHANGELOG.md

### 10.2 CI/CD
- [ ] ⬜ **Task 10.2.1**: Create test workflow
  - Create `.github/workflows/test.yml`
  - Run pytest on every PR
  - Run linters (black, flake8, pylint, mypy)
  - Upload coverage reports
  - **Best Practice**: Automated quality checks
  - **Dependencies**: Phase 8
  - **Output**: Test workflow running

- [ ] ⬜ **Task 10.2.2**: Create build workflow
  - Create `.github/workflows/build.yml`
  - Build frontend cards
  - Validate manifest.json
  - Check for breaking changes
  - **Best Practice**: Catch issues before merge
  - **Dependencies**: Phase 6
  - **Output**: Build workflow running

### 10.3 Release
- [ ] ⬜ **Task 10.3.1**: Final pre-release checks
  - All tests passing
  - Documentation complete
  - README polished
  - Example configurations tested
  - **Best Practice**: Quality gate before release
  - **Dependencies**: All previous tasks
  - **Output**: Ready for release

- [ ] ⬜ **Task 10.3.2**: Submit to HACS
  - Fork HACS default repository
  - Add integration to default list
  - Submit pull request
  - Respond to review feedback
  - **Best Practice**: Follow HACS submission process
  - **Dependencies**: Task 10.3.1
  - **Output**: Integration in HACS default

- [ ] ⬜ **Task 10.3.3**: Create v1.0.0 release
  - Tag version v1.0.0
  - Push tag to trigger release workflow
  - Verify GitHub release created
  - Announce on HA forums/Discord
  - **Best Practice**: Public announcement
  - **Dependencies**: Task 10.3.2
  - **Output**: v1.0.0 released

---

## Future Enhancements (Post v1.0.0)
**Status**: ⬜ Not Started (Deferred)

### Future Phase 1: Advanced Features
- [ ] ⬜ Add real-time playback control (requires Stremio API updates)
- [ ] ⬜ Implement notification card for new content
- [ ] ⬜ Add statistics dashboard card
- [ ] ⬜ Implement watch history timeline
- [ ] ⬜ Add multi-account support

### Future Phase 2: Integrations
- [ ] ⬜ Integrate with Jellyfin for library sync
- [ ] ⬜ Integrate with Plex for cross-platform library
- [ ] ⬜ Add Chromecast handover support
- [ ] ⬜ Add Roku handover support
- [ ] ⬜ Implement IFTTT-style recipes

### Future Phase 3: Localization
- [ ] ⬜ Add French translations
- [ ] ⬜ Add German translations
- [ ] ⬜ Add Spanish translations
- [ ] ⬜ Add Dutch translations
- [ ] ⬜ Community translation contributions

---

## Dependency Graph Summary

```
Phase 1 (Foundation)
  ├─→ Phase 2 (Core Integration)
  │    ├─→ Phase 3 (Entities)
  │    │    └─→ Phase 4 (Services & Events)
  │    │         ├─→ Phase 5 (Apple TV)
  │    │         └─→ Phase 7 (Media Source)
  │    └─→ Phase 6 (Frontend)
  └─→ Phase 8 (Testing)
       └─→ Phase 9 (Documentation)
            └─→ Phase 10 (Release)
```

---

## Best Practice References

### Key Resources
1. **HA Integration Development**: https://developers.home-assistant.io/
2. **HACS Integration Blueprint**: https://github.com/jpawlowski/hacs.integration_blueprint
3. **pytest-homeassistant-custom-component**: https://github.com/MatthewFlamm/pytest-homeassistant-custom-component
4. **Custom Cards Guide**: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
5. **Embedded Cards in Integration**: https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909
6. **DataUpdateCoordinator Pattern**: https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
7. **Config Flow Handler**: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
8. **Media Source Integration**: https://developers.home-assistant.io/docs/core/platform/media_source/

### Code Quality Standards
- **Black** for code formatting (line length: 88)
- **Flake8** for style checking
- **Pylint** for code analysis (min score: 9.0)
- **mypy** for type checking (strict mode)
- **pytest** for testing (min coverage: 80%)

---

## Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 1.0.0   | 2025-01-19 | Initial task list and implementation plan    |

---

## Notes & Decisions

### Technical Decisions
1. **Coordinator Pattern**: Using DataUpdateCoordinator for efficient API polling
2. **Card Embedding**: Cards will be served from integration (not separate HACS install)
3. **Apple TV Handover**: Hybrid AirPlay/VLC approach for maximum compatibility
4. **Testing Framework**: pytest-homeassistant-custom-component for HA compatibility

### Open Questions
- [ ] Should we support multiple Stremio accounts?
- [ ] Should we add Chromecast support in v1.0.0 or defer to v1.1.0?
- [ ] What is the optimal library sync interval (currently 5min)?

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Stremio API changes | High | Version pin stremio-api library, monitor for changes |
| Apple TV discovery failures | Medium | Provide manual device entry option |
| Large library performance | Medium | Implement pagination and lazy loading in cards |
| HACS approval delays | Low | Start submission process early, respond quickly to feedback |

---

## Progress Tracking

**Overall Progress**: 4.4% (5/113 tasks completed)

### Phase Completion
- ✅ Phase 0: Planning & Research (Complete)
- ✅ Phase 1: Foundation (5/5) - **COMPLETE**
- ⬜ Phase 2: Core Integration (0/8)
- ⬜ Phase 3: Entities (0/11)
- ⬜ Phase 4: Services & Events (0/6)
- ⬜ Phase 5: Apple TV (0/5)
- ⬜ Phase 6: Frontend (0/11)
- ⬜ Phase 7: Media Source (0/3)
- ⬜ Phase 8: Testing (0/10)
- ⬜ Phase 9: Documentation (0/9)
- ⬜ Phase 10: Release (0/9)

**Next Action**: Begin Phase 2, Task 2.1.1 - Implement config_flow.py

---

*This task list is a living document and will be updated as the project progresses. Each completed task will be marked with ✅ and timestamped.*
