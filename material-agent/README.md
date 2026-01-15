# Material Agent - Curriculum Discovery & Content Pack Builder

> **Automated OER Content Discovery System** for building curriculum-aligned learning materials using Browser-Use AI agents

---

## 🎯 Project Vision

The Material Agent is an autonomous FastAPI service that **discovers official curricula** and **curates vetted Open Educational Resources (OER)** to build complete, curriculum-aligned content packs for the Froggy AI Tutor platform.

### The Problem We're Solving

Traditional curriculum development requires:
- ✋ **Manual research** - Hours spent finding official curriculum documents
- 📚 **Content curation** - Manually vetting OER sources for quality and license compliance
- 🔗 **Alignment mapping** - Ensuring content matches learning objectives
- 📦 **Content packaging** - Organizing materials into teachable units
- 🔄 **Maintenance** - Keeping content fresh and verifying broken links

### Our Solution

An **AI-powered pipeline** that:
1. 🤖 **Automatically discovers** official curriculum docs (e.g., Quebec PFEQ, US Common Core)
2. 🔍 **Searches and scores** OER sources (Khan Academy, University OER, Government resources)
3. ✅ **Validates** content for curriculum alignment, license compliance, and quality
4. 📦 **Publishes** complete content packs ready for RAG retrieval by Froggy AI
5. 🗺️ **Generates** session-by-session learning roadmaps

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Material Agent                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  POST /content-packs/discover                                    │
│    ↓                                                              │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  4-Stage Job Pipeline (Background Processing)       │        │
│  ├─────────────────────────────────────────────────────┤        │
│  │                                                       │        │
│  │  Stage 1: CURRICULUM_DISCOVERY (Browser-Use Agent)   │        │
│  │  ├─ Discovers official curriculum docs               │        │
│  │  ├─ Extracts topics & learning objectives             │        │
│  │  └─ Scores OER sources (authority/alignment/license)  │        │
│  │                                                       │        │
│  │  Stage 2: CONTENT_EXTRACTION                          │        │
│  │  ├─ Extracts content from vetted sources              │        │
│  │  ├─ Creates KnowledgeChunks (granular teaching units) │        │
│  │  └─ Generates embeddings (text-embedding-3-small)     │        │
│  │                                                       │        │
│  │  Stage 3: VALIDATION_COVERAGE                         │        │
│  │  ├─ Validates all objectives have ≥2 chunks           │        │
│  │  ├─ Checks license compliance (100%)                  │        │
│  │  └─ Calculates coverage score (must be ≥0.95)         │        │
│  │                                                       │        │
│  │  Stage 4: PUBLISH_PACK                                │        │
│  │  ├─ Creates ContentPack with all metadata             │        │
│  │  ├─ Indexes chunks in vector DB for RAG               │        │
│  │  ├─ Uploads to S3/CDN                                 │        │
│  │  └─ Generates session-by-session roadmap template     │        │
│  │                                                       │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                   │
│  GET /content-packs/{pack_id}        → Retrieve published pack  │
│  GET /jobs/{job_id}                  → Check job status/progress│
│  GET /source-records/{curriculum_id} → View vetted sources      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │         MongoDB Collections             │
         ├────────────────────────────────────────┤
         │  • content_packs      (published packs)│
         │  • knowledge_chunks   (teaching content)│
         │  • source_records     (vetted OER URLs) │
         │  • jobs              (pipeline tracking)│
         │  • materials         (uploaded files)   │
         └────────────────────────────────────────┘
