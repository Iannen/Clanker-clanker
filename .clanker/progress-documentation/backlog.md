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
        

2. Implement .clanker files extension policy by whitelist(s), forcing alignment job.
    - progress documentation -> .cdoc
    - templates -> .template
    - prompt fragments -> .fragment
    - config fragments -> yaml

3. Space reclamation program:

III. Slated for implementation:

IV. Recently implemented:

4. UI bug: UI border shifts depending upon button state on row
    [x] fix'd: a 'friend' bungled while refactoring Button.get_repl_map
        - but he was able to help recover, so all is forgiven

V. Critical bugs
