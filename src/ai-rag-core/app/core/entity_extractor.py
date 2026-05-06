"""
Trích xuất entities từ câu hỏi của user bằng dictionary + regex (không dùng LLM).
Ported từ src/data-pipeline/extract_data.py.

Trả về:
  - technologies: tên tech / framework / ngôn ngữ lập trình / kỹ năng IT
  - job_titles:   vị trí / chức danh công việc IT
"""

import re
from typing import List

# ==========================================
# TECH DICTIONARIES
# ==========================================

TECH_ABBREVS_CASE_SENSITIVE = {
    "AI", "IT", "RPA", "AGI", "NPU", "GPU", "TPU"
}

TECH_ABBREVS = {
    "AWS", "GCP", "CSS", "PHP", "SQL", "VBA", "SAS", "ELK", "SVN",
    "API", "SDK", "IDE", "RPC", "ORM", "JWT", "SSH", "HTTP", "HTTPS",
    "REST", "SOAP", "HTML", "XML", "JSON", "YAML", "gRPC", "LLM", "GPT",
    "SIP", "RTP", "VPN", "ETL", "ERP", "CRM", "MES", "IoT", "WAF",
    "SAP", "BGP", "OSPF", "VLAN", "NAT", "DNS", "DHCP", "TCP", "UDP",
    "OCR", "STT", "TTS", "RAG", "NLP", "MLOps", "CI/CD", "OLAP", "DWH",
    "SIEM", "EDR", "HSM", "IDS", "IPS", "SSE",
    "DDoS", "MPC", "KYC", "SOC", "PAD", "SoC", "NVR", "VMS",
    "OTP", "2FA", "APK", "NFC", "ADB", "QR",
    "IPv4", "IPv6", "5G", "4G", "eSIM",
    "ROM", "CCCD", "VNeID",
    "MoE", "LPU", "ICI", "SRAM", "HBM", "EEG",
    "C2PA", "GDPR", "FCC", "CISO", "FAIR",
    "MAU", "DAU",
}

