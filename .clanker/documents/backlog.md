Most relevant stuff:

- PROMPT ASSEMBLY & TEMPLATE NORMALIZATION (PIPELINE CONSOLIDATION)
   a. Normalize prompt and ui template origin to be multiline strings (like ui is now)
      - logic involved with _Promptbuilder becomes redundant
   b. find a solution to the repl map aquistition step. it differs for the two. prompt has no good service to turn to
   c. `OutputAssemblyService` now becomes reduces to just the convert method. perhaps it can do the work for the prompt, after all? it can have two hats, letting gameengine orchestrate it.
   d. then each flow does a different thing with the output.
   d. result: Prompt generation and UI rendering are unified under a single declarative template-hydration pipeline, eliminating dynamic tag overhead and ~60 lines of builder logic.

- Bugs
    a. arrow keys interpreted as esc

Back of pipeline stuff:

- MOVE SELECTED BTN STUFF & HANDLERS INSIDE KB. MAYB IT JUST TAKES CONFIG RATHER THAN B ORCHESTRATED

- DYNAMIC GRID RENDERING ENGINE (EXTENSIBILITY PREREQUISITE)
   a. Decouple layout rendering from hardcoded MAIN_CONSOLE_TEMPLATE tokens.
   b. Implement programmatic button grid layout builder supporting flexible row sizes.
   c. Update OutputAssemblyService to render dynamic UI widths.
   d. result: Terminal console dynamically renders layouts based on arbitrary row key counts without template coupling.

- LOWER-LAYER BRIDGE ONE-SHOT STABILIZATION
   a. Finalize FileBridge and IOBridge exception boundaries (`ADOPTED_NOTICES`).
   b. Validate terminal raw-mode restoration during system exit signals.
   c. One-shot generate bottom-layer implementations and standard entrypoint.
   d. result: Low-level bridge layer and entrypoint are completely stabilized, fully integrated, and error-safe.

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