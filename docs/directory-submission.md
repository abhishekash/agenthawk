# Directory submission handoff

Status checked 2026-10-13. The first renamed release, `0.3.0`, is live on [PyPI](https://pypi.org/project/mcp-trace-inspector/) and in the [official MCP Registry namespace](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fmcp-trace-inspector/versions). Its [publishing run](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38406794634) passed both upload jobs.

## Publishing handoff

The `v0.3.0` release's [PyPI workflow](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38255591475) built successfully, then PyPI rejected its upload: `403 Invalid API Token: OIDC scoped token is not valid for project 'mcp-trace-inspector'`. A [retry](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38402523257) failed the same way. The Registry job was skipped because it depends on that upload.

The former `publish-pypi.yml` publisher overlapped with a publisher for `agenthawk` that used the same GitHub repository and workflow. A distinct **project Trusted Publisher** was added to `mcp-trace-inspector` with these fields:

| Field | Value |
|---|---|
| GitHub owner | `abhishekash` |
| GitHub repository | `mcp-trace-inspector` |
| Workflow filename | `publish-mcp-trace-inspector.yml` |
| Environment | `pypi` |

The `v0.3.0` tag was published by manually dispatching [`publish-mcp-trace-inspector.yml`](../.github/workflows/publish-mcp-trace-inspector.yml). Future GitHub releases trigger the same workflow automatically. Verify both the PyPI project and Registry namespace after each release.

## `awesome-mcp-servers` submission

The [directory PR](https://github.com/punkpeye/awesome-mcp-servers/pull/16323) is open. It adds one entry in the `Monitoring` section, between `A1-x-Tech/mcp-google-crux` and `adanb13/cirdan`:

```markdown
- [abhishekash/mcp-trace-inspector](https://github.com/abhishekash/mcp-trace-inspector) 🐍 🏠 🍎 🪟 🐧 - Query local JSONL OpenTelemetry agent traces through MCP for failures, approvals, token usage, tool health and run comparisons.
```

The directory's `check-submission` job passed on 2026-10-13. A Glama badge was omitted because its listing has not been verified. The maintainers still need to review and merge the PR.