TECH_KEYWORDS: List[str] = [
    # AI & ML & Language Models
    "ChatGPT", "Claude", "Gemini", "Copilot", "Grok", "Perplexity", "DeepSeek",
    "OpenAI", "Anthropic", "Mistral", "Llama", "VinAI", "xAI",
    "Trí tuệ nhân tạo", "Machine Learning", "Deep Learning", "Generative AI",
    "GenAI", "AI tạo sinh", "Mô hình ngôn ngữ", "Học máy", "Chatbot",
    "AI Agent", "Tác nhân AI", "Computer Vision",
    "Apple Intelligence", "Siri", "Sora", "Claude Code",
    "Deepfake", "Ransomware", "Infostealer", "Spyware",
    # Bảo mật
    "Zero Trust", "Kaspersky", "Malwarebytes", "Zscaler", "Proofpoint",
    "Watering hole", "SIM swap",
    # Chip & phần cứng
    "Snapdragon", "Tensor", "Apple Silicon", "Qualcomm",
    "chip quang tử", "qubit",
    # Hạ tầng
    "Data Center", "AI Data Center", "Trung tâm dữ liệu",
    "Public Cloud", "Private Cloud", "Hybrid Cloud",
    # Ngôn ngữ lập trình
    "Python", "Java", "JavaScript", "TypeScript",
    "Golang", "Rust", "Kotlin", "Swift", "Scala", "Ruby", "PHP",
    "Perl", "Dart", "Lua", "Groovy", "Elixir", "Erlang", "Haskell",
    "MATLAB", "Julia", "Visual Basic", "Objective-C",
    "C++", "C#",
    # Web Front-end
    "React", "ReactJS", "React.js", "Vue", "VueJS", "Vue.js",
    "Angular", "AngularJS", "Next.js", "Nuxt.js", "Svelte", "jQuery",
    "Bootstrap", "Tailwind", "TailwindCSS", "Sass", "SCSS", "Less",
    "Webpack", "Vite", "Babel",
    # Web Back-end
    "Node.js", "NodeJS", "Express", "ExpressJS", "NestJS", "Django",
    "Flask", "FastAPI", "Spring Boot", "Spring", "SpringBoot",
    "Laravel", "Symfony", "Rails", "Ruby on Rails", "ASP.NET", ".NET",
    "Gin", "Echo", "Fiber",
    # Database
    "MySQL", "PostgreSQL", "MariaDB", "SQLite", "MSSQL", "SQL Server",
    "Oracle", "MongoDB", "Redis", "Cassandra", "DynamoDB", "Elasticsearch",
    "HBase", "CouchDB", "Neo4j", "InfluxDB", "Firebase", "Firestore",
    "Supabase", "PlanetScale",
    # Cloud & Infra
    "Azure", "Google Cloud", "Google Cloud Platform",
    "Alibaba Cloud", "DigitalOcean", "CloudFront",
    "Cloudflare", "Vercel", "Netlify", "Heroku",
    # DevOps / CI-CD / Container
    "Docker", "Kubernetes", "K8s", "Jenkins", "GitLab CI", "GitHub Actions",
    "CircleCI", "Travis CI", "Ansible", "Terraform", "Puppet", "Chef",
    "Helm", "ArgoCD", "Prometheus", "Grafana", "Logstash", "Kibana",
    # Version control
    "Git", "GitHub", "GitLab", "Bitbucket",
    # AI / ML / Data Science
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Scipy",
    "XGBoost", "LightGBM", "CatBoost", "OpenCV", "NLTK", "SpaCy",
    "Transformers", "HuggingFace", "Hugging Face", "BERT", "GPT",
    "LangChain", "LlamaIndex",
    # Big Data
    "Hadoop", "Apache Spark", "Spark", "Apache Kafka", "Kafka",
    "Hive", "Apache Flink", "Flink", "Apache Airflow", "Airflow",
    "dbt", "Dask", "Presto", "Trino", "Snowflake", "Databricks",
    "BigQuery", "Redshift",
    # Testing
    "JUnit", "pytest", "Selenium", "Cypress", "Playwright", "Jest",
    "Mocha", "Jasmine", "Postman", "JMeter", "Appium", "RestAssured",
    # Protocols / tools
    "RESTful", "GraphQL", "WebSocket", "WebRTC", "VoIP",
    "RabbitMQ", "ActiveMQ", "ZeroMQ", "NATS", "Nginx", "Apache", "Tomcat",
    "Microservices", "Serverless", "Linux", "Unix", "Windows Server",
    "Agile", "Scrum", "Jira", "Confluence", "Trello", "Asana",
    "FreeSWITCH", "Asterisk", "Genesys",
    # MLOps / AI infra
    "MLflow", "Kubeflow", "DVC", "Feast",
    "FAISS", "Qdrant", "Milvus", "pgvector", "Pinecone",
    "AutoML", "Vertex AI", "SageMaker",
    # BI / Data tools
    "Power BI", "Tableau", "Looker", "Metabase",
    "Mixpanel", "Google Analytics", "Amplitude",
    "Pentaho", "Talend", "Informatica",
    # Frontend extras
    "Redux", "Zustand", "Recoil", "MobX", "Pinia", "Vuex",
    "Styled Components", "Ant Design", "D3.js", "Recharts", "Chart.js",
    # Security tools
    "Splunk", "QRadar", "Fortinet", "PaloAlto", "CheckPoint", "Imperva", "F5",
    "Cisco", "Juniper",
    # Enterprise systems
    "SAP ERP", "Oracle ERP", "Salesforce", "ServiceNow", "n8n",
    "Power Automate", "Zapier",
]

# ==========================================
# JOB_ROLE DICTIONARY
# ==========================================

