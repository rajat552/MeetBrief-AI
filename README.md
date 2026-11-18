# MeetBrief AI — Autonomous Meeting Intelligence

[![Live Demo](https://img.shields.io/badge/Demo-Live_Deployment-emerald?style=for-the-badge&logo=render)](https://meetbrief-ai-j8yo.onrender.com)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![Render](https://img.shields.io/badge/Render-Deployed_Live-brightgreen.svg)](https://meetbrief-ai-j8yo.onrender.com)
[![Tests: 49 Passed](https://img.shields.io/badge/Tests-49%20Passed-brightgreen.svg)](tests/)

> 🌐 **Live Web Application**: [https://meetbrief-ai-j8yo.onrender.com](https://meetbrief-ai-j8yo.onrender.com)  
> **Targeting Problem Statement 05 — Geek Room Global AI Hackathon 2026**  
> Autonomous, evidence-grounded meeting intelligence delivering a scannable, one-page executive briefing (< 600 words) in under 2 minutes.

---

## 🎯 Executive Overview

**MeetBrief AI** is an autonomous multi-agent intelligence platform designed to eliminate executive meeting unpreparedness. By combining **Maxim AI's Bifrost AI Gateway**, **Tavily Web Search**, and a **deterministic multi-tier evidence grounding engine**, MeetBrief AI converts a meeting title, company, and attendee name into an evidence-backed, highly scannable one-page briefing.

Unlike generic LLM wrappers that hallucinate facts or pull outdated company Wikipedia articles, MeetBrief AI enforces strict temporal bounding: **recent intelligence covers strictly the rolling 30 days preceding the scheduled meeting date**.

---

## 🚀 Key Architectural Pillars

### 1. Manual-First Executive Workflow
- **Instant Meeting Prep**: Does not gate usage behind OAuth or mandatory calendar credentials. Enter company name, attendee name, role, and meeting datetime for immediate intelligence generation.
- **Optional Calendar Sync**: Seamlessly supports calendar sync when configured, with graceful fallback to manual input when calendar services are unavailable.

### 2. Exact Rolling 30-Day Research Window
- Mathematical bounding:
  $$\text{Window} = \left[ \min(T_{\text{meeting}}, T_{\text{current}}) - 30\text{d},\; \min(T_{\text{meeting}}, T_{\text{current}}) \right]$$
- **1-Day Query Buffer**: Passes a 1-day widened start date to Tavily search queries ($T_{\text{start}} - 1\text{d}$) to absorb international timezone publication offsets.
- **Strict Post-Retrieval Validation**: Parses ISO 8601 UTC timestamps from retrieved articles, admitting only findings strictly within the 30-day window. Future-dated and undated results are rejected from recent sections.

### 3. 5-Branch Disjoint Multi-Agent Research
1. **Branch 1: Static Company Background**: Business model, core products, target market, competitive moat (deliberately not date-filtered).
2. **Branch 2: Attendee Dossier**: Verified title, career history, public quotes, recent talks, and shared affinities.
3. **Branch 3: 30-Day News & Developments**: Funding rounds, strategic partnerships, regulatory filings, and major press.
4. **Branch 4: 30-Day Product Launches**: Feature releases, version changelogs, platform integrations, and developer announcements.
5. **Branch 5: 30-Day Hiring Signals**: Active openings, departmental expansion trends, and strategic leadership hires.
- **Concurrency-Safe Deduplication**: URL and content-hash tracking via `asyncio.Lock` prevents duplicate queries and conflicting findings across parallel agents.

### 4. Deterministic Evidence Grounding Engine
- **Honest Verification Heuristic**: Explicitly rejects false claims of "zero hallucinations" or "100% ground truth".
- **Multi-Factor Grounding**:
  - Entity matching across named participants and organizations.
  - Semantic token containment heuristics against extracted source passages.
  - 3-tier domain weighting (Tier 1: Company domains/SEC; Tier 2: Reputable press; Tier 3: Aggregators).
  - Explicit contradiction detection between competing reports.
- **4 Traceable Claim Statuses**:
  - `VERIFIED_PRIMARY`: Entity match + high containment in Tier 1 source passage.
  - `REPORTED_SECONDARY`: Sourced from reputable industry journalism.
  - `UNVERIFIED`: Low containment or uncorroborated assertion.
  - `CONFLICTED`: Discrepant metrics or conflicting factual claims across sources.

### 5. Maxim Bifrost AI Gateway Integration
- **Primary Route**: Routes completions via OpenAI-compatible endpoint `http://localhost:8080/v1` (`maximhq/bifrost:v2.3.1`).
- **Authentication**: Passes Virtual Key via `x-bf-vk: sk-bf-*` header.
- **Application Dimension**: Tags requests with `x-bf-dim-app: meetbrief-ai`.
- **Response-Header Telemetry**: Automatically extracts `x-bifrost-request-id`, `x-bifrost-latency-ms`, and `x-bifrost-upstream-latency-ms`.
- **Direct-Provider Fallback**: If Bifrost is offline or occupied by an incompatible service (e.g. Apache), automatically falls back to direct provider SDKs (OpenAI / Groq) and explicitly signals `fallback_direct` in the UI and telemetry.

### 6. Safe Server-Sent Events (SSE) Streaming
- **Zero Thought Leakage**: Strictly prohibits emission of `agent_thought`, `private_thinking`, or internal prompt scratchpads.
- **Safe Event Protocol**: Emits `gateway_status`, `stage_update`, `tool_status`, `source_discovered`, `claims_verified`, `streaming`, and `complete`.

### 7. Scannable One-Page Briefing Format (< 600 Words)
- Engineered for rapid 2-minute executive scanning:
  1. Header Bar: Attendee dossier, verified title, meeting objective.
  2. Card 1: Static Company Foundation & Business Model.
  3. Card 2: 30-Day News & Material Developments.
  4. Card 3: 30-Day Product Releases & Roadmaps.
  5. Card 4: 30-Day Hiring & Strategic Expansion Signals.
  6. Card 5: Top 3 High-Impact Discussion Hooks.
  7. Card 6: Top 3 Potential Risk Blindspots.
  8. Quarantined Drawer: Undated signals segregated from verified 30-day intelligence.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Executive User]) -->|1. Manual Input: Company, Attendee, Date| UI[React 18 SPA / Vite]
    
    subgraph FastAPI Backend [MeetBrief AI Core Server]
        API[/api/briefings/generate - Safe SSE]
        Planner[Shared Query Planner\nTemporal Window Clamping]
        Dedup[(Deduplication Register\nasyncio.Lock Safe)]
        
        subgraph MultiAgent [5 Parallel Research Agents]
            A1[Branch 1: Static Background]
            A2[Branch 2: Attendee Dossier]
            A3[Branch 3: 30-Day News]
            A4[Branch 4: 30-Day Launches]
            A5[Branch 5: 30-Day Hiring]
        end
        
        TavilyEngine[Tavily Search Engine\nDate Bounding + Tiering]
        Verifier[Evidence Grounding Engine\nPassage Mapping & Conflict Check]
        Synthesizer[Executive Synthesizer\nOne-Page < 600 Words]
    end

    subgraph InferenceLayer [AI Gateway & Fallback Layer]
        Bifrost[Maxim Bifrost Gateway :8080\nVirtual Key + Telemetry Headers]
        DirectLLM[Direct Provider Fallback\nOpenAI / Groq]
    end

    UI --> API
    API --> Planner
    Planner --> MultiAgent
    MultiAgent --> TavilyEngine
    TavilyEngine <--> Dedup
    MultiAgent --> Verifier
    Verifier --> Synthesizer
    Synthesizer --> Bifrost
    Bifrost -.->|If Offline| DirectLLM
    Synthesizer -->|Safe SSE Events| UI
```

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker (optional, for running local Bifrost AI Gateway)
- Tavily API Key (free tier at [tavily.com](https://tavily.com))

### 1. Clone & Set Up Backend

```bash
# Clone the repository
git clone https://github.com/rajat552/MeetBrief-AI.git
cd MeetBrief-AI

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your TAVILY_API_KEY and OPENAI_API_KEY / GROQ_API_KEY
```

### 2. Build the Frontend UI

```bash
cd ui
npm install
npm run build
cd ..
```

### 3. Launch MeetBrief AI

```bash
# Start the unified backend server
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser to start preparing meeting briefings!

### 4. (Optional) Run Maxim Bifrost AI Gateway via Docker

```bash
docker run -d \
  -p 8080:8080 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e BIFROST_VIRTUAL_KEYS='[{"id":"sk-bf-meetbrief-prod","name":"MeetBrief AI"}]' \
  maximhq/bifrost:v2.3.1
```
*Note: If Bifrost is offline or port 8080 is unavailable, MeetBrief AI automatically runs in direct-provider fallback mode.*

---

## 🧪 Comprehensive Verification Suite

MeetBrief AI includes 44 unit, integration, and security tests covering all system layers:

```bash
pytest tests/ -v
```

### Verified Test Matrix:
| Category | File | Tests | Status |
|:---|:---|:---:|:---:|
| Gateway & Routing | `tests/test_gateway.py` | 7 | ✅ Passed |
| Configuration & Validation | `tests/test_config.py` | 4 | ✅ Passed |
| Deduplication Register | `tests/test_dedup.py` | 3 | ✅ Passed |
| Domain Schemas | `tests/test_models.py` | 4 | ✅ Passed |
| Temporal Query Planning | `tests/test_planner.py` | 4 | ✅ Passed |
| Tavily Search & Bounding | `tests/test_tavily_engine.py` | 2 | ✅ Passed |
| Evidence Grounding | `tests/test_verifier.py` | 5 | ✅ Passed |
| Executive Synthesis | `tests/test_synthesizer.py` | 1 | ✅ Passed |
| LangGraph Orchestration | `tests/test_agent_graph.py` | 5 | ✅ Passed |
| FastAPI & SSE Endpoints | `tests/test_api_endpoints.py` | 3 | ✅ Passed |
| Security & Zero Leakage | `tests/test_security.py` | 11 | ✅ Passed |
| **Total Test Suite** | **All Modules** | **49** | **100% Pass** |

---

## 📋 Hackathon Problem Statement 05 Compliance

| Requirement | Reference Repo | MeetBrief AI (Target) | Compliance |
|:---|:---:|:---:|:---:|
| **Primary Workflow** | Mandatory Google Calendar OAuth | Instant Manual Input (Company, Person, Date) | 100% Compliant |
| **Date Window** | Unbounded general search | Strict 30-day window relative to meeting date | 100% Compliant |
| **Research Architecture** | Single sequential agent | 5 disjoint parallel agents with deduplication | 100% Compliant |
| **Evidence Grounding** | None (Unverified LLM text) | Deterministic 4-status claim verification | 100% Compliant |
| **AI Gateway** | None (Direct Anthropic calls) | Maxim Bifrost Gateway with Virtual Keys & Fallback | 100% Compliant |
| **Output Length** | 4-5 page verbose dump | Scannable One-Page Executive Brief (< 600 words) | 100% Compliant |
| **Privacy / Streaming** | Emits raw agent thoughts | Safe SSE stream; zero private thought leakage | 100% Compliant |

---

## 📄 License

Dual-licensed under the [MIT License](LICENSE) &copy; 2026 MeetBrief AI Contributors. Target implementation for Geek Room Global AI Hackathon 2026.
