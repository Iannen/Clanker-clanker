Most relevant stuff:

- PIVOT ARCHITECTURE: REFACTOR APP TO GET DATA AS YML CONFIGS

   I: END GOALS

      1. Two data shapes. One is from yaml config files in .clanker/configs. the other is the hydrated app datatree 
         - the llm can assist the user with rapid dev of configs. 

      2. Dynamic resolution of config files path to app data Tree, inside a boot service.
         a: eat up all files into map of dicts (name -> dict)
         b: pass over dicts, add prereqs to str list dict.reqs given an analysis of dict member key name and value:
            - the name says the type of it. so 'domain' and 'domains' singular or list of domain instances.
            - the value then says the members of it:
               - singulars can be null if pydantic dc allows it. 
               - list of strings is interpreted as named instances of the type.
                  example: 'prompt_fragments = []' -> all frags, 'prompt_fragments = [frag1, frag2,..] -> frags in that order
               -  yaml vals that conforms to a certain regex allows us to migrate zip statements out from python and into the configs:
                  - 'populated_num_btns' : 'zip_add(num_btns, domains)'
         - Resolution Rules
            - Match Rule: member_type == singular(member_key_name) (so 'domains' and 'domain' -> class Domain)
            - Singulars: Enforced by Pydantic model as nullable (None) or strictly required.
            - Lists: Never null.
               - Empty []: Automatically populates with ALL discovered instances of that type.
               - Populated ["a", "b"]: Populates ONLY specified items in written order.
                  - Missing items trigger validation failure.
               - zip_add causes the second to be member of first
         - return hydrated app data tree to engine.

   II: MEDIUM TERM GOALS
      - keyboard changed from 'service' to data object. 
         - kb is no longer part of di, and is not instantiated in main. 
         - Sessionservice gets the responsibility of delivering the finished KB to engine on boot.
            -> we just want to get all the init inside sessionservice. no need to reach for end state.
         - engine sees some changes to bootstrap calls, and perhaps some to account for kb not beeing part of di. probably very little.

   III: IMMEDIATE GOALS

         a. Rename `KeyboardService` -> `Keyboard`, change it to pydantic dc. move it from services to data model section of file.
            - retains the same functionality. lets not clean the teacup while we juggle it.
            - the pydantic class must be flexible for now, we just want to get it working without some strictness weighting us down.

         b. Give Sessionservice the responsibility of creating kb and returning it to calling engine
               - 'get_keyboard' to replace current get_config role in engine bootstrap.
               - 'get_keyboard' simply reuses existing methods of session and the renamed keyboard class to serve engine letting ex bubble.

         c. engine now populates self.kb from the sessionservice call rather than have it be done in DI setup in main()
            - if kb contract is the same, then perhaps engine does not need alignment beyond its bootstrap method.

         d. KeyboardService does not appear in DI setup any more. i dont think it uses the .files it was given anyway         

Back of pipeline stuff:

- MOVE SELECTED BTN STUFF & HANDLERS INSIDE KB. MAYB IT JUST TAKES CONFIG RATHER THAN B ORCHESTRATED

- DYNAMIC GRID RENDERING ENGINE (EXTENSIBILITY PREREQUISITE)
   a. Decouple layout rendering from hardcoded MAIN_CONSOLE_TEMPLATE tokens.
   b. Implement programmatic button grid layout builder supporting flexible row sizes.
   c. Update OutputAssemblyService to render dynamic UI widths.
   d. result: Terminal console dynamically renders layouts based on arbitrary row key counts without template coupling.

- Bugs
    a. arrow keys interpreted as esc

Recently achieved(:

I:    RESOLVE BASE PATH BINDING
      - Replaced dynamic runtime path injection at startup with an immutable base path locked in during bridge initialization.
      - Result: Guaranteed working-directory independence and deterministic path resolution across all file operations.

II:   REFACTOR CONFIGURATION & SESSION SERVICE
      - Transferred get_config() and save_config() persistence/validation logic from KeyboardService to SessionService.
      - Decoupled KeyboardService from direct file IO and annotated class with # new name proposal: CommandRouter.
      - Updated GameEngine.bootstrap() to query SessionService for configuration lifecycle operations.

III.  EXTRACT BASE ENGINE & EXCEPTION ABSTRACTION
      - Extracted generic lifecycle execution loop, abstract hooks, and centralized exception policy into base Engine class.
      - Delegated terminal loop mechanics, service exit signals (ProgramExitNotice), and error escalation away from GameEngine.
      - Result: GameEngine becomes purely declarative, leaving runtime orchestration and exception boundaries fully encapsulated in base infrastructure.

IV.   STANDARDIZE RENDER PIPELINES & SHIFT PROMPT GEN TO GAME ENGINE
      - Consolidated UI rendering and Prompt compilation under a single, stateless hydration endpoint (`OutputAssemblyService.hydrate(template, repl_map)`).
      - Shifted flow orchestration and template ownership to `GameEngine`, extracting fragment resolution into a dedicated map builder (`get_repl_map(prompt_config)`).
      - Completely removed internal template selection, dynamic XML generation, `_PromptBuilder`, and redundant `SymbolSet` tag assembly logic.
      - Result: Unified, stateless declarative template-hydration pipeline with zero dynamic builder overhead and clean separation of concerns.