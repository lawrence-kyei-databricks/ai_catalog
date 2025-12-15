# CarMax Data Classification Platform - Solution Design

**Version:** 1.0
**Date:** 2025-12-14
**Status:** Production-Ready Design

---

## 🎯 Executive Summary

AI-powered data classification platform for CarMax that automatically classifies Unity Catalog columns against CarMax's 172-element data taxonomy using Claude 3.7 Sonnet, with smart auto-approval reducing human review burden by 90%.

---

## 📋 Core Requirements

### Business Requirements
1. Classify all Unity Catalog columns against CarMax's 172 data elements
2. Support 3 data subject types (Associate, B2B, Consumer)
3. Identify sensitive/PII data automatically
4. Provide confidence scores for all classifications
5. Human-in-the-loop review for low confidence cases
6. Apply classifications as Unity Catalog tags
7. Flexible taxonomy management (add/change/remove elements)
8. Audit trail for compliance

### Technical Requirements
1. Deploy on Databricks as a Databricks App
2. Use Claude 3.7 Sonnet for classification (best accuracy)
3. Integrate with native UC data classification features
4. Scale to millions of columns
5. Minimize latency and cost
6. Deploy via DABs (Databricks Asset Bundles)
7. Production-ready with proper error handling

---

## 🏗️ Architecture

### High-Level Components

```
┌─────────────────────────────────────────────┐
│  React UI (CarMax Branded)                  │
│  • Dashboard  • Classify  • Review          │
│  • Compliance  • Taxonomy Admin             │
└─────────────────────────────────────────────┘
                  ↕ REST API
┌─────────────────────────────────────────────┐
│  Flask Backend (Databricks App)             │
│  • Taxonomy Manager                         │
│  • Classification Engine (Claude 3.7)       │
│  • Smart Auto-Approval                      │
│  • Pattern Rules Engine                     │
│  • UC Tag Manager                           │
└─────────────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────────────┐
│  Unity Catalog (Delta Lake)                 │
│  • Taxonomy Tables (172 elements)           │
│  • Classification Governance Table          │
│  • UC Tags (172 tags)                       │
│  • System Tables (metadata)                 │
└─────────────────────────────────────────────┘
```

### Data Flow

```
1. TAXONOMY SETUP (One-time)
   Excel Files → Import → Database Tables → UC Tags

2. CLASSIFICATION FLOW
   UC Columns → Scan → Pattern Check → Native UC Check →
   Claude AI → Auto-Approval Decision → Store Result

3. REVIEW FLOW (10% of columns)
   Pending Classifications → Human Review →
   Approve/Edit/Reject → Apply to UC

4. TAG APPLICATION
   Approved Classifications → Create/Apply UC Tags →
   Governance Hub → Compliance Reports
```

---

## 🗄️ Database Schema

### Taxonomy Schema (main.carmax_taxonomy)

**1. data_elements** - 172 CarMax classification elements
```sql
- element_id (PK)
- element_name
- element_category
- element_description
- sensitive_flag
- keywords (array)
- active (boolean)
- created_at, updated_at
```

**2. data_categories** - 14 categories
```sql
- category_id (PK)
- category_name
- element_count
- active
```

**3. subject_types** - 3 data subjects
```sql
- subject_type_id (PK)
- subject_type_name (Associate, B2B, Consumer)
- subject_description
- active
```

**4. taxonomy_versions** - Change tracking
```sql
- version_id (PK, identity)
- version_number
- change_type
- change_description
- changes_json
- changed_at, changed_by
```

### Governance Schema (main.carmax_governance)

**classification_governance** - Main classification tracking table
```sql
- id (PK, identity)
- catalog_name, schema_name, table_name, column_name
- column_type
- suggested_element, suggested_category
- confidence_score
- sensitive_flag
- data_subjects (array)
- reasoning
- review_status (PENDING, AUTO_APPROVED, APPROVED, REJECTED, APPLIED)
- approval_tier (1, 2, 3)
- requires_review (boolean)
- review_priority (HIGH, MEDIUM, LOW)
- approved_element
- reviewer, review_notes
- created_at, reviewed_at, applied_at
- sample_values (JSON)
- model_used
- classification_source (CLAUDE, UC_NATIVE, PATTERN_RULE, CACHE)
- UNIQUE(catalog, schema, table, column)
- CLUSTERED BY (review_status, review_priority, catalog, schema)
```

