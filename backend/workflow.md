# MP-Box Cybersecurity Workflow

```
   ┌────────────────────────────┐
   │  SSB Cybersecurity Log     │
   │  Server   (external)       │
   └──────────────┬─────────────┘
                  │ pull window of new logs
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │  Trigger sources                                       │
   │   ┌──────────────────────────────┐                     │
   │   │ app/service/                 │  scheduled tick     │
   │   │   cybersecurity_scheduler.py │  (production)       │
   │   └──────────────┬───────────────┘                     │
   │                  │                                     │
   │   ┌──────────────┴───────────────┐                     │
   │   │ POST /ingest  (FastAPI)      │  one-shot run       │
   │   │   manual fire for testing /  │  (testing / demo)   │
   │   │   demo of the analysis flow  │                     │
   │   └──────────────┬───────────────┘                     │
   └──────────────────┼─────────────────────────────────────┘
                      │ raw log batch
                      ▼
   ┌────────────────────────────────────────────────────────┐
   │  Ingest stage                                          │
   │  ─ normalize fields (host, ts, severity, payload)      │
   │  ─ persist raw rows                                    │
   └──────────────┬─────────────────────────────────────────┘
                  │ normalized rows
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │  LLM Analyzer (cybersecurity helper)                   │
   │  ─ prompt: "is this log line an incident?"             │
   │  ─ structured output (JSON / tool use)                 │
   │  ─ classify · score · summarize · suggest action       │
   └──────────────┬─────────────────────────────────────────┘
                  │ verdict + metadata
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │  PostgreSQL  (app/db/models)                           │
   │   • analysis.py            → pipeline run / SSB batch  │
   │   • events.py              → tb_security_events        │
   │                              tb_event_history          │
   │   • user_role.py           → assignee / actor          │
   │   • function_access.py     → who may see which event   │
   └──────────────┬─────────────────────────────────────────┘
                  │ analyzed events available for triage
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │  FastAPI  /events  router      (CRUD on analyzed data) │
   │   GET    /events                list + filter          │
   │   GET    /events/{id}           detail                 │
   │   PATCH  /events/{id}           status / assignee      │
   │   GET    /events/{id}/history   audit trail            │
   │   POST   /events/{id}/history   append note / action   │
   └──────────────┬─────────────────────────────────────────┘
                  │ HTTPS + JWT
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │  Frontend SPA  :5173                                   │
   │  analyst dashboard → triage → resolve / escalate       │
   └────────────────────────────────────────────────────────┘

         ╭──────────── feedback loop ────────────╮
         │ analyst PATCH / history POST writes   │
         │ back to tb_event_history → future LLM │
         │ prompts can use prior verdicts        │
         ╰───────────────────────────────────────╯
```

Two ways to fire the analysis pipeline, one persistence:
- **Production**: `cybersecurity_scheduler` ticks on interval → pull → analyze → persist.
- **Testing / demo**: `POST /ingest` runs the same pipeline once on demand.
- **Always**: `/events` exposes CRUD over the analyzed rows for the SPA.

## Service Structure

```
                       ┌──────────────────────────┐
                       │  Browser / SPA  :5173    │
                       └────────────┬─────────────┘
                                    │ HTTPS + JWT
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
   ║  │   • CORSMiddleware  (allow http://localhost:5173)   │  ║
   ║  │   • RequestResponseHandlerMiddleware  (logging)     │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║  ┌─────────────────────────────────────────────────────┐  ║
   ║  │ Routers (app/api/*)                                 │  ║
   ║  │   /auth        login / token                        │  ║
   ║  │   /user /users profile · /auth/me                   │  ║
   ║  │   /roles       role mgmt (fn_role)                  │  ║
   ║  │   /functions   function-permission catalog          │  ║
   ║  │   /navigation  dynamic sidebar                      │  ║
   ║  │   /events      CRUD on analyzed security events     │  ║
   ║  │   /ingest      one-shot analysis run (test / demo)  │  ║
   ║  │   /health      liveness probe                       │  ║
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
   ║  │     analysis.py       SSB pipeline runs             │  ║
   ║  │     events.py         tb_security_events · history  │  ║
   ║  │     user_role.py      tb_users · tb_roles · link    │  ║
   ║  │     function_access.py tb_functions · role-fn ACL   │  ║
   ║  └────────────────────────┬────────────────────────────┘  ║
   ║                           ▼                               ║
   ║                 ┌──────────────────┐                      ║
   ║                 │   PostgreSQL     │                      ║
   ║                 └──────────────────┘                      ║
   ║                                                           ║
   ║  logger_utils  →  structured app/system logs              ║
   ╚═══════════════════════════════════════════════════════════╝
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │ External: SSB log server │
                       │ (pulled by scheduler or  │
                       │  by manual /ingest call) │
                       └──────────────────────────┘
```

Three execution paths, one data layer:
- **Scheduled pull** (background): lifespan starts `cybersecurity_scheduler` → pull SSB → analyze → write events.
- **Manual pull** (request): `POST /ingest` → same analyzer → write events. Used for testing / demo.
- **Triage** (request): SPA → `/events` CRUD → ORM → PostgreSQL.
