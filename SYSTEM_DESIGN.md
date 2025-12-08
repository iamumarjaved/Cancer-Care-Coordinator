# Cancer Care Coordinator - System Design

## Overview

An AI-powered clinical decision support system for oncologists. It analyzes patient data, genomic reports, and clinical notes to generate personalized treatment recommendations using multi-agent AI architecture.

## Core Features

| Feature | Description |
|---------|-------------|
| **Patient Management** | CRUD operations with cancer staging, comorbidities, ECOG status |
| **AI Analysis** | Multi-agent system generates treatment plans from patient data |
| **Clinical Notes** | Doctor updates that feed into AI context for better recommendations |
| **Document Processing** | PDF/genomic report parsing and analysis |
| **AI Chat** | Contextual Q&A about specific patients |

## Tech Stack

```
Frontend:  Next.js + TypeScript + TailwindCSS + React Query
Backend:   FastAPI + SQLAlchemy + aiosqlite
AI:        OpenAI GPT-4 + LangChain + Multi-Agent Orchestration
Auth:      Clerk
```

---

## Architecture Diagram

```mermaid
graph TB
    subgraph Client
        UI[Next.js Frontend]
    end

    subgraph Auth
        CL[Clerk Auth]
    end

    subgraph API[FastAPI Backend]
        RT[Routers]
        SV[Services]
        AG[AI Agents]
    end

    subgraph Storage
        DB[(RDB)]
        VS[(Vector Store)]
    end

    subgraph External
        OAI[OpenAI API]
    end

    UI <--> CL
    UI <--> RT
    RT <--> SV
    RT <--> AG
    SV <--> DB
    AG <--> VS
    AG <--> OAI
```

---

## Multi-Agent Architecture

```mermaid
graph TB
    subgraph Input
        PT[Patient Data]
        GR[Genomic Reports]
        CN[Clinical Notes]
        DOC[Documents]
    end

    subgraph Orchestrator
        ORC[Orchestrator Agent]
    end

    subgraph Specialist Agents
        MH[Medical History Agent]
        GN[Genomics Agent]
        TR[Treatment Agent]
        CT[Clinical Trials Agent]
        EV[Evidence Agent]
        PC[Patient Communication Agent]
    end

    subgraph Output
        RP[Comprehensive Treatment Report]
    end

    PT --> ORC
    GR --> ORC
    CN --> ORC
    DOC --> ORC

    ORC --> MH
    ORC --> GN
    ORC --> TR
    ORC --> CT
    ORC --> EV
    ORC --> PC

    MH --> RP
    GN --> RP
    TR --> RP
    CT --> RP
    EV --> RP
    PC --> RP
```

### Agent Responsibilities

| Agent | Role |
|-------|------|
| **Orchestrator** | Coordinates all agents, merges outputs into final report |
| **Medical History** | Analyzes patient history, comorbidities, ECOG status |
| **Genomics** | Interprets mutations, biomarkers, targeted therapy options |
| **Treatment** | Recommends chemotherapy regimens, dosing, scheduling |
| **Clinical Trials** | Matches patient to eligible ongoing trials |
| **Evidence** | Cites guidelines (NCCN, ESMO) and recent publications |
| **Patient Communication** | Generates patient-friendly explanations |

---

## User Flow

```mermaid
flowchart TD
    subgraph Authentication
        A[Landing Page] --> B{Signed In?}
        B -->|No| C[Sign In / Sign Up]
        C --> D[Clerk Auth]
        D --> E[Dashboard]
        B -->|Yes| E
    end

    subgraph Dashboard
        E[Dashboard] --> F[View Stats]
        E --> G[Recent Patients]
        G --> H[Select Patient]
    end

    subgraph Patient List
        E --> I[Patients Page]
        I --> J[Search/Filter]
        J --> H
        I --> K[Add New Patient]
        K --> H
    end

    subgraph Patient Detail Tabs
        H --> L[Patient Detail Page]
        L --> T1[Summary Tab]
        L --> T2[Clinical Notes Tab]
        L --> T3[Genomics Tab]
        L --> T4[Clinical Trials Tab]
        L --> T5[Evidence Tab]
        L --> T6[Treatment Tab]
        L --> T7[Schedule Tab]
        L --> T8[AI Chat Tab]
    end

    subgraph AI Analysis Flow
        L --> M[Run Analysis Button]
        M --> N[Analysis Page]
        N --> O[Orchestrator Starts]
        O --> P[Agents Process in Parallel]
        P --> Q[Stream Results via SSE]
        Q --> R[Display Treatment Report]
    end
```

---

## Patient Detail Tabs

```mermaid
graph LR
    subgraph Patient View
        S[Summary] --> N[Notes]
        N --> G[Genomics]
        G --> T[Trials]
        T --> E[Evidence]
        E --> TR[Treatment]
        TR --> SC[Schedule]
        SC --> C[Chat]
    end

    S -.-> |Patient Info| D1[Demographics, Cancer Details, ECOG]
    N -.-> |Doctor Updates| D2[Clinical Notes from Doctors]
    G -.-> |Mutations| D3[Genomic Report Analysis]
    T -.-> |Matching| D4[Eligible Clinical Trials]
    E -.-> |Guidelines| D5[NCCN/ESMO Evidence]
    TR -.-> |AI Generated| D6[Treatment Recommendations]
    SC -.-> |Calendar| D7[Treatment Schedule & Cycles]
    C -.-> |AI Assistant| D8[Patient-Specific Q&A]
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant D as Doctor
    participant FE as Frontend
    participant API as FastAPI
    participant ORC as Orchestrator
    participant AG as Specialist Agents
    participant LLM as OpenAI

    D->>FE: Click "Run Analysis"
    FE->>API: POST /analysis/start/{patient_id}
    API->>ORC: Initialize with Patient Context

    par Parallel Agent Execution
        ORC->>AG: Medical History Agent
        AG->>LLM: Analyze History
        LLM-->>AG: History Insights
        AG-->>ORC: Section Complete
    and
        ORC->>AG: Genomics Agent
        AG->>LLM: Analyze Mutations
        LLM-->>AG: Genomic Insights
        AG-->>ORC: Section Complete
    and
        ORC->>AG: Treatment Agent
        AG->>LLM: Generate Plan
        LLM-->>AG: Treatment Plan
        AG-->>ORC: Section Complete
    and
        ORC->>AG: Clinical Trials Agent
        AG->>LLM: Match Trials
        LLM-->>AG: Trial Matches
        AG-->>ORC: Section Complete
    and
        ORC->>AG: Evidence Agent
        AG->>LLM: Cite Guidelines
        LLM-->>AG: Evidence Citations
        AG-->>ORC: Section Complete
    end

    ORC->>API: Compile Final Report
    API->>FE: Stream Results (SSE)
    FE->>D: Display Treatment Plan
```

---

## Key Design Decisions

1. **Multi-Agent over Monolithic LLM** - Specialized agents produce more accurate domain-specific outputs
2. **SSE for Analysis** - Real-time streaming shows progress during long-running AI tasks
3. **Clinical Notes Integration** - Doctor observations directly influence AI recommendations
4. **Tab-Based Patient View** - Organized access to different aspects of patient care
5. **React Query** - Automatic caching, polling, and state management for API data
