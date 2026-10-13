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

## `awesome-mcp-servers` submission

The [directory PR](https://github.com/punkpeye/awesome-mcp-servers/pull/16323) is open. It adds one entry in the `Monitoring` section, between `A1-x-Tech/mcp-google-crux` and `adanb13/cirdan`:

```markdown
- [abhishekash/mcp-trace-inspector](https://github.com/abhishekash/mcp-trace-inspector) 🐍 🏠 🍎 🪟 🐧 - Read-only MCP queries for local JSONL OpenTelemetry agent traces: failures, approvals, token usage, tool health, and run comparisons.
```

The directory's `check-submission` job passed on 2026-10-13. A Glama badge was omitted because its listing has not been verified. The maintainers still need to review and merge the PR.
