# Troubleshooting

## Common Issues

### Integration Not Loading

**Symptoms:** Integration doesn't appear in the integrations list

**Solutions:**
1. Verify the `custom_components/stremio` folder exists
2. Check Home Assistant logs for errors: Settings → System → Logs
3. Restart Home Assistant after installation
4. Ensure `manifest.json` is valid JSON

### Authentication Fails

**Symptoms:** "Invalid credentials" error during setup

**Solutions:**
1. Verify your Stremio email and password are correct
2. Try logging into Stremio web/app to confirm credentials
3. Check if your Stremio account is active
4. Wait a few minutes and try again (rate limiting)

### Entities Not Updating

**Symptoms:** Sensors show "unavailable" or old data

**Solutions:**
1. Check network connectivity to api.strem.io
2. Verify scan interval in integration options
3. Check Home Assistant logs for API errors
4. Try refreshing manually: Developer Tools → Services → `stremio.refresh_library`

### Apple TV Handover Not Working

**Symptoms:** Can't stream to Apple TV

**Solutions:**
1. Ensure Apple TV integration is set up
2. Verify Apple TV is on the same network
3. Check if Apple TV is powered on
4. For VLC method, ensure VLC app is installed on Apple TV
5. Try switching handover method in options

## Debug Logging

To enable debug logging, add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.stremio: debug
```

Restart Home Assistant and check logs.

## Getting Help

- **GitHub Issues:** https://github.com/tamaygz/hacs-stremio/issues
- **Home Assistant Community:** Search or post in the Community forum
- **Documentation:** Check all docs in `/docs/` folder

## Reporting Bugs

When reporting issues, please include:
1. Home Assistant version
2. Integration version
3. Error messages from logs
4. Steps to reproduce
5. Expected vs actual behavior
