I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1. Asset & domain sharing for Clanker & other PUDs (Project under development):

    a. Shared assets: Clanker should carry a host of reusable assets that all projects can use. 
        - Shared assets located relative to the path of the clanker.py script under execution
        - PUD assets are relative to cwd, as they are now
        Challenges:
            - Reduced visibility of shared assets from the PUD increases likelyhood of filename collisions
            - Switching to full path resolution is not an option
            - Perhaps change clanker asset discovery code to put tuples of (fullpath, filename) into one big collection.
            - Then resolve unambiguous files, work out a solution for collisions.
            - Should probably implement (config based) global excludes from above logic

    b. Shared domains: Clanker should carry a set of shared domains, which are always available in any PUD on keys fixed by clanker business logic
            - Config & asset development domain. 
            - Presentation domain
        Challenges:
            - Repo content resolver: Domains of Clanker cannot pass repo content resolver specifics to PUDs. 

1. Implement dual-source asset discovery with collision resolution and global excludes
    [ ] 'clanker.py': Update FileBridge path expansion and resolution logic for shared assets
        - Scan both script_dir relative Clanker shared assets directory and CWD-relative PUD paths into a unified collection of (fullpath, filename) tuples
        - Enforce deterministic collision handling giving PUD-local files precedence over shared assets
        - Integrate configuration-based global excludes to filter out specific shared paths or patterns

This is thought to promote ease of document management and consistency of common workflows
   
III. Slated for implementation:

IV. Recently implemented:
