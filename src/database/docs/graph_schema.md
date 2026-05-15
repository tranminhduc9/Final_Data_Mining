# Graph Schema - Neo4j

## Tổng Quan

Hệ thống sử dụng **Neo4j Aura** (cloud managed service) làm graph database để lưu trữ các thực thể và mối quan hệ. Schema được thiết kế cho ứng dụng **Job Market Intelligence** - phân tích thị trường việc làm công nghệ.

### Kết Nối Neo4j Aura

```bash
# Connection String Format
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

> **Lưu ý:** Neo4j Aura sử dụng protocol `neo4j+s` (secure) để kết nối. Đảm bảo firewall cho phép outbound connections.

## Node Types

### 1. Article Node

Lưu trữ bài viết tin tức công nghệ.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `id` | String | Unique ID (MD5 hash of URL) | `"abc123..."` |
| `title` | String | Tiêu đề bài viết | `"OpenAI ra mắt GPT-5"` |
| `content` | String | Nội dung đầy đủ | `"Nội dung..."` |
| `url` | String | URL gốc | `"https://vnexpress.net/..."` |
| `source_platform` | String | Nền tảng nguồn | `"VNExpress"` |
| `published_date` | String | Ngày đăng | `"2026-05-14"` |

```cypher
CREATE (a:Article {
    id: "abc123",
    title: "OpenAI ra mắt GPT-5",
    content: "...",
    url: "https://vnexpress.net/...",
    source_platform: "VNExpress",
    published_date: "2026-05-14"
})
```

### 2. Technology Node

Công nghệ, ngôn ngữ lập trình, framework.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `name` | String | Tên công nghệ (unique) | `"Python"` |
| `mention_count` | Integer | Số lần được nhắc | `150` |

```cypher
CREATE (t:Technology {
    name: "Python",
    mention_count: 150
})
```

### 3. Company Node

Thông tin công ty.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `id` | String | Unique ID (slugified name) | `"fpt"` |
| `name` | String | Tên công ty | `"FPT"` |
| `location` | String | Địa điểm | `"Hà Nội"` |

```cypher
CREATE (c:Company {
    id: "fpt",
    name: "FPT",
    location: "Hà Nội"
})
```

### 4. Job Node

Tin tuyển dụng.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `id` | String | Unique ID (MD5 hash) | `"def456..."` |
| `name` | String | Tiêu đề job | `"Senior AI Engineer"` |
| `description` | String | Mô tả công việc | `"...` |
| `requirement` | String | Yêu cầu | `"...` |
| `benefit` | String | Quyền lợi | `"...` |
| `salary` | String | Mức lương | `"25-40 triệu"` |
| `url` | String | URL gốc | `"https://topcv.vn/..."` |
| `source_platform` | String | Nền tảng nguồn | `"TopCV"` |

```cypher
CREATE (j:Job {
    id: "def456",
    name: "Senior AI Engineer",
    description: "...",
    requirement: "...",
    benefit: "...",
    salary: "25-40 triệu",
    url: "https://topcv.vn/...",
    source_platform: "TopCV"
})
```

### 5. Skill Node

Kỹ năng yêu cầu.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `name` | String | Tên kỹ năng (unique) | `"Problem Solving"` |
| `mention_count` | Integer | Số lần được yêu cầu | `75` |

```cypher
CREATE (s:Skill {
    name: "Problem Solving",
    mention_count: 75
})
```

### 6. Location Node

Địa điểm.

| Property | Type | Mô tả | Ví dụ |
|----------|------|-------|-------|
| `name` | String | Tên địa điểm (unique) | `"Hà Nội"` |

```cypher
CREATE (l:Location {
    name: "Hà Nội"
})
```

## Relationship Types

### 1. MENTIONS (Article → Technology/Company/Location)

Article nhắc đến công ty/công nghệ/địa điểm.

```cypher
// Article mentions Technology
(a:Article)-[:MENTIONS]->(t:Technology)

// Article mentions Company
(a:Article)-[:MENTIONS]->(c:Company)

// Article mentions Location
(a:Article)-[:MENTIONS]->(l:Location)
```

### 2. POSTED_BY (Job → Company)

Job được đăng bởi công ty.