```

---

## 📊 Data Flow Example

### Input: User Request
```json
POST /content-packs/discover
{
  "country": "CA",
  "region": "QC",
  "grade": "4",
  "subject": "Spanish",
  "language": "fr-CA"
}
```

### Output: Published Content Pack
```json
{
  "pack_id": "tpl_spanish_grade4_ca_qc_v1",
  "status": "PUBLISHED",
  "curriculum": {
    "curriculum_id": "cur_ca_qc_spanish_grade4_v1",
    "topic_count": 3,
    "objective_count": 6,
    "official_source_documents": [
      {
        "url": "https://www.education.gouv.qc.ca/.../PFEQ_espagnol.pdf",
        "title": "Programme de formation - Espagnol",
        "publisher": "Ministère de l'Éducation du Québec",
        "authority_level": "OFFICIAL_GOVERNMENT"
      }
    ]
  },
  "materials_by_topic": {
    "t1_greetings_introductions": [
      {
        "source_id": "src_khan_greetings",
        "url": "https://www.khanacademy.org/.../spanish-greetings",
        "title": "Spanish Greetings and Introductions",
        "publisher": "Khan Academy",
        "license": "CC-BY-NC-SA 3.0",
        "total_score": 16,
        "chunk_count": 2
      }
    ]
  },
  "chunk_ids_by_topic": {
    "t1_greetings_introductions": ["ck_tpl_greet_001", "ck_tpl_greet_002"],
    "t2_numbers_counting": ["ck_tpl_num_001", "ck_tpl_num_002"],
    "t3_colors_shapes": ["ck_tpl_color_001"]
  },
  "statistics": {
    "total_chunks": 10,
    "total_sources": 7,
    "coverage_score": 1.0,
    "license_compliance_score": 1.0
  },
  "deployment": {
    "vector_db_indexed": true,
    "embeddings_generated": true,
    "rag_searchable": true
  },
  "roadmap_template": {
    "session_count": 9,
    "sessions": [
      {
        "session_number": 1,
        "topic_id": "t1_greetings_introductions",
        "title": "Greetings for Different Times of Day",
        "duration_minutes": 30,
        "chunk_ids": ["ck_tpl_greet_001", "ck_tpl_greet_004"],
        "objectives": ["o1_greet_appropriately"],
        "activities": ["video", "vocabulary-practice", "pronunciation-drill"]
      }
    ]
  }
}
```

---

## 🗂️ Database Schema

### Core Collections

#### 1. **content_packs** - Published Curriculum Bundles
```typescript
{
  pack_id: "tpl_spanish_grade4_ca_qc_v1",
  pack_type: "TEMPLATE" | "INSTANCE",
  status: "PUBLISHED",
  version: "1.0.0",
  curriculum_id: "cur_ca_qc_spanish_grade4_v1",
  metadata: {
    jurisdiction: { country: "CA", region: "QC" },
    grade: "4",
    subject: "Spanish",
    language: "fr-CA",
    tags: ["spanish", "grade4", "quebec", "elementary"]
  },
  curriculum: { /* official docs, topic/objective counts */ },
  materials_by_topic: { /* scored OER sources per topic */ },
  chunk_ids_by_topic: { /* knowledge chunk IDs */ },
  statistics: { /* totals, averages, diversity metrics */ },
  quality_assurance: { /* validation scores, readiness */ },
  deployment: { /* S3 paths, CDN URLs, vector DB status */ },
  roadmap_template: { /* generated learning sessions */ }
}
```

#### 2. **knowledge_chunks** - Granular Teaching Content
```typescript
{
  chunk_id: "ck_tpl_greet_001",
  scope: "TEMPLATE" | "INSTANCE",
  topic_id: "t1_greetings_introductions",
  objective_id: "o1_greet_appropriately",
  chunk_type: "CONCEPT_EXPLANATION" | "EXAMPLE" | "STEP_BY_STEP" | ...,
  content: "Buenos días is used from sunrise until noon...",
  embedding: [0.123, -0.456, ...],  // 1536 dimensions
  tags: ["greetings", "vocabulary", "time-of-day"],
  skill_tags: ["pronunciation", "cultural-context"],
  difficulty: "easy",
  source: {
    source_type: "OER",
    source_id: "src_khan_greetings",
    license: "CC-BY-NC-SA 3.0"
  }
}
```

#### 3. **source_records** - Vetted OER Sources
```typescript
{
  source_id: "src_khan_greetings",
  curriculum_id: "cur_ca_qc_spanish_grade4_v1",
  source_type: "EDUCATIONAL_PLATFORM",
  url: "https://www.khanacademy.org/.../spanish-greetings",
  title: "Spanish Greetings and Introductions",
  publisher: "Khan Academy",
  license: "CC-BY-NC-SA 3.0",
  scoring: {
    authority: 4,      // 0-5: Educational platform with reputation
    alignment: 5,      // 0-5: Perfect match with curriculum objectives
    license: 5,        // 0-5: Open license, allows derivatives
    extractability: 2, // 0-3: Video content, moderate extraction
    total: 16          // Must be ≥12 to pass
  },
  verification: {
    status: "VERIFIED",
    last_verified_at: "2026-01-14T12:00:00Z",
    http_status_code: 200
  },
  topic_ids: ["t1_greetings_introductions"],
  created_chunk_ids: ["ck_tpl_greet_001", "ck_tpl_greet_002"]
}
```

#### 4. **jobs** - Background Job Tracking
```typescript
{
  job_id: "job_discover_abc123",
  job_type: "CURRICULUM_DISCOVERY",
  status: "RUNNING" | "COMPLETED" | "FAILED",
  priority: "NORMAL",
  input_data: { country: "CA", region: "QC", grade: "4", subject: "Spanish" },
  output_data: { curriculum_id: "...", sources_discovered: 7 },
  progress: {
    percentage: 75,
    current_step: "Scoring OER sources",
    message: "Processed 5/7 sources"
  },
  timing: {
    queued_at: "2026-01-14T12:00:00Z",
    started_at: "2026-01-14T12:00:05Z",
    duration_ms: 45000
  },
  metrics: {
    browser_actions_count: 23,
    pages_visited: 12,
    tokens_used: 15420
  }
}
```

---

## 🛠️ Technology Stack

### Core Framework
- **FastAPI 0.115.0** - High-performance async API framework
- **Python 3.13** - Latest Python with performance improvements
- **Pydantic 2.9** - Data validation and settings management
- **Motor 3.6** - Async MongoDB driver

### AI & Automation
- **Browser-Use 0.1.1** - AI agent for web automation (curriculum discovery)
- **OpenAI API** - Text embeddings (text-embedding-3-small, 1536 dims)
- **ChatBrowserUse** - Optimized LLM for browser automation tasks

### Storage & Deployment
- **MongoDB** - Document database for all collections
- **AWS S3** - File storage (PDFs, extracted content)
- **boto3** - S3 integration

### Development
- **uvicorn** - ASGI server with hot reload
- **python-dotenv** - Environment variable management

---

## 📁 Project Structure

```
material-agent/
├── app/
│   ├── models/               # MongoDB document models (Pydantic)
│   │   ├── __init__.py       # Clean exports
│   │   ├── base.py           # Shared PyObjectId type
│   │   ├── knowledge_chunk.py
│   │   ├── material.py
│   │   ├── job.py
│   │   ├── source_record.py
│   │   └── content_pack.py
│   │
│   ├── schemas/              # API request/response validation
│   │   └── __init__.py       # Pydantic schemas for FastAPI
│   │
│   ├── repositories/         # Data access layer (CRUD operations)
│   │   ├── __init__.py
│   │   ├── knowledge_chunk_repository.py
│   │   ├── content_pack_repository.py
│   │   └── job_repository.py
│   │
│   ├── services/             # Business logic layer (TODO)
│   │   ├── __init__.py
│   │   ├── curriculum_discovery_service.py  # Job 1: Browser-Use agent
│   │   ├── content_extraction_service.py    # Job 2: Extract & chunk
│   │   ├── validation_service.py            # Job 3: Coverage check
│   │   ├── publishing_service.py            # Job 4: Publish pack
│   │   └── embedding_service.py             # OpenAI embeddings
│   │
│   ├── api/                  # FastAPI route handlers (TODO)
│   │   ├── __init__.py
│   │   ├── content_packs.py  # /content-packs endpoints
│   │   └── jobs.py           # /jobs endpoints
│   │
│   └── temp/                 # NestJS schema files for migration
│       ├── content-pack.schema.ts
│       ├── source-record.schema.ts
│       ├── job.schema.ts
│       ├── roadmap-template.schema.ts (updated)
│       └── roadmap-instance.schema.ts (updated)
│
├── main.py                   # FastAPI app entry point
├── config.py                 # Configuration (env vars, settings)
├── database.py               # MongoDB connection manager
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── README.md                 # This file
│
└── Example Outputs/          # Reference JSON files
    ├── curriculum-discovery-schema.json
    ├── job1-curriculum-discovery-output.json
    ├── job2-topic-material-extraction-output.json
    ├── job3-validation-coverage-output.json
    └── job4-publish-pack-output.json
