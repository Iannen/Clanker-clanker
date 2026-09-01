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

III. Slated for implementation:

4.  Add 'repo_manifest' resolver: Produces a flat list of workspace files with line count metrics, for the benefit of repo analysis & config development
    Example yaml declaration: 
'''
- { id: <attachment_token_id>, type: repo-manifest, pud_fileset: <fileset_name>, shared_fileset: <fileset_name_of_optional_fileset> }
'''
    [ ] 'clanker.py': 
        - add 'REPO_MANIFEST = "repo-manifest"' to 'Resolver' 'Type' enum 
        - 'AssembleyService._resolve':add if branch and logic:
            - produce a 'pud_files' list of files for mandatory pud_fileset (no fallback) (logic similar to REPO_CONTENT branch)
            - produce 'pud_manifest' string from the 'pud_files'
            - then envelop 'pud_manifest' content in '<pud-manifest>' tags
            - if 'shared_fileset' is supplied:
                - produce a 'shared_files' list of files (no fallback)
                - produce 'shared_manifest' string from the 'shared_files'
                - then envelop 'shared_manifest' in '<shared-manifest>' tags
            - then concatenate the two into resolver return value
'''
<pud-manifest>
clanker.py : 512 lines
adapters.py : 180 lines
utilities.py : 95 lines
.clanker/config.yaml : 32 lines
.clanker/shared-assets/config-fragments/kb_def.yaml : 40 lines
</pud-manifest>
<shared-manifest>
clanker.py : 512 lines
adapters.py : 180 lines
utilities.py : 95 lines
.clanker/config.yaml : 32 lines
.clanker/shared-assets/config-fragments/kb_def.yaml : 40 lines
</shared-manifest>
'''
        - if no shared files was supplied, then no 'shared manifest' shall display

IV. Recently implemented:

3. Refactor 'FileBridge.get_pud_files' support tokenized arg payload, move trailing '/' from 'BasePathTokens' to 'CfgFragments' members:
    - [x] `clanker.py` & 'adapters.py', 'FileBridgePort' & 'FileBridge':
        - 'BasePathTokens' members: 
            - "<PUD>/" -> "<PUD>" 
            - ..
        - 'CfgFragments' members:
            - ".clanker/config.yaml" -> "/.clanker/config.yaml"
            - ..
        - Align 'FileBridge.get_file_contents' to accept new token and pathstr format
        - Refactor `get_pud_files`:
            def get_files(
                self,
                basepath_token: str ,
                rel_roots: list[str | Path], 
                missing_ok: bool = False
            ) -> set[Path]: pass
        - `AssemblyService`:
            - Update existing `REPO_CONTENT` branch to call `self.files.get_files(BasePathTokens.PUD, ...)`.

V. Critical bugs
