# tenant-research-skill

Source-of-truth repo for the **tenant-research** Claude skill — deep-dive CRE
tenant risk analysis that produces a polished PDF presentation.

This is the same skill that powers [TenantIQ](https://github.com/jonathansorenson/TenantIQ)
and that runs locally as `anthropic-skills:tenant-research` in Claude Code.

## Layout

```
tenant-research-skill/
├── tenant-research/            # the skill itself — this is what gets zipped
│   ├── SKILL.md                # system prompt + instructions
│   └── scripts/
│       ├── charts.py           # ReportLab chart builders for the PDF
│       └── logos.py            # logo fetching/rendering helpers
├── build.py                    # zips tenant-research/ into tenant-research.skill
├── install.py                  # copies tenant-research/ into the Claude install
└── README.md
```

## Edit workflow

1. **Edit** files under `tenant-research/` (`SKILL.md`, `scripts/charts.py`, etc.).
2. **Install locally** so the running Claude session picks up the change:
   ```sh
   python install.py
   ```
   No restart needed — the next time the skill triggers, it loads the new copy.
3. **Test** by triggering the skill in Claude and reviewing the PDF output.
4. **Commit** the change to this repo with a clear message describing what
   changed and why.
5. **Rebuild the distributable zip** (so the `.skill` artifact stays current):
   ```sh
   python build.py
   ```
   This produces `tenant-research.skill` in the repo root.

## Build

```sh
python build.py
# → ./tenant-research.skill (zip with tenant-research/SKILL.md + scripts/)
```

Pass `--output PATH` to write the zip elsewhere.

## Install

```sh
python install.py            # auto-detects %APPDATA%\Claude\...\skills\tenant-research
python install.py --dry-run  # show what would be copied
python install.py --install-dir /custom/path  # override target
```

The auto-detect is Windows-only. On macOS/Linux pass `--install-dir` explicitly
to your Claude skills-plugin folder.

## What the skill does

Triggered when a user mentions tenant research, tenant underwriting, prospective
tenant analysis, or any variation of "look into [company name] for that space".

Produces an institutional-quality PDF covering:

- **6 scoring dimensions** — Financial Strength, Leadership & Personnel, Market
  Position, Legal & Regulatory, CRE Track Record, Industry Outlook
- **7 research domains** (A–G) — full coverage of financials, market, leadership,
  legal, CRE signals, industry outlook, ESG/reputation
- **Site-specific analysis** when a property address is provided

See [`tenant-research/SKILL.md`](tenant-research/SKILL.md) for the full prompt
and rendering rules.
