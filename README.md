# Clanker

Clanker is an AI-driven, terminal-based repository development utility by morning, and a basic prompt assembler by night.

The idea is to elevate the familiar browser-based copy/paste vibe coding experience.

---

### I: Why

For the hell of it. We all love tooling here, right?

---

### II: Highlights

- **YAML-Driven Prompt Configuration**: 
    - Let the LLM write your YAML - configuring domains of interest with prompts to suit your workflows
- **Self-Refining Loop**: 
    - Use Clanker on itself to refactor, debloat, and evolve the tool as you see fit.
- **Keyboard-Driven Flow**: 
    1. Numkeys 1-0 -> select a domain
    2. QWER -> fetch a prompt to the clipboard
    3. Paste & go

---

### III: Installation

`cd` into a directory of your choice, and then:

#### Option A: Clone the repo (Recommended)
Step right into my shoes with the current set of supporting markdown assets and my DIY project documentation.

```bash
git clone https://github.com/Iannen/Clanker-clanker.git
cd Clanker-clanker
```

#### Option B: Script only
Download or paste clanker.py directly as a standalone script.
```bash
nano clanker.py
# Paste full script contents, save & exit:
# Ctrl+Shift+V -> Ctrl+X -> Y -> Enter
```

#### Make it executable & symlink to your PATH
```bash
chmod +x clanker.py
sudo ln -s "$(pwd)/clanker.py" /usr/local/bin/clank
```

### IV: Hello World!

Run the app, grab a prompt, and feed it to your model:

```bash
clank
# Press '4', then 'q'.
```
A prompt is now on your clipboard. Give this to some LLM and ask it what in the world this is.

### IV: Project status:

**31.08.26**
It's quite functional, so I will leave it be for now.
If I think of something clever, I'll just put it in the NS document.
... well I will probably wind up aligning doc extensions in this and other projects, cleaning up the configs and such.