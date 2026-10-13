# Directory submission handoff

Status checked 2026-10-13. The server is public and installable from its `v0.3.0` Git tag. The [official MCP Registry namespace](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fmcp-trace-inspector/versions) is active at `0.2.2`, backed by the earlier PyPI distribution. The `0.3.0` [`server.json`](../server.json) passes `mcp-publisher validate`.

## Publish the renamed PyPI distribution and update the MCP Registry

The `v0.3.0` release's [PyPI workflow](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38255591475) built successfully, then PyPI rejected its upload: `403 Invalid API Token: OIDC scoped token is not valid for project 'mcp-trace-inspector'`. A [retry](https://github.com/abhishekash/mcp-trace-inspector/actions/runs/38402523257) failed the same way. The Registry job was skipped because it depends on that upload.

The PyPI account already has an empty `mcp-trace-inspector` project. Its `publish-pypi.yml` publisher overlaps with a publisher for `agenthawk` that uses the same GitHub repository and workflow. Add a distinct **project Trusted Publisher** to `mcp-trace-inspector` with these fields:

| Field | Value |
|---|---|
| GitHub owner | `abhishekash` |
| GitHub repository | `mcp-trace-inspector` |
| Workflow filename | `publish-mcp-trace-inspector.yml` |
| Environment | `pypi` |

Then dispatch [`publish-mcp-trace-inspector.yml`](../.github/workflows/publish-mcp-trace-inspector.yml) with `tag=v0.3.0`. It checks out that tag, uploads the distribution, and publishes its Registry metadata after upload succeeds. Future releases use this workflow automatically. Verify both the [PyPI project](https://pypi.org/project/mcp-trace-inspector/) and [Registry namespace](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fmcp-trace-inspector/versions) afterward.

## `awesome-mcp-servers` submission

The [directory PR](https://github.com/punkpeye/awesome-mcp-servers/pull/16323) is open. It adds one entry in the `Monitoring` section, between `A1-x-Tech/mcp-google-crux` and `adanb13/cirdan`:

```markdown
- [abhishekash/mcp-trace-inspector](https://github.com/abhishekash/mcp-trace-inspector) 🐍 🏠 🍎 🪟 🐧 - Query local JSONL OpenTelemetry agent traces through MCP for failures, approvals, token usage, tool health and run comparisons.
```

The directory's `check-submission` job passed on 2026-10-13. A Glama badge was omitted because its listing has not been verified. The maintainers still need to review and merge the PR.