---

## 🧠 Classification Strategy

### Three-Tier Auto-Approval System

**Tier 1: Auto-Approve (90% confidence)**
- Confidence ≥ 95%
- Pattern match score ≥ 0.8
- Status: AUTO_APPROVED
- Human review: NOT REQUIRED

**Tier 2: Conditional Auto-Approve (5% effort)**
- Confidence ≥ 85%
- Not sensitive OR pattern matched
- Status: AUTO_APPROVED
- Human review: NOT REQUIRED

**Tier 3: Human Review Required (5% manual effort)**
- Confidence < 85%
- Sensitive data + confidence < 95%
- Pattern mismatch
- Status: PENDING
- Priority: HIGH (sensitive + low confidence) / MEDIUM / LOW

### Classification Sources (Priority Order)

1. **Native UC Classification** (Highest confidence - 99%)
   - Databricks automatic PII detection
   - SSN, email, credit card, phone, etc.
   - Auto-approve immediately

2. **Pattern Rules** (99% confidence)
   - Regex pattern matching
   - Column name matching
   - Auto-approve if 80%+ samples match

3. **Cache** (95% confidence)
   - Previously classified similar columns
   - Fingerprint-based matching
   - Auto-approve if cached result

4. **Claude 3.7 AI** (Variable confidence)
   - Full analysis with sample data
   - Returns confidence score
   - Auto-approve if criteria met

---

## 🚀 Performance Optimizations

### Database Optimizations
1. **Liquid Clustering** - CLUSTER BY (review_status, priority, catalog, schema)
2. **Auto Optimize** - delta.autoOptimize.optimizeWrite = true
3. **Materialized Views** - Pre-aggregated dashboard metrics
4. **Change Data Feed** - Track all changes

### Query Optimizations
1. **System Tables** - Use system.information_schema for metadata
2. **Incremental Processing** - Only classify new/changed columns
3. **Batch Processing** - Process 50-100 columns per batch
4. **Async Queue** - Background processing, non-blocking UI

### Cost Optimizations
1. **Serverless SQL** - Auto-scaling, scale to zero
2. **Prompt Caching** - Claude 3.7 cache taxonomy (90% cost reduction)
3. **Batch API Calls** - Reduce API overhead
4. **Smart Sampling** - Only fetch 5-10 sample values per column
5. **Off-Peak Scheduling** - Run batch jobs during low-cost hours

**Estimated Monthly Cost:** $50-100
- SQL Warehouse (serverless): $30-60
- Claude 3.7 API (with caching): $15-30
- Storage: $5-10

---

## 🎨 UI Design

### CarMax Branding
- **Primary Color:** #FFD500 (Yellow)
- **Secondary Color:** #003087 (Navy Blue)
- **Accent Bars:** 5 horizontal bars (logo style)

### Pages (5 total)

1. **Dashboard**
   - Classification coverage by schema
   - Sensitive data count
   - Recent classifications
   - Confidence score distribution

2. **Classify**
   - Select catalog/schema
   - Trigger classification
   - View progress
   - Queue status

3. **Review** (Smart filtering)
   - High priority only (default)
   - Sensitive data only
   - Low confidence only
   - Bulk approval actions

4. **Compliance**
   - Apply approved classifications
   - Export reports
   - Tag coverage metrics
   - Governance Hub integration

5. **Taxonomy Admin**
   - Import from Excel
   - Add/edit/remove elements
   - View change history
   - Export current taxonomy

---

## 📦 Deployment (DABs)

