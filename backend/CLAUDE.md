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
- Scheduled AI helper: Scheduled task that runs on setting period

## Project structure
```
backend/
├── app/                              # FastAPI application source
│   ├── api/                          # HTTP route handlers 
│   │   ├── schema/                   # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── company_data.py
│   │   │   ├── events.py
│   │   │   ├── fn_ai_partner_chat.py # AI 夥伴對話 schemas
│   │   │   ├── ingest.py
│   │   │   ├── roles.py
│   │   │   ├── navigation.py
│   │   │   └── user.py
│   │   ├── auth.py                   # Login / token endpoints
│   │   ├── fn_ai_partner_chat.py     # AI 夥伴對話 endpoints (fn_ai_partner_chat)
│   │   ├── company_data.py           # Company background data CRUD (fn_company_data)
│   │   ├── events.py                 # Security event endpoints
│   │   ├── health.py                 # Liveness / readiness probe
│   │   ├── ingest.py                 # A signle execution point of schedule tasks
│   │   ├── navigation.py             # Dynamic sidebar / nav endpoints
│   │   ├── roles.py                  # Role management (fn_role)
│   │   └── user.py                   # User endpoints
│   ├── config/
│   │   └── settings.py               # Env-driven settings (pydantic-settings)
│   ├── db/
│   │   ├── connector.py              # SQLAlchemy engine / session factory
│   │   └── models/                   # ORM models (tb_* tables)
│   │       ├── analysis.py           # Pipeline / analysis tables
│   │       ├── base.py               # Declarative Base + mixins
│   │       ├── events.py             # Security event tables
│   │       ├── fn_ai_partner_chat.py # tb_conversations · tb_messages · tb_role_ai_partners
│   │       ├── fn_company_data.py    # tb_company_data · tb_ai_partners · tb_partners_company_data
│   │       ├── function_access.py    # Function/folder + role-function ACL
│   │       └── user_role.py          # Users, roles, user-role link
│   ├── services/                     # External integrations
│   │   ├── llm_client.py             # Anthropic API 封裝（單次呼叫，含 retry）
│   │   └── ai_agent.py               # Agentic loop（tool_call 迴圈，上限 5 次）
│   ├── logger_utils/                 # Centralized logging setup
│   │   ├── log_channels.py
│   │   └── logger_config.json
│   ├── middlewares/
│   │   └── request_response_handler.py  # Request/response logging middleware
│   ├── tasks/                           # Background tasks
│   │   └── cybersecurity_scheduler.py   # Periodic job runner (log pull / analysis)
│   ├── utils/
│   │   └── util_store.py             # Shared helpers
│   └── main.py                       # FastAPI app entrypoint (uvicorn target)
│
├── bpBoxAlembic/                     # Alembic migration root
│   ├── versions/                     # Migration revisions (auto-generated)
│   ├── env.py                        # Alembic runtime config
│   ├── script.py.mako                # Migration template
│   └── README
│
├── tests/                            # pytest suite (fixtures + API tests)
│
├── .claude/                          # Claude Code project config
│   ├── agents/                       # Custom subagent definitions
│   └── skills/                       # Project-scoped skills
│
├── alembic.ini                       # Alembic CLI config
├── requirements.txt                  # Exported pin list
├── dockerfile                        # Container build
├── bash.sh                           # Local dev entrypoint
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
   ║  │   ▸ start system_logger                             │  ║
   ║  │   ▸ launch cybersecurity_scheduler                  │  ║
   ║  │   ▸ on shutdown: stop scheduler, log duration       │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Middleware                                          │  ║
   ║  │   • CORSMiddleware  (allow all origin for dev)      │  ║
   ║  │   • RequestResponseHandlerMiddleware  (logging)     │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Routers (app/api/*)                                 │  ║
   ║  │   /auth                                             │  ║
   ║  │   /user                                             │  ║
   ║  │   /roles                                            │  ║
   ║  │   /functions     function-permission catalog        │  ║
   ║  │   /navigation    dynamic sidebar                    │  ║
   ║  │   /company-data  company background data CRUD       │  ║
   ║  │   /events        CRUD on analyzed security events   │  ║
   ║  │   /ingest        one-shot analysis run (test / demo)│  ║
   ║  │   /health        liveness probe                     │  ║
   ║  └──────┬───────────────────────────────────┬──────────┘  ║
   ║         │                                   │             ║
   ║         ▼                                   ▼             ║
   ║  ┌──────────────┐                   ┌──────────────────┐  ║
   ║  │ api/schema   │                   │ utils/util_store │  ║
   ║  │ Pydantic DTOs│                   │  authenticate    │  ║
   ║  │              │                   │  AuthContext     │  ║
   ║  └──────────────┘                   └──────────────────┘  ║
   ║                                                           ║
   ║  ┌───────────────────────────┐                            ║
   ║  │ app/task                  │                            ║
   ║  │   cybersecurity_scheduler │  scheduled fire            ║
   ║  │     • interval job        │                            ║
   ║  │     • shared analyzer ◀───┼─── also invoked by /ingest ║
   ║  │     • LLM client          │                            ║
   ║  └─────────────┬─────────────┘                            ║
   ║                ▼                                          ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Data layer  (app/db)                                │  ║
   ║  │   connector.get_db   →  SQLAlchemy Session          │  ║
   ║  │   models/                                           │  ║
   ║  │     analysis.py        SSB pipeline runs            │  ║
   ║  │     events.py          tb_security_events · history │  ║
   ║  │     user_role.py       tb_users · tb_roles · link   │  ║
   ║  │     function_access.py tb_functions · role-fn ACL   │  ║
   ║  │     fn_company_data.py tb_company_data · ai_partners│  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║                 ┌──────────────────┐                      ║
   ║                 │   PostgreSQL     │                      ║
   ║                 └──────────────────┘                      ║
   ║                                                           ║
   ║  logger_utils  →  structured app/system logs              ║
   ╚═══════════════════════════════════════════════════════════╝
```