I. Asset & domain sharing for Clanker & other PUDs (Project under development):

    1. Shared assets: Clanker should carry a host of reusable assets that all projects can use. 
        - Shared assets located relative to the path of the clanker.py script under execution
        - PUD assets are relative to cwd, as they are now
        Challenges:
            - Reduced visibility of shared assets from the PUD increases likelyhood of filename collisions
            - Switching to full path resolution is not an option
            - Perhaps change clanker asset discovery code to put tuples of (fullpath, filename) into one big collection.
            - Then resolve unambiguous files, work out a solution for collisions.
            - Should probably implement (config based) global excludes from above logic

    2. Shared domains: Clanker should carry a set of shared domains, which are always available in any PUD on keys fixed by clanker business logic
            - Config & asset development domain. 
            - Presentation domain
        Challenges:
            - Repo content resolver: Domains of Clanker cannot pass repo content resolver specifics to PUDs. 

This is thought to promote ease of document management and consistency of common workflows

II. Standardize .clanker dir structure and progress-documentation defaults
    1. Proposed dir structure. This is just organizational, as asset resolution is path independent.
        clanker repo:
            .clanker
                progress-documentation
                prompt-assets
                shared-prompt-assets
                config.yaml
        other PUDs:
            .clanker
                progress-documentation
                prompt-assets
                config.yaml

    2. Progress-documentation: Standardize document names & their internal structure
'''backlog.md
I. Ideas, complaints and non-critical bugs:
II. Items to refine & QC:
III. Slated for implementation:
IV. Recently implemented:
'''
'''north-star.md
'''
'''project-history.md
'''
'''architecture.md
'''
    Bonus: Embed the formats of document internal items into clanker, at least for shared domains and their renders. 

III. Implement functionality to support the management of a Github Profile Repository as a root / management project of the user.
    - I expect this would need a new resolver to 'peek' at content of other repositories (local repositories)