```

---

## ✅ What We've Built So Far

### ✅ Phase 1: Foundation (COMPLETED)
- [x] FastAPI server initialization
- [x] MongoDB connection with Motor
- [x] Environment configuration with Pydantic Settings
- [x] Health check endpoints (/, /health)
- [x] CORS middleware
- [x] Hot reload development setup

### ✅ Phase 2: Data Models (COMPLETED)
- [x] Enterprise-level model organization (separate files)
- [x] **knowledge_chunk.py** - Teaching content with embeddings
- [x] **material.py** - Uploaded materials tracking
- [x] **job.py** - Background job pipeline tracking
- [x] **source_record.py** - Vetted OER sources with scoring
- [x] **content_pack.py** - Published curriculum bundles
- [x] Clean exports in `__init__.py`

### ✅ Phase 3: Repository Layer (COMPLETED)
- [x] **KnowledgeChunkRepository** - CRUD + vector similarity search
- [x] **ContentPackRepository** - Pack storage and retrieval
- [x] **JobRepository** - Job tracking with status updates
- [x] Index creation methods for optimal query performance

### ✅ Phase 4: API Schemas (COMPLETED)
- [x] Request/response validation models
- [x] **CurriculumDiscoveryRequest** - Input validation
- [x] **CurriculumDiscoveryResponse** - Job creation response
- [x] **KnowledgeChunkCreate/Response** - Chunk API models

### ✅ Phase 5: NestJS Integration (COMPLETED)
- [x] Created TypeScript schemas for NestJS migration
- [x] **content-pack.schema.ts** - New schema for content packs
- [x] **source-record.schema.ts** - New schema for vetted sources
- [x] **job.schema.ts** - New schema for job tracking
- [x] **roadmap-template.schema.ts** - Updated with content pack references
- [x] **roadmap-instance.schema.ts** - Updated with chunk-level tracking

---

## 🚧 What's Left To Build

### 🔴 Phase 6: Service Layer (HIGH PRIORITY)

#### **curriculum_discovery_service.py** (Job 1)
```python
# TODO: Implement Browser-Use agent for curriculum discovery
class CurriculumDiscoveryService:
    async def discover_curriculum(
        self,
        country: str,
        region: str,
        grade: str,
        subject: str,
        language: str
    ) -> CurriculumDiscoveryResult:
        """
        Uses Browser-Use agent to:
        1. Search for official curriculum docs (e.g., "Quebec PFEQ Spanish Grade 4")
        2. Extract topics and learning objectives
        3. Search for OER sources (Khan Academy, OpenStax, etc.)
        4. Score each source (authority/alignment/license/extractability)
        5. Filter sources with total_score ≥ 12
        6. Return CurriculumMap with vetted sources
        """
        pass
