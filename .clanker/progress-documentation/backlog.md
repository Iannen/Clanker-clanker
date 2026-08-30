I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1. Implement per-repo config-based global excludes for asset discovery (low prio)
    [ ] 'clanker.py': Update Config model and FileBridge asset mapping
        - Add `global_excludes` field to the Config model with sensible defaults
        - Modify FileBridge.getAssetMap() to filter out paths matching the repository's configured global excludes
        - Ensure global excludes are strictly per-repo and not aggregated or inherited globally

III. Slated for implementation:

IV. Recently implemented:
