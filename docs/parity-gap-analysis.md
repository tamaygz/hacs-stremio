# Stremio Home Assistant Integration Parity / Gap Analysis

## Executive summary

`tamaygz/hacs-stremio` already goes well beyond the other Stremio-for-Home-Assistant projects that are easy to find. Today it covers authentication, library and continue-watching sync, media browsing, catalog browsing, recommendations, similar content, events, Lovelace cards, and Apple TV handover. The biggest remaining opportunity areas are broader device playback, better write-back/sync flows, deeper use of the Stremio addon ecosystem, and surfacing more of the Stremio account/addon model inside Home Assistant.

This report combines:
- the current repo feature set (`README.md`, `docs/`, `custom_components/stremio/`)
- direct community demand signals from Stremio and Home Assistant sources
- official Stremio platform capabilities
- examples from adjacent or competing solutions

## What this extension offers today

Based on the current repository, the integration already provides:

### Core account, library, and playback features
- Config-flow login and stored account access (`custom_components/stremio/manifest.json`, `custom_components/stremio/config_flow.py`)
- Library sync, continue watching, current watching, last watched, and library management (`README.md`, `custom_components/stremio/stremio_client.py`)
- A Stremio media player entity plus browseable media source support (`README.md`, `custom_components/stremio/media_player.py`, `custom_components/stremio/media_source.py`)
- Add/remove library operations and manual refresh (`docs/services.md`, `custom_components/stremio/services.yaml`)

### Entities and automation hooks
- Sensors for library count, current watching, current stream URL, last watched, and continue watching count (`custom_components/stremio/sensor.py`)
- Binary sensors for is watching, has continue watching, and has new episodes (`custom_components/stremio/binary_sensor.py`)
- Button entities for force refresh, refresh library, and optional Apple TV handover (`custom_components/stremio/button.py`)
- Events for playback started/stopped, new content, new episodes detected, and resume available (`docs/events.md`, `custom_components/stremio/const.py`)

### Playback, browsing, and UI
- Stream lookup and catalog browsing/search services (`docs/services.md`, `custom_components/stremio/services.yaml`)
- Recommendations, similar content, upcoming episodes, and addon listing services (`docs/services.md`, `custom_components/stremio/services.yaml`)
- Apple TV handover via Home Assistant (`README.md`, `docs/configuration.md`)
- Auto-registered custom Lovelace cards for library, continue watching, browsing, and recommendations (`README.md`, `custom_components/stremio/frontend/`)

### Current positioning vs other Stremio/HA projects
- `AboveColin/stremio-ha` focuses on library tracking, current watching, sensors, media source browsing, and a `get_streams` service, but explicitly lists remote playback on Android TV/Desktop and direct playback as future plans: https://github.com/AboveColin/stremio-ha
- `hudsonbrendon/HA-stremio` is much narrower: it surfaces top movies/series from Cinemeta for dashboards and works with `upcoming-media-card`: https://github.com/hudsonbrendon/HA-stremio
- `timojokinen/hassio-stremio-server` solves a different but adjacent job by running Stremio's streaming server on the Home Assistant machine: https://github.com/timojokinen/hassio-stremio-server

**Bottom line:** this repo is already the most complete Home Assistant integration in the Stremio niche, but there is still meaningful parity headroom when compared with the broader Stremio ecosystem and with mature HA media integrations.

## User voices: what people appear to want most

### 1) Stronger Trakt sync and watch-state portability
This is the clearest recurring signal.

- Stremio feature request `#344` asks for two-way sync between the Stremio library/watch history and Trakt: https://github.com/Stremio/stremio-features/issues/344
- Commenters on that issue describe it as a switch-enabling feature:
  - "Without two way Trakt sync, I can't justify switching."
  - "The 1 and only feature stremio needs is this. Full trakt integration with up next is game changer."
  - "I actually got a Trakt account hoping this is how it worked... Could be a big deal to a lot of people myself included."
- Stremio later marked the request completed and noted that sync can be triggered from the user panel on stremio.com, which shows the demand is real even if the UX is still incomplete from a Home Assistant angle: https://github.com/Stremio/stremio-features/issues/344#issuecomment-2152656386
- Community addon examples show sustained demand beyond the official app:
  - `redd-ravenn/stremio-trakt-addon` adds Trakt watchlists, personalized recommendations, history sync, token refresh, and marking content watched: https://github.com/redd-ravenn/stremio-trakt-addon
  - `MyTrakt Sync` positions itself as an advanced Stremio-Trakt integration: https://mytrakt.elfhosted.com/

**Implication for this repo:** users do not just want read-only library visibility; they want Stremio to participate in a larger cross-device watch-state workflow.

### 2) Better discovery: recommendations, similar content, and richer catalogs
- Reddit users ask for recommendation addons and "similar shows" style discovery help; one cited example is a request thread for recommendation addons in `r/StremioAddons`: https://www.reddit.com/r/StremioAddons/comments/1cp8ck1/add_on_for_recommendations/
- The popularity of Trakt/MDBList-style Stremio addons points the same way: users want curated lists, personal watchlists, and better discovery flows, not just raw library views.
- This repo already has `get_recommendations`, `get_similar_content`, and browse/search catalog capabilities, which is a strength.

