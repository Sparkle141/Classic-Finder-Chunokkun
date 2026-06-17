# Release Workflow

Use this workflow when maintaining this repository, preparing a GitHub push, or publishing a release.

## Version Naming

Use semantic version tags:

- `v0.1.0` for the first public usable release
- `v0.1.1` for README, typo, documentation, or small compatibility fixes
- `v0.2.0` for meaningful workflow, script, output, or source-policy improvements
- `v1.0.0` only after the agent instructions, scripts, and output formats are stable

Release titles may be Korean and user-facing. Prefer titles that explain the capability, for example:

```text
한국어 문장에서 원전 후보를 찾는 첫 공개판
```

## Change Management

Before committing or pushing:

1. Inspect the current worktree.
2. Identify exactly which files belong to the requested change.
3. Do not stage unrelated local changes.
4. Run the most relevant checks available.
5. Summarize what changed and what passed.
6. Ask for or confirm user approval before pushing when the user has not already requested a push.

For this repository, the minimum local smoke check is:

```bash
python scripts/smoke_test_reverse_trace.py
```

If a change touches JSON fixtures or configuration, also validate JSON files before release.

## Push Procedure

When the user approves a push:

1. Stage only the intended files.
2. Commit with a short, descriptive message.
3. Fetch the remote before pushing.
4. If the remote has new commits, rebase or merge without discarding user work.
5. Resolve conflicts by preserving remote user changes unless explicitly instructed otherwise.
6. Rerun the relevant checks after conflict resolution.
7. Push to the requested branch.

## Release Procedure

Create a release only after:

1. The intended changes are committed.
2. The branch is pushed to GitHub.
3. The worktree is clean.
4. Relevant checks have passed.
5. The user has explicitly asked for or approved release publication.

Recommended first release:

```text
Tag: v0.1.0
Title: 한국어 문장에서 원전 후보를 찾는 첫 공개판
```

Suggested release notes:

```markdown
첫 공개 버전입니다.

주요 기능:
- 한국어 문장 기반 역추적 워크플로
- 다국어 검색어 확장
- 원전, 번역본, 주석, 2차 문헌 후보 분류
- 공개 자료원 검색 보조
- 권리 상태 확인 흐름
- 인용 생성
- 한국어 번역 작업지 생성

검증:
- reverse trace smoke test 통과
```

Use an annotated tag when possible:

```bash
git tag -a v0.1.0 -m "한국어 문장에서 원전 후보를 찾는 첫 공개판"
git push origin v0.1.0
```

If a GitHub Release object cannot be created from the available tools, push the tag and tell the user exactly what remains to do in the GitHub UI.
