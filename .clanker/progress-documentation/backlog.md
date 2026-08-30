I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1. Relocate all template and config out of script and into .clanker (of Clanker)
    [ ] 

1. Relocate the config of the Clanker project from inside the script out to '.clanker/config.yaml'
    - 'KB_DEF' 

III. Slated for implementation:

IV. Recently implemented:

2. Update PUD initialization for streamlined directory scaffolding and template seeding
    [x] 'clanker.py': Update .clanker directory and subdirectory creation
        - Create desired subdirectories: .clanker/progress-documentation and .clanker/prompt-fragments
    [x] 'clanker.py': Update default config and documentation seeding from shared script assets
        - Locate documentation templates relative to clanker.py at .clanker/shared-assets/templates/documentation
        - Iterate over files, filtering for the .template extension
        - Save new files in the PUD under .clanker/progress-documentation/ with the .cdoc extension (converting <filename>.template to <filename>.cdoc)
    Implementation note: with ref to 'is_cwd_script_dir' logic, paths of Clanker's '.clanker' dir are relative to 'script_dir', while paths of the PUD's '.clanker' dir are relative to cwd