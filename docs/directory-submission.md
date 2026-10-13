# Listing and rename status

SpanHound is the new name for mcp-trace-inspector. The old `0.3.x` PyPI package
and MCP Registry listing remain available for existing users. The new distribution
and server namespace are `spanhound` and `io.github.abhishekash/spanhound`.

## Release

The release workflow publishes a tagged build to PyPI using a Trusted Publisher,
then publishes the matching `server.json` to the official MCP Registry. PyPI's
publisher for `spanhound` is active with:

| Field | Value |
|---|---|
| GitHub owner | `abhishekash` |
| GitHub repository | `spanhound` |
| Workflow filename | `publish-spanhound.yml` |
| Environment | `pypi` |

`v0.4.0` reached PyPI but its Registry
publish was rejected because the description exceeded the Registry's 100-character
limit. `v0.4.1` fixed that. `v0.4.2` is live on
[PyPI](https://pypi.org/project/spanhound/0.4.2/) and the
[MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fspanhound/versions).
It adds `spanhound demo` and a validated
[MCP Bundle](https://github.com/abhishekash/spanhound/releases/download/v0.4.2/spanhound-v0.4.2.mcpb)
for desktop clients. The public PyPI wheel and extracted bundle were both
smoke-tested against the recorded regression trace.
The workflow now validates Registry metadata before uploading to PyPI.

## Directories

- The [awesome-mcp-servers PR](https://github.com/punkpeye/awesome-mcp-servers/pull/16323)
  now lists `abhishekash/spanhound` and OTLP JSON support. Its automated check
  passed; maintainer review remains pending.
- The [Glama submission](https://glama.ai/mcp/servers) is pending review under the
  former name. Its submitted GitHub URL redirects to SpanHound. The listing's
  displayed name needs an update once Glama has reviewed it.

Use the new name in outreach. The prior package and GitHub redirect are for
existing links and installs.
