# Commit

Stage all changes, create a meaningful SSH-signed commit, and push to the remote.

## Optional message

If the user typed text after `/commit`, treat it as the commit message hint or full message. Otherwise, draft one from the staged diff.

## Steps

1. Inspect the repo state in parallel via the Shell tool:
   - `git status`
   - `git diff` and `git diff --cached`
   - `git log -5 --oneline` (match this repo's commit style)

2. If the worktree and index are clean:
   - If the branch is ahead of its remote, skip to step 8 (push only)
   - Otherwise stop and say there is nothing to commit or push

3. Stage everything:

```bash
git add --all
```

4. Draft a concise conventional commit message (1 line, optional short body):
   - Prefer `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `style:`
   - **Entire message must be lowercase** (type and subject), e.g. `feat: update api docs`
   - Focus on why, not a file list
   - Follow recent `git log` style
   - If the user provided a message after `/commit`, lowercase it before use (unless they explicitly ask to preserve casing)
   - If they provided a short hint, expand it into a proper conventional lowercase message
   - Never commit secrets (`.env`, credentials, private keys). Warn and unstage those files if present.

5. Commit with SSH signing using `~/.ssh/vid_ed25519` (do not change global git config). Use a HEREDOC for the message:

```bash
git -c gpg.format=ssh \
  -c user.signingkey="$HOME/.ssh/vid_ed25519" \
  -c commit.gpgsign=true \
  commit -S -m "$(cat <<'EOF'
COMMIT_MESSAGE_HERE

EOF
)"
```

Request `all` permissions for the Shell tool so the SSH key is readable outside the sandbox.

6. If the commit fails (hooks, signing, etc.), fix the issue and create a **new** commit. Do not amend unless the user explicitly asks and amend rules allow it.

7. Confirm the new commit with `git status` / `git log -1 --oneline`.

8. Push the current branch to `origin` with the same SSH key:

```bash
GIT_SSH_COMMAND='ssh -i "$HOME/.ssh/vid_ed25519" -o IdentitiesOnly=yes' \
  git push -u origin HEAD
```

Use `all` permissions for push (SSH key + network). If Auto-review blocks the push, retry with `request_smart_mode_approval` so the user can approve.

9. Report the commit hash/subject and push result (remote URL / branch up to date).

## Examples

- `/commit` → analyze diff, `git add --all`, sign-commit, push
- `/commit feat: update api docs` → use that exact message (already lowercase), then push
- `/commit Intro Copy` → draft/lowercase to `docs: expand introduction and why actx0`, then push

## Notes

- Always push after a successful commit (or when already ahead with a clean tree).
- Commit subjects are always lowercase (see `.cursor/rules/commit-lowercase.mdc`).
- Do not update git config.
- Do not skip hooks (`--no-verify`) unless the user explicitly asks.
- Do not force-push unless the user explicitly asks.
- Signing and push key is always `~/.ssh/vid_ed25519` for this command.
