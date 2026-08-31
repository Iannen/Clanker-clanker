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

4. Refactor remaining UI template sourcing from in-script to file reads
    [ ] 'AssemblyService._resolve, Resolver.Type.KB_INFO' & 'keyboard.build_ui_repl_map': migrate kb method out to the switch, then delete kb method
        - 'AssemblyService._resolve, Resolver.Type.KB_INFO' shall query kb for the unique button, and then process them  in the switch case to produce the repl map (inheriting the logic seen in 'keyboard.build_ui_repl_map') to do so
    [ ] 'Layout' enum class: add new members to support filereads:
        - '.clanker/shared-assets/layouts/btn_active.layout'
        - '.clanker/shared-assets/layouts/btn_hl.layout'
        - '.clanker/shared-assets/layouts/btn_inactive.layout'
    [ ] 'AssemblyService._resolve, Resolver.Type.KB_INFO'
        - Rather than use in-script constants, it will source the templates by filereads using enum values and 'files.read_clanker_asset'
    [ ] Eliminate now redundant in-script button constants.

III. Slated for implementation:

IV. Recently implemented:

3. Refactor prompt & ui template sourcing, introduced new 'layout' terminology
    [x] delete 'get_clanker_files' from port and adapter
    [x] Declare a global 'layouts' enum:
        - UI_LAYOUT = ".clanker/shared-assets/layouts/ui.layout"
        - PROMPT_LAYOUT ".clanker/shared-assets/layouts/prompt.layout"
    [x] Refactor FileBridgePort and FileBridge 'read_clanker_asset' to accept a string not a Path, returning the content of the file at the path
    [x] 'AssemblyService.get_template': 
        - refactor to a switch over layouts, passing the appropriate member into  'files.read_clanker_asset'
    [x] 'AssemblyService.BUILTIN_TEMPLATES', 'UI_TEMPL', 'PROMPT_TEMPLATE': eliminate
V. Critical bugs
