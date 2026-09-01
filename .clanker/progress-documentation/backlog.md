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
        

2. Runtime Configuration validation
    [ ] Create declarative rules for the aggregated runtime config
    [ ] On bootstrap: Validate RT config agains rules
        - Aggregate violations into a collection 
        - When validation is complete:
            - If no violations, proceed to next phase (next validation phase or bootstrap completion)
            - Else convert violations collection into a text, put text into a 'class ConfigViolation(Failure)' instance
                - Then let app crash, displaying the failure contents to produce a nice path for user to correct issues
    The validation is non-destructive, it only serves to inform the user if he has 'work to do'

3. Space reclamation program:
    - Easy pickings have been had - what else?

III. Slated for implementation:

IV. Recently implemented:

V. Critical bugs
