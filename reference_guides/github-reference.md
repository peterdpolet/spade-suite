# GitHub Reference

> A curated, tiered reference for working developers. Not a
> comprehensive manual — a guide to what you actually need to know,
> when you need it. Updated 17 Jul 2026 — substantially revised from
> the June version to fold in real incidents since, not just new
> commands.

---

## The three tiers

- **Must Know** — you will use these every single day. Not knowing
  them stops you dead.
- **Should Know** — you'll need these within the first week of a real
  project. Life is painful without them.
- **Good to Know** — diagnostics, edge cases, and recovery. You'll
  reach for these when something goes wrong.

---

## Must Know

### `git init`
Initialise a new local repository.

### `git clone <url>`
Copy a remote repository to your local machine.

### `git add <file>` / `git add .`
Stage changes. Prefer naming specific files over `.` when you've been
doing anything else in the working directory (debugging, stray test
files) — `.` sweeps up everything indiscriminately, including things
you didn't mean to commit.

### `git commit -m "message"`
Commit staged changes. `-m` supplies the message inline rather than
opening an editor. Keep messages specific — you'll be scanning `git
log` for exactly this text months later.

### `git push` / `git pull`
Send/receive commits to/from the remote. See **the single most
important gotcha in this whole document**, below.

### `git status`
Shows the current branch, staged/unstaged changes, and untracked
files. **Read the branch name on the first line every single time** —
see the Good to Know section for why this one habit would have saved
a genuinely expensive mistake.

### `git log --oneline`
Compact commit history. `-3` limits to the last 3 commits — useful for
a quick "did that just work" check after a push or pull.

### `.gitignore`
Excludes files from version control (`.env`, `__pycache__/`,
`node_modules/`, build artifacts). Set this up before your first
commit, not after you've already committed something you shouldn't
have.

---

## Should Know

### `git diff --cached`
Shows exactly what's staged, before you commit it. Cheap insurance —
run this before every commit that touches more than a file or two, so
you're not trusting your memory of what you changed.

### `git branch --show-current`
Prints just the current branch name, nothing else — the cleanest way
to check before running any deploy command. See the incident below for
why this specific command earns a permanent place in any deploy
checklist.

### `git checkout -b <branch>`
Create and switch to a new branch in one step.

### `git remote -v`
Shows what remote(s) a repo is configured against, and whether it's
SSH or HTTPS. Worth checking if push/pull behaves unexpectedly after
cloning a repo a different way than usual.

### `git stash`
Temporarily shelve uncommitted changes without committing them —
useful when you need a clean working directory to switch branches
without losing work in progress.

### `git tag`
Mark specific commits (releases, deploy points) with a human-readable
label rather than a hash.

---

## Good to Know

### The wrong-branch trap — the most expensive mistake documented
this cycle

`git pull` printing `Already up to date.` is **not proof you're where
you think you are** — it's only proof the currently checked-out branch
matches its own remote. A production server sat on a feature branch
(`inventory-restructure`) for an extended period, silently missing
every commit made to `main`, including several real deploys' worth of
work — and `git pull` never once complained, because from that
branch's own point of view, it genuinely was up to date.

**The fix that would have caught this instantly:** read the branch
name on the very first line of `git status`, every time, before
running any deploy step. Don't just check that a pull or push
"succeeded" — check *what* it succeeded on.

```bash
git branch --show-current    # must say what you expect, every time
git log --oneline -3         # confirm the commit hash matches what you pushed
```

If a server is ever found on the wrong branch:
```bash
git status              # confirm no uncommitted local changes first
git fetch origin
git checkout main
git pull origin main
```
If `main` already contains the feature branch's history (merged via
`--no-ff` at some point), this is a clean fast-forward — no risk of
losing anything.

### `git reflog`
A log of *every* place `HEAD` has pointed, including commits that are
no longer on any branch. The recovery tool of last resort after a bad
`reset --hard` or a branch you thought you deleted for good.

### `git reset --soft` vs `--mixed` vs `--hard`
- `--soft` — moves the branch pointer, keeps changes staged
- `--mixed` (default) — moves the pointer, unstages changes, keeps them
  in the working directory
- `--hard` — moves the pointer and **discards changes entirely**. The
  one that can genuinely lose work — never run this without being sure.

### `git revert` vs `git reset`
`revert` creates a new commit that undoes a previous one — safe for
anything already pushed/shared. `reset` rewrites history — fine
locally, dangerous on a shared branch others have already pulled.

### `git bisect`
Binary-searches commit history to find exactly which commit introduced
a bug — genuinely useful once a regression is confirmed but the guilty
commit isn't obvious.

### SSH vs HTTPS remotes
SSH (`git@github.com:...`) uses key-based auth, no password prompt once
configured. HTTPS prompts for credentials (or a token) each time unless
a credential helper is set up. Mixing the two across machines cloning
the same repo is a common source of "why does this one ask for a
password and the other doesn't" confusion.

### Confirm which machine you're actually on
When a laptop and a server are both Ubuntu and both have the project
checked out at a similar path, the terminal can look identical. Before
running anything destructive or deploy-related, `hostname` and `pwd`
are a two-second sanity check worth making habitual, not just for
emergencies.
