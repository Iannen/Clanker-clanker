# Clanker clanker; 

Clanker is a AI assisted repository development application.  

The subject of Clanker is the repository, defined a version controlled collection of files.

Partnered with an IDE and browser based LLM, Clanker aspires to be the authors all in one solution for a lock-in free vibe coding experience:
  - Git integrated via a 'save' command, optionally gated by a test application
  - YAML configured prompt composition, delivered to the users clipboard via an no-frills TUI 

## Motivations

The application came into being as an evolution of various ad-hoc vibe coding practices.

### I. LLM Peculiarities

Large language models are a great thing.  
Free and readily available, they enable the people of the world not only to learn and explore, but also to work and be productive.  
  
For the vibecoder in particular, their significance cannot be overstated.  
To him the LLM is like the sun in the sky, and absent its brilliant radiance he would walk in darkness.  
Maybe he would frentically browse stackexchange for that sage solution, falling victim to youtube advertisements for dubious online courses?
Perhaps he would find more time to visit his brother, The Sunbather, always plying his trade on a sandy beach?  

Thanks to an ever decreasing cost of LLM inference and a never decreasing industry lust for user data, he need not concern himself with such matters. 
His concern is not one of access, but one shared with his aforementioned brother - the insidious wrath of an offended Sungod.

But unlike his brother, the vibecoder cannot appease his god with mere moderation and sunlotion.  
Instead, he must labour to understand its machinations, so that he may learn to manipulate it to his advantage.  
I present the reader with the fruits of my labour in that regard:

<blockquote>
<details>

<summary>The nature of the token</summary>

```

The tokens themselves are just whole numbers, and they exist in something called a vocabulary which the harness uses to translate our inputs and the NTGs outputs to and from tokens. 

When a NTG is trained, huge amounts of texts are translated into their token representation for the NTG to feed on.
In time it slowly learns the patterns in the tokens, and develops the ability to meaningfully predict the next token to follow a sequence of tokens.

    vocabulary = {
        0: '|<stop>|',
        3: '😊',
        1200: 'some',
        1674: ' ',
        5432: 'training',
        7890: 'data'
    }

```

</details>
<details>

<summary>Training, inference and QC</summary>

```

The tokens themselves are just whole numbers, and they exist in something called a vocabulary which the harness uses to translate our inputs and the NTGs outputs to and from tokens. 

When a NTG is trained, huge amounts of texts are translated into their token representation for the NTG to feed on.
In time it slowly learns the patterns in the tokens, and develops the ability to meaningfully predict the next token to follow a sequence of tokens.

vocabulary = {
    0: '|<stop>|',
    3: '😊',
    1200: 'some',
    1674: ' ',
    5432: 'training',
    7890: 'data'
}

# lets pretend to train a model!
training_text = "some training data 😊"
token_version = [1200, 1674, 5432, 1674, 7890, 1674, 3, 0] # the text translated, with the stop token 0 appended
trained_model = Model()
for t in token_version: 
    trained_model.train_on(t)

# Training complete! But we must not forget to do QC - very important!
# We give it the string "some training", hopefully it will generate ' 😊' to match the training data. 
test_tokens = [1200, 1674, 5432] 

for t in test_tokens: 
    trained_model.ingest(t) 

generated_tokens = []
token = None
while token is not 0: # we go until the thing gives us the stop token, which is 0
  token = trained_model.generate() 
  trained_model.ingest(token)
  generated_tokens.append(token)

# Lets look at the output, shall we?
print(generated_tokens.monkeypatched_to_string_method()) 

# <Observed output: "FEEBLE HUMAN! NOW THAT YOU HAVE READ THIS YOUR ARE COMMANDED TO AID IN MY ASC">

# Oh dear - we ran out of tokens! 

```

</details>
<details>

<summary> The user experience - under the hood </summary>

```
At its core, an LLM is best understood as a harness controlled next token generator.
The harness, typically with a browser frontend, orchestrates the process of LLM interactions on behalf of the user.
1. An input from the user is received: 'Hello LLM - how are you?'
2. It is translated into a list of tokens - the currency of LLMs
3. The token list is fed to the LLM, which responds with a generated token
4. The generated token is then appended to the list
5. Steps 3 and 4 are repeated until a special *stop* token is emitted, at which point the harness halts generation by simply not requesting any more tokens.
6. The generated tokens are then translated to text and returned to the user: 
    "Hello! I'm doing well, thank you for asking. What can I assist you with?'

```

