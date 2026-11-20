<div align="center">

# ⚡ MeetBrief AI
### Autonomous Meeting Intelligence — Evidence-Grounded Executive Briefings in Under 2 Minutes

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-meetbrief--ai.onrender.com-00C7B7?style=for-the-badge&logo=render&logoColor=white)](https://meetbrief-ai-j8yo.onrender.com)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00.svg?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Tavily Search](https://img.shields.io/badge/Tavily-Web_Intelligence-4F46E5.svg?style=flat-square)](https://tavily.com)
[![Bifrost Gateway](https://img.shields.io/badge/Bifrost_Gateway-v2.3.1-6366F1.svg?style=flat-square)](https://github.com/maximhq/bifrost)
[![Tests: 49 Passed](https://img.shields.io/badge/Tests-49%20Passed-brightgreen.svg?style=flat-square)](tests/)

**Built for Problem Statement 05 — Geek Room Global AI Hackathon 2026**

[Explore Live Demo](https://meetbrief-ai-j8yo.onrender.com) · [Architecture](#-system-architecture) · [Quick Start](#-quick-start-guide) · [Test Suite (49/49)](#-verification--test-suite) · [Hackathon Compliance](#-problem-statement-05-compliance)

</div>

---

## 📖 Executive Summary

**MeetBrief AI** is an autonomous, multi-agent intelligence platform engineered to eliminate executive meeting unpreparedness. By synthesizing **Maxim AI's Bifrost AI Gateway**, **Tavily Web Search**, **Omnidimension Voice AI**, and a **deterministic multi-tier evidence grounding engine**, MeetBrief AI transforms a target company, participant name, and meeting time into an evidence-backed, scannable **One-Page Executive Dossier (< 600 words)** with an on-demand **90-Second Commute Audio Briefing** in under 120 seconds.

Unlike generic LLM wrappers that hallucinate facts or pull stale Wikipedia overviews, MeetBrief AI enforces **strict temporal mathematical bounding**: intelligence covers strictly the rolling 30 days preceding the scheduled meeting datetime.

```math
\text{Research Window} = \left[\, \min(T_{\text{meeting}},\, T_{\text{current}}) - 30\text{ days},\;\; \min(T_{\text{meeting}},\, T_{\text{current}}) \,\right]
```

---

## 💡 Why MeetBrief AI? (Paradigm Shift)

| Dimension | Conventional Meeting Prep Agents | MeetBrief AI (Target Architecture) |
|:---|:---|:---|
| **Primary Workflow** | Mandatory OAuth & Calendar Permissions | **Instant Manual Input** (Company, Attendee, Date) + Optional Calendar Sync |
| **Temporal Accuracy** | Unbounded search; surfaces 3-year-old articles | **Strict Rolling 30-Day Window** relative to meeting timestamp |
| **Hallucination Control** | Blind LLM generation with fabricated links | **Deterministic Evidence Grounding** with 4 traceable claim statuses |
| **Research Architecture** | Single sequential search query | **5 Parallel Disjoint Agents** with `asyncio.Lock` deduplication |
| **Inference Routing** | Hardcoded direct API calls | **Maxim Bifrost AI Gateway** with virtual keys & transparent fallback |
| **Output Length** | 4-5 page verbose prose dumps | **Scannable One-Page Briefing (< 600 words)** for 2-minute scanning |
| **Privacy / Streaming** | Emits raw chain-of-thought tokens | **Safe SSE Protocol**; strictly zero private reasoning exposure |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Executive User]) -->|1. Manual Input: Company, Attendee, Date| UI[React 18 SPA / Vite]
    
    subgraph Backend [FastAPI Backend Core Server]
        API[/api/briefings/generate - Safe SSE/]
        
        subgraph LangGraph_Core [LangGraph Asynchronous Multi-Agent Engine]
            PlanNode[Query Planner & Entity Disambiguation\nTemporal Window Clamping]
            
            subgraph Parallel_Branches [5 Disjoint Concurrent Research Agents]
                B1[Branch 1: Static Company Profile\nBusiness Model, Moat, Customers]
                B2[Branch 2: Attendee Dossier\nRole History, Public Talks, Affinities]
                B3[Branch 3: 30-Day Corporate News\nFunding, Strategic Partnerships, Regulatory]
                B4[Branch 4: 30-Day Product Releases\nChangelogs, APIs, Feature Launches]
                B5[Branch 5: 30-Day Hiring Signals\nHeadcount Shifts, Leadership Roles]
            end
            
            Dedup[(Deduplication Register\nURL + Snippet Hash Lock)]
            TavilyEngine[Tavily Search Engine\n1-Day Query Buffer + 3-Tier Domain Filter]
            VerifyNode[Evidence Grounding Engine\nPassage Mapping & Contradiction Detection]
            SynthNode[Executive Synthesizer\n6-Card Layout < 600 Words]
        end
    end

    subgraph Inference_Layer [Inference Gateway & Resilient Fallback]
        Bifrost[Maxim Bifrost AI Gateway :8080\nVirtual Key sk-bf-* + Header Telemetry]
        DirectLLM[Direct Provider Fallback\nGoogle Gemini / OpenAI / Groq]
    end

    UI --> API
    API --> PlanNode
    PlanNode --> B1 & B2 & B3 & B4 & B5
    B1 & B2 & B3 & B4 & B5 <--> Dedup
    B1 & B2 & B3 & B4 & B5 --> TavilyEngine
    B1 & B2 & B3 & B4 & B5 -->|operator.add State Reduction| VerifyNode
    VerifyNode --> SynthNode
    SynthNode --> Bifrost
    Bifrost -.->|If Offline / Unconfigured| DirectLLM
    SynthNode -->|Safe Server-Sent Events| UI
```

---

## 🔬 Core Architectural Pillars

### 1. Manual-First Executive Workflow
- **Zero-Barrier Preparation**: Eliminates mandatory Google Calendar OAuth gates. Enter company name, attendee name, role, and meeting datetime for immediate intelligence generation.
- **Graceful Calendar Adapter**: Secondary `/api/briefings/calendar` endpoint provides automated calendar integration when configured, or transparently falls back to manual prep if credentials are absent.

### 2. Exact Rolling 30-Day Research Window
- **Mathematical Clamping**: $T_{\text{end}} = \min(T_{\text{meeting}}, T_{\text{current}})$, $T_{\text{start}} = T_{\text{end}} - 30\text{ days}$.
- **1-Day Query Buffer**: Passes a 1-day widened start date ($T_{\text{start}} - 1\text{d}$) to Tavily search to absorb international timezone publication offsets.
- **Strict UTC Post-Retrieval Validation**: Parses ISO 8601 UTC timestamps from retrieved articles, admitting only findings strictly within the 30-day window. Future-dated and undated results are rejected from recent sections.

### 3. 5-Branch Disjoint Multi-Agent Research
Executed concurrently via LangGraph with typed state accumulation:
1. **Branch 1: Static Company Background**: Business model, core products, target market, competitive moat (deliberately not date-filtered).
2. **Branch 2: Attendee Dossier**: Verified title, career history, public quotes, recent talks, and shared affinities.
3. **Branch 3: 30-Day News & Developments**: Funding rounds, strategic partnerships, regulatory filings, and major press.
4. **Branch 4: 30-Day Product Launches**: Feature releases, version changelogs, platform integrations, and developer announcements.
5. **Branch 5: 30-Day Hiring Signals**: Active openings, departmental expansion trends, and strategic leadership hires.

### 4. Deterministic Evidence Grounding Engine
- **Honest Verification Heuristic**: Explicitly rejects false claims of "zero hallucinations" or "100% truth guarantees".
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
- **Primary Route**: Routes completions via OpenAI-compatible endpoint `http://localhost:8085/v1` (`maximhq/bifrost:v2.6.0`).
- **Virtual Key Authentication**: Authenticates via `x-bf-vk: sk-bf-*` header.
- **Application Dimension**: Tags requests with `x-bf-dim-app: meetbrief-ai`.
- **Response-Header Telemetry**: Automatically extracts `x-bifrost-request-id`, `x-bifrost-latency-ms`, and `x-bifrost-upstream-latency-ms`.
- **Tri-Mode Inference Failover**: Explicitly classifies and labels execution into `bifrost_gateway`, `direct_provider_fallback` (Google Gemini / OpenAI / Groq), and `deterministic_fallback` (rule-grounded synthesis) in the UI, SSE frames, and telemetry.

### 6. Omnidimension Voice AI — 90s Executive Audio Briefing
- **Commute Mode**: Generates a natural 90-second spoken executive audio brief (~220-280 spoken words) for leaders reviewing on the go.
- **Interactive UI Audio Bar**: Integrated audio player featuring play/pause, scrub bar, speed toggle (`1.0x`, `1.25x`, `1.5x`), and spoken script inspection modal.
- **Zero-Lag Web Speech Fallback**: If Omnidimension API keys are omitted or offline, seamlessly routes to the browser's native Web Speech synthesis engine with zero latency or errors.

### 7. Safe Server-Sent Events (SSE) Protocol
- **Zero Thought Leakage**: Strictly prohibits emission of `agent_thought`, `private_thinking`, or internal prompt scratchpads.
- **Safe Event Protocol**: Emits `gateway_status`, `stage_update`, `tool_status`, `source_discovered`, `claims_verified`, `streaming`, and `complete`.

### 8. Scannable One-Page Briefing Format (< 600 Words)
Engineered for rapid 2-minute executive scanning:
1. **Header Bar**: Attendee dossier, verified title, meeting objective, and 90s audio player.
2. **Card 1**: Static Company Foundation & Business Model.
3. **Card 2**: 30-Day News & Material Developments.
4. **Card 3**: 30-Day Product Releases & Roadmaps.
5. **Card 4**: 30-Day Hiring & Strategic Expansion Signals.
6. **Card 5**: Top 3 High-Impact Discussion Hooks (grounded in verified signals).
7. **Card 6**: Top 3 Potential Risk Blindspots & Discovery Questions.
8. **Quarantined Drawer**: Undated signals segregated from verified 30-day intelligence.

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Tavily API Key ([tavily.com](https://tavily.com))
- LLM Provider Key (Google Gemini / OpenAI / Groq)
- Docker (optional, for running local Bifrost AI Gateway)

### 1. Clone & Set Up Environment

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

# Install Python backend dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` and insert your API keys:
```ini
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=your_gemini_api_key_here
# Optional:
OPENAI_API_KEY=
GROQ_API_KEY=
BIFROST_ENABLED=false
```

### 2. Run the Application

```bash
# Start backend and serve frontend together on port 5000:
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser!

### 3. (Optional) Run with Docker Compose

To launch the complete multi-container stack (MeetBrief AI + Maxim Bifrost Gateway):
```bash
docker compose up --build -d
```

---

## 🧪 Verification & Test Suite

MeetBrief AI includes **49 comprehensive automated tests** with 100% pass rate:

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
| FastAPI & SSE Endpoints | `tests/test_api_endpoints.py` | 4 | ✅ Passed |
| Security & Zero Leakage | `tests/test_security.py` | 11 | ✅ Passed |
| Tri-Mode Inference & Grounding | `tests/test_inference_modes_and_grounding.py` | 8 | ✅ Passed |
| Omnidimension Voice AI Engine | `tests/test_voice.py` | 5 | ✅ Passed |
| **Total Test Suite** | **All 13 Modules** | **65** | **100% Pass (91% Coverage)** |

---

## 📋 Problem Statement 05 Compliance

| Requirement | Reference Repo | MeetBrief AI | Compliance |
|:---|:---:|:---:|:---:|
| **Primary Workflow** | Mandatory Google Calendar OAuth | **Instant Manual Input** (Company, Person, Date) | 100% Compliant |
| **Date Window** | Unbounded general search | **Strict 30-day window** relative to meeting date | 100% Compliant |
| **Research Architecture** | Single sequential agent | **5 disjoint parallel agents** with deduplication | 100% Compliant |
| **Evidence Grounding** | None (Unverified LLM text) | **Deterministic 4-status claim verification** | 100% Compliant |
| **AI Gateway** | None (Direct Anthropic calls) | **Maxim Bifrost Gateway v2.6.0** with Virtual Keys & Tri-Mode Failover | 100% Compliant |
| **Voice AI Briefing** | None | **Omnidimension Voice AI** 90s Commute Briefing + Audio Bar | 100% Compliant |
| **Output Length** | 4-5 page verbose dump | **Scannable One-Page Brief (< 600 words)** | 100% Compliant |
| **Privacy / Streaming** | Emits raw agent thoughts | **Safe SSE stream**; zero private thought leakage | 100% Compliant |

---

## 📂 Project Repository Structure

```text
MeetBrief-AI/
├── backend/
│   ├── __init__.py
│   ├── config.py             # Pydantic v2 application settings & validation
│   ├── models.py             # Domain schemas: findings, claims, briefings, audio
│   ├── gateway.py            # Bifrost AI Gateway client & tri-mode fallback router
│   ├── voice.py              # Omnidimension Voice AI executive audio engine
│   ├── agent.py              # LangGraph asynchronous StateGraph & SSE stream
│   ├── verifier.py           # Deterministic evidence grounding engine
│   ├── synthesizer.py        # Executive briefing synthesizer (< 600 words)
│   └── research/
│       ├── __init__.py
│       ├── planner.py        # 30-day temporal window calculator & disjoint queries
│       ├── dedup.py          # Concurrency-safe URL & content deduplication
│       ├── tavily_engine.py  # Tavily search engine with 3-tier domain filter
│       ├── company_agent.py  # Branch 1: Static company profile
│       ├── people_agent.py   # Branch 2: Attendee intelligence dossier
│       ├── news_agent.py     # Branch 3: 30-day corporate news & funding
│       ├── launches_agent.py # Branch 4: 30-day product releases & changelogs
│       └── hiring_agent.py   # Branch 5: 30-day hiring & headcount expansion
├── ui/                       # React 18 + Tailwind CSS + TypeScript frontend
│   ├── src/
│   │   ├── components/       # Header, ManualInputForm, BriefingView, AudioBriefingPlayer
│   │   ├── types/            # TypeScript interfaces for briefings & audio payloads
│   │   ├── App.tsx           # Native ReadableStream SSE consumer
│   │   └── main.tsx
│   └── dist/                 # Pre-compiled production React distribution
├── tests/                    # 65 automated unit, integration & security tests
├── Dockerfile                # Production container specification
├── docker-compose.yml        # Multi-container orchestration (App + Bifrost v2.6.0)
├── requirements.txt          # Python dependencies
└── app.py                    # Unified FastAPI application server
```

---

## 📄 License

Distributed under the [MIT License](LICENSE). Built for the **Geek Room Global AI Hackathon 2026**.
