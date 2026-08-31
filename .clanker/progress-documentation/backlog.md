I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1. Leverage ports & adapters split -> offload non-business logic to adapters, leave behind clean code


    [ ] SessionService.get_keyboard: system path construction (os.path.realpath(__file__)) and manual existence checks
    [ ] SessionService.initialize_workspace: delegate workspace template discovery, directory creation, and path operations to the adapter
    

2. Implement .clanker files extension policy by whitelist(s), forcing alignment job.
    - progress documentation -> .cdoc
    - templates -> .template
    - prompt fragments -> .fragment
    - config fragments -> yaml

3. Space reclamation program:

III. Slated for implementation:

IV. Recently implemented:

V. Critical bugs