**Implication for this repo:** discovery is already part of the product; expanding from Cinemeta-only flows to broader addon-backed catalogs would align with real user behavior.

### 3) Device handoff and simpler playback from HA
- The Home Assistant forum thread about this project highlights interest in Stremio playback handoff for Apple TV and asks about similar support for other device types: https://community.home-assistant.io/t/stremio-integration-for-apple-tv/976514
- `AboveColin/stremio-ha` also calls out remote playback on Android TV/Desktop as a future plan, which is a good proxy for unmet demand: https://github.com/AboveColin/stremio-ha
- The repo's own examples and docs already lean heavily into "movie night", auto-resume, and playback-driven automations (`examples/`, `docs/events.md`).

**Implication for this repo:** Home Assistant users want Stremio to be an automation source *and* a playback launcher, not just a passive status feed.

### 4) Upcoming content and proactive notifications
- This repo already includes `get_upcoming_episodes`, which matches a common media-automation job: proactive awareness of new content (`docs/services.md`).
- Adjacent Stremio/Trakt tools and addons also emphasize Up Next, watchlists, and release awareness rather than only "what am I watching right now".

**Implication for this repo:** release calendars, notification-friendly entities, and more structured "what should I watch next / what drops soon" experiences fit both HA and Stremio user expectations.

## Stremio capabilities we are not yet using enough

Official Stremio docs show a wider surface area than the integration currently exposes.

### 1) Subtitle resources
The Stremio Addon SDK has a first-class `subtitles` resource and handler support: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/README.md

**What we do today:** no subtitle service or subtitle-oriented entity is documented in this repo.

**Opportunity:**
- add `get_subtitles`
- expose available subtitle languages for the current item
- support subtitle-aware handoff or automation logic

### 2) Deep links (`stremio://`)
Stremio documents deep links for opening pages, search, library, and item detail inside the Stremio app: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/deep-links.md

Examples include:
- `stremio:///library`
- `stremio:///search?search={query}`
- `stremio:///detail/{type}/{id}/{videoId}`

**What we do today:** the repo focuses on stream URL retrieval and Apple TV handover, but not deep-link launch back into Stremio.

**Opportunity:**
- `open_in_stremio` service for HA mobile companion users
- actionable notifications that jump straight into Stremio content
- card buttons that launch detail/search/library views directly in the Stremio app

### 3) Full addon resource model, not just Cinemeta-centric flows
The Stremio addon model includes `catalog`, `metadata`, `streams`, `subtitles`, and `addon_catalog` resources: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/README.md

**What we do today:**
- browse/search catalog is strong
- stream fetching is strong
- the visible product story still centers mostly on Cinemeta plus installed stream addons

**Opportunity:**
- browse user-installed catalog addons, not only the default catalog source
- surface addon capabilities more explicitly inside HA
- let users choose catalog providers/lists more dynamically

### 4) Addon/account write-back possibilities
Official Stremio client APIs and ecosystem examples suggest more is possible than read-only addon inspection.

**Potential directions:**
- sync addon ordering/preferences back to the Stremio account rather than only keeping them locally in HA
- install/add addons from HA via manifest URL
- surface addon configuration/status inside HA

This area needs careful verification against the current internal API client behavior before implementation, but it is a credible product opportunity.

### 5) Broader stream handling
The Stremio stream model supports more than simple direct URLs, including addon-provided stream metadata and alternate transport behaviors: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/README.md

**Opportunity:**
- improve compatibility with a wider set of addon stream responses
- expose more stream metadata to cards/services so users can choose quality, source, language, subtitle availability, or provider more deliberately

## Comparison with adjacent popular solutions

## Example 1: `AboveColin/stremio-ha`
Source: https://github.com/AboveColin/stremio-ha

What it proves:
- there is demand for Stremio library state inside Home Assistant
- users value entity-rich metadata (user, watch time, current item details, installed addons)

Where this repo is already ahead:
- Apple TV handover
- richer Lovelace UX
- library add/remove
- recommendations/similar content/upcoming episodes
- more automation-oriented event support

What is still useful to borrow:
- explicit user/profile visibility
- richer metadata surfacing patterns
- clearer roadmap framing around remote playback targets

## Example 2: `HA-stremio`
Source: https://github.com/hudsonbrendon/HA-stremio

What it proves:
- there is a dashboard/discovery use case independent of playback control
- users like card-ready sensors that plug into `upcoming-media-card`

What is useful to borrow:
- card interoperability with popular media dashboard patterns
- more polished "discovery feed" style output for dashboard-first users

## Example 3: `hassio-stremio-server`
Source: https://github.com/timojokinen/hassio-stremio-server

What it proves:
- some users want Home Assistant to host the Stremio streaming backend itself
- centralizing streaming/transcoding on the HA box is a valid user job

What is useful to borrow:
- a local-server story could make HA feel like the Stremio control plane
- there may be future value in pairing the integration with a supported HA add-on or setup guide for the Stremio server

