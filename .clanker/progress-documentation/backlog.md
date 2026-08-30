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

1. Implement per-repo config-based global excludes for asset discovery (low prio)
    [ ] 'clanker.py': Update Config model and FileBridge asset mapping
        - Add `global_excludes` field to the Config model with sensible defaults
        - Modify FileBridge.getAssetMap() to filter out paths matching the repository's configured global excludes
        - Ensure global excludes are strictly per-repo and not aggregated or inherited globally

2. Implement shared domains and named include/exclude sets in configuration (hp)
    [x] '.clanker/shared-assets/config-fragments/shared_domains.yaml' exists with a test domain. Its content:
'''
domains:
- name: "test"
  renders:
    - name: 'test'
      resolvers:
        - { id: "repo_content", type: "repo_content", includes: ["."], excludes: [".clanker"], sorting: "normal" } 
'''
    [ ] Update runtime configuration assembly in SessionService
        - Construct runtime configuration by prepending shared domains to those declared in config.yaml to ensure fixed key consistency
    [ ] Support named include/exclude sets
        - Add a model class 'RepoContent' to hold include/exclude sets
        - (?) Delay parsing of domains (and their resolvers) untill all repocontent is resolved
        - then, when parsing domains, substitute any 'reponame' with an appropriate dict
        - hmm, is our resolver flexiblility an asset for us here, in that we dont need to change the model of the resolver?

III. Slated for implementation:
        
IV. Recently implemented: