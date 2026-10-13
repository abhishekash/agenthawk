# Listing and rename status

SpanHound is the new name for mcp-trace-inspector. The old `0.3.x` PyPI package
and MCP Registry listing remain available for existing users. The new distribution
and server namespace are `spanhound` and `io.github.abhishekash/spanhound`.

## Release

The release workflow publishes a tagged build to PyPI using a Trusted Publisher,
then publishes the matching `server.json` to the official MCP Registry. For the
new package, PyPI needs a pending publisher with:

| Field | Value |
|---|---|
| GitHub owner | `abhishekash` |
| GitHub repository | `spanhound` |
| Workflow filename | `publish-spanhound.yml` |
| Environment | `pypi` |

`v0.4.0` reached [PyPI](https://pypi.org/project/spanhound/) but its Registry
publish was rejected because the description exceeded the Registry's 100-character
limit. `v0.4.1` shortens the description and validates `server.json` before upload.
After release, check the [PyPI project](https://pypi.org/project/spanhound/)
and [Registry entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fspanhound/versions).

## Directories

- The [awesome-mcp-servers PR](https://github.com/punkpeye/awesome-mcp-servers/pull/16323)
  was submitted under the former name. Update its entry to `abhishekash/spanhound`
  and mention local OTLP JSON exports before requesting review.
- The [Glama submission](https://glama.ai/mcp/servers) is pending review under the
  former name. Ask Glama to update its name and repository URL after the GitHub
  rename, or submit the new listing if their review process requires it.

Use the new name in outreach. The archived package and GitHub redirect are for
existing links and installs.
