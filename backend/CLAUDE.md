# MP-box
This is a project under development to handle AI workers to help company's workflow

## Feature
A server that holds AI helpers to improve human work, currently building an AI helper that schedule checks cybersecurity logs from SSB server

## Framework
- Server: Build by FastAPI framework with basic server functions
  - Authenticate(auth)
  - User management(user)
  - User permission control(Role)
  - Cybersecurity report management(events)
  - Frontend display controller(navigation)
  - AI partner chat / config / tools (fn_ai_partner_*)
  - Cybersecurity expert settings (fn_expert_setting)
  - Company background data (fn_company_data)
  - User feedback collection (fn_feedback)
- Scheduled AI helper: APScheduler-driven jobs
  - `haiku_job` — interval-based per-chunk log analysis (Claude Haiku)
  - `sonnet_job` — daily aggregation of chunk events (Claude Sonnet)
  - `settings_sync` — periodic reload of `tb_expert_settings` into runtime cache

## Project structure
```
backend/
├── app/                              # FastAPI application source
│   ├── api/                          # HTTP route handlers
│   │   ├── schema/                   # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── company_data.py
│   │   │   ├── events.py
│   │   │   ├── fn_ai_partner_chat.py    # AI partner chat schemas
│   │   │   ├── fn_ai_partner_config.py  # AI partner config schemas
│   │   │   ├── fn_ai_partner_tool.py    # AI tool schemas
│   │   │   ├── fn_expert_setting.py     # Cybersecurity expert setting schemas
│   │   │   ├── fn_feedback.py           # User feedback schemas
│   │   │   ├── ingest.py
│   │   │   ├── navigation.py
│   │   │   ├── pagination.py            # Shared paginated list envelope
│   │   │   ├── roles.py
│   │   │   └── user.py
│   │   ├── auth.py                   # Login / token endpoints
│   │   ├── company_data.py           # Company background data CRUD (fn_company_data)
│   │   ├── events.py                 # Security event endpoints
│   │   ├── fn_ai_partner_chat.py     # AI partner chat endpoints
│   │   ├── fn_ai_partner_config.py   # AI partner config management endpoints
│   │   ├── fn_ai_partner_tool.py     # AI tool management endpoints (HTTP tool registry)
│   │   ├── fn_expert_setting.py      # Cybersecurity expert single-row settings (GET/PUT only)
│   │   ├── fn_feedback.py            # User feedback collection
│   │   ├── health.py                 # Liveness / readiness probe
│   │   ├── ingest.py                 # One-shot execution of scheduled task
│   │   ├── navigation.py             # Dynamic sidebar / nav endpoints
│   │   ├── roles.py                  # Role management (fn_role)
│   │   └── user.py                   # User endpoints
│   ├── config/
│   │   └── settings.py               # Env-driven settings (pydantic-settings)
│   ├── db/
│   │   ├── connector.py              # SQLAlchemy engine / session factory
│   │   └── models/                   # ORM models (tb_* tables)
│   │       ├── analysis.py               # Pipeline / chunk-result tables
│   │       ├── base.py                   # Declarative Base + mixins
│   │       ├── events.py                 # Security event tables
│   │       ├── fn_ai_partner_chat.py     # tb_conversations · tb_messages · tb_role_ai_partners
│   │       ├── fn_ai_partner_config.py   # tb_ai_partners · tb_ai_partner_configs · partner-tool link
│   │       ├── fn_ai_partner_tool.py     # tb_tools · tb_tool_body_params
│   │       ├── fn_company_data.py        # tb_company_data
│   │       ├── fn_expert_setting.py      # tb_expert_settings (single-row config)
│   │       ├── fn_feedback.py            # tb_feedbacks
│   │       ├── function_access.py        # tb_functions + role-function ACL
│   │       └── user_role.py              # tb_users · tb_roles · user-role link
│   ├── services/                     # External integrations
│   │   ├── llm_client.py             # Anthropic API wrapper (single-shot, retry)
│   │   └── ai_agent.py               # Agentic loop (tool_call loop, max 5)
│   ├── logger_utils/                 # Centralized logging setup
│   │   ├── log_channels.py
│   │   └── logger_config.json
│   ├── middlewares/
│   │   └── request_response_handler.py  # Request/response logging middleware
│   ├── tasks/                           # Cybersecurity pipeline modules
│   │   ├── claude_flash.py              # Haiku per-chunk event extraction
│   │   ├── claude_pro.py                # Sonnet daily event aggregation
│   │   ├── haiku_task.py                # Haiku orchestrator (pull -> preagg -> analyze -> persist)
│   │   ├── pro_task.py                  # Sonnet orchestrator (group -> aggregate -> upsert)
│   │   ├── log_preaggregator.py         # FortiGate log summarization (token-saving)
│   │   ├── ssb_client.py                # SSB REST API client
│   │   └── ssb_search.py                # Canonical SSB search expression
│   ├── utils/
│   │   ├── crypto.py                 # AES-GCM helpers for stored secrets
│   │   └── util_store.py             # Shared helpers (authenticate, AuthContext, ...)
│   ├── scheduler.py                  # APScheduler integration + runtime settings cache
│   └── main.py                       # FastAPI app entrypoint (uvicorn target)
│
├── bpBoxAlembic/                     # Alembic migration root
│   ├── versions/                     # Migration revisions (auto-generated)
│   ├── env.py                        # Alembic runtime config
│   ├── script.py.mako                # Migration template
│   └── README
│
├── tests/                            # pytest suite (fixtures + API tests)
├── logs/                             # Runtime log output
│
├── alembic.ini                       # Alembic CLI config
├── pyproject.toml                    # Project metadata + dependencies (uv)
├── uv.lock                           # uv-managed lock file
├── requirements.txt                  # Exported pin list
├── dockerfile                        # Container build
├── bash.sh                           # Local dev entrypoint
├── workflow.md                       # Cybersecurity pipeline workflow doc
├── CLAUDE.md                         # Project instructions for Claude Code
└── README.md                         # Project instructions for human
```

