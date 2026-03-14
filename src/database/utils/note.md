HIỆN TẠI (VN-Express/Dân Trí)        →    SCHEMA MỚI (Job Market)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Article                              →    Article (giữ nguyên)
  - title                            →    title
  - description                      →    content
  - created_at                       →    published_date
  - (cần tính sentiment)             →    sentiment_score

Organization (OpenAI, Apple,...)    →    Company
  - name                             →    name
  - (cần NLP để extract)             →    industry
  
Technology (AI, GPU,...)             →    Technology
  - name                             →    name
  - (cần research)                   →    category, description, trend_score

Person (CEO,...)                     →    Person
  - name                             →    name
  - (cần extract role)               →    role

(KHÔNG CÓ)                           →    Job (cần crawl từ nguồn khác)
(KHÔNG CÓ)                           →    Skill (cần extract từ Job/Article)