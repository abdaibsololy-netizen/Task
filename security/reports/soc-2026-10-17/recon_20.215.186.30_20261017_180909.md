# تقرير استطلاع التطبيق — http://20.215.186.30

- **البداية:** 2026-10-17T18:08:23+00:00
- **النهاية:** 2026-10-17T18:09:09+00:00
- **نقاط النهاية المكتشفة:** 124
- **الملاحظات:** high:13 | medium:1 | low:1

## خريطة نقاط النهاية

| المسار |ethods | الملاحظات |
|---|---|---|
| `/` | GET | catch-all (SPA) |
| `/api/activities` | GET |  |
| `/api/ai/analyze-comprehensive` | POST |  |
| `/api/ai/recommendations` | POST |  |
| `/api/ai/status` | GET |  |
| `/api/ai/summarize` | POST |  |
| `/api/ai/test` | POST |  |
| `/api/alerts` | GET, POST |  |
| `/api/alerts/dead-letter` | GET |  |
| `/api/alerts/dead-letter/{dlq_id}/retry` | POST |  |
| `/api/alerts/ingest` | POST |  |
| `/api/alerts/mitre/navigator-layer` | GET | 200 بلا مصادقة |
| `/api/alerts/stats/summary` | GET | 200 بلا مصادقة |
| `/api/alerts/webhook` | POST |  |
| `/api/alerts/{alert_id}` | DELETE, GET, PUT | 200 بلا مصادقة |
| `/api/alerts/{alert_id}/evidence` | GET | 200 بلا مصادقة |
| `/api/alerts/{alert_id}/investigate` | POST |  |
| `/api/alerts/{alert_id}/investigation-status/{task_id}` | GET | 200 بلا مصادقة |
| `/api/alerts/{alert_id}/notes` | POST |  |
| `/api/alerts/{alert_id}/verdict` | PUT |  |
| `/api/analytics/artifacts` | GET |  |
| `/api/analytics/artifacts/analyze` | POST |  |
| `/api/analytics/artifacts/similarity-references` | POST |  |
| `/api/analytics/behavior/observations` | GET |  |
| `/api/analytics/network/analyze` | POST |  |
| `/api/analytics/network/observations` | GET |  |
| `/api/analytics/network/suricata` | POST |  |
| `/api/analytics/network/zeek` | POST |  |
| `/api/auth/api-keys` | GET, POST |  |
| `/api/auth/api-keys/{key_id}` | DELETE |  |
| `/api/auth/change-password` | POST |  |
| `/api/auth/login` | POST |  |
| `/api/auth/me` | GET, PUT |  |
| `/api/auth/mfa/activate` | POST |  |
| `/api/auth/mfa/disable` | POST |  |
| `/api/auth/mfa/setup` | POST |  |
| `/api/auth/mfa/status` | GET |  |
| `/api/auth/register` | POST |  |
| `/api/auth/token` | POST |  |
| `/api/auth/users` | GET |  |
| `/api/auth/users/{user_id}` | DELETE, PUT |  |
| `/api/context/assets/{hostname}` | PUT |  |
| `/api/context/identities/{identity}` | PUT |  |
| `/api/context/indicators` | POST |  |
| `/api/detection-rules` | GET, POST |  |
| `/api/detection-rules/export` | GET |  |
| `/api/detection-rules/hot-reload` | POST |  |
| `/api/detection-rules/sync` | POST |  |
| `/api/detection-rules/{rule_id}` | GET, PUT |  |
| `/api/detection-rules/{rule_id}/revisions` | GET |  |
| `/api/detection-rules/{rule_id}/rollback` | POST |  |
| `/api/detection-rules/{rule_id}/transition` | POST |  |
| `/api/detection-rules/{rule_id}/validate` | POST |  |
| `/api/dispatch/connectors` | GET, PUT |  |
| `/api/dlp/status` | GET |  |
| `/api/docs` | - | 200 (html/text) |
| `/api/evaluation/guard` | GET |  |
| `/api/evaluation/guard/run` | POST |  |
| `/api/evaluation/run` | POST |  |
| `/api/evaluation/runs` | GET |  |
| `/api/evidence/{evidence_id}` | DELETE |  |
| `/api/findings` | GET |  |
| `/api/findings/{finding_id}/status` | PUT |  |
| `/api/incidents` | GET |  |
| `/api/incidents/mitre/coverage` | GET |  |
| `/api/incidents/{incident_id}` | GET |  |
| `/api/incidents/{incident_id}/explain` | POST |  |
| `/api/incidents/{incident_id}/notes` | POST |  |
| `/api/incidents/{incident_id}/recompute` | POST |  |
| `/api/incidents/{incident_id}/status` | PUT |  |
| `/api/incidents/{public_id}/contain` | POST |  |
| `/api/incidents/{public_id}/contain/plan` | GET |  |
| `/api/incidents/{public_id}/dispatch` | POST |  |
| `/api/incidents/{public_id}/evidence` | GET, POST |  |
| `/api/incidents/{public_id}/timeline` | GET |  |
| `/api/intel/decay/run` | POST |  |
| `/api/intel/feeds/import` | POST |  |
| `/api/intel/indicators` | GET |  |
| `/api/policies` | GET, PUT |  |
| `/api/response/actions` | GET, POST |  |
| `/api/response/actions/catalog` | GET |  |
| `/api/response/actions/{public_id}` | GET |  |
| `/api/response/actions/{public_id}/approve` | POST |  |
| `/api/response/actions/{public_id}/cancel` | POST |  |
| `/api/response/actions/{public_id}/reject` | POST |  |
| `/api/response/actions/{public_id}/rollback` | POST |  |
| `/api/response/audit` | GET |  |
| `/api/response/automation/halt` | POST |  |
| `/api/response/automation/resume` | POST |  |
| `/api/response/automation/status` | GET |  |
| `/api/response/connectors/health` | GET |  |
| `/api/response/metrics` | GET |  |
| `/api/response/playbooks` | GET |  |
| `/api/response/playbooks/reload` | POST |  |
| `/api/response/playbooks/{playbook_id}/simulate` | POST |  |
| `/api/response/safeguards` | GET, POST |  |
| `/api/response/safeguards/{safeguard_id}` | DELETE |  |
| `/api/retention` | GET |  |
| `/api/retention/run` | POST |  |
| `/api/settings` | GET, PUT |  |
| `/api/settings/test-connection` | POST |  |
| `/api/threat-intel/abuseipdb/{ip_address}` | GET |  |
| `/api/threat-intel/alienvault/{ip_address}` | GET |  |
| `/api/threat-intel/bulk-check` | POST |  |
| `/api/threat-intel/bulk-lookup` | POST |  |
| `/api/threat-intel/cache/clear` | POST |  |
| `/api/threat-intel/cache/info` | GET |  |
| `/api/threat-intel/cache/stats` | GET |  |
| `/api/threat-intel/check-domain` | POST |  |
| `/api/threat-intel/check-ip` | POST |  |
| `/api/threat-intel/check-ip/{ip_address}` | GET |  |
| `/api/threat-intel/check-url` | POST |  |
| `/api/threat-intel/lookup` | POST |  |
| `/api/threat-intel/virustotal/{ip_address}` | GET |  |
| `/api/v1/audit/verify` | GET |  |
| `/api/v1/reports/compliance-posture` | GET |  |
| `/api/v1/reports/executive-summary` | GET |  |
| `/api/v1/system/soc-health` | GET |  |
| `/api/v1/triage/{incident_id}` | POST |  |
| `/health` | GET | 200 بلا مصادقة |
| `/health/deep` | GET | 200 بلا مصادقة |
| `/livez` | GET | 200 بلا مصادقة |
| `/ready` | GET | catch-all (SPA) |
| `/readyz` | GET | 200 بلا مصادقة |

