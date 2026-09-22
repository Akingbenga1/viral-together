# Progressive Update — Major Codebase Flaws

No — there’s more under the hood. The biggest flaws:

### Security (worst)
- Many important APIs have **no auth** — collaborations, promotions, document generate/download, analytics, AI agents, web search. Anyone who can reach the API can change data or pull other users’ stuff.
- **Documents/downloads** take `user_id` from the request or a filename — classic IDOR / possible path-traversal risk.
- **JWT/password crypto is duplicated** — hardcoded secret in some files, env secret in others; bcrypt in one place, pbkdf2 in another. Easy to mint or verify with the wrong scheme.
- **CORS is wide open** (`*` + credentials). Rate limiting barely covers anything.

### Architecture / reliability
- **Huge god files** (documents ~2k lines, strategy service ~2k, big Celery task modules). Hard to change safely.
- **Celery is fragile** — mix of async ORM, raw `psycopg2`, and `asyncio.run` inside thread workers; tasks can get lost (`acks_late=False`).
- **Auth helpers are inconsistent** — several `get_current_user` / `verify_token` versions; some routes even have `TODO: add auth`.

### Quality / ops
- Almost **no real automated tests** (mostly manual `.http` scripts).
- Errors often leak `str(e)` to clients; SQL `echo=True` logs everything.
- Some “delete account” style endpoints **don’t actually delete**.
- Config can start with missing secrets; password rules on register are weak.

**Bottom line:** feature surface is large, but the security model is incomplete and uneven — newer AI/docs/collab paths are the riskiest.

---

# Capability check (live, 2026-09-21)

Checked against API at `http://127.0.0.1:8001`, Postgres `viral_together`, Redis, Ollama, and Celery worker `viral-together@DESKTOP-ONED2Q7`.

## Surface size
- **227** OpenAPI paths / **265** operations
- **42** DB tables with real seed/test data (e.g. 26 users, 21 influencers, 13 businesses, 41 promotions, 55 generated docs, 361 notifications)

## Infrastructure
| Service | Result |
|---------|--------|
| API (uvicorn :8001) | UP |
| Postgres | UP |
| Ollama | UP |
| Redis | Was **DOWN** mid-session (container exited); restarted `redis` Docker container → OK |
| Celery worker | Reconnected after Redis restart → ping OK |

## Feature capability matrix

| Feature | In API? | Live smoke | Notes |
|---------|---------|------------|-------|
| Auth (register/token) | Yes | Token endpoint validates (422 without body) | Working surface |
| Countries | Yes | **200** list | OK |
| Public influencers / fans | Yes | **200** `/api/influencers/public` | OK; DB has fans requests |
| Businesses nearby (new) | Yes | Route present | Needs auth + influencer id |
| Documents | Yes | **200** list | Data present; auth weak (known flaw) |
| AI agents | Yes | **200** list | 10 agents in DB |
| Enhanced AI agents | Yes | **200** capabilities + data-sources | Reports web_search active |
| Subscriptions | Yes | **200** `/subscription/plans` | OK |
| Social platforms | Yes | **200** `/social-media-platforms/list` | OK |
| Blog | Yes | **200** `/blog/blogs` | OK (3 posts) |
| Downloads catalog | Yes | **200** `/api/downloads` | OK |
| Location nearby (biz/inf) | Yes | **422** without lat/lng | Endpoint alive, params required |
| Promotions | Yes | **401** | Auth required on list |
| Notifications | Yes | **401** | Auth required |
| Coaching | Yes | **401** | Auth required |
| Admin / roles | Yes | **401** | Auth required |
| Analytics | Yes | **401** | Auth required |
| Collaborations | Yes | **500** | Broken: UUID returned as UUID type, schema expects string |
| Chat | Yes | POST-only (405 on GET) | Routes exist |
| Recommendations / growth | Yes | Method/path sensitive | Present; not smoke-tested end-to-end with AI |
| Rate cards | Yes | No simple list root | Nested under influencer/platform paths |
| Background emails / AI tasks | Yes (Celery) | Worker online after Redis fix | Depends on Redis staying up |

## Broken / fragile findings from this check
1. **`GET /collaborations` returns 500** — Pydantic `ResponseValidationError` on `uuid` field (UUID vs string). Feature is registered and DB has rows, but list API is broken.
2. **Redis dropped** while Celery was running — worker spent ~20 minutes reconnecting; background emails/AI jobs would have failed during that window.
3. Many features are **present and gated by 401** — capability exists but was not fully exercised with a real login token in this pass.
4. Root paths are inconsistent (`/blog/` 404 vs `/blog/blogs` 200) — easy to think a feature is missing when the path is just non-obvious.

## Verdict
Most major product areas are **wired and discoverable** in OpenAPI, and several public/read paths return real data. The clearest live failure is **collaborations list (500)**. Background-task capability is **fragile** because it depends on Redis staying up. Full auth-protected flows (create collab, generate docs as user, coaching, analytics) still need authenticated end-to-end testing.