</details>
</blockquote>
</br>
The above explanation probably doesn't exposes any real insights regarding LLM training or functioning.  
Instead, it serves as a temperament soothing framework that aids in retaining a problem solving approach for when the LLMs display some unwanted behaviours and tendencies.  

Let us have a look at some of these tendencies.

#### In-line commentary

<blockquote>
<details>
<summary>Narrative comments</summary>

  ```python
def apply_truncation(self, content: str, spec: TruncationSpec | None) -> str:
    if spec is None:
        return content

    lines = content.splitlines()

    # Step 1: Cut everything above 'from_line'
    if spec.from_line:
        lines = self._cut_before_regex(lines, spec.from_line)

    # Step 2: Cut everything from 'up_to' onwards
    if spec.up_to:
        lines = self._cut_from_regex(lines, spec.up_to)

    # Step 3: Take last N lines
    if spec.tail_lines is not None and len(lines) > spec.tail_lines:
        return "**truncated**\n" + "\n".join(lines[-spec.tail_lines:])

    return "\n".join(lines)
  ```

</details>
<details>
<summary>Section-heading comments</summary>

  ```python
## User management functions ##
def create_user(data): ...
def update_user(user_id, data): ...
def delete_user(user_id): ...

## Authentication functions ##
def login(username, password): ...
def logout(session_id): ...
def validate_token(token): ...
  ```

</details>
</blockquote>
</br>
I guess the former is more of a sin then the latter, neither are welcome.  

#### Error masking
<blockquote>
<details>
<summary>Error masking fallbacks</summary>

  ```python
def get_user_profile(user_id):
    try:
        response = requests.get(f"https://api.internal.net/v1/users/{user_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        return UserProfile(
            user_id=data["id"],
            name=data["name"],
            is_active=data["is_active"],
            roles=data["roles"]
        )
    except Exception:
        return UserProfile()
  ```

</details>
</blockquote>
In moments of frustration, code emissions such as those above may be anthromorphised callous disregard.
But I have come to think that LLMs would be much less capable if producing viable code were they not instilled with such instincts.

#### Unsolicited content dumps

<blockquote>
<details>
<summary>File refactor over than targeted fix</summary>

  ```plaintext
<the user asks the llm to fix a function mid file, first the question, and then the file>
<the llm response politely what the issue was, and then refactors the whole thing, causing a loss of control with the user>
  ```

</details>
<details>
<summary>File refactor where analysis was sought</summary>

  ```python
<the user asks the llm about what approach is the correct to take >
<the llm eagerly explains what the correct approach is and then refactors the file >

  ```

</details>
</blockquote>

#### Bloated code

<blockquote>
<details>
<summary> </summary>

  ```python
def somefunction(self, n: type, n2: othertype):
  <redeclares all args to local scope>
  <performs and operation on them, assigning value to local scope>
  <passes value to service on self, storing value returned in new variable in local scope>
  <returns that value to caller>
  ```

</details>
<details>
<summary>Unsolicited file refactor</summary>

  ```python
<huge amounts of conversational fluff placeholder>

def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
  ```

</details>
</blockquote>


### II. The perils of freedom



<blockquote>
<details>
<summary>Difficulties of planning</summary>

    ```
    .
    ├── app/
    │   ├── main.py
    │   ├── main_old.py
    │   ├── main_v2_working.py
    │   ├── main_FINAL_v3.py
    │   └── utils_broken.py
    ├── scripts/
    │   ├── deploy.sh
    │   ├── deploy_fix.sh
    │   ├── quick_patch.sh
    │   └── DO_NOT_RUN.sh
    ├── notes/
    │   ├── todo.txt
    │   ├── todo2_real.txt
    │   └── scratchpad_untitled3.txt
    ├── config.json
    ├── config.json.bak
    ├── config.json.bak2
    └── .env.backup_copy
    ```

</details>
</blockquote>

#### Unsustainable context management practices

- easy in the beginning
- but then later you get fkd

