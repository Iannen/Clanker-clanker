# Clanker

Clanker is a lightweight, terminal-based repository development utility designed to elevate the browser-based copy/paste vibe coding experience in a vendor-agnostic manner.

---

### Why

For the hell of it. We all love tooling here, right?

---

### Highlights

- **Self-Refining Loop**: You can use Clanker on Clanker itself to refactor, debloat, and evolve the tool as you see fit. 
- **Not just for code!**: The intent is that the user can organize and work on non-coding projects too. Food recipies, 
- **Keyboard-Driven Flow**: Quickly switch active task domains and package repo context directly to your clipboard in a single keystroke.
---

### Installation (linux only)

```bash
# Clone the repository
git clone [https://github.com/your-username/clanker.git](https://github.com/your-username/clanker.git)
cd clanker

# Make executable or alias to your PATH
chmod +x clanker.py
ln -s "$(pwd)/clanker.py" /usr/local/bin/clanker
```

---

### Usage

1. Run `clanker` in any repository root.
2. Select an active working domain using the number keys (`1`–`0`).
3. Tap a prompt key (`q`, `w`, `e`, `r`) to compile the relevant repository state, task backlogs, and instructions directly into your clipboard.
4. Paste into your browser-based AI model of choice.