```

**Key Tasks:**
- [ ] Initialize Browser-Use agent with ChatBrowserUse LLM
- [ ] Implement curriculum document discovery logic
- [ ] Parse topics/objectives from official docs
- [ ] Implement OER source search strategy
- [ ] Build scoring rubric (authority 0-5, alignment 0-5, license 0-5, extractability 0-3)
- [ ] Create SourceRecord documents in MongoDB
- [ ] Return structured CurriculumMap

#### **content_extraction_service.py** (Job 2)
```python
# TODO: Extract content and create knowledge chunks
class ContentExtractionService:
    async def extract_content_from_sources(
        self,
        source_records: List[SourceRecord],
        curriculum_map: CurriculumMap
    ) -> List[KnowledgeChunk]:
        """
        For each vetted source:
        1. Extract text content (PDF, HTML, video transcripts)
        2. Chunk content into teaching units (concept, example, step-by-step)
        3. Map chunks to curriculum objectives
        4. Generate embeddings (OpenAI text-embedding-3-small)
        5. Store in MongoDB with proper metadata
        """
        pass
```

**Key Tasks:**
- [ ] Implement PDF extraction (PyPDF2 or pdfplumber)
- [ ] Implement HTML extraction (BeautifulSoup, html2text)
- [ ] Implement video transcript extraction (YouTube API if needed)
- [ ] Build chunking algorithm (paragraph-based, semantic splitting)
- [ ] Integrate OpenAI embedding API
- [ ] Create KnowledgeChunkModel documents
- [ ] Link chunks to source_records

#### **validation_service.py** (Job 3)
```python
# TODO: Validate curriculum coverage and quality
class ValidationService:
    async def validate_coverage(
        self,
        curriculum_map: CurriculumMap,
        chunks: List[KnowledgeChunk]
    ) -> ValidationReport:
        """
        Validates:
        1. Every objective has ≥ 2 knowledge chunks
        2. License compliance: 100% of sources are OER-licensed
        3. Coverage score ≥ 0.95 (95% of objectives covered)
        4. Source diversity: Multiple publishers per topic
        5. Quality score: Average source score ≥ 14
        """
        pass