### Bundle Structure
```
carmax-classification/
├── databricks.yml           # Main bundle config
├── app.yml                  # App-specific config
├── resources/
│   ├── apps.yml            # App resource definition
│   └── jobs.yml            # Background jobs
├── app/
│   ├── main.py             # Flask backend
│   ├── taxonomy_manager.py
│   ├── classification_engine.py
│   └── pattern_rules.py
├── frontend/               # React app
├── static/                 # Built frontend
├── sql/
│   ├── setup_taxonomy.sql
│   └── setup_governance.sql
└── README.md
```

### Environments
- **dev** - Development environment
- **staging** - Staging environment
- **prod** - Production environment

### Deployment Commands
```bash
# Deploy to dev
databricks bundle deploy -t dev

# Deploy to prod
databricks bundle deploy -t prod
```

---

## 🔒 Security & Compliance

1. **Authentication** - Service principal with minimal permissions
2. **Authorization** - RBAC for admin functions
3. **Data Privacy** - Sample data configurable (can disable)
4. **Audit Trail** - All changes logged with user, timestamp
5. **Encryption** - Delta Lake encryption at rest
6. **Secrets** - Databricks secrets for API keys
7. **Tag Policies** - Enforce consistent tagging

---

## 📊 Success Metrics

### Classification Metrics
- **Coverage:** % of columns classified
- **Accuracy:** % of approved classifications
- **Efficiency:** % auto-approved (target: 90%)
- **Velocity:** Columns classified per hour

### Business Metrics
- **Sensitive Data Inventory:** Count of sensitive columns
- **Compliance Readiness:** % of columns tagged
- **Review Time:** Time to complete human reviews
- **Cost per Classification:** Total cost / columns classified

---

## 🔄 Taxonomy Lifecycle

### Initial Setup
1. Upload Excel files (172 elements, 3 subjects)
2. Import to database tables
3. Create UC tags (172 tags)
4. System ready for classification

### Ongoing Changes
1. **Add Element:** Admin UI → Database → UC Tag → AI Prompt (5 min)
2. **Update Element:** Admin UI → Database → Version Log → Propagate
3. **Remove Element:** Soft delete → Deactivate → Preserve history

### Version Management
- All changes logged in taxonomy_versions
- Change JSON stored for audit
- Rollback capability
- Export/import for backup

---

## 🚦 Implementation Phases

### Phase 1: Foundation (Week 1)
- Database schema setup
- Taxonomy import from Excel
- UC tag creation
- Basic Flask API

### Phase 2: Classification Engine (Week 1-2)
- Pattern rules engine
- Native UC integration
- Claude 3.7 classification
- Smart auto-approval

### Phase 3: UI Development (Week 2)
- CarMax branded React app
- Dashboard page
- Classify page
- Review page

### Phase 4: Production Ready (Week 2-3)
- Compliance page
- Taxonomy admin page
- Error handling
- Testing
- Documentation

### Phase 5: Deployment (Week 3)
- DABs configuration
- Environment setup
- Production deployment
- User training

---

## 📚 Key Technologies

- **AI Model:** Claude 3.7 Sonnet (Databricks Foundation Model API)
- **Backend:** Flask + Databricks SDK for Python
- **Frontend:** React 18 + TailwindCSS + Vite
- **Database:** Delta Lake + Unity Catalog
- **Deployment:** Databricks Apps + DABs
- **Compute:** Serverless SQL Warehouse
- **Version Control:** Git + GitHub

---

## ✅ Production Readiness Checklist

- [ ] Database schemas created
- [ ] Taxonomy imported from Excel
- [ ] UC tags synchronized
- [ ] Classification engine tested
- [ ] UI functional and branded
- [ ] DABs deployment configured
- [ ] Error handling implemented
- [ ] Logging and monitoring setup
- [ ] Documentation complete
- [ ] User permissions configured
- [ ] Cost monitoring enabled
- [ ] Backup/restore tested
- [ ] UAT completed
- [ ] Go-live approved

---

**This document serves as the guide rails for implementation. All development should align with this design.**
