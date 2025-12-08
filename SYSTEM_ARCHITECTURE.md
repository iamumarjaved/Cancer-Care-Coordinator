# Cancer Care Coordinator - System Architecture & Flow Diagram

## Table of Contents
1. [Detailed Component Diagram](#1-detailed-component-diagram)
2. [AI Analysis Pipeline](#2-ai-analysis-pipeline)
3. [AWS Infrastructure](#3-aws-infrastructure)
4. [API Endpoints Reference](#4-api-endpoints-reference)
5. [External Integrations](#5-external-integrations)

---

## 1. Detailed Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND LAYER                                    │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Next.js 14 Application                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │ │
│  │  │    Pages     │  │  Components  │  │    Hooks     │  │   API Client     │   │ │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────────┤   │ │
│  │  │ /            │  │ PatientCard  │  │ usePatients  │  │ axios instance   │   │ │
│  │  │ /patients    │  │ AddPatient   │  │ useAnalysis  │  │ with Clerk token │   │ │
│  │  │ /patients/[id]│ │ EditPatient  │  │ useChat      │  │ interceptors     │   │ │
│  │  │ /analysis    │  │ AnalysisTab  │  │ useGenomics  │  │                  │   │ │
│  │  │ /sign-in     │  │ ChatWindow   │  │ useTrials    │  │ Base URL:        │   │ │
│  │  │ /sign-up     │  │ ProceduresTab│  │ useTreatment │  │ /api/v1          │   │ │
│  │  │ /api/health  │  │ ClinicalNotes│  │ useProcedures│  │                  │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘   │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                        Clerk Authentication                              │  │ │
│  │  │  • ClerkProvider (wraps entire app)                                     │  │ │
│  │  │  • useAuth() hook for JWT tokens                                        │  │ │
│  │  │  • SignedIn / SignedOut components                                      │  │ │
│  │  │  • Middleware protection for routes                                      │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ REST API + SSE + WebSocket
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    BACKEND LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                            FastAPI Application                                  │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                           API ROUTERS                                    │  │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │  │ │
│  │  │  │  /patients  │ │  /analysis  │ │   /chat     │ │  /genomics  │       │  │ │
│  │  │  │  CRUD ops   │ │  AI pipeline│ │  Q&A bot    │ │  mutations  │       │  │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │  │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │  │ │
│  │  │  │  /trials    │ │  /evidence  │ │ /treatment  │ │   /notes    │       │  │ │
│  │  │  │  matching   │ │  guidelines │ │  planning   │ │  clinical   │       │  │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │  │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────────┐       │  │ │
│  │  │  │  /cycles    │ │ /procedures │ │     /notifications          │       │  │ │
│  │  │  │  treatment  │ │  scheduling │ │     email alerts            │       │  │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────────────────┘       │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                          SERVICES LAYER                                  │  │ │
│  │  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                  │  │ │
│  │  │  │  LLMService   │ │ PatientService│ │  EmailService │                  │  │ │
│  │  │  │  OpenAI GPT-4 │ │  CRUD + DB    │ │  SendGrid     │                  │  │ │
│  │  │  └───────────────┘ └───────────────┘ └───────────────┘                  │  │ │
│  │  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                  │  │ │
│  │  │  │ VectorStore   │ │ PubMedService │ │ TrialsService │                  │  │ │
│  │  │  │ ChromaDB/RAG  │ │ Literature    │ │ ClinicalTrials│                  │  │ │
│  │  │  └───────────────┘ └───────────────┘ └───────────────┘                  │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                      MULTI-AGENT AI SYSTEM                               │  │ │
│  │  │                                                                          │  │ │
│  │  │                    ┌─────────────────────────┐                           │  │ │
│  │  │                    │   OrchestratorAgent     │                           │  │ │
│  │  │                    │   (Workflow Controller) │                           │  │ │
│  │  │                    └───────────┬─────────────┘                           │  │ │
│  │  │           ┌────────────────────┼────────────────────┐                    │  │ │
│  │  │           │          │         │         │          │                    │  │ │
│  │  │           ▼          ▼         ▼         ▼          ▼                    │  │ │
│  │  │  ┌─────────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────────┐        │  │ │
│  │  │  │  Medical    ││Genomics ││ Trials  ││Evidence ││ Treatment   │        │  │ │
│  │  │  │  History    ││ Agent   ││ Agent   ││ Agent   ││ Agent       │        │  │ │
│  │  │  │  Agent      ││         ││         ││         ││             │        │  │ │
│  │  │  └─────────────┘└─────────┘└─────────┘└─────────┘└─────────────┘        │  │ │
│  │  │                                                                          │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                            │
            ┌───────────────────────────────┼───────────────────────────────┐
            │                               │                               │
            ▼                               ▼                               ▼
┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
│      DATA LAYER       │      │   EXTERNAL SERVICES   │      │    AWS SERVICES       │
│  ┌─────────────────┐  │      │  ┌─────────────────┐  │      │  ┌─────────────────┐  │
│  │   PostgreSQL    │  │      │  │    OpenAI API   │  │      │  │ Secrets Manager │  │
│  │   (RDS)         │  │      │  │    GPT-4o-mini  │  │      │  │ (API Keys)      │  │
│  │                 │  │      │  └─────────────────┘  │      │  └─────────────────┘  │
│  │  • patients     │  │      │  ┌─────────────────┐  │      │  ┌─────────────────┐  │
│  │  • analyses     │  │      │  │    SendGrid     │  │      │  │ EFS Storage     │  │
│  │  • chat_msgs    │  │      │  │    Email API    │  │      │  │ (ChromaDB)      │  │
│  │  • procedures   │  │      │  └─────────────────┘  │      │  └─────────────────┘  │
│  │  • cycles       │  │      │  ┌─────────────────┐  │      │  ┌─────────────────┐  │
│  │  • notes        │  │      │  │  Clerk Auth     │  │      │  │ CloudWatch      │  │
│  │  • events       │  │      │  │  OAuth/JWT      │  │      │  │ (Logs)          │  │
│  └─────────────────┘  │      │  └─────────────────┘  │      │  └─────────────────┘  │
│  ┌─────────────────┐  │      │  ┌─────────────────┐  │      │  ┌─────────────────┐  │
│  │   ChromaDB      │  │      │  │   PubMed API    │  │      │  │ ACM Certificate │  │
│  │   (Vector DB)   │  │      │  │   Literature    │  │      │  │ (SSL/TLS)       │  │
│  └─────────────────┘  │      │  └─────────────────┘  │      │  └─────────────────┘  │
│                       │      │  ┌─────────────────┐  │      │                       │
│                       │      │  │ClinicalTrials   │  │      │                       │
│                       │      │  │.gov API         │  │      │                       │
│                       │      │  └─────────────────┘  │      │                       │
└───────────────────────┘      └───────────────────────┘      └───────────────────────┘
```

---

## 2. AI Analysis Pipeline

### Multi-Agent Workflow

```
                                    ┌────────────────────────────┐
                                    │     Analysis Request       │
                                    │  patient_id, user_questions│
                                    └─────────────┬──────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────┐
                              │        ORCHESTRATOR AGENT          │
                              │   Controls workflow, manages state │
                              └────────────────────┬───────────────┘
                                                   │
        ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
        │                                          │                                          │
        ▼                                          │                                          │
┌───────────────────┐                              │                              ┌───────────────────┐
│ STEP 1: INIT      │                              │                              │ STEP 7: SYNTHESIS │
│ Load patient data │                              │                              │ Compile final     │
│ Progress: 0-5%    │                              │                              │ report            │
└───────────────────┘                              │                              │ Progress: 90-100% │
                                                   │                              └───────────────────┘
                                                   │                                          ▲
        ┌──────────────────────────────────────────┼──────────────────────────────────────────┤
        │                                          │                                          │
        ▼                                          ▼                                          │
┌───────────────────┐              ┌───────────────────────────┐              ┌───────────────────┐
│ STEP 2: MEDICAL   │              │ STEP 3: GENOMICS AGENT    │              │ STEP 6: TREATMENT │
│ HISTORY AGENT     │              │                           │              │ AGENT             │
│                   │              │ • Analyze mutations       │              │                   │
│ • Analyze clinical│              │ • Identify actionable     │              │ • Generate        │
│   picture         │              │   variants                │              │   recommendations │
│ • Extract key     │              │ • Map to therapies        │              │ • Score options   │
│   findings        │              │ • Check OncoKB database   │              │ • Add rationale   │
│                   │              │                           │              │                   │
└───────────────────┘              └───────────────────────────┘              └───────────────────┘
                                                   │
        ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
        │                                          │                                          │
        ▼                                          ▼                                          ▼
┌───────────────────┐              ┌───────────────────────────┐              ┌───────────────────┐
│ STEP 4: TRIALS    │              │ STEP 5: EVIDENCE AGENT    │              │ OUTPUT            │
│ AGENT             │              │                           │              │                   │
│                   │              │ • Search NCCN guidelines  │              │ • Summary         │
│ • Search Clinical │              │ • Query PubMed           │              │ • Key findings    │
│   Trials.gov      │              │ • Retrieve ESMO recs     │              │ • Treatment plan  │
│ • Match eligibility│             │ • Grade evidence levels  │              │ • Clinical trials │
│ • Score relevance │              │                           │              │ • Evidence refs   │
│                   │              │                           │              │ • Sources used    │
└───────────────────┘              └───────────────────────────┘              └───────────────────┘
```

---

## 3. AWS Infrastructure

### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS CLOUD                                           │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              VPC (10.0.0.0/16)                                  │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    PUBLIC SUBNETS (10.0.1.0/24, 10.0.2.0/24)             │  │ │
│  │  │                                                                          │  │ │
│  │  │    ┌───────────────────────────────────────────────────────────────┐    │  │ │
│  │  │    │              Application Load Balancer (ALB)                   │    │  │ │
│  │  │    │                                                                │    │  │ │
│  │  │    │   • healthcare.umarjaved.me                                   │    │  │ │
│  │  │    │   • Port 80 (HTTP) → Redirect to 443                          │    │  │ │
│  │  │    │   • Port 443 (HTTPS) → Target Groups                          │    │  │ │
│  │  │    │   • ACM Certificate for SSL/TLS                               │    │  │ │
│  │  │    │                                                                │    │  │ │
│  │  │    │   Routing Rules:                                              │    │  │ │
│  │  │    │   • /* (default) ──────────► Frontend Target Group            │    │  │ │
│  │  │    │   • /api/*, /health, /docs ─► Backend Target Group            │    │  │ │
│  │  │    └───────────────────────────────────────────────────────────────┘    │  │ │
│  │  │                                                                          │  │ │
│  │  │    ┌─────────────────┐                                                  │  │ │
│  │  │    │   NAT Gateway   │  (For private subnet internet access)           │  │ │
│  │  │    └─────────────────┘                                                  │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                          │                                     │ │
│  │                                          ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                   PRIVATE SUBNETS (10.0.10.0/24, 10.0.11.0/24)          │  │ │
│  │  │                                                                          │  │ │
│  │  │    ┌─────────────────────────────────────────────────────────────────┐  │  │ │
│  │  │    │                      ECS CLUSTER (Fargate)                       │  │  │ │
│  │  │    │                                                                  │  │  │ │
│  │  │    │   ┌────────────────────────┐   ┌────────────────────────┐       │  │  │ │
│  │  │    │   │   Frontend Service     │   │   Backend Service      │       │  │  │ │
│  │  │    │   │                        │   │                        │       │  │  │ │
│  │  │    │   │   • Task: Next.js      │   │   • Task: FastAPI      │       │  │  │ │
│  │  │    │   │   • CPU: 256           │   │   • CPU: 512           │       │  │  │ │
│  │  │    │   │   • Memory: 512 MB     │   │   • Memory: 1024 MB    │       │  │  │ │
│  │  │    │   │   • Port: 3000         │   │   • Port: 8000         │       │  │  │ │
│  │  │    │   │   • Desired: 1         │   │   • Desired: 1         │       │  │  │ │
│  │  │    │   │                        │   │                        │       │  │  │ │
│  │  │    │   │   Environment:         │   │   Environment:         │       │  │  │ │
│  │  │    │   │   • NODE_ENV           │   │   • DATABASE_URL       │       │  │  │ │
│  │  │    │   │   • CLERK_*            │   │   • OPENAI_API_KEY     │       │  │  │ │
│  │  │    │   │   • API_URL            │   │   • SENDGRID_*         │       │  │  │ │
│  │  │    │   └────────────────────────┘   │   • CLERK_*            │       │  │  │ │
│  │  │    │                                │   • LANGSMITH_*        │       │  │  │ │
│  │  │    │                                └────────────────────────┘       │  │  │ │
│  │  │    └─────────────────────────────────────────────────────────────────┘  │  │ │
│  │  │                                                                          │  │ │
│  │  │    ┌──────────────────────────┐   ┌───────────────────────────────┐     │  │ │
│  │  │    │      RDS PostgreSQL      │   │        EFS Storage            │     │  │ │
│  │  │    │                          │   │                               │     │  │ │
│  │  │    │   • Engine: PostgreSQL 15│   │   • ChromaDB vector store    │     │  │ │
│  │  │    │   • Instance: db.t3.micro│   │   • Persistent embeddings    │     │  │ │
│  │  │    │   • Storage: 20 GB       │   │   • Mounted to backend task  │     │  │ │
│  │  │    │   • Multi-AZ: No         │   │                               │     │  │ │
│  │  │    │                          │   │                               │     │  │ │
│  │  │    │   Tables:                │   │                               │     │  │ │
│  │  │    │   • patients             │   │                               │     │  │ │
│  │  │    │   • analysis_results     │   │                               │     │  │ │
│  │  │    │   • chat_messages        │   │                               │     │  │ │
│  │  │    │   • treatment_cycles     │   │                               │     │  │ │
│  │  │    │   • treatment_procedures │   │                               │     │  │ │
│  │  │    │   • clinical_notes       │   │                               │     │  │ │
│  │  │    └──────────────────────────┘   └───────────────────────────────┘     │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           SUPPORTING SERVICES                                 │   │
│  │                                                                               │   │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │   │
│  │   │  Secrets Mgr    │  │      ECR        │  │  CloudWatch     │              │   │
│  │   │                 │  │                 │  │                 │              │   │
│  │   │  Secrets:       │  │  Repositories:  │  │  Log Groups:    │              │   │
│  │   │  • DATABASE_URL │  │  • backend      │  │  • /ecs/backend │              │   │
│  │   │  • OPENAI_KEY   │  │  • frontend     │  │  • /ecs/frontend│              │   │
│  │   │  • CLERK_*      │  │                 │  │                 │              │   │
│  │   │  • SENDGRID_*   │  │                 │  │                 │              │   │
│  │   └─────────────────┘  └─────────────────┘  └─────────────────┘              │   │
│  │                                                                               │   │
│  │   ┌─────────────────┐  ┌─────────────────┐                                   │   │
│  │   │  ACM (SSL)      │  │  S3 (Terraform) │                                   │   │
│  │   │                 │  │                 │                                   │   │
│  │   │  Certificate:   │  │  State Bucket:  │                                   │   │
│  │   │  healthcare.    │  │  cancer-care-   │                                   │   │
│  │   │  umarjaved.me   │  │  terraform-state│                                   │   │
│  │   └─────────────────┘  └─────────────────┘                                   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. API Endpoints Reference

### Patient Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients` | List patients with pagination |
| POST | `/api/v1/patients` | Create new patient |
| GET | `/api/v1/patients/{id}` | Get patient details |
| PUT | `/api/v1/patients/{id}` | Update patient |
| DELETE | `/api/v1/patients/{id}` | Delete patient |
| PATCH | `/api/v1/patients/{id}/status` | Update status (active/closed) |
| GET | `/api/v1/patients/{id}/timeline` | Get event timeline |

### AI Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analysis/run` | Start AI analysis |
| GET | `/api/v1/analysis/{id}/status` | Get analysis status |
| GET | `/api/v1/analysis/{id}/stream` | SSE progress stream |
| GET | `/api/v1/analysis/{id}/results` | Get final results |
| POST | `/api/v1/analysis/{id}/stop` | Cancel analysis |

### Clinical Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients/{id}/genomics` | Get genomic report |
| GET | `/api/v1/patients/{id}/trials` | Get matched trials |
| GET | `/api/v1/patients/{id}/evidence` | Get evidence summary |
| GET | `/api/v1/patients/{id}/treatment` | Get treatment plan |

### Chat & Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/{id}/message` | Send chat message |
| GET | `/api/v1/chat/{id}/history` | Get chat history |
| POST | `/api/v1/patients/{id}/clinical-notes` | Add clinical note |
| GET | `/api/v1/patients/{id}/clinical-notes` | List clinical notes |

### Treatment Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/treatment-cycles/patients/{id}` | Create treatment cycle |
| GET | `/api/v1/treatment-cycles/patients/{id}` | List cycles |
| POST | `/api/v1/treatment-cycles/{id}/procedures` | Add procedure |
| POST | `/api/v1/treatment-cycles/{id}/procedures/generate` | Generate schedule |
| GET | `/api/v1/patients/{id}/procedures/calendar` | Calendar view |

---

## 5. External Integrations

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICE INTEGRATIONS                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   OPENAI                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Model: GPT-4o-mini (128k context)                                        │  │
│  │  Usage: All AI completions, agent reasoning, chat responses               │  │
│  │  API Key: OPENAI_API_KEY (from Secrets Manager)                           │  │
│  │                                                                            │  │
│  │  Request Flow:                                                            │  │
│  │  Backend ─────► OpenAI API ─────► Response                                │  │
│  │         └─ System prompt + Patient context + User query                   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    CLERK                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Type: OAuth 2.0 / JWT Authentication                                     │  │
│  │  Domain: clerk.umarjaved.me                                               │  │
│  │                                                                            │  │
│  │  Flow:                                                                    │  │
│  │  User ──► Clerk Sign-in ──► JWT Token ──► Frontend ──► Backend            │  │
│  │                                            │                              │  │
│  │                                            └─► Bearer token in headers    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  SENDGRID                                        │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Type: Email Delivery Service                                             │  │
│  │                                                                            │  │
│  │  Triggers:                                                                │  │
│  │  • Analysis completion ──► Send results summary email                     │  │
│  │  • Patient file opened ──► Notification email                             │  │
│  │  • Patient file closed ──► Notification email                             │  │
│  │                                                                            │  │
│  │  From: SENDGRID_FROM_EMAIL                                                │  │
│  │  To: Doctor's email (from Clerk user profile)                             │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PUBMED & CLINICALTRIALS.GOV                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  PubMed API (Free)                     ClinicalTrials.gov API (Free)      │  │
│  │  ├─ Search medical literature          ├─ Search clinical trials          │  │
│  │  ├─ Retrieve abstracts                 ├─ Filter by condition/phase       │  │
│  │  └─ Evidence for treatment recs        └─ Match patient eligibility       │  │
│  │                                                                            │  │
│  │  Used by: EvidenceAgent                Used by: ClinicalTrialsAgent       │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                             LANGSMITH                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Type: LLM Observability & Tracing                                        │  │
│  │                                                                            │  │
│  │  Features:                                                                │  │
│  │  • Trace all LLM calls                                                    │  │
│  │  • Debug agent workflows                                                  │  │
│  │  • Monitor token usage                                                    │  │
│  │  • Evaluate response quality                                              │  │
│  │                                                                            │  │
│  │  Enabled: LANGSMITH_TRACING_ENABLED=true                                  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

The Cancer Care Coordinator is a full-stack AI-powered healthcare application with:

- **Frontend**: Next.js 14 with Clerk auth, React Query, and Tailwind CSS
- **Backend**: FastAPI with multi-agent AI system using OpenAI GPT-4
- **Database**: PostgreSQL (RDS) + ChromaDB (EFS) for vector storage
- **Infrastructure**: AWS ECS Fargate, ALB, VPC, Secrets Manager
- **External Services**: OpenAI, Clerk, SendGrid, PubMed, ClinicalTrials.gov

The system enables doctors to manage cancer patients, run AI-powered analyses, chat with an AI assistant, and schedule treatment procedures - all with real-time updates and email notifications.
