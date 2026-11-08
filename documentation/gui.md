# GUI

A local web page to look at what the generator produces and to run it:

```bash
# in the project folder (see overview.md)
dforge gui [--port 8765] [--no-browser]
```

It needs nothing beyond the project's requirements, and opens in your
browser. Press Ctrl+C in the terminal to quit; a generation run still in
progress is stopped.

| view | shows |
|---|---|
| Conversation | one rendered conversation of the selected template, with tool calls and results, whether the validators accept it, which phrase of each pool was drawn, and the template's tags. "Render another" (or `R`) draws again. |
| Tools | the tool schemas of the domain or variant, exactly as the model gets them, as a table and as JSON, plus what a translated variant still has to translate. |
| Generate | what a selection of domains and variants would produce and where it goes; runs the [orchestrator](workflow.md) with progress and log. |

Phrases and templates are read from disk on every render, so edits show up
with the next "Render another". After changing tool schemas or `domain.yaml`,
reload the page; Python code needs a restart of the GUI.

A rendered draw the validators reject is drawn again, as during generation.
If none passes, the last one is shown with its errors.

## Generating

A run is the orchestrator with the selected `--domain` arguments, so it writes
to `Synthetic_Data/` and to the merge folder shown on the page (see
[domains](domains.md#generating-and-merging-several-domains)).

- A run that would replace an existing merged dataset needs a confirmation,
  and the server refuses it otherwise. The page says so more loudly for a
  dataset listed in `approved_datasets`.
- The GUI never publishes. See [publishing](publishing.md).
- Stopping a run keeps the conversations written so far in `Synthetic_Data/`;
  merging does not happen.

## Security

The server listens on `127.0.0.1` only. Because it can start a run, it also
rejects requests with another `Host` or `Origin`, so a website open in the same
browser cannot reach it. Domains and templates in a request must be ones the
generator lists, since they end up in file paths.
