# Clanker

Clanker is an AI-driven, terminal-based repository development utility by morning, and a basic prompt assembler by night.

The idea is to elevate the familiar browser-based copy/paste vibe coding experience.

---

### I: Why

For the hell of it. We all love tooling here, right?

---

### II: Highlights

- **YAML-Driven Prompt Configuration**: Let the LLM write your prompt definitions and supporting assets.
- **Self-Refining Loop**: Use Clanker on Clanker itself to refactor, debloat, and evolve the tool as you see fit.
- **Keyboard-Driven Flow**: Quickly switch active task domains and package repo context directly to your clipboard in a single keystroke.

---

### III: Installation

`cd` into a directory of your choice, and then:

#### Option A: Clone the repo (Recommended)
Step right into my shoes with the current set of supporting markdown assets and my DIY project documentation.

```bash
git clone [https://github.com/Iannen/Clanker-clanker.git](https://github.com/Iannen/Clanker-clanker.git)
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
# Press '1', then 'q'.
# Your prompt is now on your clipboard. Paste it into your browser LLM and ask: "What in the world is this?"
```