```

**Key Tasks:**
- [ ] Build objective coverage checker
- [ ] Implement license compliance validator
- [ ] Calculate coverage metrics
- [ ] Generate validation report with pass/fail status
- [ ] Create warnings for low-quality areas

#### **publishing_service.py** (Job 4)
```python
# TODO: Publish content pack and generate roadmap
class PublishingService:
    async def publish_content_pack(
        self,
        curriculum_map: CurriculumMap,
        chunks: List[KnowledgeChunk],
        validation_report: ValidationReport
    ) -> ContentPack:
        """
        Publishes:
        1. Create ContentPack document with all metadata
        2. Upload extracted content to S3
        3. Index chunk embeddings in vector DB
        4. Generate session-by-session roadmap template
        5. Mark pack as PUBLISHED and rag_searchable
        """
        pass
```

**Key Tasks:**
- [ ] Build ContentPack assembly logic
- [ ] Integrate AWS S3 upload (boto3)
- [ ] Implement vector DB indexing (MongoDB Atlas Vector Search)
- [ ] Generate roadmap template (session planning algorithm)
- [ ] Create ContentPackModel document
- [ ] Update deployment status

#### **embedding_service.py**
```python
# TODO: OpenAI embedding generation
class EmbeddingService:
    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Uses OpenAI text-embedding-3-small to generate 1536-dim embeddings
        Cost: $0.02 per 1M tokens
        """
        pass
```

**Key Tasks:**
- [ ] Integrate OpenAI embeddings API
- [ ] Implement batching for efficiency
- [ ] Add retry logic with exponential backoff
- [ ] Track token usage and costs

---

### 🟡 Phase 7: API Routes (MEDIUM PRIORITY)

#### **content_packs.py**
```python
# TODO: Content pack endpoints
@router.post("/content-packs/discover")
async def discover_curriculum(request: CurriculumDiscoveryRequest):
    """Triggers curriculum discovery job"""
    pass

@router.get("/content-packs/{pack_id}")
async def get_content_pack(pack_id: str):
    """Retrieves published content pack"""
    pass

@router.get("/content-packs")
async def list_content_packs(
    country: Optional[str] = None,
    grade: Optional[str] = None,
    subject: Optional[str] = None
):
    """Lists available content packs with filters"""
    pass
```

**Key Tasks:**
- [ ] Create FastAPI router for /content-packs
- [ ] Implement POST /discover endpoint (triggers Job 1)
- [ ] Implement GET /{pack_id} endpoint
- [ ] Implement GET / with filtering
- [ ] Add proper error handling and validation

#### **jobs.py**
```python
# TODO: Job tracking endpoints
@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Returns job status, progress, and results"""
    pass