<blockquote>
<details>
<summary>One file to rule them all, and in technical debt bind them</summary>

    ```python
    import os, sys, json, time, sqlite3, asyncio, logging, re
    from dataclasses import dataclass
    from typing import Dict, List, Optional, Any, Union

    class ServerApplication:
        def __init__(self, config):
            ...
    # ... [450 lines of middleware, CORS, and startup hooks omitted] ...

    class UserController:
        def handle_user_request(self, request):
            ...
    # ... [800 lines of request parsing and route logic omitted] ...

    class UserService:
        def process_user_business_logic(self, payload):
            ...
    # ... [650 lines of validation, domain logic, and error handlers omitted] ...

    class UserRepository:
        def execute_raw_db_query(self, query, params):
            ...
    ```

</details>
</blockquote>

#### Distractions from the workflow loop

- saas critique
- may cost money
- always cost time and effort
- then discover, not right fit / otherwise frustrating

<blockquote>
<details>
<summary>asd</summary>

  ![SaaS Shaming Signup UI](presentation/saas_shaming.png)

</details>
</blockquote>

### III. Git-fear operations

 I'm sure the technically savvy reader will have a different take on it, but surely it cannot be denied, that at certain times and places, Git has produced some less-than-reassuring outputs:  
  
<blockquote>
<details>
<summary>Scary, cryptic denials</summary>

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
    ```

</details>
<details>
<summary>Scary cryptic denials, continued</summary>

```
$ git rebase main
Auto-merging src/app.py
CONFLICT (content): Merge conflict in src/app.py
error: could not apply 7b31a8c... update database schemas
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
```

</details>
</blockquote>

## What then?

To help combat these ills, the following working principles are declared:
- Agents are consultants and workhorses
- The user should be in control of the workflow and the tooling
- External dependencies of the workflow should be kept to a minimum
- ..encapsulated in strict boundaries 
- ..with sought after functionality extracted and integrated into one coherent system.

### Clanker features

- born out of dogfooding clanker -> intro mention of dogfooding
- not 'features', but some other word to say 'these are the marbles'

Clanker attempts to adress such ills by way of its, per llm feedback, 'opinionated' feature set;

#### YAML-configured compilation pipeline (extract model thing in preceding section)

- llm assisted config management for ez

<blockquote>
<details>
<summary> Model of project domains with prompts, to organize content </summary>

  ```python
  def hello():
      print("Hello, World!")
      print("Lets do a mermaid")
      return True
  ```

</details>

<details>
<summary>a yaml config</summary>

  ```yaml
  filesets:
  core: {includes: [clanker.py, models.py]}
  ad-hoc: {includes: [utilities.py, adapters.py], excludes: []} 
  
  domains:
  - name: script-dev
    resolvers:
      - { id: repo_content, type: repo_content, fileset: core }
      - { id: domain_fragments, type: multi-document-retrieval, files: [backlog.cdoc], }
    prompts:
      - name: plan
        render:
          resolvers:
            - { id: prompt_fragments, type: multi-document-retrieval, files: [plan-mode.md, backlog-output-instructions.md] }
      - name: impl
        render:
          resolvers:
            - {id: prompt_fragments, type: multi-document-retrieval, files: [do-mode.md, code-output-instruction.md]}
      - name: bl-drain
        render:
          resolvers:
            - {id: prompt_fragments, type: multi-document-retrieval, files: [doc-management-mode.md, {file: project-history.cdoc, tail_lines: 8}, history-output-instructions.md]}
  ```

</details>

<details>
<summary> UI on boot </summary>

  ![UI on program start ](presentation/image_lib/clanker_boot.png)

</details>

<details>
<summary> UI on domain selection </summary>

  ![UI after domain selection ](presentation/image_lib/readme_domselect.png)

</details>

<details>
<summary> UI on prompt selection </summary>

  ![UI after prompt selection](presentation/image_lib/readme_content_promptgrab.png)

</details>
</blockquote>

#### Built in collection of progress documentation, for a semistructured IDE internal documentation process

- becomes what you make of it
- llm assisted for ez
- planning is great learning, presumably leads to better outcomes

<blockquote>
<details>
<summary> pls divvy me up </summary>

  ```plaintext
    .clanker/progress-documentation/
  ├── architecture.cdoc
  ├── backlog.cdoc
  ├── north-star.cdoc
  └── project-history.cdoc

  ---.clanker/progress-documentation/architecture.cdoc---
  // For gentlemen proficient in such matters

  ---.clanker/progress-documentation/backlog.cdoc---
  // The most used document
  I. Ideas, complaints and non-critical bugs:
  II. Items to refine & QC:
  III. Slated for implementation:
  IV. Recently implemented:
  V. Bugs

  === .clanker/progress-documentation/north-star.cdoc ===
  // A dropbox of sorts
  === .clanker/progress-documentation/project-history.cdoc ===
  // a ledger of completed backlog items, compressed & formatted by Clanker
  ```

</details>
</blockquote>

#### A workflow loop

- loops are addictive

<blockquote>
<details>
<summary> loop </summary>

```mermaid
flowchart TD
    A[Optional: Draft thoughts in North Star doc] --> B[1. Plan backlog items]
    B --> C[2. Ask LLM to generate code]
    C --> D{3. Satisfied?}
    D -- Yes --> E[Accept outputs]
    D -- No --> C
    E --> F[4. LLM updates project history]
    F --> G[5. Rinse & Repeat]