JOB_ROLE_KEYWORDS: List[str] = [
    # Quản lý cấp cao
    "Chief Executive Officer", "Chief Technology Officer", "Chief Information Officer",
    "Chief Product Officer", "Chief Data Officer", "Chief Operating Officer",
    "Vice President", "General Manager", "Managing Director",
    "Giám đốc điều hành", "Giám đốc công nghệ", "Giám đốc kỹ thuật",
    "Giám đốc sản phẩm", "Giám đốc dữ liệu", "Giám đốc vận hành",
    "Tổng giám đốc", "Phó giám đốc", "Trưởng phòng", "Phó phòng",
    "Trưởng nhóm", "Trưởng bộ phận", "Quản lý dự án",
    # IT / Tech roles
    "Software Engineer", "Software Developer", "Senior Software Engineer",
    "Junior Software Engineer", "Full Stack Developer", "Full-Stack Developer",
    "Frontend Developer", "Front-end Developer", "Backend Developer", "Back-end Developer",
    "Mobile Developer", "iOS Developer", "Android Developer",
    "DevOps Engineer", "Cloud Engineer", "Data Engineer", "Data Scientist",
    "Data Analyst", "Business Analyst", "System Analyst", "System Administrator",
    "Database Administrator", "Network Engineer", "Security Engineer",
    "QA Engineer", "QA Tester", "Test Engineer", "Automation Engineer",
    "AI Engineer", "ML Engineer", "Machine Learning Engineer",
    "Product Manager", "Project Manager", "Scrum Master", "Tech Lead",
    "Solution Architect", "Technical Architect", "Enterprise Architect",
    "UI/UX Designer", "UX Designer", "UI Designer", "UX Researcher",
    "IT Manager", "IT Director", "IT Specialist", "IT Support",
    # Tiếng Việt
    "Kỹ sư phần mềm", "Lập trình viên", "Nhà phát triển phần mềm",
    "Kỹ sư dữ liệu", "Kỹ sư AI", "Kỹ sư học máy",
    "Kỹ sư hệ thống", "Kỹ sư mạng", "Kỹ sư bảo mật",
    "Kỹ sư DevOps", "Kỹ sư cloud", "Kỹ sư kiểm thử",
    "Chuyên viên phân tích dữ liệu", "Chuyên viên phân tích nghiệp vụ",
    "Chuyên viên phát triển phần mềm", "Chuyên viên IT",
    "Nhà khoa học dữ liệu", "Kiến trúc sư phần mềm",
    "Quản lý sản phẩm", "Quản lý dự án IT",
    "Nhà thiết kế UI", "Nhà thiết kế UX", "Nhà thiết kế giao diện",
    # Roles phổ biến
    "Penetration Tester", "Pentest Engineer",
    "VoIP Engineer", "Telephony Engineer", "Network Security Engineer",
    "Pre-Sale Engineer", "Pre-Sales Engineer",
    "Creative Designer", "Graphic Designer", "Art Designer",
    "IT Helpdesk", "IT Coordinator",
    "Senior AI Engineer", "Junior AI Engineer",
    "Manual Tester", "Automation Tester",
    "BrSE", "Fresher Developer", "Fresher Engineer",
    "DevOps/Cloud Engineer", "Cloud DevOps Engineer",
    "SAP Consultant", "ERP Consultant",
    "Data Lake Engineer", "MLOps Engineer",
    "Lập Trình Viên", "Kỹ Thuật Viên", "Chuyên Viên IT",
    "Nhân Viên IT", "Nhân Viên Triển Khai",
    # Viết tắt
    "CEO", "CTO", "CIO", "CPO", "CDO", "COO", "CFO",
    "VP", "GM", "PM", "PO", "BA", "SA", "DBA",
    "SDE", "SWE", "QA", "QC",
]

# ==========================================
# COMPILE REGEX PATTERNS
# ==========================================

_ABBREV_CASE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in sorted(TECH_ABBREVS_CASE_SENSITIVE, key=len, reverse=True)) + r")\b",
)

_ABBREV_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in sorted(TECH_ABBREVS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_TECH_SORTED = sorted(TECH_KEYWORDS, key=len, reverse=True)
_TECH_PATTERN = re.compile(
    r"(?<![\w.])" + "(" + "|".join(re.escape(t) for t in _TECH_SORTED) + ")" + r"(?![\w.])",
    re.IGNORECASE,
)

_JOB_ROLE_SORTED = sorted(JOB_ROLE_KEYWORDS, key=len, reverse=True)
_JOB_ROLE_PATTERN = re.compile(
    r"(?<![\w.])(" + "|".join(re.escape(j) for j in _JOB_ROLE_SORTED) + r")(?![\w.])",
    re.IGNORECASE,
)

# ==========================================
# EXTRACTION FUNCTIONS
# ==========================================


def _extract_tech(text: str) -> List[str]:
    seen: set = set()
    result: List[str] = []
    for pattern in (_ABBREV_CASE_PATTERN, _ABBREV_PATTERN, _TECH_PATTERN):
        for m in pattern.finditer(text):
            kw = m.group()
            key = kw.lower()
            if key not in seen:
                seen.add(key)
                result.append(kw)
    return result


def _extract_job_roles(text: str) -> List[str]:
    seen: set = set()
    result: List[str] = []
    for m in _JOB_ROLE_PATTERN.finditer(text):
        kw = m.group()
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            result.append(kw)
    return result


def extract_query_entities(query: str) -> dict:
    """
    Trích xuất technologies và job_titles từ câu hỏi user
    bằng dictionary + regex (không cần LLM / API).

    Trả về:
      {"technologies": [...], "job_titles": [...]}
    """
    return {
        "technologies": _extract_tech(query),
        "job_titles":   _extract_job_roles(query),
    }