## Project Workflow
```
                       ┌──────────────────────────┐
                       │  Frontend       :5173    │
                       └────────────┬─────────────┘
                                    │ HTTP + JWT
                                    ▼
   ╔═══════════════════════════════════════════════════════════╗
   ║              FastAPI app  (app/main.py)                   ║
   ║                                                           ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Lifespan                                            │  ║
   ║  │   - start system_logger                             │  ║
   ║  │   - start APScheduler (app/scheduler.py)            │  ║
   ║  │   - on shutdown: stop scheduler, log duration       │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Middleware                                          │  ║
   ║  │   - CORSMiddleware  (allow http://localhost:5173)   │  ║
   ║  │   - RequestResponseHandlerMiddleware  (logging)     │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Routers (app/api/*)                                 │  ║
   ║  │   /auth                 login / token               │  ║
   ║  │   /user                 user CRUD + profile         │  ║
   ║  │   /roles                role management (fn_role)   │  ║
   ║  │   /navigation           dynamic sidebar             │  ║
   ║  │   /company-data         company background CRUD     │  ║
   ║  │   /ai-partner-chat      AI partner chat             │  ║
   ║  │   /ai-partner-config    AI partner config mgmt      │  ║
   ║  │   /tool                 AI tool registry mgmt       │  ║
   ║  │   /api/expert           expert single-row settings  │  ║
   ║  │   /feedback             user feedback collection    │  ║
   ║  │   /events               CRUD on analyzed events     │  ║
   ║  │   /ingest               one-shot pipeline run       │  ║
   ║  │   /health               liveness probe              │  ║
   ║  └──────┬───────────────────────────────────┬──────────┘  ║
   ║         │                                   │             ║
   ║         ▼                                   ▼             ║
   ║  ┌──────────────┐                   ┌──────────────────┐  ║
   ║  │ api/schema   │                   │ utils/util_store │  ║
   ║  │ Pydantic DTOs│                   │  authenticate    │  ║
   ║  │              │                   │  AuthContext     │  ║
   ║  └──────────────┘                   └──────────────────┘  ║
   ║                                                           ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ app/scheduler.py  (APScheduler BackgroundScheduler) │  ║
   ║  │   - settings_sync  reload tb_expert_settings cache  │  ║
   ║  │   - haiku_job      interval -> app/tasks/haiku_task │  ║
   ║  │   - sonnet_job     daily cron -> app/tasks/pro_task │  ║
   ║  └─────────────┬───────────────────────────────────────┘  ║
   ║                ▼                                          ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ app/tasks  (cybersecurity pipeline)                 │  ║
   ║  │   ssb_client + ssb_search   -> pull SSB logs        │  ║
   ║  │   log_preaggregator         -> FortiGate summarize  │  ║
   ║  │   claude_flash (Haiku)      -> per-chunk extract    │  ║
   ║  │   claude_pro   (Sonnet)     -> daily aggregate      │  ║
   ║  │   shared analyzer  <-- also invoked by /ingest      │  ║
   ║  └─────────────┬───────────────────────────────────────┘  ║
   ║                ▼                                          ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Data layer  (app/db)                                │  ║
   ║  │   connector.get_db   ->  SQLAlchemy Session         │  ║
   ║  │   models/                                           │  ║
   ║  │     analysis.py            pipeline / chunk runs    │  ║
   ║  │     events.py              tb_security_events       │  ║
   ║  │     user_role.py           tb_users · tb_roles      │  ║
   ║  │     function_access.py     tb_functions · ACL       │  ║
   ║  │     fn_expert_setting.py   tb_expert_settings (1)   │  ║
   ║  │     fn_company_data.py     tb_company_data          │  ║
   ║  │     fn_ai_partner_*.py     AI partner / tool tables │  ║
   ║  │     fn_feedback.py         tb_feedbacks             │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║                 ┌──────────────────┐                      ║
   ║                 │   PostgreSQL     │                      ║
   ║                 └──────────────────┘                      ║
   ║                                                           ║
   ║  logger_utils  ->  structured app/system logs             ║
   ╚═══════════════════════════════════════════════════════════╝
```
