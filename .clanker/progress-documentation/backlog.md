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
        

2. Implement .clanker files extension policy by whitelist(s), forcing alignment job in app projects.
    - progress documentation -> .cdoc
    - templates -> .template
    - prompt fragments -> .fragment
    - config fragments -> yaml

3. Space reclamation program:
    - Easy pickings have been had - what else?

4. Resolver Include / Exclude error handling:
    [ ] 'clanker.py': Update REPO_CONTENT resolver callsite for path retrieval
        - Pass missing_ok=False for include paths to preserve error raising on missing members
        - Pass missing_ok=True for exclude paths to silently swallow missing member errors (e.g., .git)
    [ ] 'clanker.py': Update FileBridgePort interface signature
        - Add missing_ok: bool = False parameter to the get_pud_files abstract method
    [ ] 'adapters.py': Update file bridge implementation for missing_ok support
        - Adjust get_pud_files logic to handle missing paths gracefully according to the missing_ok flag


III. Slated for implementation:

IV. Recently implemented:

V. Critical bugs