```cypher
(j:Job)-[:POSTED_BY]->(c:Company)
```

### 3. REQUIRES (Job → Technology/Skill)

Job yêu cầu công nghệ/kỹ năng.

```cypher
// Job requires Technology
(j:Job)-[:REQUIRES]->(t:Technology)

// Job requires Skill
(j:Job)-[:REQUIRES]->(s:Skill)
```

## Constraints & Indexes

```cypher
// Unique constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE;
```

## Graph Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEO4J GRAPH SCHEMA                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌───────────┐                      ┌───────────┐                         │
│    │  Article  │──── MENTIONS ───────▶│ Technology│                         │
│    └─────┬─────┘                      └───────────┘                         │
│          │                                                                   │
│          │ MENTIONS                                                         │
│          ▼                                                                   │
│    ┌───────────┐                      ┌───────────┐                         │
│    │  Company  │◀──── POSTED_BY ──────│    Job    │                         │
│    └───────────┘                      └─────┬─────┘                         │
│          ▲                                  │                               │
│          │                                  │ REQUIRES                      │
│          │                                  ▼                               │
│          │                            ┌───────────┐                         │
│          │                            │   Skill   │                         │
│          │                            └───────────┘                         │
│          │                                  ▲                               │
│          │                                  │ REQUIRES                      │
│          │                                  │                               │
│          │ MENTIONS                         │                               │
│          │                            ┌─────┴─────┐                         │
│          │                            │Technology │                         │
│          │                            └───────────┘                         │
│          │                                                                   │
│          │ MENTIONS                                                         │
│          ▼                                                                   │
│    ┌───────────┐                                                            │
│    │ Location  │                                                            │
│    └───────────┘                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cypher Query Examples

### 1. Tìm công nghệ được nhắc nhiều nhất

```cypher
MATCH (t:Technology)<-[:MENTIONS]-(a:Article)
RETURN t.name, count(a) as mention_count
ORDER BY mention_count DESC
LIMIT 10;
```

### 2. Tìm công ty đang tuyển nhiều nhất

```cypher
MATCH (c:Company)<-[:POSTED_BY]-(j:Job)
RETURN c.name, count(j) as job_count
ORDER BY job_count DESC
LIMIT 10;
```

### 3. Tìm kỹ năng hot theo công nghệ

```cypher
MATCH (t:Technology)<-[:REQUIRES]-(j:Job)-[:REQUIRES]->(s:Skill)
WHERE t.name = "AI"
RETURN s.name, count(j) as demand_count
ORDER BY demand_count DESC
LIMIT 10;
```

### 4. Tìm công ty theo location

```cypher
MATCH (c:Company)<-[:POSTED_BY]-(j:Job)-[:REQUIRES]->(t:Technology)
WHERE c.location CONTAINS "Hà Nội"
RETURN c.name, collect(DISTINCT t.name) as technologies
ORDER BY size(technologies) DESC;
```

### 5. Co-occurrence của công nghệ

```cypher
MATCH (t1:Technology)<-[:MENTIONS]-(a:Article)-[:MENTIONS]->(t2:Technology)
WHERE t1.name < t2.name
RETURN t1.name, t2.name, count(a) as co_occurrence
ORDER BY co_occurrence DESC
LIMIT 20;
```

### 6. Trending technologies theo thời gian

```cypher
MATCH (t:Technology)<-[:MENTIONS]-(a:Article)
WHERE a.published_date >= "2026-05-01"
RETURN t.name, count(a) as recent_mentions
ORDER BY recent_mentions DESC
LIMIT 15;
```

## Data Statistics

Sau khi import, database có thể đạt:

| Node Type | Count (estimated) |
|-----------|-------------------|
| Article | 100-500/day |
| Job | 50-200/day |
| Technology | 200+ unique |
| Company | 100+ unique |
| Skill | 150+ unique |
| Location | 20+ unique |

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh graph visualization tại đây
> 
> ![Graph Visualization](./images/graph_visualization.png)
> *Hình 1: Minh họa đồ thị Neo4j với các node và relationship*

> **Ghi chú:** Thêm ảnh schema diagram tại đây
> 
> ![Schema Diagram](./images/schema_diagram.png)
> *Hình 2: Sơ đồ chi tiết Neo4j schema*