## Example 4: `stremio-trakt-addon` / MyTrakt Sync
Sources:
- https://github.com/redd-ravenn/stremio-trakt-addon
- https://mytrakt.elfhosted.com/

What they prove:
- users want personalized catalogs, watchlists, recommendations, and watch-history sync
- Trakt is not a minor niche enhancement; it is one of the main ways users extend Stremio

What is useful to borrow:
- OAuth/account linking flows
- personalized watchlist/recommendation surfaces
- "mark watched" and history sync primitives

## Example 5: adjacent Home Assistant media patterns
These are not Stremio projects, but they solve the same jobs.

- Spotcast is a strong pattern reference for "launch media on a target device from Home Assistant": https://github.com/fondberg/spotcast
- Plex/Jellyfin/Kodi integrations are strong references for device-centric playback control, richer now-playing entities, and automation around media sessions (see Home Assistant integration docs and community discussions referenced in web research)
- `upcoming-media-card` remains a useful comparison point for release- and discovery-oriented dashboards because other Stremio integrations already target it: https://github.com/custom-cards/upcoming-media-card

## Highest-value gaps and ideas

### Priority 1: likely highest user value
1. **Trakt-aware workflows in Home Assistant**
   - OAuth or linked-account approach
   - watchlist / history / Up Next surfacing
   - mark watched / sync completion flows
2. **Generalized playback routing**
   - evolve from `handover_to_apple_tv` to a broader `play_on_device`
   - target Chromecast, Android TV, Kodi, and generic HA `media_player` entities where feasible
3. **Write-back watch-state services**
   - `mark_as_watched`
   - `mark_as_unwatched`
   - completion-driven automations

### Priority 2: strong parity / ecosystem opportunities
4. **Subtitle support**
   - fetch available subtitles
   - expose subtitle languages/options
5. **Open-in-app / deep-link support**
   - actionable notifications and dashboard buttons into Stremio
6. **Broader catalog-addon support**
   - browse installed addon catalogs and user-curated lists

### Priority 3: power-user and platform opportunities
7. **Optional local Stremio server story**
   - docs or add-on integration for Home Assistant-hosted Stremio server
8. **Richer analytics entities**
   - daily/weekly watch time, unwatched count, release counts, source/provider trends
9. **More addon/account management from HA**
   - addon install/reorder/status/config surfaces where the API safely allows it

## Recommended product framing

A useful way to frame the roadmap is:

1. **Best-in-class Stremio automation bridge**
   - continue investing in events, entities, notifications, and dashboard flows
2. **Best-in-class Stremio launcher / handoff layer**
   - expand playback targets beyond Apple TV
3. **Best-in-class Stremio ecosystem bridge**
   - pull Trakt, addon catalogs, subtitles, and deep links into the HA experience

That framing matches both the existing strengths of the repo and the strongest external demand signals.

## References

### Current repo
- `/home/runner/work/hacs-stremio/hacs-stremio/README.md`
- `/home/runner/work/hacs-stremio/hacs-stremio/docs/services.md`
- `/home/runner/work/hacs-stremio/hacs-stremio/docs/events.md`
- `/home/runner/work/hacs-stremio/hacs-stremio/docs/configuration.md`
- `/home/runner/work/hacs-stremio/hacs-stremio/custom_components/stremio/services.yaml`
- `/home/runner/work/hacs-stremio/hacs-stremio/custom_components/stremio/sensor.py`
- `/home/runner/work/hacs-stremio/hacs-stremio/custom_components/stremio/binary_sensor.py`
- `/home/runner/work/hacs-stremio/hacs-stremio/custom_components/stremio/button.py`

### External sources
- Stremio Addon SDK resources: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/README.md
- Stremio deep links: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/deep-links.md
- Stremio feature request for Trakt sync: https://github.com/Stremio/stremio-features/issues/344
- `AboveColin/stremio-ha`: https://github.com/AboveColin/stremio-ha
- `hudsonbrendon/HA-stremio`: https://github.com/hudsonbrendon/HA-stremio
- `timojokinen/hassio-stremio-server`: https://github.com/timojokinen/hassio-stremio-server
- `redd-ravenn/stremio-trakt-addon`: https://github.com/redd-ravenn/stremio-trakt-addon
- MyTrakt Sync: https://mytrakt.elfhosted.com/
- Home Assistant community thread for this integration: https://community.home-assistant.io/t/stremio-integration-for-apple-tv/976514
- Reddit recommendation-addon demand signal: https://www.reddit.com/r/StremioAddons/comments/1cp8ck1/add_on_for_recommendations/
- `upcoming-media-card`: https://github.com/custom-cards/upcoming-media-card
- Spotcast: https://github.com/fondberg/spotcast

## Notes / caveats
- Some web sources (especially Reddit and Home Assistant forum pages) were available via search results and citations but not directly fetchable from this environment; they are included as source URLs and demand signals, but the strongest directly-verified user quotes in this report come from the Stremio GitHub feature request thread.
- Stremio's officially documented extension surface is much clearer around addon resources and deep links than around account/library write APIs, so write-back opportunities should be treated as promising but implementation-sensitive.
