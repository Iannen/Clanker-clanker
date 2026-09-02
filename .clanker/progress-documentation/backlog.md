I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1.  Leverage ports & adapters split -> offload non-business logic to adapters, leave behind clean code
    The classes that depend directly upon adapters are candidates for review:
        - SessionService
        - AssemblyService
        - IOService   
    Methodology is review of service class methods
        - the usage of 'self.files.write_default_documents' in SessionService.initialize_workspace is thought to be a good example of desired outcomes.
        - do other methods carry out stuff that the adapter could take care of for them?

2. Space reclamation program:
    - Easy pickings have been had - what else?

3.  Shared Domains & seed config, overhaul for the purpose of Iannen metarepo:
    - Seed domain 'manifest analysis': 
        - domain fragment -> 'manifest resolver' 
        - prompt 'on-init': 
            prompt_fragments: MDF resolver
                -> a 'config frags package', containing shared, kb def & pud config
                -> 'explore-repo.pfrag': make it generate further prompts in domain
                -> 'config-dev-output.instruction'
                -> domain / render output instructions: for ez

    - Shared domain 'presentation': 
        - Should include 'core' fileset, exposing the business logic alongside readme and instructional prompt fragments
            - 'core' fileset is pud specific: needs to feature in config template and any pud config.

4. Move templates and layouts out of shared assets dir
    - shared assets just config and prompt frags

'''
§base_fragments§ -> sits in 'kb def', taken
§domain_fragments§ -> 
§prompt_fragments§ ->
§repo_content§
'''

git push checklist
    - Clanker compiles prompts?
        - yes

    - Iannen too?
        - yes 

    - Cloudproject?

    - testrepo -> fresh init all g?



III. Slated for implementation:

IV. Recently implemented:

V. Critical bugs
