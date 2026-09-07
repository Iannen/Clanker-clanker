# Clanker: AI-Driven Terminal Prompt Assembly Utility

Clanker is a homegrown TUI application which attempts to solve the challenges facing the vibecoding solo develpoer, as experienced by its author.
  
  
- *Redundant in-line commentary, error masking default values*  
    ```python
    # function to retrieve and return the users items
    def process_user_items(user_id, items):
        #todo: find nice example
    ```
- *Fear-inducing git operations*
    ```
    $ git add .
    $ git commit -m "fixed minor bug in process_user_items"
    [main 4f82a1c] fixed minor bug in process_user_items
    1 file changed, 2 insertions(+), 1 deletion(-)
    $ git push origin main
    To github.com:user/clanker.git
    ! [rejected]        main -> main (fetch first)
    error: failed to push some refs to 'github.com:user/clanker.git'
    hint: Updates were rejected because the remote contains work that you do
    ...
- *Enslavement by registrations*
    ```html
    <!-- Verification Required -->
    <div class="auth-modal">
      <h3>Enter 6-Digit Authenticator Code</h3>
      <p>We sent a push notification to your registered mobile device...</p>
      <input type="text" placeholder="000 000" maxlength="6" autofocus />
      <button class="btn-primary" disabled>Verify (Resend in 45s)</button>
      
      <div class="error-banner">
        Session expired. Please <a href="/sso/login">log in again</a> to request a new code.
      </div>
    </div>
    ```

<then features to mitigate>
  - 
Lightweight, keyboard-mapped navigation; zero vendor lock-in; YAML-based template resolution; integrated progress tracking.
- **Status & Roadmap**: Functional active prototype with a stable resolution pipeline, full keyboard interface, and core template engine. Continuous efforts are directed toward refining default asset schemas and stabilizing progress tracking mechanisms.

---

# Terminal-First Prompt Engineering Workflow
Clanker serves as a bridge between local repository state and external LLM environments, standardizing project context into clipboard-ready prompts without external API dependencies.

- **Use-Case Breakdown**:
  - **Context Aggregation**: Automatically packs repository trees, individual files, and configuration fragments using delimited tags.
  - **Dynamic Resolution**: Evaluates YAML configurations to bundle domain-specific prompt layouts with active code files.
  - **Progress Tracking**: Tracks evolving architecture across development sessions using a template-driven documentation system (`.cdoc`).

- **Architecture & Structure**:
  - `clanker.py`: Implements the presentation, execution engine (`AppEngine`), state management (`SessionService`), and template hydration pipeline (`AssemblyService`).
  - `models.py`: Defines core data classes, protocol interfaces (`FileBridgePort`, `IOBridgePort`), custom domain exception hierarchies, and domain entities (`Keyboard`, `Resolver`, `Domain`).

- **Usage & Workflow**:
  1. Launch `clank` within any project repository.
  2. Press numeric keys `1-0` to toggle active development domains.
  3. Press hotkeys (`Q`, `W`, `E`, `R`) to compile context-aware prompts directly into the system clipboard.
  4. Paste into your preferred LLM chat window.

---

# Project Access & Setup

- **Review Options**:
  - **Manual Review**: Examine `clanker.py` and `models.py` for decoupled service architecture and protocol contracts.
  - **Conversational Agent Review**: Pass the repository URL directly to an AI agent for code pattern analysis.
  - **Evaluative Review**: Pass `evalcopy.zip` to an AI model for structured architecture audits.

- **Installation & Prerequisites**:
  - **Prerequisites**: Python 3.10+ and `ruamel.yaml`.
    '''bash
    pip install ruamel.yaml
    '''
  - **Clone Repository**:
    '''bash
    git clone https://github.com/Iannen/Clanker-clanker.git
    cd Clanker-clanker
    '''
  - **Symlink Setup**:
    '''bash
    chmod +x clanker.py
    sudo ln -s "$(pwd)/clanker.py" /usr/local/bin/clank
    '''

- **Notes & Disclaimers**:
  - **LLM Performance Notes**:
    - *Gemini*: Recommended choice for consistent handling of long structured context templates.
    - *ChatGPT*: Highly functional, though occasionally sensitive to very large prompt payloads.
    - *Grok*: Operational, but bound by free-tier volume limits.
    - *Claude*: Performs accurately across initial tested configurations.
  - **General Notice**: This tool is developed with LLM assistance. Users should inspect local scripts prior to running execution symlinks in critical production environments.