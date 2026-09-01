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

1. Add filetree resolver
    - produces a filetree, giving an overview over all files of the repository from a root (defaults to repo root)
    - useful for the llm to be able to assist in config development, without providing file contents.
    - would be intensely more useful if dependencies of files could also be resolved.

2. Space reclamation program:
    - Easy pickings have been had - what else?

III. Slated for implementation:

IV. Recently implemented:

2. Enforce per-file validation against duplicate inline filesets
    [x] 'clanker.py' & 'utilities.py', 'ConfigValidator' & 'ConfigValidatorProtocol':
        - '_assert_no_quotes' -> 'assert_no_quotes(raw_text: str, filepath: str = "")'
        - 'validate_cfg_frag' -> 'get_as_dict(raw_text: str)'
        - new method 'assert_filesets_not_neglected(cfg_frag: dict, filepath: str = "")':
            - declare 'violations' list
            - helper to derive string key from includes & excludes:
                - sort includes and excludes separately, stringify to form deterministic string key
            - declare 'named_fileset_map: str -> str' (string_key -> fileset name)
            - populate 'named_fileset_map' from top-level 'sets' in cfg_frag
            - declare 'inline_filesets: list[tuple[str, str | None, str | None]]' tracking (string_key, domain_name, render_name)
            - traverse repo_content resolvers in 'domains' / 'renders':
                - skip if resolver uses 'fileset' or 'varname' key
                - compute string_key for resolver's includes/excludes
                - record entry in 'inline_filesets'
            - for each (string_key, domain, render) in 'inline_filesets':
                - if string_key in 'named_fileset_map':
                    - append violation: f"    domain '{domain}' render '{render}': use named fileset '{named_fileset_map[string_key]}'"
            - if violations list is non-empty, raise ConfigViolations(filepath, violations)
    [x] 'clanker.py, SessionService._get_validated_cfg_fragment':
        - Refactor to carry out asserts & conversion visibly in a logical order:
            1. raw-text assertions (self.validator.assert_no_quotes)
            2. convert (self.validator.get_as_dict)
            3. dict-based assertions (self.validator.assert_filesets_not_neglected)
            4. return dict to caller

3. Create helper on SessionService and introduce BasePathTokens to streamline config fragment loading (II.4 prereq):
    [x] 'clanker.py': Introduce BasePathTokens and update CfgFragments path definitions
        - add BasePathTokens class to define basepath prefix tokens (e.g., PUD and SHARED)
        - prefix CfgFragments path constants using BasePathTokens configuration
    [x] 'clanker.py' & 'adapters.py': Update FileBridgePort and FileBridge for tokenized paths
        - import BasePathTokens in adapters.py
        - combine 'pud_file_as_string' and 'shared_file_as_string' into a single 'get_file_contents' method
        - inspect path token prefix to resolve the correct basepath and retrieve file content
    [x] 'clanker.py': Add _get_validated_cfg_fragment helper method to SessionService
        - accepts strings from 'CfgFragments', which were previously passed to methods 'pud_file_as_string', 'validate_cfg_frag' and 'shared_file_as_string'
        - utilize tokenized paths to fetch raw file content via unified file bridge call
        - execute validation via self.validator 
        - the conversion of raw text into dict via self.validator, which it returns to caller
        - catches 'ConfigViolations', reraises to 'UserTask', so caller need not worry about ex handling for the call.
    [x] 'clanker.py': update various call sites in SessionService to utilize '_get_validated_cfg_fragment'
        - 'get_keyboard': 3 sites
        - 'initialize_workspace': 1 site
        
V. Critical bugs