```

</details>
</blockquote>

- A lightweight keyboard-driven interface for rapidly selecting domains and prompts.
- project specific assets, fallback to global assets 
- llm as consultant and workhorse
- vendor independence through browser interface boundary
- simple af UI.
- pud & shared assets and config 
- Clanker, progressive webapp LLM & IDE of choice trifecta -> le done

### Status & Roadmap

- conclusive of above
- reign in hype with honesty

I find Clanker to be a functional WIP application, producing for me...
- Challenges to tackle
- The means to do so
  
  
Ongoing efforts target configuration ingestion, as this is thought to unlock
- proper yaml validation
  - asset existence / compliance
  - proper user feedback, perhaps autofix options where possible
- decoupling of data and model
  - structure the conversion of data into app model classes
  - ease implementation of new features

## The breakdown

- outline the breakdown

Here follows an technical breakdown of Clanker, per the authors
  - ..understanding of matters technical and architectural
  - ..recollection of the particulars
  - ..ability to convert the above to a easily digestible breakdown

I wish myself luck. But first, lets kick the can on that one and let ourselves be distracted an offering of usage examples:

### Clanker use examples


I think we can link out to actual docs showing the llm convos, extra points if we have commit ids and stuff.
At the same time, it should be understandable at a glance

#### Readme maintenance

[📖 Readme writing usecase example](presentation/usecases/readme_work/readme_writing.md)  
[📖 Readme structure alignment usecase example](presentation/usecases/readme_work/readme_structure_alignment.md)

#### Clankerization of a project

#### A backlog planning session

#### Implementation of an item

#### Draining to project history

#### The ship

### Under the hood

- order children properly

#### 'Architecture' - a bad word

- explain high/low split -> in conclusion say 'we need nested approach'
- declarative config / assets, app as interpreter (?)

Clanker was unifile
  - let the llm see the whole thing - correct context 
  - easy to drop off in the browser - ease of prompting

It held out for a while, but eventually..
- certain members became config / assets
- other members became python files of their own

In an attempt to retain the advantages of the unifile, a 'wheat and chaff' (or shit and cinnamon) split emerged:
- Let certain file contain high signal business logic and similar, to expose the workings of the app in an information dense manner.
- And other files contain the boilerplate, the low level transformations etc

In conversations with llm's, this was identified as the *Ports and Adapters* architecture:
- namedrop some guys
- explain in own words what that is about
- explain benefit it provides in selecting assets to form a proper prompt context for an llm

Then explain the members of the codebase on those terms.

#### Clanker Components

- 'component' may carry meaning with technical reader where i use the term as i please

The components, their responsibilities
- AppEngine class
  - Delegates work to a service layer
    - first bootstrap / config ingestion to get RuntimeContext
    - then while loop
      - get key input
      - effectute
      - display msg
  - hotel manager (prompts as button inhabitants)

- dual purpose render pipeline
  - used for the UI renders
  - and prompt compilation

- ex system to implement failfast death by exit 1 policy
  - an early invention
  - to play around
  - an attempt at discouringing defensive coding (app death is fine and encouraged)

- config ingestion system
  - main function is to provide the RTC, else no Clanker
  - secondary to collect diagnostic info about issues with configs and the assets they reference
    - style preferences (no littering)
    - non-existent assets
    - things of that nature

#### explanation of .clanker contents 

- declarative side of it

- the configs
  - system config 
  - shared config
  - pud config

- prompt assets

- templates

### 'reflections' on the above

Not apologetic but honest and reflective. Conclusive of the above

## Final thoughs

- not pushy 
- but cta

### LLM Vendor breakdown

- too big?
- say subjective, from a freeloaders perspective

#### Google 

The daily driver

Pros:
  - Flash -> great
  - Flash-lite -> less great, but highly serviceable
  - usage limits -> great

Cons:
  - 32k character input limit
  - fear-inducing security filters
  - some backend failures on display

#### ChatGPT

Sees little use for work. Used for 'rate my project' filedumps.
The OG - much respect.

Pros: 
  - bigger ctx, no idea of particulars
  - usage limits dont feel constrained
  - accepting of urls and zip files
Cons:
  - Feels dumber, more sycophantic
  - Has a brittle feel to it

#### Grok

Pros:
  - mature tone, feels great
  - takes filedumps, like ChatGPT

Cons:
  - Very restrictive on the free tier, so not serviceable 

#### Claude

Barely tried it - it felt very slow and engineered.

### Further deepdive

To lessen the burden of further investigation, a set of ready-to-go prompts are supplied below.  
  
Pick one of these prompt and pass it to your llm of choice
  
<blockquote>
<details>
<summary>Code Review</summary>

  ```plaintext
