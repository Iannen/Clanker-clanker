I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

from north-star.md document:
"
1. Asset & domain sharing for Clanker & other PUDs (Project under development):

    a. Shared assets: Clanker should carry a host of reusable assets that all projects can use. 
        - Shared assets located relative to the path of the clanker.py script under execution
        - PUD assets relative to cwd
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

This is thought to promote ease of document management and consistency of common workflows
"
the bl item under development:
1. Implement dual-source asset discovery with collision resolution and global excludes
    [ ] 'clanker.py': Declare a new Failure exception for unresolvable asset collisions
        - Define a specific exception class to handle illegal or ambiguous asset filename clashes
        - Ensure it triggers an application crash and error trace on detection
    [ ] 'clanker.py': Adapt AssemblyService._resolve for dual-source mapping and collision handling
        - Integrate get_clanker_files and get_pud_files into a unified collection of (fullpath, filename) tuples
        - Enforce deterministic override rule where PUD-local files shadow Clanker shared assets
        - Raise the new collision Failure exception when ambiguous conflicts occur

III. Slated for implementation:

IV. Recently implemented:
