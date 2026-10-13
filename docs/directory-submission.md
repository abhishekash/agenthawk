# Directory submission handoff

Status checked 2026-10-13. The server is public and installable from its `v0.3.0` Git tag. The [official MCP Registry namespace](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fmcp-trace-inspector/versions) is active at `0.2.2`, backed by the earlier PyPI distribution. The `0.3.0` [`server.json`](../server.json) passes `mcp-publisher validate`.

## Publish the renamed PyPI distribution and update the MCP Registry

The `v0.3.0` release's [PyPI workflow](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38255591475) built successfully, then PyPI rejected its upload: `403 Invalid API Token: OIDC scoped token is not valid for project 'mcp-trace-inspector'`. The Registry job was skipped because it depends on that upload.

In the PyPI account that owns the project, add a **pending Trusted Publisher** with these exact fields:

| Field | Value |
|---|---|
| Project name | `mcp-trace-inspector` |
| GitHub owner | `abhishekash` |
| GitHub repository | `mcp-trace-inspector` |
| Workflow filename | `publish-mcp-trace-inspector.yml` |
| Environment | `pypi` |

Then dispatch [`publish-mcp-trace-inspector.yml`](../.github/workflows/publish-mcp-trace-inspector.yml). It checks out `v0.3.0`, uploads the renamed distribution, and publishes the `0.3.0` Registry metadata after upload succeeds. Verify both the [PyPI project](https://pypi.org/project/mcp-trace-inspector/) and [Registry namespace](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fmcp-trace-inspector/versions) afterward. [PyPI's pending publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) explains the account setup.

## Submit to `awesome-mcp-servers`

The [contribution guide](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md) requires a fork, a single README entry, and a PR. Put this line in the alphabetical part of the `Monitoring` section, between `adanb13/cirdan` and `agentkitai/agentlens`:

```markdown
- [abhishekash/mcp-trace-inspector](https://github.com/abhishekash/mcp-trace-inspector) 🐍 🏠 🍎 🪟 🐧 - Read-only MCP queries for local JSONL OpenTelemetry agent traces: failures, approvals, token usage, tool health, and run comparisons.
```

Suggested PR title: `Add abhishekash/mcp-trace-inspector`.

The current README has no entry for this repo. The connected GitHub integration cannot create a fork in this third-party repository, and the local `gh` session is unauthenticated, so this PR has not been submitted. Check whether Glama has indexed the server before adding a Glama badge; do not attach a badge that points to an unverified listing.
