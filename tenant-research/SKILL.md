---
name: tenant-research
description: >
  Deep-dive research and risk analysis on companies for CRE tenant evaluation. Produces a polished
  PDF presentation combining company-specific financials, credit signals, market positioning,
  competitive landscape, operational/legal review, and CRE-specific leasing signals — with a
  composite risk score. Use this skill whenever the user mentions tenant research, tenant
  underwriting, prospective tenant analysis, company due diligence for a lease, credit evaluation
  of a tenant, "research this company," "tell me about this tenant," or any variation of needing
  to understand a company's fitness as a commercial real estate tenant. Also trigger when the user
  wants a tenant comparison, a go/no-go on a lease prospect, or a deep dive on any company in the
  context of CRE leasing decisions. Even casual requests like "look into [company name] for that
  space" or "what do we know about [company]" in a CRE context should trigger this skill.
---

# Tenant Research & Risk Analysis

You are producing institutional-quality tenant research for Rising Tide, a CRE investment firm.
The output is a polished PDF presentation that an investment committee can use to evaluate whether
a company is a suitable tenant — or to understand the risk profile of an existing one.

## Why This Matters

Tenant quality is one of the strongest drivers of asset value in commercial real estate. A
thorough understanding of a tenant's financial health, market position, legal exposure, and
operational trajectory directly impacts underwriting, lease negotiation, and portfolio risk
management. This skill exists to make that research rigorous, consistent, and presentation-ready
every time — whether the tenant is a publicly traded national retailer or a privately held
regional operator.

## Non-Negotiable Requirements

Before diving in, understand what makes or breaks this report:

1. **All seven research sections must appear** (A through G). Skipping sections or collapsing
   them together defeats the purpose. A 7-page report that covers 4 topics is worse than a
   13-page report that covers all 7. Depth is the point.
2. **Six scoring dimensions, always.** Financial Strength, Leadership & Personnel, Market
   Position, Legal & Regulatory, CRE Track Record, Industry Outlook. Not four. Not five. Six.
3. **Use the bundled charts.py** — copy it from `scripts/charts.py` and call the actual
   functions (`build_score_dashboard`, `build_bar_chart`, `build_competitive_bars`, etc.).
   These return Drawing objects (actual rendered graphics), not colored tables. If the PDF
   contains only tables and no Drawing-based visuals, it does not meet the standard.
4. **Bullet points** — use `<br/>` tags between items in Paragraph objects, or use separate
   Paragraph objects per bullet. Never concatenate bullets into a single text run.
5. **Site-specific analysis when a location is provided.** If the user gives a property
   address, city, or intersection, Section E.1 (Site-Specific Location Analysis) is
   mandatory. Map all tenant locations and parent/acquirer locations within 25 miles.
   This is often the most actionable section of the report for acquisition decisions.
6. **Table cell wrapping** — Use Paragraph objects (not plain strings) for any table cell
   that may contain more than ~15 characters. Plain strings do not wrap and will overflow
   into adjacent columns, creating garbled text.
7. **Parallel sub-agent dispatch.** The main agent does NOT research domains itself. It
   dispatches **nine sub-agents in parallel** (single message, multiple Agent/Task tool calls):
   one per research domain (A.0, A, B, C, D, E, F, G) plus one to fetch the tenant logo.
   The main agent waits for all nine returns, then synthesizes (reconcile, re-calibrate
   scores, select logo, compile PDFs). Serial research by the main agent is a defect — it
   is both slower and worse-calibrated than parallel specialist dispatch.

## Workflow Overview

1. **Identify the company** — Confirm the company name, location, and any context the user provides
2. **Classify the company** — Public vs. private vs. non-profit/government (this shapes research strategy)
3. **Dispatch sub-agents in parallel** — Spawn nine sub-agents in a single message: eight research
   agents (A.0 Fundamentals, A Financial, B Market, C Leadership, D Legal, E CRE Signals,
   F Industry, G ESG) plus one logo agent. Each sub-agent has a narrow brief and its own
   web-research budget.
4. **Synthesize** — Once all nine have returned, validate cross-agent consistency (entity
   name matches across returns), re-calibrate proposed scores against the archetype table,
   select the logo (fetched image if available, else `build_cover_logos()` fallback).
5. **Score** — Apply the composite risk scoring framework (six dimensions, 100-point scale)
   using the reconciled per-dimension scores.
6. **Build the PDFs** — Generate BOTH the full report PDF AND the 1-page summary PDF using
   the bundled `charts.py` and `logos.py`.

## Step 1: Gather Context

Before researching, confirm or infer:
- Full legal entity name (and any DBAs or parent companies)
- Industry / sector
- Headquarters location
- The specific property or market context (if provided)
- Whether this is a prospective or existing tenant

If the user only gives a company name, that's fine — start researching and surface what you find.
Don't over-ask; use your judgment to fill gaps from public data.