## الملاحظات

| # | الخطورة | النوع | الملاحظة | المسار |
|---|---|---|---|---|
| 1 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /api/alerts/mitre/navigator-layer | `/api/alerts/mitre/navigator-layer` |
| 2 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /api/alerts/stats/summary | `/api/alerts/stats/summary` |
| 3 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1 | `/api/alerts/1` |
| 4 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1/evidence | `/api/alerts/1/evidence` |
| 5 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1/investigation-status/1 | `/api/alerts/1/investigation-status/1` |
| 6 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /health | `/health` |
| 7 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /health/deep | `/health/deep` |
| 8 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /livez | `/livez` |
| 9 | HIGH | Broken Access Control | نقطة API ترجع بيانات بلا مصادقة: /readyz | `/readyz` |
| 10 | HIGH | Broken Access Control | المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) | `/health` |
| 11 | HIGH | Broken Access Control | المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) | `/health/deep` |
| 12 | HIGH | Broken Access Control | المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) | `/livez` |
| 13 | HIGH | Broken Access Control | المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) | `/readyz` |
| 14 | MEDIUM | API | مواصفة OpenAPI/Swagger منشورة | `` |
| 15 | LOW | API | صفحة توثيق API منشورة | `` |

### 1. نقطة API ترجع بيانات بلا مصادقة: /api/alerts/mitre/navigator-layer `[API-001]`
- **الخطورة:** high
- **المسار:** `/api/alerts/mitre/navigator-layer`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"name":"Smart SOC — Cumulative Detections","versions":{"attack":"14","navigator":"4.9.1","layer":"4.5"},"domain":"enterprise-attack","description":"Auto-generated from Smart SOC alert corpus","techniques":[{"techniqueID":"T1078","score":726,"comment":"T1078","tactic":"Defense Evasion","enabled":tru
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 2. نقطة API ترجع بيانات بلا مصادقة: /api/alerts/stats/summary `[API-001]`
- **الخطورة:** high
- **المسار:** `/api/alerts/stats/summary`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"total_alerts":3614,"severity_breakdown":{"medium":131,"info":87,"critical":79,"high":1279,"low":2038},"analysis_status":{"with_ai_analysis":2010,"with_threat_intel":3614,"with_file_hash_indicator":3,"with_ueba_anomaly":284,"pending_investigation":1604},"true_positive_analysis":{"true_positive":1,"
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 3. نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1 `[API-001]`
- **الخطورة:** high
- **المسار:** `/api/alerts/1`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"alert_name":"Suspicious encoded PowerShell launched by Microsoft Word","severity":"critical","category":"windows","source_ip":null,"destination_ip":null,"hostname":"WIN-SERVER-2022","source_port":null,"destination_port":null,"network_protocol":null,"destination_domain":null,"dns_query":null,"url":
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 4. نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1/evidence `[API-001]`
- **الخطورة:** high
- **المسار:** `/api/alerts/1/evidence`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"alert_id":1,"wazuh_id":"manual-wazuh-powershell-001","raw_event":null,"full_log":null,"normalized_event":{"schema_version":"soc-ocsf-subset/1.0","metadata":{"product":"wazuh","source":"wazuh_alert","original_event_uid":"manual-wazuh-powershell-001"},"time":"2026-08-24T12:00:00+00:00","class_name":
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 5. نقطة API ترجع بيانات بلا مصادقة: /api/alerts/1/investigation-status/1 `[API-001]`
- **الخطورة:** high
- **المسار:** `/api/alerts/1/investigation-status/1`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"task_id":"1","alert_id":1,"state":"PENDING"}
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 6. نقطة API ترجع بيانات بلا مصادقة: /health `[API-001]`
- **الخطورة:** high
- **المسار:** `/health`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"status":"healthy","database":"healthy","wazuh":{"manager":"configured","indexer":"configured"},"cors_origins_count":9,"timestamp":"2026-10-17T18:08:54.889807"}
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 7. نقطة API ترجع بيانات بلا مصادقة: /health/deep `[API-001]`
- **الخطورة:** high
- **المسار:** `/health/deep`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"status":"degraded","database":{"status":"healthy"},"schema":{"status":"healthy","required_migration":null,"missing_tables":[],"missing_columns":{}},"rules":{"status":"healthy","loaded_rules":38},"broker":{"status":"healthy"},"workers":{"status":"healthy","workers":{"ai@70ad55e9bd37":{"ok":"pong"},
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 8. نقطة API ترجع بيانات بلا مصادقة: /livez `[API-001]`
- **الخطورة:** high
- **المسار:** `/livez`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"status":"live","timestamp":"2026-10-17T18:09:07.442883"}
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 9. نقطة API ترجع بيانات بلا مصادقة: /readyz `[API-001]`
- **الخطورة:** high
- **المسار:** `/readyz`
- **التفسير:** الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.

```
{"status":"ready","checks":{"database":true,"schema":true,"rules":true,"redis_cache":true,"broker":true},"database":{"status":"healthy"},"schema":{"status":"healthy","required_migration":null,"missing_tables":[],"missing_columns":{}},"rules":{"status":"healthy","loaded_rules":38},"redis_cache":{"sta
```

- **الإصلاح:** أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).

### 10. المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) `[API-002]`
- **الخطورة:** high
- **المسار:** `/health`
- **التفسير:** الاستجابة تغيّرت مع توكن Bearer عشوائي — الخادم لا يتحقق من صحة التوكن بشكل صحيح.

```
status: 200 → 200
```

- **الإصلاح:** تحقق من التوقيع/الصلاحية/الصلاحية الزمنية لكل طلب.

### 11. المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) `[API-002]`
- **الخطورة:** high
- **المسار:** `/health/deep`
- **التفسير:** الاستجابة تغيّرت مع توكن Bearer عشوائي — الخادم لا يتحقق من صحة التوكن بشكل صحيح.

```
status: 200 → 200
```

- **الإصلاح:** تحقق من التوقيع/الصلاحية/الصلاحية الزمنية لكل طلب.

### 12. المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) `[API-002]`
- **الخطورة:** high
- **المسار:** `/livez`
- **التفسير:** الاستجابة تغيّرت مع توكن Bearer عشوائي — الخادم لا يتحقق من صحة التوكن بشكل صحيح.

```
status: 200 → 200
```

- **الإصلاح:** تحقق من التوقيع/الصلاحية/الصلاحية الزمنية لكل طلب.

### 13. المصادقة تُقبل بتوكن وهمية (token validation ضعيفة) `[API-002]`
- **الخطورة:** high
- **المسار:** `/readyz`
- **التفسير:** الاستجابة تغيّرت مع توكن Bearer عشوائي — الخادم لا يتحقق من صحة التوكن بشكل صحيح.

```
status: 200 → 200
```

- **الإصلاح:** تحقق من التوقيع/الصلاحية/الصلاحية الزمنية لكل طلب.

### 14. مواصفة OpenAPI/Swagger منشورة `[API-020]`
- **الخطورة:** medium
- **المسار:** ``
- **التفسير:** أي زائر يستطيع قراءة كل نقاط النهاية والمخططات.

```
/api/openapi.json → 163538B
```

- **الإصلاح:** احمِ المواصفة (Basic auth / allowlist / أزلها من الإنتاج).

### 15. صفحة توثيق API منشورة `[API-021]`
- **الخطورة:** low
- **المسار:** ``
- **التفسير:** توثيق تفاعلي متاح بلا مصادقة.

```
/api/docs
```

- **الإصلاح:** قيّد الوصول لصفحة التوثيق.
