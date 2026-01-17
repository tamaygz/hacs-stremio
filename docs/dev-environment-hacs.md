# Development Environment Setup

This guide covers setting up HACS and the Stremio integration in a Home Assistant Core development environment.

## Understanding Home Assistant Installations

There are different types of Home Assistant installations:

1. **Home Assistant OS** - Full OS with Supervisor (has Add-ons menu)
2. **Home Assistant Supervised** - Linux with Supervisor (has Add-ons menu)
3. **Home Assistant Container** - Docker without Supervisor (no Add-ons)
4. **Home Assistant Core** - Python standalone (no Add-ons) ← **This is what we have**

**Important:** The "Add-ons" menu only exists in OS and Supervised installations. In Core installations, you manage dependencies directly.

## HACS Setup in Development Environment

### Step 1: HACS is Already Installed

HACS is already present in `/config/custom_components/hacs/`. You need to set it up through the UI.

### Step 2: Start Home Assistant

```bash
cd /workspaces/hacs-stremio
./scripts/start_homeassistant.sh
```

### Step 3: Access the Web UI

Open http://localhost:8123 in your browser.

### Step 4: Complete Onboarding

If this is your first time:

1. Create a user account
2. Set up your location
3. Skip analytics if desired

### Step 5: Set Up HACS

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **+ Add Integration** (bottom right)
3. Search for **"HACS"**
4. Follow the setup wizard:
   - Accept the terms
   - GitHub authentication is optional for development
   - Skip the GitHub token if you don't need private repos

**Note:** HACS appears as an integration in the sidebar after setup, not under Add-ons.

### Step 6: Set Up Stremio Integration

1. Still in **Settings** → **Devices & Services** → **Integrations**
2. Click **+ Add Integration**
3. Search for **"Stremio"**
4. Enter your Stremio credentials:
   - Email: Your Stremio account email
   - Password: Your Stremio account password
5. Complete the setup

## Why No Add-ons Menu?

In Home Assistant Core (development environment):

- ✅ Custom integrations work (like HACS and Stremio)
- ✅ HACS appears in the sidebar after setup
- ✅ All integrations available via Configuration → Integrations
- ❌ No "Add-ons" menu (only in OS/Supervised)
- ❌ No Supervisor API

## Common Issues

### "Can't see HACS in the menu"

HACS is configured through Integrations, not as a standalone menu item in Core installations.

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Look for HACS in the list
3. If not there, click **+ Add Integration** and search for HACS

### "Discovery integration not found"

This is normal. The `discovery` component is deprecated. It's now removed from the configuration.

### "DHCP error about libpcap"

Already fixed! `libpcap-dev` has been installed.

### "FFmpeg not found"

Install if needed:

```bash
sudo apt-get install ffmpeg
```

## Verifying Everything Works

### Check Integration Status

```bash
# View logs
tail -f /workspaces/hacs-stremio/config/home-assistant.log

# Look for:
# - "Setting up stremio"
# - "Setting up hacs"
```

### Check in Web UI

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. You should see:
   - **HACS** (if configured)
   - **Stremio** (if configured)

### Access HACS

After HACS is set up:

1. Look for **HACS** in the left sidebar
2. Click it to browse integrations and themes

## Development Workflow

### Installing Python Packages

The integration now uses native `aiohttp` (already in Home Assistant) instead of `stremio-api`:

```bash
cd /workspaces/hacs-stremio
source .venv/bin/activate
pip install -r requirements_dev.txt
```

### Running Tests

```bash
cd /workspaces/hacs-stremio
source .venv/bin/activate
pytest tests/
```

### Restarting Home Assistant

After code changes:

1. In HA UI: **Developer Tools** → **YAML** → **Restart**
2. Or: Stop the process and run `./scripts/start_homeassistant.sh` again

## Summary

- ✅ No Add-ons menu is normal for Core installations
- ✅ HACS works as an integration, accessible from Integrations page
- ✅ Stremio integration works with native aiohttp (no external dependencies)
- ✅ All custom components are in `/config/custom_components/`

For more information:

- [Home Assistant Installation Types](https://www.home-assistant.io/installation/)
- [HACS Documentation](https://hacs.xyz/)
- [Stremio Integration Docs](../docs/setup.md)
