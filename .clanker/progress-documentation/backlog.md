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

4. Enforce per-file validation against duplicate inline filesets and expose explicit validation workflow in clanker.py
    [ ] 'clanker.py' & 'utilities.py', 'ConfigValidator' & 'ConfigValidatorProtocol':
        - '_assert_no_quotes' -> 'assert_no_quotes'
        - 'validate_cfg_frag' -> 'get_as_dict' 
        - new method 'assert_filesets_not_neglected'
            - ensures no declaration of fileset in a config fragment is neglected by the config declaring identical fileset inline
                - mechanism: ?
    [ ] 'clanker.py': Update SessionService to orchestrate explicit validation steps
        - add a helper method to retrieve raw configuration text and execute assertions sequentially (assert 1, assert 2, etc.)
        - when all asserts pass, return the dict to call site

III. Slated for implementation:

3. Create helper on SessionService and introduce BasePathTokens to streamline config fragment loading (II.4 prereq):
    [ ] 'clanker.py': Introduce BasePathTokens and update CfgFragments path definitions
        - add BasePathTokens class to define basepath prefix tokens (e.g., PUD and SHARED)
        - prefix CfgFragments path constants using BasePathTokens configuration
    [ ] 'clanker.py' & 'adapters.py': Update FileBridgePort and FileBridge for tokenized paths
        - import BasePathTokens in adapters.py
        - combine 'pud_file_as_string' and 'shared_file_as_string' into a single 'get_file_contents' method
        - inspect path token prefix to resolve the correct basepath and retrieve file content
    [ ] 'clanker.py': Add _get_validated_cfg_fragment helper method to SessionService
        - accepts strings from 'CfgFragments', which were previously passed to methods 'pud_file_as_string', 'validate_cfg_frag' and 'shared_file_as_string'
        - utilize tokenized paths to fetch raw file content via unified file bridge call
        - execute validation via self.validator 
        - the conversion of raw text into dict via self.validator, which it returns to caller
        - catches 'ConfigViolations', reraises to 'UserTask', so caller need not worry about ex handling for the call.
    [ ] 'clanker.py': update various call sites in SessionService to utilize '_get_validated_cfg_fragment'
        - 'get_keyboard': 3 sites
        - 'initialize_workspace': 1 site

IV. Recently implemented:

V. Critical bugs