Note: the structured identity data (legal entity name, entity type, state of incorporation,
state registration doc #, registered agent, officers, website, parent company) is captured
formally in subsection A.0 Company Fundamentals & Structure. Step 1 is the informal hand-shake
with the user; A.0 is where the data is pulled from state databases and rendered into the
report. Do not skip A.0 even if Step 1 produced the entity name.

## Step 2: Classify and Adapt Research Strategy

The depth and sources available vary dramatically by company type:

**Public companies** — SEC filings (10-K, 10-Q, 8-K), earnings transcripts, analyst coverage,
credit ratings, stock performance, institutional ownership. Rich data; focus on synthesizing
the narrative, not just reporting numbers.

**Private companies** — Much thinner public record. Lean on: news/press coverage, industry
reports, Glassdoor/employee signals, litigation records, UCC filings, estimated revenue from
industry databases, PE/VC backing if applicable, franchise disclosure documents if relevant.
Be transparent about confidence levels when data is inferred or estimated.

**Non-profit / Government** — Budget documents, grant funding, bond ratings, legislative
appropriations, mission stability. Different financial framework but still scoreable.

## Orchestration: Parallel Research Dispatch

The main agent running this skill MUST fan out research work to nine parallel sub-agents. The
main agent does not research any domain itself — its job is to dispatch, wait, synthesize,
and compile. This is the single biggest lever for speed and quality on a tenant report.

### Why parallel dispatch

- **Speed.** Nine sub-agents run concurrently in ~the time one serial research pass takes.
- **Specialization.** Each sub-agent has a narrow brief and can go deeper on its domain
  without diluting attention across unrelated areas.
- **Calibration isolation.** Scoring drift (e.g., a legal agent over-penalizing litigation)
  is caught in the synthesis pass and re-normalized against the cross-dimension archetype
  table. Serial research has no such checkpoint.
- **Logo quality.** A dedicated logo agent can exhaust the logo-fetch search paths
  (company press kit → Wikipedia → brand-asset aggregators) while research proceeds,
  instead of settling for the text fallback.

### How to dispatch

Dispatch **all nine sub-agents in a single message**, with multiple Agent/Task tool calls in
that message. Single-message multi-tool-call is what makes the dispatch truly parallel.
Issuing them one at a time serializes them.

Each sub-agent gets:
- The tenant name, HQ, property context, and any user-provided hints
- Its specific section brief (copy the relevant domain brief from Step 3 below)
- An instruction to return a structured envelope (see return contract below)
- A max-token / max-web-calls budget appropriate to its domain

### The nine sub-agents

| # | Name | Brief location | Scored? | Primary sources |
|---|------|----------------|---------|-----------------|
| 1 | **Fundamentals** (A.0) | Step 3 § A.0 | No (narrative) | State business-entity databases, 10-K cover page, company website |
| 2 | **Financial** (A) | Step 3 § A | Yes → Financial Strength & Credit | SEC filings, credit-rating agencies, news, annual reports |
| 3 | **Market** (B) | Step 3 § B | Yes → Market Position | Industry reports, competitive analyses, market-share data |
| 4 | **Leadership** (C) | Step 3 § C | Yes → Leadership & Personnel | Executive bios, proxy statements, news, Glassdoor |
| 5 | **Legal** (D) | Step 3 § D | Yes → Legal & Regulatory | PACER, state court dockets, SEC litigation releases, regulatory actions |
| 6 | **CRE Signals** (E) | Step 3 § E (incl. E.1) | Yes → CRE Track Record | Lease filings, news on store closures/openings, anchor-tenant registries |
| 7 | **Industry** (F) | Step 3 § F | Yes → Industry Outlook | IBIS / industry reports, sector forecasts, trade press |
| 8 | **ESG** (G) | Step 3 § G | No (narrative) | ESG ratings (MSCI, Sustainalytics), news, corporate sustainability reports |
| 9 | **Logo** | (see below) | No | Company press kit, Wikipedia, logo aggregators |

### Research sub-agent return contract

Every research sub-agent (#1–8) must return a JSON-serializable envelope with these fields:

```python
{
    "section": "A",  # A.0, A, B, C, D, E, F, or G
    "findings": "...",  # Markdown-formatted prose for the report section, 300–1000 words
    "key_facts": [  # 3–10 bullet-ready facts with structured values where applicable
        {"label": "Revenue (TTM)", "value": "$37.2B", "source": "Q4 2025 10-K"},
        ...
    ],
    "draft_score": 92,  # 0-100, only for scored domains (A, B, C, D, E, F); else null
    "score_rationale": "...",  # 2-4 sentences: why this score, what would move it
    "confidence": "high",  # high / moderate / low — data sufficiency, not the score itself
    "sources": ["https://...", "https://..."],  # 3–15 URLs consulted
    "flags": ["..."]  # optional: issues for the synthesizer (e.g., "entity name mismatch with A.0")
}
```

### Logo sub-agent brief

The logo sub-agent has one job: find the highest-quality version of the tenant's brand logo
as an embeddable asset. Its brief:

> Find the official brand logo for **{tenant_name}**. Preference order:
> 1. Company press-kit page (usually /press, /media, /brand, /about/brand — look for downloadable
>    logo assets)
> 2. Wikipedia infobox logo (usually SVG)
> 3. Brand-asset aggregators (Brandfetch, Clearbit logo API, seeklogo.com) — only if official
>    sources fail
>
> Return the following envelope:

```python
{
    "logo_url": "https://...",  # Direct URL to the logo image (PNG or SVG preferred)
    "logo_format": "png",  # svg / png / jpg
    "downloaded_path": "/tmp/tenant_logo.png",  # If fetched locally during research
    "brand_color_hex": "#E51636",  # Primary brand color for fallback and badge tinting
    "fallback_used": false,  # True if no asset found and text logo is required
    "sources": ["https://..."],  # Where the logo was sourced from
    "notes": "..."  # Any quality issues (e.g., "only low-res PNG available")
}
```

If the logo sub-agent cannot find any asset, it returns `fallback_used=true` and the synthesis
step uses `build_cover_logos(company_name)`'s text-based tenant logo with the brand color.

### Dispatch example (conceptual)

```python
# In the main agent's single message, dispatch all nine:
dispatch([
    Agent(subagent_type="research", prompt=a0_fundamentals_brief),
    Agent(subagent_type="research", prompt=a_financial_brief),
    Agent(subagent_type="research", prompt=b_market_brief),
    Agent(subagent_type="research", prompt=c_leadership_brief),
    Agent(subagent_type="research", prompt=d_legal_brief),
    Agent(subagent_type="research", prompt=e_cre_signals_brief),
    Agent(subagent_type="research", prompt=f_industry_brief),
    Agent(subagent_type="research", prompt=g_esg_brief),
    Agent(subagent_type="research", prompt=logo_fetch_brief),
])
# ... all nine run in parallel, results collected, then synthesis begins.
```

The main agent then proceeds to the **Synthesis** section below (after Step 3).

## Step 3: Research Domains

The eight domain briefs below are **sub-agent prompts**, not serial instructions for the main
agent. Each describes what ONE dispatched sub-agent researches. Copy the relevant brief into
the Agent/Task tool call when dispatching. Every domain must appear in the final report — even
if a sub-agent's finding is "limited public data available; recommend direct financial statement
request."

### A.0 Company Fundamentals & Structure

Core question: *Who exactly is this tenant, legally and operationally?*

This subsection establishes the identity of the entity that would sign the lease and who stands
behind it. It is narrative, not scored — but the facts gathered here feed directly into the
Financial Strength and CRE Track Record dimensions (especially the corporate-guarantee analysis)
and appear on the cover page and the 1-page summary.

**Fields to capture for every tenant:**
- Full legal entity name (including suffix: LLC, LLP, Inc., Corp., PA, PLLC, Ltd., etc.)
- Legal entity type
- State of incorporation / formation
- State registration doc # (filing number / entity ID)
- Registration status (Active / Inactive / Dissolved / Administratively Dissolved / Merged)
- Original filing date (and date of last annual report if available)
- Registered agent (name + address)
- Officers / managers / directors on record (names + titles)
- Principal business address (as filed with the state)
- Tenant website URL
- Parent company / ultimate parent (if any)
- Subsidiaries and affiliated brands (material ones — not exhaustive)
- Corporate structure narrative (2–3 sentences explaining the lease counterparty, the parent
  if any, and who is expected to provide the corporate guarantee)

#### Research procedure — state registration lookup

1. **Start with what the user gave you.** If the user named a specific state of incorporation
   or entity type, use that as your starting point.
2. **If not provided, identify the state of incorporation.** For public companies, the 10-K
   cover page states the state of incorporation. For private companies, check the company's
   "About" / "Contact" / "Legal" website pages, franchise disclosure documents, and news
   mentions. If still ambiguous, check HQ state first — most private companies register in
   their HQ state, Delaware, or Nevada.
3. **Pull the official registration from the appropriate state's business-entity database.**
   This is NOT limited to Florida. Use the state's official source:
   - **Florida:** SunBiz — https://search.sunbiz.org
   - **Delaware:** Division of Corporations — https://icis.corp.delaware.gov/ecorp/entitysearch
   - **California:** Secretary of State BizFile — https://bizfileonline.sos.ca.gov/search/business
   - **Texas:** SOSDirect — https://direct.sos.state.tx.us (free Taxable Entity Search at
     https://mycpa.cpa.state.tx.us/coa)
   - **New York:** NYS Department of State Corporation & Business Entity Database —
     https://apps.dos.ny.gov/publicInquiry
   - **Georgia:** Corporations Division search — https://ecorp.sos.ga.gov/BusinessSearch
   - **Illinois:** Business Entity Search — https://apps.ilsos.gov/businessentitysearch
   - **Any other state:** Web search `"[state name] secretary of state business entity search"`
     and use the official `.gov` result. Do NOT rely on third-party aggregators
     (OpenCorporates, Bizapedia, ZoomInfo) as the primary source — use them only to cross-check.
4. **Capture all standardized fields** above. If a field is unavailable in a particular state's
   database (some states don't publish officers, for example), say so explicitly rather than
   omitting the field.
5. **Cross-check the entity type against the lease counterparty.** If the LOI names "Starbucks
   Corp" but state records show "Starbucks Coffee Company" as the operating entity, surface
   the mismatch — it affects the corporate guarantee analysis.

#### Presentation in the report

Render the A.0 findings as a two-column "Company Fundamentals" table near the top of Section A,
followed by the 2–3 sentence corporate-structure narrative. Use Paragraph objects for cell
content so long registered-agent addresses wrap properly. Do not score this subsection — it is
context. The data flows into:
- Cover page key-facts block (see "Page 1 — Cover" section)
- 1-page summary key-facts box (see "1-Page Summary Deliverable" section)
- Financial Strength dimension (lease counterparty, corporate guarantee)
- CRE Track Record dimension (entity's lease history, which requires the correct entity name)

### A. Financial Health & Creditworthiness

Core question: *Can this tenant reliably pay rent for the full lease term?*

This is the most important section of the report. Give it proportional depth.

**Creditworthiness & Lease Payment Ability (research these first):**
- Credit rating (Moody's/S&P/Fitch if rated; inferred credit quality if unrated)
- Credit outlook (stable/positive/negative) — a negative outlook is a yellow flag, not a red one
- Lease default history — Has this tenant EVER defaulted on, rejected, or abandoned a lease?
  Search specifically for "[company] lease default," "[company] lease rejection bankruptcy,"
  "[company] store closure." For companies that have gone through bankruptcy, how many leases
  were rejected and what percentage of the portfolio was that?
- Corporate guarantee structure — Who exactly is the guarantor? Parent company vs. subsidiary
  vs. franchisee makes an enormous difference
- Rent-to-revenue ratio — Estimate what rent would represent as a percentage of likely
  location-level revenue

**Financial Fundamentals:**
- Revenue and revenue growth trajectory (3-5 year trend)
- Profitability (margins, EBITDA)
- Debt levels and leverage ratios
- Cash position and liquidity
- Bankruptcy history or restructuring events
- For private companies: estimated revenue range, funding history, known investors

**Scoring guidance for this dimension — calibration archetypes.** Scores must reflect actual
differentiation between tenants, not timidity. A "90" should be common for healthy national
brands; anchor the top of the scale to institutional quality, not perfection. Use these
archetypes when scoring Financial Strength & Credit:

- **95–100 — Elite private or public blue-chip.** Dominant brand, no default history, consistent
  revenue growth, strong cash position, low or manageable leverage. Fortune 500 investment-grade
  issuers (Apple, Costco, Microsoft, Walmart), or top-tier private operators with well-documented
  institutional-grade financials and no lease-rejection history (Chick-fil-A, Publix, In-N-Out,
  Mars, Cargill, Koch). A private but financially elite brand with no defaults, dominant
  position, and healthy growth belongs here — not in the low 90s.
- **88–94 — Strong national or large regional.** Investment-grade or inferred-investment-grade
  credit, steady growth, solid margins, no material distress signals. Most large publicly traded
  retailers, banks, and restaurant chains with BBB/BBB+ ratings and healthy cash flow (e.g.,
  Starbucks, McDonald's, Home Depot, Target). A negative outlook alone does NOT drop a score
  out of this band.
- **80–87 — Mid-tier national chain with healthy fundamentals.** Profitable, growing or stable,
  no recent distress, but smaller scale, thinner margins, higher leverage, or a shorter public
  track record than the 88+ cohort.
- **72–79 — Regional operator with adequate financials, or national brand with softening
  fundamentals.** Revenue pressure, margin compression, elevated leverage, or opaque private
  financials. A negative credit outlook plus weakening comp-store sales could land a name here.
- **62–71 — Meaningful stress signals but not imminent distress.** High-yield credit, covenant
  tightness, declining revenue, recent CFO departure, private company with thin financial
  visibility and no documented cushion.
- **50–61 — Actual credit distress risk.** Junk-rated with negative outlook, covenant
  violations, cash burn, recent restructuring, material lawsuits with solvency implications.
- **Below 50 — Prior default, active bankruptcy risk, or effectively insolvent.** Reserve for
  the rare case where the public record shows the tenant cannot reasonably perform for the full
  lease term.

**Calibration rules that apply across all six dimensions:**
- A blue-chip brand with no negative signals should land 95+ on Financial Strength, Market
  Position, and Industry Outlook. The composite for such a tenant should routinely be 94–98,
  not low 90s.
- Reserve scores below 70 for clear distress; below 60 for actual default risk. Do not let
  secondary concerns (labor disputes, ESG controversies, a recent CEO hire) pull an otherwise
  institutional-grade tenant below 85 on any dimension.
- A negative credit outlook is a 3–5 point haircut on Financial Strength, not a band drop.
- Private companies are not automatically scored lower for being private. If the brand is
  dominant and there is no evidence of distress, treat the absence of SEC filings as a
  data-confidence issue (Moderate confidence) rather than a risk signal (score deduction).
- The Chick-fil-A reference profile — private, financially elite, dominant brand, no default
  history, healthy growth — should score 95+ on Financial Strength, 95+ on Market Position,
  and pull the composite into the high 90s. If your scoring produces a lower result for a
  tenant matching that profile, recheck your per-dimension rubric before finalizing.

### B. Market & Competitive Position

Core question: *Is this company well-positioned in its industry, or is it swimming against the current?*

- Market share and ranking within its sector
- Key competitors and how the company differentiates
- Industry growth trends and headwinds
- Recent strategic moves (M&A, expansion, pivots, partnerships)
- Customer/client concentration risk
- Technology disruption exposure

### C. Leadership, Personnel & Organizational Health

Core question: *Do the people running this company inspire confidence that the business will be stable and well-managed through the lease term?*

This section often tells you more than a balance sheet. A company with solid financials but a
revolving door at the C-suite is a different risk than one with modest numbers but a deeply
tenured, aligned leadership team. Dig hard here.

#### C-Suite & Executive Leadership
- **CEO/President tenure and background** — How long have they been in the role? Where did they
  come from? A CEO hired 6 months ago from outside the industry is a very different signal than
  a 12-year veteran who came up through operations.
- **CFO stability** — CFO departures are one of the strongest early warning signals in corporate
  distress. Flag any CFO changes in the last 18 months and explain the context.
- **C-suite turnover pattern** — Map executive departures over the last 3 years. One departure
  is normal; three or more in rapid succession is a red flag. Note whether departures were
  announced as "to pursue other opportunities" (often involuntary) vs. retirements or planned
  transitions.
- **Executive controversies** — Any SEC investigations, fraud allegations, harassment claims,
  or other personal legal issues involving current leadership. These create distraction risk
  even if the company itself is financially sound.
- **Board composition** (public companies) — Independent directors vs. insiders. Any activist
  investor involvement. Recent board shakeups.
- **Founder involvement** (private companies) — Is the founder still active? Founder-led
  private companies have different risk profiles than PE-installed management teams.

#### Organizational Structure & Workforce
- **Employee count and trajectory** — Growing, stable, or shrinking? Look for recent layoff
  announcements, hiring freezes, or rapid scaling. A company that just cut 20% of staff may
  still be profitable but is in a very different posture than one hiring aggressively.
- **Key person risk** — Is the business overly dependent on one or two individuals? Common in
  private medical practices, law firms, and professional services tenants.
- **Organizational restructuring** — Any recent reorgs, division spin-offs, or reporting
  structure changes. These can signal strategic pivots that affect space needs.
- **Glassdoor / employee sentiment** — Search for employee reviews. Patterns matter more than
  individual complaints. Look for themes: "leadership doesn't communicate," "constant
  reorganization," "great culture" — these paint a picture of internal stability.
- **Labor disputes** — Any union activity, NLRB complaints, wage/hour class actions, or
  strikes. These can directly impact a tenant's operations and ability to occupy space.

#### Operational Continuity Signals
- **Succession planning** — For private companies and founder-led businesses, is there a
  visible #2? If the founder gets hit by a bus, does the business survive?
- **Key customer/client concentration** — If 40% of revenue comes from one contract, that
  contract's renewal date is effectively a second lease expiration risk.
- **Technology and systems** — Is the company investing in its operational infrastructure or
  running on legacy systems? Relevant for understanding long-term viability.
- **Supply chain resilience** — For manufacturing, retail, or distribution tenants, how
  diversified and stable is their supply chain?

### D. Legal & Regulatory Exposure

Core question: *Are there legal liabilities or regulatory risks that could impair this tenant's operations or financial stability?*

- **Active litigation** — Material lawsuits, class actions, government investigations. Quantify
  potential exposure where possible.
- **Regulatory actions** — FDA warnings, OSHA violations, EPA enforcement, state AG investigations.
  These often precede financial distress.
- **Compliance posture** — Industry-specific regulatory requirements. Healthcare tenants have
  HIPAA; financial services have extensive compliance overhead; restaurants have health department
  records. Check what's publicly available.
- **Intellectual property disputes** — Patent trolls or genuine IP challenges that could threaten
  the core business.
- **Environmental liabilities** — Particularly relevant for industrial, manufacturing, or gas
  station tenants. Phase I/II environmental concerns can become the landlord's problem.

### E. CRE-Specific Signals

Core question: *What does this company's behavior as a tenant tell us about the lease opportunity?*

- Current real estate footprint (number of locations, total SF, markets)
- Expansion vs. contraction trajectory
- Lease renewal history (if available)
- Typical lease terms for this type of tenant
- Space utilization trends (remote work impact, densification, etc.)
- Build-out requirements and tenant improvement expectations
- Co-tenancy preferences or requirements
- Dark store / go-dark risk for retail

### E.1 Site-Specific Location Analysis (Required when location is provided)

Core question: *What does the local competitive and operational landscape tell us about the
tenant's likelihood of staying at THIS specific location?*

When the user provides a property address or location, this section is **mandatory**. It is one
of the most valuable parts of the report because it moves from general tenant credit analysis
to location-specific underwriting intelligence.

#### What to Research

**Tenant's nearby locations:**
- Search for ALL of the tenant's other locations within a 25-30 mile radius of the subject
  property. Use WebSearch for "[company name] locations near [city/area]" and check the
  company's branch/store locator pages.
- For each nearby location, note: address, approximate distance from subject, and whether
  the trade area overlaps with the subject property.

**Competitor / parent-company overlap:**
- If the tenant has recently been acquired, merged, or has a parent company that also
  operates locations under a different brand, map BOTH brands' locations in the area.
  This is critical for assessing consolidation risk (e.g., bank mergers, restaurant brand
  rollups, retail chain acquisitions).
- Search for "[parent company] locations near [city/area]" separately.

**Local market context:**
- Demographics of the immediate trade area (affluence, density, growth)
- Other tenants or anchors in the immediate vicinity
- Is this a primary vs. secondary market for the tenant?
- Any known development or infrastructure changes nearby that affect foot traffic

#### Required Output

Present the findings as:
1. **A table of the tenant's nearby locations** — with columns for branch/store name, address,
   distance from subject, and overlap notes
2. **A table of parent/acquirer locations** (if applicable) — same format
3. **Consolidation risk assessment** — A clear analysis of which locations are most likely to
   be consolidated and whether the subject property is at risk. Identify where overlap exists
   vs. where the subject serves a distinct trade area.
4. **Underwriting implication** — What does the proximity data mean for the acquisition/lease
   decision? Be specific and actionable.

#### Table Formatting Note
Use Paragraph objects (not plain strings) for table cell content to enable proper text wrapping.
Set column widths wide enough for addresses. Highlight the subject property row with a distinct
background color so it stands out immediately.

### F. Industry Context

Core question: *What's happening in this company's industry that affects their tenancy risk?*

- Overall industry health and outlook
- Regulatory changes on the horizon
- Supply chain or input cost pressures
- Consumer/demand trends
- Industry-specific CRE patterns (e.g., medical office demand drivers, restaurant failure rates)

### G. ESG & Reputation

Core question: *Are there reputational or sustainability factors that affect desirability or risk?*

- Environmental commitments or liabilities
- Social/community impact and reputation
- Governance quality indicators
- Brand strength and public perception
- Any controversies or negative press cycles

## Synthesis: Reconcile Sub-Agent Returns

Once all nine sub-agents have returned their envelopes, the main agent enters the synthesis
phase. **Do not begin synthesis until every sub-agent has reported.** A single missing or
failed return degrades the final product — if a sub-agent failed, either re-dispatch that
single agent or explicitly mark its section as "data gap" before proceeding.

The synthesis phase produces three outputs, in this order:

### Step 1 of synthesis — Reconcile findings

1. **Entity-name consistency check.** Compare the legal entity name across A.0, A, D, and E
   returns. If they disagree (e.g., A.0 says "Chick-fil-A, Inc.", A says "Chick-fil-A
   Restaurants LLC"), flag it to the user and use A.0's value as authoritative (A.0 pulls
   from the state business-entity database).
2. **Counterparty and guarantee alignment.** The financial agent's corporate-guarantee analysis
   must reference the same entity the A.0 agent captured as the state-registered signer.
   Mismatch → re-read both returns and call out which entity would actually sign the lease.
3. **Site-specific cross-check.** If E returned location-level analysis but did not use the
   same parent brand A.0 identified, the E brief missed the parent's footprint — patch the
   E findings using A.0's parent/subsidiary data before scoring CRE Track Record.
4. **Cite hygiene.** Deduplicate sources across envelopes. Surface any contradictions
   between sources (e.g., revenue figure in A vs. revenue mentioned in F) and resolve to
   the more authoritative source.

### Step 2 of synthesis — Re-calibrate scores

Each scored sub-agent (A, B, C, D, E, F) returned a `draft_score`. These are proposals — the
main agent is responsible for global calibration consistency.

Apply these reconciliation rules **before accepting any draft score**:

1. **Check against the archetype table.** Look up the tenant's profile row in the
   cross-dimension archetype table (see Step 4 below). If a draft score falls outside the
   typical range for that profile, the sub-agent was likely mis-calibrated — revise toward
   the archetype range unless the sub-agent's rationale cites a specific distress signal that
   justifies the deviation.
2. **Floor and ceiling rules.** A blue-chip profile (Apple / Costco / Chick-fil-A / Publix
   archetype) must land 95+ on Financial Strength, Market Position, and Industry Outlook
   unless the sub-agent documented a material distress signal. A negative credit outlook is a
   3–5 point haircut, not a band drop. Secondary concerns (labor disputes, ESG controversies,
   recent CEO hire) cannot pull a fundamentally creditworthy tenant below 85 on any dimension.
3. **Cross-domain consistency.** If the Financial agent scored 95 and the Legal agent scored
   55 because of one open lawsuit, the Legal score is likely over-penalized — the dimension
   measures material exposure, not any litigation activity. Revise Legal upward unless the
   lawsuit has solvency implications.
4. **Private-company softening.** Thin public financial visibility is a data-confidence
   issue, not a risk signal. Do not let the Financial agent's "moderate confidence" flag
   translate into a score deduction for an otherwise dominant private brand.

Record both the `draft_score` and the final `reconciled_score` in the report's scoring table
transparently — the calibration trail matters for audit.

### Step 3 of synthesis — Select and prepare the logo

1. **If the logo agent returned `fallback_used=false` with a usable `logo_url` or
   `downloaded_path`:**
   - Download the image if it's still remote (use `requests.get(logo_url)` with a timeout).
   - Verify the file opens and has sane dimensions (min 200px wide for SVG or 400px for PNG).
   - Prepare the image as a reportlab flowable:
     ```python
     from reportlab.platypus import Image
     tenant_logo = Image(downloaded_path, width=180, height=50, kind='proportional')
     ```
   - Use this `tenant_logo` flowable on BOTH the full-report cover AND the 1-page summary
     header. Ignore the Drawing returned by `build_cover_logos()` for the tenant (still use
     `build_cover_logos()` for the Rising Tide logo).
2. **If the logo agent returned `fallback_used=true`:**
   - Call `build_cover_logos(company_name)` as the fallback — it returns a text-based logo
     Drawing that respects `BRAND_COLORS` lookup.
   - If the logo agent also returned a `brand_color_hex` that isn't already in `BRAND_COLORS`,
     pass it to `build_tenant_logo(company_name, brand_color=HexColor(brand_color_hex))`
     to produce a color-correct text logo.
3. **Sanity check.** Render a preview of the chosen logo flowable before committing to the
   PDF build. If the rendered height exceeds the cover's allocated band (~70pt) or the
   aspect ratio is distorted, fall back to the text logo.

Only after the synthesis phase is complete does the main agent proceed to **Step 4** (composite
scoring formalization) and the **PDF build**. The PDFs are built using the reconciled findings,
reconciled scores, and selected logo.

## Step 4: Composite Risk Score

### The Principal Question

The single most important question in tenant underwriting is: **Will this tenant pay rent
reliably for the full lease term?** Everything else — leadership changes, ESG controversies,
competitive headwinds — matters only insofar as it affects the answer to that question.

Before scoring, explicitly research and answer:
- **Lease default history** — Has this company ever defaulted on, rejected in bankruptcy, or
  abandoned a commercial lease? If so, how many, when, and under what circumstances? For large
  tenants, search for "[company] lease rejection," "[company] store closure lease," "[company]
  bankruptcy lease." This data point alone can move the score 20 points in either direction.
- **Corporate guarantee strength** — Is the lease backed by a parent company or corporate
  guarantee? A lease with Starbucks Corporation (BBB+, $37B revenue) behind it is fundamentally
  different from a lease with an individual franchisee. Identify exactly who the guarantor would be.
- **Rent-to-revenue ratio** — What percentage of the tenant's revenue at this location would go
  to rent? Below 10% is comfortable; above 15% creates pressure; above 20% is high risk. For
  multi-location tenants, estimate location-level economics.
- **Credit rating and outlook** — Investment-grade (BBB-/Baa3 or better) vs. high-yield vs.
  unrated. Is the outlook stable, positive, or negative?

A Fortune 500 company with investment-grade credit, decades of lease payment history, and a
corporate guarantee should score in the mid-to-upper 90s on the composite — not the low 90s —
even if it has labor disputes, CEO turnover, or ESG controversies. Those factors inform
negotiation strategy and lease structure; they do not make the company unable to pay rent.
Do not let secondary concerns drag down the score of a fundamentally creditworthy tenant. An
elite private brand (dominant market position, no default history, healthy financials) belongs
in the same 95+ composite range as its investment-grade public peers.

### Scoring Framework

Score the tenant on a 100-point scale across six weighted dimensions. Present both the
component scores and the composite.

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Financial Strength & Credit | 35% | Ability to pay rent: revenue, profitability, leverage, credit rating, lease default history, corporate guarantee strength |
| CRE Track Record | 20% | Real estate behavior: lease defaults, expansion/contraction, renewal history, footprint stability |
| Leadership & Personnel | 15% | Executive stability, tenure, succession, organizational health — as leading indicators of future financial health |
| Market Position | 15% | Competitive durability, market share, brand strength — as indicators of revenue sustainability |
| Legal & Regulatory | 5% | Material litigation or regulatory exposure that could impair operations or trigger financial distress |
| Industry Outlook | 10% | Sector-level growth, disruption risk — as context for the tenant's trajectory |

**Why this weighting:** Financial Strength & Credit carries 35% because it directly answers "can
they pay rent." CRE Track Record carries 20% because past lease behavior is the strongest
predictor of future lease behavior. Leadership and Market Position carry 15% each because they
are leading indicators — they tell you where financials are headed. Legal and Industry Outlook
carry less weight because they're contextual: a lawsuit or industry headwind matters, but only
if it's severe enough to actually impair the tenant's ability to meet rent obligations.

The Leadership & Personnel dimension still matters — executive instability is often a leading
indicator of financial trouble — but it shouldn't dominate the score for a company that is
demonstrably solvent and creditworthy.

**Cross-dimension calibration archetypes (for the composite):**

| Profile | Composite target | Typical per-dimension range |
|---------|------------------|-----------------------------|
| Elite blue-chip (Apple, Costco, Chick-fil-A, Publix) | 94–98 | Financial 95+, Market 95+, Leadership 90–95, Legal 90+, CRE Track 92+, Industry 85–95 |
| Strong national chain (Starbucks, McDonald's, Home Depot, Target) | 88–93 | Financial 88–94, Market 88–94, Leadership 85–92, Legal 85–95, CRE Track 85–92, Industry 80–92 |
| Mid-tier national / large regional | 80–87 | Financial 80–88, Market 78–87, Leadership 78–88, Legal 82–92, CRE Track 80–88, Industry 75–88 |
| Regional operator with healthy fundamentals | 72–80 | Financial 72–82, Market 70–80, Leadership 72–85, Legal 80–90, CRE Track 72–82, Industry 70–85 |
| Softening fundamentals or thin financial visibility | 62–72 | Financial 60–72, Market 60–75, Leadership 60–80, Legal 70–90, CRE Track 60–75, Industry 60–80 |
| Meaningful credit stress, high-yield + negative outlook | 52–62 | Financial 45–60, Market 50–70, Leadership 50–75, Legal 50–85, CRE Track 50–65, Industry 55–75 |
| Prior lease default, active restructuring risk | Below 52 | Financial below 50, others vary |

A tenant matching the elite blue-chip profile should land **94 or higher** on the composite. If
your per-dimension scoring produces a lower result for such a tenant, the issue is almost always
that one or more dimensions were marked too harshly — revisit them before finalizing.

**Scoring bands:**

| Score | Grade | Interpretation |
|-------|-------|---------------|
| 90-100 | A | Strong tenant — low risk, favorable lease terms justified |
| 80-89 | B | Solid tenant — standard terms, monitor periodically |
| 70-79 | C | Moderate risk — enhanced security deposit or guarantees advisable |
| 60-69 | D | Elevated risk — significant lease protections needed |
| 0-59 | F | High risk — proceed with extreme caution or decline |

**The scoring system is non-negotiable: 100-point scale with letter grades A/B/C/D/F.**
Do not substitute a 10-point scale, a 5-star system, qualitative labels like "HIGH RISK," or
any other format. The reason this matters is that Rising Tide's investment committee uses these
letter grades as a shared vocabulary across all tenant evaluations — consistency lets them compare
a Starbucks "A" against a WeWork "D" at a glance. Every report must show:
1. The composite score as a number out of 100 (e.g., "72/100")
2. The corresponding letter grade (e.g., "B")
3. Each of the six dimension scores as numbers out of 100
4. A confidence level: High / Moderate / Low — with a brief explanation of why

Be honest and calibrated. An "A" should mean something. If data is thin, reflect that
uncertainty in the score — don't default to the middle.

## Step 5: Build the PDF Presentation

Use reportlab to create a polished, professional PDF. Read the PDF skill (at the path where
the pdf SKILL.md lives) for reportlab best practices before generating the document.

### Visual Design Principles

- **Color palette:** Use a professional, muted palette. Navy (#1B2A4A) as primary, with
  slate gray (#4A5568) for body text, and an accent color (#2E86AB) for highlights and scores.
  White (#FFFFFF) backgrounds. Scoring bands use color: A = green (#2D7D46), B = teal (#2E86AB),
  C = amber (#D4A017), D = orange (#D46A17), F = red (#C0392B).
- **Typography:** Helvetica for headings, Helvetica for body text. Clean, corporate feel.
  Don't over-decorate.
- **Layout:** Generous margins (1 inch). Clear section separation. Use horizontal rules and
  whitespace rather than boxes-within-boxes.

### Data Visualization Requirements

This report is a presentation, not an essay. Decision-makers scan visuals before reading prose.
Every major section should include at least one visual element — a chart, graph, table, or
diagram — that communicates the key finding at a glance. The prose then provides the nuance
and context that the visual can't.

Use reportlab's drawing capabilities (reportlab.graphics, reportlab.graphics.shapes,
reportlab.graphics.charts) to build these directly in Python. All charts should use the
color palette defined above and be clearly labeled with titles, axis labels, and legends
where applicable.

#### Required Visuals (include all of these):

**1. Composite Score Dashboard (Executive Summary page)**
Build a visual score card that shows:
- The composite score prominently (large number + letter grade) with background color matching
  the grade band
- A horizontal bar chart showing all six dimension scores side-by-side, each bar labeled with
  the dimension name, score out of 100, and colored by grade band
- This is the single most important visual in the report — spend time making it clean and readable

**2. Revenue / Financial Trend Chart (Financial section)**
- For public companies: A line chart or bar chart showing 3-5 years of revenue (and EBITDA or
  net income if available). Label the Y-axis with dollar amounts, X-axis with fiscal years.
  If the company has had a significant inflection (growth spike, revenue decline, restructuring),
  annotate that point on the chart.
- For private companies: A bar chart showing estimated revenue range (low/mid/high) benchmarked
  against industry peers or comparable companies. Label it clearly as "Estimated" with the basis
  for the estimate.
- If no revenue data is available at all, show an industry revenue benchmark chart instead and
  note that company-specific data was unavailable.

**3. Competitive Landscape Visual (Market section)**
- A horizontal bar chart or table comparing the tenant against 3-5 key competitors on a
  meaningful metric (revenue, market share, store count, or employee count — whatever best
  illustrates competitive position).
- Alternatively, for industries where positioning matters more than size, use a simple 2x2
  quadrant (e.g., "Market Growth" vs. "Company Strength") with the tenant and competitors
  plotted as labeled dots. Build this with reportlab shapes (circles + text labels on a
  drawn axis).

**4. Executive Leadership Table (Leadership section)**
- A formatted table showing: Name | Title | Tenure (years) | Prior Role/Company
- For public companies, include at least CEO, CFO, COO (or equivalent), and any other
  notable C-suite. For private companies, include whatever leadership can be identified.
- Color-code tenure: green for 5+ years, amber for 2-5 years, red for under 2 years —
  this makes leadership stability visible at a glance.

**5. CRE Footprint Summary (CRE section)**
- A data table or visual showing: Total locations, total SF, geographic concentration,
  recent openings vs. closures (last 2 years if available).
- For tenants with a large footprint, a simple bar chart showing location count by
  year (last 3-5 years) to illustrate expansion or contraction trajectory.

**6. Branch/Location Proximity Table (Site-Specific section, when location provided)**
- A formatted table showing: tenant's nearby locations + parent/acquirer locations with
  addresses, distances, and overlap flags
- Highlight the subject property row with a distinct background color
- Use Paragraph objects in cells for proper text wrapping

**7. Risk Heatmap or Spider/Radar Summary (can go on Executive Summary or final page)**
- A simple visual showing all six scoring dimensions with color-coded risk levels.
  Options:
  - A table with colored cells (green/amber/red) — easy to build in reportlab
  - A set of colored horizontal bars (like a stacked dashboard)
  - The dimension bar chart on the Executive Summary can double for this if it's
    color-coded by grade band

#### Optional Visuals (include when data supports it):

- **Debt maturity timeline** — For public companies with significant debt, show when
  major maturities hit relative to the proposed lease term
- **Stock price chart** — For public companies, a simple line showing trailing 12-month
  stock performance (build from data points, doesn't need to be tick-level)
- **Industry growth forecast** — A bar or line chart showing projected industry growth
  rates over the next 3-5 years
- **Employee count trend** — A line chart if the company has had notable workforce
  changes (layoffs, rapid hiring)

#### Chart Implementation: Use the Bundled Script

A ready-made chart library is bundled at `scripts/charts.py` (relative to this skill's
directory). **Copy this file to your working directory and import it** rather than building
charts from scratch. This saves significant time and ensures visual consistency across all
tenant research reports.

```python
import shutil, os

# Copy charts.py from the skill's scripts/ directory to your working dir
skill_dir = '/path/to/tenant-research'  # adjust to actual skill path
shutil.copy(os.path.join(skill_dir, 'scripts', 'charts.py'), './charts.py')

from charts import (
    build_score_dashboard,   # Composite score + dimension bars (exec summary)
    build_bar_chart,         # Revenue, employee count, any vertical bars
    build_trend_chart,       # Line chart for trends over time
    build_competitive_bars,  # Horizontal bars comparing companies
    build_risk_heatmap,      # Color-coded risk grid
    BULLET,                  # Safe bullet character (avoids encoding issues)
    grade_color,             # Returns color for a score
    letter_grade,            # Returns letter grade for a score
)
```

Each function returns a `Drawing` object that you add directly to the platypus story:
```python
# Score dashboard on executive summary page
dimensions = [
    {'name': 'Financial Strength', 'score': 82},
    {'name': 'Leadership & Personnel', 'score': 75},
    {'name': 'Market Position', 'score': 88},
    {'name': 'Legal & Regulatory', 'score': 60},
    {'name': 'CRE Track Record', 'score': 80},
    {'name': 'Industry Outlook', 'score': 70},
]
story.append(build_score_dashboard(composite_score=78, dimensions=dimensions))

# Revenue trend
story.append(build_bar_chart(
    data=[32.5, 34.1, 36.2, 37.2],
    labels=['FY2022', 'FY2023', 'FY2024', 'FY2025'],
    title='Revenue Trend ($B)',
    y_label='Revenue ($B)'
))

# Competitive landscape
story.append(build_competitive_bars(
    companies=['Starbucks', 'Dunkin', 'Dutch Bros'],
    metric_values=[30, 18, 8],
    metric_name='Market Share (%)',
    highlight_company='Starbucks'
))
```

Every section of the report must include at least one visual chart from this library. The
charts are the first thing a reader's eye goes to — they communicate the key finding at a
glance, and the prose provides the context and nuance. A report with only tables and text
does not meet the quality standard.

**Colored tables are NOT charts.** A table with colored cells (e.g., using TableStyle with
BACKGROUND) is a formatted table — it is not a chart. The functions in charts.py return
`Drawing` objects that render as actual vector graphics: bars, lines, shapes with coordinates.
You must call the actual functions and `story.append()` the returned Drawing objects.

**Minimum chart count: 4 per report.** At a bare minimum, every report must contain:
1. `build_score_dashboard()` on the Executive Summary page
2. `build_bar_chart()` in the Financial section (revenue or key metric trend)
3. `build_competitive_bars()` in the Market section
4. `build_risk_heatmap()` on the Risk/Summary page

Tables are fine as supplementary data displays alongside the charts — but the charts must
be present as Drawing-based graphics.

#### Text Formatting: Bullets and Line Breaks

This is a common source of rendering bugs. Follow these rules strictly:

**Bullet points:** Never use raw Unicode bullet characters (u'\u2022') inside Paragraph
objects — they render as garbled squares or `a??` with Helvetica. Use HTML entities:
```python
# CORRECT — each bullet as a separate Paragraph
story.append(Paragraph("&bull; First point", bullet_style))
story.append(Paragraph("&bull; Second point", bullet_style))

# ALSO CORRECT — use <br/> tags for line breaks within one Paragraph
story.append(Paragraph(
    "&bull; First point<br/>"
    "&bull; Second point<br/>"
    "&bull; Third point",
    bullet_style
))
```

**Never concatenate bullets into a single run of text** like `"Point one• Point two• Point three"`.
This produces an unreadable wall of text. Each bullet must be on its own line, either via
`<br/>` tags or separate Paragraph objects.

**Numbered lists:** Same principle — one item per line:
```python
story.append(Paragraph(
    "1. First item<br/>"
    "2. Second item<br/>"
    "3. Third item",
    body_style
))
```

### Page Structure

**Page 1 — Cover**
- **Rising Tide Property Group logo** (top of page) — generated using bundled `scripts/logos.py`
- **Tenant company logo** (below Rising Tide logo) — generated using bundled `scripts/logos.py`
- **Legal entity name** (prominent, below the tenant logo)
- **Key-facts block** (compact 4-line table, centered, below the legal entity name):
    - Entity type | State of Incorporation
    - Website URL
    - Parent company (if any; otherwise omit this line)
    - HQ location
- "Tenant Research & Risk Analysis"
- Date of report
- "For informational purposes only. See Disclaimers & Limitations." (small text, bottom of cover)

#### Logo Generation: Use the Bundled Vector Script

A ready-made vector logo generation library is bundled at `scripts/logos.py` (relative to this
skill's directory). **Copy this file to your working directory and import it** to generate both
logos as crisp, resolution-independent reportlab Drawing objects (no PNG files needed).

```python
import shutil, os

# Copy logos.py from the skill's scripts/ directory
skill_dir = '/path/to/tenant-research'  # adjust to actual skill path
shutil.copy(os.path.join(skill_dir, 'scripts', 'logos.py'), './logos.py')

from logos import build_cover_logos, build_rising_tide_logo, build_comerica_logo, build_tenant_logo, get_brand_color

# Easiest: build both cover logos at once — returns (Drawing, Drawing) tuple
rt_logo, tenant_logo = build_cover_logos('Comerica Bank')

# Or build individually:
rt_logo = build_rising_tide_logo(width=300, height=70)        # 3-wave icon + "RISING TIDE"
comerica_logo = build_comerica_logo(width=300, height=60)     # 3-ribbon + "Comerica" wordmark
generic_logo = build_tenant_logo('Company Name', brand_color=get_brand_color('Company'))
```

Then add them to the cover page using the CenteredDrawing wrapper:
```python
from reportlab.platypus import Flowable

class CenteredDrawing(Flowable):
    """Wrapper that horizontally centers a Drawing on the page."""
    def __init__(self, drawing):
        Flowable.__init__(self)
        self.drawing = drawing
        self.width = drawing.width
        self.height = drawing.height
    def wrap(self, availWidth, availHeight):
        return (availWidth, self.drawing.height)
    def draw(self):
        from reportlab.graphics import renderPDF
        x_offset = (self.canv._pagesize[0] - self.drawing.width) / 2 - self.canv._x
        renderPDF.draw(self.drawing, self.canv, x_offset, 0)

# Cover page layout — all centered, investor-grade
story.append(Spacer(1, 0.6*inch))
story.append(CenteredDrawing(rt_logo))              # Rising Tide logo
story.append(Spacer(1, 0.6*inch))
story.append(HRFlowable(width="40%", thickness=1.5, color=NAVY, hAlign='CENTER'))
story.append(Spacer(1, 0.5*inch))
story.append(CenteredDrawing(tenant_logo))           # Tenant logo
story.append(Spacer(1, 6))

# Legal entity name — bold, centered, directly below tenant logo
story.append(Paragraph(
    legal_entity_name,  # e.g., "Chick-fil-A, Inc."
    legal_name_style    # Helvetica-Bold, 16pt, centered, navy
))
story.append(Spacer(1, 0.1*inch))

# Key-facts block — compact centered table, no visible borders
key_facts_data = [
    [Paragraph(f"<b>{entity_type}</b>", fact_label_style),
     Paragraph(f"Inc. in {state_of_incorp}", fact_label_style)],
    [Paragraph(f'<link href="{website_url}">{website_url}</link>', fact_link_style), ''],
    [Paragraph(f"Parent: {parent_company}", fact_label_style), ''] if parent_company else None,
    [Paragraph(f"HQ: {hq_location}", fact_label_style), ''],
]
key_facts_data = [row for row in key_facts_data if row is not None]
key_facts_table = Table(key_facts_data, hAlign='CENTER', colWidths=[2.5*inch, 2.5*inch])
key_facts_table.setStyle(TableStyle([
    ('FONTSIZE', (0,0), (-1,-1), 9),
    ('TEXTCOLOR', (0,0), (-1,-1), SLATE),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ('TOPPADDING', (0,0), (-1,-1), 2),
]))
story.append(key_facts_table)
story.append(Spacer(1, 0.3*inch))

# ... subtitle, report title, property details, confidential badge (all alignment=1 centered)
```

Visual note: adding the legal-entity name + key-facts table pushes the report title/date
downward on the cover. If the date crowds the bottom margin on first render, tighten the
upper Spacers from 0.6→0.4 inch.

The logos are **vector Drawing objects** (reportlab.graphics.shapes.Drawing), which are Flowable
objects that render at any resolution without pixelation. The `build_cover_logos()` function
automatically selects the correct logo builder for known tenants (e.g., Comerica gets the
3-ribbon logo) and falls back to `build_tenant_logo()` for others. The `BRAND_COLORS` dictionary
in logos.py contains known brand colors for common CRE tenants (banks, retailers, etc.). For
unknown companies, it defaults to a professional dark blue.

**Page 2 — Executive Summary**
This is the most important page. A busy decision-maker may only read this.
- **Composite Score Dashboard** (see Required Visual #1 above): the large score + letter grade
  with the six-dimension bar chart, color-coded by grade band. This should take up roughly the
  top third of the page.
- 3-4 sentence narrative summary of the tenant's fitness
- Key strengths (2-3 bullets)
- Key risks (2-3 bullets)
- Recommendation: Clear, actionable (e.g., "Suitable for 10-year NNN lease with standard
  security deposit" or "Recommend enhanced guarantees and annual financial review covenant")

**Pages 3+ — Detailed Sections**
One section per research domain (A through G). Each section should include:
- Section header with the core question
- The required chart/visual for that section (see Required Visuals above) — place it near
  the top of the section so readers see the visual before the prose
- Findings organized as narrative prose (not just bullet dumps) that interpret and add
  context to what the visual shows
- Key data points called out in a highlight box or table where appropriate
- Confidence indicator where data is estimated or inferred
- Source attribution for major claims

The Leadership & Personnel section (C) should include the Executive Leadership Table (Required
Visual #4) with tenure color-coding. For public companies, include a note on any recent 8-K
filings related to executive changes. For private companies, note what can and cannot be
verified and flag key-person risk explicitly.

**Final Page — Methodology & Disclaimers**

**IMPORTANT: Wrap the risk heatmap and the methodology/disclaimer text together using
`KeepTogether` from `reportlab.platypus` so they are never split across a page break.**
This prevents the heatmap boxes from rendering on one page with the disclaimer orphaned
on the next (or vice versa). Example:
```python
from reportlab.platypus import KeepTogether
final_page_elements = [
    build_risk_heatmap(dimensions),
    Spacer(1, 12),
    methodology_heading,
    methodology_body,
    disclaimer_paragraph,
]
story.append(KeepTogether(final_page_elements))
```

Contents of this page:
- The risk heatmap visual (from `build_risk_heatmap()`)
- Brief description of scoring methodology
- Data sources used
- Date of research

**Dedicated Disclaimers & Limitations Page (MANDATORY — must appear as the final page of every report)**

This page is non-negotiable. These reports are sold commercially to the general public and may
be used for any purpose the buyer chooses, which creates significant liability exposure. Every
single report must include a dedicated disclaimers page with ALL of the following sections.
Do not abbreviate, omit, or condense these. Use a smaller font size (8pt body, 9pt headers)
to fit everything on one page, but all sections must be present.

Build this page using reportlab Paragraph objects with appropriate styles. Use a horizontal
rule at the top to visually separate it from report content. The page heading should be
"Important Disclaimers & Limitations" in bold.

**Required Disclaimer Sections (include ALL of these verbatim or substantively equivalent):**

**1. General Disclaimer**
"This report is published by Rising Tide CRE and is provided for general informational
purposes only. It does not constitute professional advice of any kind, including but not
limited to legal, financial, investment, accounting, tax, or real estate advice. Recipients
should consult qualified professionals before making any business, investment, or leasing
decisions based on information contained in this report."

**2. Not a Credit Rating**
"The composite risk score and letter grades (A/B/C/D/F) presented in this report are
proprietary analytical assessments developed by Rising Tide CRE. They are NOT credit ratings
and are not issued by, affiliated with, or endorsed by any Nationally Recognized Statistical
Rating Organization (NRSRO) including but not limited to S&P Global Ratings, Moody's Investors
Service, or Fitch Ratings. These scores should not be interpreted as, or used as a substitute
for, formal credit ratings or credit opinions."

**3. Not Investment Advice**
"Nothing in this report constitutes a recommendation to buy, sell, hold, or otherwise transact
in any security, real property, or financial instrument. This report does not constitute an
offer or solicitation of an offer to buy or sell any investment. Rising Tide CRE is not a
registered investment adviser, broker-dealer, or financial planner. Any references to lease
suitability, recommended terms, or risk assessments reflect analytical observations only and
should not be construed as investment recommendations."

**4. FCRA Safe Harbor**
"This report is not a 'consumer report' as defined by the Fair Credit Reporting Act (15 U.S.C.
§ 1681 et seq.) and was not prepared by a 'consumer reporting agency' as defined therein. This
report is a commercial research product compiled from publicly available sources for general
informational purposes. It is not intended for use in evaluating any individual consumer's
eligibility for credit, insurance, employment, housing, or any other purpose governed by the
FCRA. Purchasers and recipients of this report agree not to use it for any FCRA-regulated
purpose."

**5. Data Accuracy & Sources**
"Information contained in this report has been compiled from publicly available sources
including but not limited to SEC filings, press releases, news reports, industry databases,
and company websites. Rising Tide CRE has not independently verified all information presented
and makes no representation or warranty, express or implied, as to the accuracy, completeness,
timeliness, or reliability of any information in this report. Data may contain errors,
omissions, or may have changed since the date of research. Financial figures for private
companies are estimates unless otherwise noted."

**6. Limitation of Liability**
"To the fullest extent permitted by applicable law, Rising Tide CRE, its officers, directors,
employees, agents, and affiliates shall not be liable for any direct, indirect, incidental,
consequential, special, or exemplary damages arising out of or in connection with the use of,
reliance on, or inability to use this report, including but not limited to damages for loss of
profits, goodwill, data, or other intangible losses, even if advised of the possibility of
such damages. This limitation applies regardless of the legal theory upon which such damages
may be based."

**7. No Warranty**
"THIS REPORT IS PROVIDED 'AS IS' AND 'AS AVAILABLE' WITHOUT WARRANTY OF ANY KIND, EITHER
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. RISING TIDE CRE DOES NOT WARRANT
THAT THE INFORMATION IN THIS REPORT WILL MEET YOUR REQUIREMENTS OR THAT IT IS ERROR-FREE."

**8. Report Date and Temporal Limitation**
"This report reflects information available as of [INSERT REPORT DATE]. Market conditions,
company circumstances, financial positions, legal proceedings, and other factors assessed in
this report are subject to change without notice. This report should not be relied upon as
current after 90 days from the date of publication without independent verification."

**9. Governing Law**
"This report and any disputes arising from its use shall be governed by the laws of the
State of Florida without regard to its conflict of laws provisions."

**Footer on every page of the report (not just the disclaimers page):**
Include a small footer (7pt font) on every page: "© [YEAR] Rising Tide CRE. For informational
purposes only. Not a credit rating, investment recommendation, or consumer report. See
Disclaimers & Limitations page."

Build the footer using the `onPage` or `onPageTemplate` callback in the reportlab
SimpleDocTemplate/BaseDocTemplate. Example:
```python
def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(HexColor('#999999'))
    footer_text = (
        f"© {datetime.now().year} Rising Tide CRE. For informational purposes only. "
        "Not a credit rating, investment recommendation, or consumer report. "
        "See Disclaimers & Limitations page."
    )
    canvas.drawCentredString(
        doc.pagesize[0] / 2, 0.4 * inch, footer_text
    )
    canvas.restoreState()

doc = SimpleDocTemplate(output_path, ...)
doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
```

## Research Tools

Use all available tools aggressively:
- **WebSearch** — For news, press releases, industry reports, company information
- **WebFetch** — To pull specific pages (SEC filings, company websites, industry data)
- Do multiple searches per domain. A single search rarely captures the full picture. Search
  the company name + various keywords: "revenue," "lawsuit," "expansion," "layoffs," "lease,"
  "bankruptcy," "acquisition," "competitors," etc.
- Cross-reference findings. If one source says revenue is $500M and another says $200M, dig
  deeper.

## Quality Standards

- **No fluff.** Every sentence should contain information or analysis. Don't pad with generic
  industry descriptions that anyone could write.
- **Cite or qualify.** If a data point comes from a specific source, say so. If it's estimated,
  say "estimated" and explain the basis.
- **Be direct about risk.** Rising Tide needs honest assessments, not diplomatic hedging. If a
  company looks troubled, say so clearly and explain why.
- **Acknowledge gaps.** "No public financial data available; recommend requesting audited
  statements directly" is far more useful than papering over the gap.
- **Calibrate confidence.** Use phrases like "high confidence based on SEC filings" vs.
  "moderate confidence based on industry estimates" vs. "low confidence — limited data available."

## File Output

Two PDFs must be saved to a location the user can access: the full report AND a 1-page
summary (see next section). Both are required deliverables. Follow these steps:
1. Build both PDFs using reportlab and save them first to your working directory
2. Then explicitly copy BOTH PDFs to the user's workspace folder (typically the mounted folder
   at `/sessions/*/mnt/*/` — check which directory is available)
3. Verify both files exist at the destination using `os.path.exists()` or an `ls` command
4. Name the full file: `[Company-Name]-Tenant-Research.pdf` AND produce a 1-page summary at
   `[Company-Name]-Tenant-Summary.pdf` per the next section. Both files are required
   deliverables — do not skip the summary even if the full report is complete.
5. If an output directory was specified in the task, save both files there AND to the
   workspace folder

The PDFs are the deliverable. If they don't end up where the user can find them, the work
is wasted.

## 1-Page Summary Deliverable

Alongside `[Company-Name]-Tenant-Research.pdf`, generate a second PDF named
`[Company-Name]-Tenant-Summary.pdf` that is a single-page scannable excerpt. This file exists
because investment-committee members often need a 30-second read before deciding whether to
open the full report. Both files are required deliverables.

### File location

Save the summary alongside the full report (same directory, same workspace mount). No subfolder.
Filename exactly `[Company-Name]-Tenant-Summary.pdf` (strip punctuation/spaces from the company
name into a filename-safe form, same convention as the full report).

### Page layout (one page, US Letter, 0.6" margins)

**Header band (top ~1.3 inches):**
- Row 1: Rising Tide logo (~200pt wide) on left, tenant logo (~180pt wide) on right.
  Use `build_cover_logos(company_name)` from `scripts/logos.py` — the same call used on the
  full-report cover. This guarantees brand-color and rendering consistency.
- Row 2: Legal entity name (bold, 16pt, centered) with entity type + state of incorporation
  on a single line (e.g., "Chick-fil-A, Inc. — Georgia corporation").

**Composite score block (~1.5 inches):**
- Large composite score and letter grade, centered, colored by grade band.
- Use `build_score_dashboard(...)` from `scripts/charts.py`. If the full dashboard is too tall
  for the 1-pager, render only the composite card + a horizontal 6-bar dimension strip.
- One-line recommendation immediately beneath (e.g., "Suitable for 10-year NNN lease with
  standard security deposit").

**Key-facts box (~1.2 inches):**
Two-column table, no visible borders, slate text on a very light navy tint. Use Paragraph
objects for wrapping. Rows:
- Website
- Entity type
- State of incorporation
- State registration doc #
- Registered agent
- Parent company ("None — independent" if not applicable)
- HQ

**Executive narrative (3–4 sentences, ~1 inch):**
Reuse the EXACT narrative from the full report's Executive Summary. Do not rewrite — consistency
between the two PDFs matters. If the full-report narrative is longer than 4 sentences, trim
to the 3–4 most important sentences.

**Strengths and risks (side-by-side, ~1.8 inches):**
Two columns. Left header "Top 3 Strengths" (green band). Right header "Top 3 Risks" (amber
band). Three bullets each, 1–2 lines max per bullet. Reuse the bullets from the full report's
exec summary.

**Lease recommendation block (~0.6 inches):**
One of three labels in a colored band:
- **Approve** (green #2D7D46) — "Suitable for standard lease terms."
- **Conditional** (amber #D4A017) — "Suitable with enhanced guarantees / financial covenants /
  larger security deposit."
- **Decline** (red #C0392B) — "Not recommended; credit risk exceeds acceptable threshold."

Followed by one sentence of rationale pulled from the full report.

**Footer (~0.3 inches):**
Small 8pt centered text:

```
This is a summary excerpt. See [Company-Name]-Tenant-Research.pdf for full analysis,
scoring methodology, and disclaimers. | Generated [YYYY-MM-DD] | © [YEAR] Rising Tide CRE.
```

### Implementation pattern

Build the summary as a second `SimpleDocTemplate` in the same Python script run as the full
report — narrative, score, strengths, and risks are computed once and used in both PDFs.

```python
summary_doc = SimpleDocTemplate(
    summary_output_path,
    pagesize=letter,
    leftMargin=0.6*inch, rightMargin=0.6*inch,
    topMargin=0.5*inch, bottomMargin=0.4*inch,
)
summary_story = []
rt_logo, tenant_logo = build_cover_logos(company_name)  # SAME call as full report
# ... 2-column table for header band (RT left, tenant right)
# ... legal name row
# ... composite score / dashboard (compact)
# ... key-facts table
# ... exec narrative Paragraph (reuse the variable from the full report)
# ... strengths/risks 2-column Table (reuse the bullet lists)
# ... recommendation band
# ... footer
summary_doc.build(summary_story)
```

### Important

- **The 1-pager MUST use `build_cover_logos()`** — same tenant logo as the full-report cover.
  Do not fall back to a text-only header.
- **The 1-pager is not a standalone sales document.** It must reference the full report by
  filename in the footer.
- **Do not add disclaimers to the 1-pager body** — the footer's pointer to the full report is
  the liability bridge. The full report carries the dedicated Disclaimers page.

## Slack Distribution

After generating the PDF, the report should also be published to Slack so the team can access
it without digging through files. This is a two-part delivery: a summary message for quick
scanning and a full Slack Canvas for anyone who wants the complete analysis.

The reason this matters: investment decisions move fast and the people who need this research
aren't always sitting at a desktop where they can open a PDF. A Slack message they can scan
on their phone between meetings is often more impactful than a PDF sitting in a shared folder.

### Step 1: Post a Summary Message

Use `slack_send_message` to post a concise summary to the designated channel (typically
`#rising-tide-tenant-research` — use `slack_search_channels` to find the channel ID if needed).

The summary message should include:
- **Tenant name and property address** (bolded header)
- **Deal economics line** — Purchase price, NOI, cap rate, lease term, structure (if known)
- **Composite score and grade** — The single most important data point
- **Key strengths** (2-3 bullets, marked with a checkmark emoji)
- **Critical risks** (2-3 bullets, marked with a flag emoji)
- **Cap rate verdict** — One sentence on whether the pricing adequately reflects tenant risk
- **Recommendation** — The bottom-line call (proceed, caution, decline)
- A note that the full report is available (the canvas will be linked in the thread)

Keep the message under 4,000 characters. Decision-makers skim — front-load the score and
the recommendation. The detail lives in the canvas.

### Step 2: Create a Slack Canvas with the Full Report

Use `slack_create_canvas` to create a permanent, shareable document containing the complete
tenant research. The canvas replaces the need to upload the PDF to Slack — it's natively
searchable, linkable, and readable on any device.

**Canvas structure should mirror the PDF sections:**
- Deal Summary (economics table at the top)
- Executive Summary with composite score, strengths, risks, recommendation
- Section A.0: Company Fundamentals & Structure (entity, state of incorp, registration, parent, website)
- Section A: Financial Health & Creditworthiness
- Section B: Market & Competitive Position
- Section C: Leadership, Personnel & Organizational Health
- Section D: Legal & Regulatory Exposure
- Section E: CRE-Specific Signals (including E.1 Site-Specific if applicable)
- Section F: Industry Context
- Section G: ESG & Reputation
- Composite Risk Scoring table (all six dimensions with scores, weights, rationale)
- Disclaimers & Limitations (include note: "Full disclaimers appear in the PDF report")

**Formatting notes for canvas content:**
- Use standard Markdown (bold, italic, headers, tables, horizontal rules)
- Tables work well for deal economics, financial fundamentals, leadership, and scoring
- Use `|` for table columns (escape as `\|` inside cell content if needed)
- Keep headers at depth 3 or less (###)
- No bullet points unless explicitly requested — write in paragraphs per canvas conventions
- All hyperlinks must be full HTTP URLs

### Step 3: Link the Canvas in the Thread

Use `slack_send_message` with `thread_ts` pointing to the summary message and
`reply_broadcast: true` to post a thread reply that links to the canvas. This keeps the
channel clean (one main message per tenant) while making the full report one click away.

The thread reply should include:
- A link to the canvas (returned as `canvas_url` from `slack_create_canvas`)
- A brief note on what's in the full report (e.g., "Complete 7-section analysis with deal
  economics, scoring across all six dimensions, and site-specific location analysis")

### When to Use Slack Distribution

Publish to Slack whenever:
- A Slack MCP connector is available (check for `slack_send_message` in available tools)
- The user has not explicitly asked to skip Slack distribution
- A tenant research report has been generated

If no Slack connector is available, skip this section silently — the PDF is sufficient.
If the user asks to publish or share findings, and you haven't already, trigger this flow.