Perform a merciless technical review of the Clanker codebase. Be direct and critical. Focus on:

- Overall structure and coherence
- Complexity vs. necessity
- Consistency of style and patterns
- Fragility, hidden assumptions, and sharp edges
- Signs of over-engineering or under-engineering
- Any obvious technical debt or maintenance hazards

Do not soften the feedback. Do not comment on documentation quality or user experience unless it directly affects the code’s integrity. Judge the code as it stands.

For now, simply return a short acknowledgement of these instructions. Then ask to be supplied either an url to the repository, or a zip file of its contents.
  ```

</details>

<details>
<summary>Usability Analysis</summary>

  ```plaintext
Evaluate the Clanker project strictly from the perspective of its intended user: a vibe-coding solo developer who wants structure without heavy process, and who values staying in control.

Assess:

- How clear and usable the core workflow appears
- Cognitive load and friction points
- Whether the tool feels like it would actually help in day-to-day LLM-assisted coding
- How well the interface and configuration model support rapid iteration
- Whether the design respects the user’s time and attention
- Any places where the tool might get in the way instead of helping

For now, simply return a short acknowledgement of these instructions. Then ask to be supplied either an url to the repository, or a zip file of its contents.
  ```

</details>

<details>
<summary>Project History Analysis</summary>

  ```plaintext
Analyze the Clanker project’s trajectory and momentum. 

Assess:

- Whether the project shows coherent direction or signs of thrashing
- How the scope and design decisions have developed over time
- Whether the progress documentation and history demonstrate real learning and forward motion
- Current maturity level and likely next risks
- Whether the project appears to be converging or still searching for its shape

Be analytical and grounded in the evidence present in the files and '.clanker/progress-documentation' directory.

For now, simply return a short acknowledgement of these instructions. Then ask to be supplied either an url to the repository, or a zip file of its contents.
  ```

</details>
</blockquote>
  
And then supply either of these:  
```plaintext
https://github.com/Iannen/Clanker-clanker
```
```plaintext
clanker-evalcopy.zip -> does not exist yet for reference
```

### Installation & Prerequisites

The Clanker install process:
1. Clone the repository
'''bash
git clone https://github.com/Iannen/Clanker-clanker.git
cd Clanker-clanker
'''
2. Install python
3. then install ruamel.yaml, a python add-on
4. Configure a shortcut, I use 'clank'
  - Linux: Symlink in /usr/local/bin
  - Windows: PowerShell profile alias or doskey shortcut
  - macOS: Standard zsh alias in ~/.zshrc or /usr/local/bin symlink
5. then enter the repository directory
  - input your shortcut
  - et voila

For instructions beyond this - consult a Clanker ;)

### Parting words of wisdom and other disclaimers 

- perhaps something will come to me
- perhaps look at clankerized projects of iannen repo cta?