@router.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None
):
    """Lists jobs with filters"""
    pass

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancels a running job"""
    pass
```

**Key Tasks:**
- [ ] Create FastAPI router for /jobs
- [ ] Implement GET /{job_id} endpoint
- [ ] Implement GET / with filtering
- [ ] Implement POST /{job_id}/cancel
- [ ] Register routers in main.py

---

### 🟢 Phase 8: Background Job Queue (LOW PRIORITY)

**Options:**
1. **Celery + Redis** - Industry standard, robust
2. **ARQ** - Lightweight, Redis-based, async-first
3. **FastAPI BackgroundTasks** - Simple, built-in (good for MVP)

**Key Tasks:**
- [ ] Choose job queue technology
- [ ] Implement job worker process
- [ ] Add job scheduling and retry logic
- [ ] Implement job progress updates
- [ ] Add job cancellation support

---

### 🔵 Phase 9: Testing & Deployment (FUTURE)

**Key Tasks:**
- [ ] Unit tests for services
- [ ] Integration tests for API endpoints
- [ ] MongoDB index optimization
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production deployment (AWS ECS, Railway, Render)
- [ ] Monitoring and logging (Sentry, DataDog)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- MongoDB 4.4+ (local or Atlas)
- OpenAI API key
- Browser-Use API key (optional, for optimized browser automation)

### Installation

1. **Navigate to project directory**
```bash
cd material-agent
```

2. **Create virtual environment**
```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and MongoDB URI
```

5. **Run the server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. **Test the API**
```bash
curl http://localhost:8000/health
```

### Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=material_agent

# OpenAI
OPENAI_API_KEY=sk-...

# Browser-Use (optional)
BROWSER_USE_API_KEY=...

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=froggy-content-packs

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Validation
MIN_TOTAL_SCORE=12
MIN_LICENSE_SCORE=3
```

---

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎯 Success Criteria

A content pack is considered **production-ready** when:
- ✅ Coverage score ≥ 0.95 (95% of objectives have content)
- ✅ License compliance = 1.0 (100% OER-licensed)
- ✅ Source quality score ≥ 0.9 (average source score ≥ 14/18)
- ✅ Every objective has ≥ 2 knowledge chunks
- ✅ Vector DB indexed = true
- ✅ Embeddings generated = true

---

## 🤝 Contributing

This is an internal project for the Froggy AI Tutor platform. For questions or contributions, contact the development team.

---

## 📝 License Compliance

All content curated by this system must be:
- **Open Educational Resources (OER)** with permissive licenses
- **Accepted licenses**: CC-BY, CC-BY-SA, CC-BY-NC-SA, Public Domain, CC0
- **License verification**: Automated checks in validation stage
- **Attribution**: All sources properly attributed in metadata

---

## 🔗 Related Systems

- **Froggy NestJS Server** - Main tutor backend (receives published content packs)
- **Roadmap Instance System** - Creates personalized learning paths from content packs
- **RAG Query Engine** - Searches knowledge chunks using vector embeddings

---

**Last Updated**: January 14, 2026  
**Status**: Foundation Complete, Service Layer In Progress  
**Next Milestone**: Implement Job 1 (Curriculum Discovery Service)
