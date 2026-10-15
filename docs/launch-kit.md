# SpanHound launch kit

SpanHound is an MIT-licensed local trace capture tool and read-only stdio MCP
server for **agent traces**. It can auto-instrument supported Python libraries,
receive OTLP/HTTP traces, or read saved JSONL and OTLP JSON files. It answers
questions about recorded tool errors, approvals, token usage, and run changes.

## One-line demonstration

```bash
uvx spanhound demo
```

This uses a bundled **scripted regression trace**. It shows a blocked
`run_shell` call, the returned workspace-boundary error, and an automated
approval event. No clone, account, trace backend, or MCP client is needed.

- Project: https://github.com/abhishekash/spanhound
- 48-second captioned video: https://github.com/abhishekash/spanhound/blob/main/docs/media/shell-root-escape-demo.mp4
- Reproducible story: https://github.com/abhishekash/spanhound/blob/main/docs/shell-boundary-story.md
- Package: https://pypi.org/project/spanhound/

## Where to share

| Priority | Place | Why and format | Submission |
|---|---|---|---|
| 1 | [r/mcp](https://www.reddit.com/r/mcp/) | The exact MCP audience. Use a short project post with a specific trace question. A [community discussion](https://www.reddit.com/r/mcp/comments/1up2woj/how_do_you_promote_an_mcp_server/) asks builders to show one problem and keep the pitch brief. | [Create a post](https://www.reddit.com/r/mcp/submit/) |
| 2 | [Show HN](https://news.ycombinator.com/showhn.html) | A runnable, nontrivial open-source tool with a no-signup demo fits the official Show HN guidelines. Link the repo; explain the scripted fixture in the first comment. | [Submit](https://news.ycombinator.com/submit) |
| 3 | [DEV #showdev](https://dev.to/t/showdev) | The tag explicitly welcomes project launches that are community-driven and not salesy. Tell the failure story with command output and the video. | [Create post](https://dev.to/new) |
| 4 | [r/Observability](https://www.reddit.com/r/Observability/) | A [recent open-source OTel project post](https://www.reddit.com/r/Observability/comments/1wyokpd/splunk_just_launched_a_new_open_source_project_to/) shows audience overlap. Focus on the retained diagnostic and saved OTLP JSON, with exact format limits. | [Create a post](https://www.reddit.com/r/Observability/submit/) |
| 5 | [r/SideProject](https://www.reddit.com/r/SideProject/) | A broader feedback audience. Use the maker story and ask whether the demo is understandable without MCP background. | [Create a post](https://www.reddit.com/r/SideProject/submit/) |
| Later | [Product Hunt](https://help.producthunt.com/en/articles/17350772-launch-guide) | The video and GIF are ready. Its own guide advises building a maker presence and launch page before selecting a day, so use it after initial technical feedback. | [Launch guide](https://help.producthunt.com/en/articles/17350772-launch-guide) |

Check each subreddit's live sidebar, flair, and account requirements immediately
before posting. r/LocalLLaMA is a poor launch target unless the post demonstrates
a local-model-specific workflow and the account meets its participation rules.
Avoid repeating the same post across communities or dropping the repo into
unrelated issues and discussions.

## Ready-to-adapt copy

### r/mcp

**Title:** I built SpanHound to inspect the error an agent tool actually returned

**Text:** A regression agent tried `cat ../outside.txt`. The tool blocked it,
but the trace initially recorded only the call, not the returned error. I fixed
the trace and built SpanHound, a local read-only MCP server that can query saved
JSONL spans and OTLP JSON exports for failures and approval decisions. It can
also capture supported Python agents with `spanhound run` or receive OTLP/HTTP.

You can see the bundled scripted case with `uvx spanhound demo` (no MCP client
needed), then capture a Python agent with `spanhound run` or send OTLP/HTTP
traces to `spanhound collect`. The 48-second video
and formats are in the repo: https://github.com/abhishekash/spanhound

If you debug MCP tool failures, which piece of evidence do your traces most
often fail to keep?

### Show HN

**Title:** Show HN: SpanHound – inspect recorded agent failures through MCP

**URL:** https://github.com/abhishekash/spanhound

**First comment:** I built this after a regression agent tried to read outside
its workspace. The tool blocked the call, but our old trace only said the call
happened. I added the returned diagnostic and approval event to the trace, then
made a read-only MCP server to query that evidence from local JSONL spans or
OTLP JSON exports. `spanhound run` can auto-capture supported Python library
calls; `uvx spanhound collect` can receive OTLP/HTTP traces from another runtime.
`uvx spanhound demo` shows the bundled scripted trace
without setup; the README has the 48-second video and exact format requirements.
It stores local OTLP/HTTP requests as files. I would value
feedback on which failure or approval questions are hard to answer from your
current agent traces.

### DEV #showdev

**Title:** I built SpanHound after an agent trace lost the error that mattered

**Tags:** `showdev`, `mcp`, `opensource`, `python`

An agent in my scripted regression attempted `cat ../outside.txt`. The tool
correctly rejected the path, but the trace initially said only that `run_shell`
was called. That was too little evidence to explain the result later.

I fixed the harness trace and built SpanHound to inspect saved local trace
files through read-only MCP tools. It reads the supported JSONL span format and
saved OTLP JSON exports, captures supported Python libraries, and receives local
OTLP/HTTP traces. A client can ask for failed calls, recorded approvals, token
use, or differences between runs.

Try the exact case with `uvx spanhound demo`. It prints the blocked call, the
returned error, and the automated approval from a bundled scripted trace. The
[repo](https://github.com/abhishekash/spanhound) has a 48-second video,
supported formats, and setup for your own files. The demo proves the trace
plumbing, not how a live model behaves. What would you need in the output to
trust an agent's explanation of a failed tool call?

### r/Observability

**Title:** A local OTLP receiver for AI-agent traces that keeps the returned tool error

**Text:** I was testing an agent workspace-boundary case: `run_shell` blocked
`cat ../outside.txt`, but the original trace recorded the call without its
returned diagnostic. I fixed that and made SpanHound to query existing local
agent traces through MCP. It reads supported JSONL spans and OTLP JSON exports,
and receives OTLP/HTTP traces locally from an instrumented agent.

The scripted case runs with `uvx spanhound demo`, and the repo includes the
48-second walkthrough: https://github.com/abhishekash/spanhound

For people instrumenting agents: do you preserve tool result text and approval
decisions on the same span, or correlate them some other way?

### r/SideProject

**Title:** I made a one-command demo for an agent debugging tool; is the failure clear?

**Text:** I built SpanHound after an agent test exposed a missing detail in my
trace: the tool blocked a path outside the workspace, but the trace had lost
the returned error. The project now reads saved agent traces through MCP, and
`uvx spanhound demo` shows the exact failure from a bundled scripted case.

There is a 48-second video in the README:
https://github.com/abhishekash/spanhound

I am trying to make the first minute understandable to someone who has not
used MCP. Does the demo explain why keeping the actual tool result matters?

## Existing distribution

For a live dashboard alongside file-based MCP investigation, link to
[Agent Observatory](https://github.com/abhishekash/agent-observatory), now public.
These tools have different inputs: Observatory reads supported local session
records and received telemetry; SpanHound queries JSONL and OTLP JSON trace files.

- Published on [PyPI](https://pypi.org/project/spanhound/) and the
  [official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fspanhound/versions).
- [awesome-mcp-servers PR #16323](https://github.com/punkpeye/awesome-mcp-servers/pull/16323)
  is open for maintainer review. Do not create duplicate PRs.
- [Glama](https://glama.ai/mcp/servers) submission is pending under the former
  project name; verify its displayed name when it is indexed.

After a post goes live, answer questions in that thread and record concrete
confusions or unsupported formats as issues. Use that feedback to improve the
README, demo, or parser before posting another channel-specific example.
