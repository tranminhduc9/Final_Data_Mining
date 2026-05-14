// Package entity_extractor provides entity extraction functionality using rule-based approach
package entity_extractor

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"log"
	"regexp"
	"sort"
	"strings"
	"time"
	"unicode"

	"github.com/segmentio/kafka-go"
	"github.com/techpulse/graph_database/pkg/config"
	"github.com/techpulse/graph_database/pkg/models"
)

// Extractor handles entity extraction from articles and jobs
type Extractor struct {
	config *config.Config
	writer *kafka.Writer

	// Tech keywords dictionaries
	techAbbrevCaseSensitive map[string]bool // AI, IT, RPA... (case sensitive)
	techAbbrev              map[string]bool // AWS, API, SQL... (case insensitive)
	techKeywords            []string        // Python, Machine Learning...

	// Regex patterns
	datePatterns     []*regexp.Regexp
	salaryPatterns   []*regexp.Regexp
	jobRolePattern   *regexp.Regexp
	techPattern      *regexp.Regexp
	abbrevPattern    *regexp.Regexp
	abbrevCasePattern *regexp.Regexp

	// Job role keywords
	jobRoleKeywords []string

	// Location keywords
	locationKeywords []string
}

// NewExtractor creates a new entity extractor with comprehensive rule-based patterns
func NewExtractor(cfg *config.Config) *Extractor {
	e := &Extractor{
		config: cfg,
	}
	e.initTechKeywords()
	e.initDatePatterns()
	e.initSalaryPatterns()
	e.initJobRolePatterns()
	e.initLocationKeywords()
	return e
}

func (e *Extractor) initTechKeywords() {
	// Case-sensitive abbreviations (must match exact case: AI, IT, not "ai" in Vietnamese)
	techAbbrevCaseSensitive := []string{
		"AI", "IT", "RPA", "AGI", "NPU", "GPU", "TPU",
	}
	e.techAbbrevCaseSensitive = make(map[string]bool)
	for _, abbr := range techAbbrevCaseSensitive {
		e.techAbbrevCaseSensitive[abbr] = true
	}

	// Case-insensitive abbreviations
	techAbbrev := []string{
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
	e.techAbbrev = make(map[string]bool)
	for _, abbr := range techAbbrev {
		e.techAbbrev[strings.ToLower(abbr)] = true
	}

	// Tech keywords (longer phrases)
	e.techKeywords = []string{
		// AI & ML & Language Models
		"ChatGPT", "Claude", "Gemini", "Copilot", "Grok", "Perplexity", "DeepSeek",
		"OpenAI", "Anthropic", "Mistral", "Llama", "VinAI", "xAI",
		"Trí tuệ nhân tạo", "Machine Learning", "Deep Learning", "Generative AI",
		"GenAI", "AI tạo sinh", "Mô hình ngôn ngữ", "Học máy", "Chatbot",
		"AI Agent", "Tác nhân AI", "Computer Vision",
		"Apple Intelligence", "Siri", "Sora", "Claude Code", "Claude Mythos",
		"Cursor AI", "Odoo", "AI Workplace Service",
		"Deepfake", "GhostChat", "Anatsa", "Stealerium",
		"Ransomware", "Infostealer", "Spyware",
		"Zero Trust", "iVerify", "Lookout", "Kaspersky", "Malwarebytes",
		"Zscaler", "Proofpoint", "BreachForums", "nTrust",
		"iCallme", "Verichains", "IDMerit",
		"Watering hole", "SIM swap", "Pig Butchering",
		"Snapdragon", "Tensor", "Apple Silicon", "Qualcomm",
		"chip quang tử", "qubit",
		"Data Center", "AI Data Center", "Trung tâm dữ liệu",
		"Public Cloud", "Private Cloud", "Hybrid Cloud",
		"AI Readiness", "AI-First",

		// Programming Languages
		"Python", "Java", "JavaScript", "TypeScript",
		"Golang", "Rust", "Kotlin", "Swift", "Scala", "Ruby", "PHP",
		"Perl", "Dart", "Lua", "Groovy", "Elixir", "Erlang", "Haskell",
		"MATLAB", "Julia", "Visual Basic", "Objective-C",
		"C++", "C#",

		// Web Front-end
		"React", "ReactJS", "React.js", "Vue", "VueJS", "Vue.js",
		"Angular", "AngularJS", "Next.js", "Nuxt.js", "Svelte", "jQuery",
		"Bootstrap", "Tailwind", "TailwindCSS", "Sass", "SCSS", "Less",
		"Webpack", "Vite", "Babel",

		// Web Back-end
		"Node.js", "NodeJS", "Express", "ExpressJS", "NestJS", "Django",
		"Flask", "FastAPI", "Spring Boot", "Spring", "SpringBoot",
		"Laravel", "Symfony", "Rails", "Ruby on Rails", "ASP.NET", ".NET",
		"Gin", "Echo", "Fiber",

		// Database / Datastore
		"MySQL", "PostgreSQL", "MariaDB", "SQLite", "MSSQL", "SQL Server",
		"Oracle", "MongoDB", "Redis", "Cassandra", "DynamoDB", "Elasticsearch",
		"HBase", "CouchDB", "Neo4j", "InfluxDB", "Firebase", "Firestore",
		"Supabase", "PlanetScale",

		// Cloud & Infra
		"Azure", "Google Cloud", "Google Cloud Platform",
		"Alibaba Cloud", "DigitalOcean", "CloudFront",
		"Cloudflare", "Vercel", "Netlify", "Heroku",

		// DevOps / CI/CD / Container
		"Docker", "Kubernetes", "K8s", "Jenkins", "GitLab CI", "GitHub Actions",
		"CircleCI", "Travis CI", "Ansible", "Terraform", "Puppet", "Chef",
		"Helm", "ArgoCD", "Prometheus", "Grafana", "Logstash", "Kibana",

		// Version control
		"Git", "GitHub", "GitLab", "Bitbucket",

		// AI / ML / Data Science
		"TensorFlow", "PyTorch", "Keras", "Scikit-learn",
		"Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Scipy",
		"XGBoost", "LightGBM", "CatBoost", "OpenCV", "NLTK", "SpaCy",
		"Transformers", "HuggingFace", "Hugging Face", "BERT", "GPT",
		"LangChain", "LlamaIndex",

		// Big Data
		"Hadoop", "Apache Spark", "Spark", "Apache Kafka", "Kafka",
		"Hive", "Apache Flink", "Flink", "Apache Airflow", "Airflow",
		"dbt", "Dask", "Presto", "Trino", "Snowflake", "Databricks",
		"BigQuery", "Redshift",

		// Testing
		"JUnit", "pytest", "Selenium", "Cypress", "Playwright", "Jest",
		"Mocha", "Jasmine", "Postman", "JMeter", "Appium", "RestAssured",

		// Protocols / tools
		"RESTful", "GraphQL", "WebSocket", "WebRTC", "VoIP",
		"RabbitMQ", "ActiveMQ", "ZeroMQ", "NATS", "Nginx", "Apache", "Tomcat",
		"Microservices", "Serverless", "Linux", "Unix", "Windows Server",
		"Agile", "Scrum", "Jira", "Confluence", "Trello", "Asana",
		"FreeSWITCH", "Asterisk", "Genesys",

		// MLOps / AI infra
		"MLflow", "Kubeflow", "DVC", "Feast",
		"FAISS", "Qdrant", "Milvus", "pgvector", "Pinecone",
		"AutoML", "Vertex AI", "SageMaker",

		// BI / Data tools
		"Power BI", "Tableau", "Looker", "Metabase",
		"Mixpanel", "Google Analytics", "Amplitude",
		"Pentaho", "Talend", "Informatica",

		// Frontend extras
		"Redux", "Zustand", "Recoil", "MobX", "Pinia", "Vuex",
		"Styled Components", "Emotion", "Ant Design", "Element Plus", "Vuetify",
		"D3.js", "Recharts", "TradingView", "Chart.js",

		// Security tools
		"Splunk", "QRadar", "Trellix", "Symantec", "Trend Micro",
		"Fortinet", "PaloAlto", "CheckPoint", "Imperva", "F5",
		"SonicWALL", "Barracuda", "Cisco", "Juniper", "Aruba",

		// 3D / Design tools
		"Blender", "Cinema4D", "Unity", "Unreal", "SketchUp",
		"Revit", "Rhino", "3ds Max", "V-Ray", "Lumion", "Enscape",
		"Substance 3D", "Figma", "Adobe Photoshop", "Adobe Illustrator",
		"Adobe Premiere", "After Effects", "InDesign", "CapCut",

		// Enterprise systems
		"SAP ERP", "Oracle ERP", "Salesforce", "ServiceNow", "n8n",
		"Power Automate", "Zapier",

		// AI Models & Products
		"Muse Spark", "TurboQuant", "Gemma 4", "DLSS 5", "OpenClaw",
		"Atlas 350", "Agents SDK", "Project Glasswing", "Constitutional AI",
		"Trinity Large Thinking", "Claude Opus",
		"Gemini CLI", "Google AI Edge Eloquent", "WisperFlow", "SuperWhisper",

		// AI concepts
		"agentic AI", "Physical AI", "vibe-coding", "vibe coding",
		"KV cache", "frame generation", "ray tracing",
		"sideloading", "AI Factory", "AI inference", "AI reasoning",
		"Sovereign Cloud", "reCAPTCHA", "AI streamer",

		// AI Models
		"GPT-5.4", "GPT-5.3", "GPT-5.2", "GPT-4o",
		"Gemini 3", "Gemini 3 Flash", "Gemini 3.1 Flash", "Gemini 2.5",
		"Nano Banana", "Nano Banana Pro", "Personal Intelligence",
		"Images 2.0", "TurboDiffusion", "NeMoClaw",
		"Mixture of Experts", "Mô hình hỗn hợp chuyên gia",

		// AI concepts
		"AI washing", "Content Credentials", "peer preservation",
		"adversarial poetry", "Predictive AI", "Foundation Models",
		"Model Extraction", "Grokipedia",
		"Iceberg Index", "exaflop", "petaflop",
		"Cursor", "Claude Code",
	}

	// Sort by length descending for regex matching
	sort.Slice(e.techKeywords, func(i, j int) bool {
		return len(e.techKeywords[i]) > len(e.techKeywords[j])
	})

	// Build regex patterns for tech keywords
	e.buildTechPatterns()
}

func (e *Extractor) buildTechPatterns() {
	// Case-sensitive abbreviations pattern
	abbrevCaseList := make([]string, 0)
	for abbr := range e.techAbbrevCaseSensitive {
		abbrevCaseList = append(abbrevCaseList, regexp.QuoteMeta(abbr))
	}
	sort.Slice(abbrevCaseList, func(i, j int) bool {
		return len(abbrevCaseList[i]) > len(abbrevCaseList[j])
	})
	e.abbrevCasePattern = regexp.MustCompile(`\b(` + strings.Join(abbrevCaseList, "|") + `)\b`)

	// Case-insensitive abbreviations pattern
	abbrevList := make([]string, 0)
	for abbr := range e.techAbbrev {
		abbrevList = append(abbrevList, regexp.QuoteMeta(abbr))
	}
	sort.Slice(abbrevList, func(i, j int) bool {
		return len(abbrevList[i]) > len(abbrevList[j])
	})
	e.abbrevPattern = regexp.MustCompile(`(?i)\b(` + strings.Join(abbrevList, "|") + `)\b`)

	// Tech keywords pattern - use word boundaries instead of lookbehind
	// Go regexp (RE2) doesn't support lookbehind assertions
	escapedKeywords := make([]string, len(e.techKeywords))
	for i, kw := range e.techKeywords {
		escapedKeywords[i] = regexp.QuoteMeta(kw)
	}
	e.techPattern = regexp.MustCompile(`(?i)\b(` + strings.Join(escapedKeywords, "|") + `)\b`)
}

func (e *Extractor) initDatePatterns() {
	patterns := []string{
		// ngày dd tháng mm năm YYYY (tiếng Việt đầy đủ)
		`(?i)\b(ng[aà]y\s+\d{1,2}\s+th[aá]ng\s+\d{1,2}(?:\s+n[aă]m\s+\d{4})?)\b`,
		// tháng X năm YYYY / tháng X
		`(?i)\b(th[aá]ng\s+\d{1,2}(?:\s+n[aă]m\s+\d{4})?)\b`,
		// Quý I/II/III/IV hoặc Q1–4 + năm tuỳ chọn
		`(?i)\b(Qu[yý]\s+(?:I{1,3}|IV|[1-4])(?:\s*/\s*\d{4})?)\b`,
		`\b(Q[1-4]\s*/\s*\d{4})\b`,
		// dd/mm/yyyy hoặc dd-mm-yyyy
		`\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\b`,
		// mm/yyyy hoặc mm-yyyy - use word boundary instead of lookbehind
		`\b(\d{1,2}[/\-]\d{4})\b`,
		// Tên tháng tiếng Anh + YYYY
		`(?i)\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b`,
		// năm YYYY đứng sau từ 'năm' hoặc 'year'
		`(?i)\b(?:n[aă]m|year)\s+((?:19|20)\d{2})\b`,
		// Thứ trong tuần
		`(?i)\b(Th[ứu]\s+(?:[2-7]|Hai|Ba|Tư|Năm|Sáu|B[aả]y))\b`,
	}

	for _, p := range patterns {
		re, err := regexp.Compile(p)
		if err == nil {
			e.datePatterns = append(e.datePatterns, re)
		}
	}
}

func (e *Extractor) initSalaryPatterns() {
	patterns := []string{
		// X - Y triệu
		`(?i)\b(\d+(?:[,.]\d+)?\s*[-–]\s*\d+(?:[,.]\d+)?\s*tri[eệ]u(?:\s*VNĐ|\s*VND|\s*đồng)?)\b`,
		// X triệu
		`(?i)\b(\d+(?:[,.]\d+)?\s*tri[eệ]u(?:\s*VNĐ|\s*VND|\s*đồng)?)\b`,
		// upto/up to X triệu
		`(?i)\b(upto\s+\d+(?:[,.]\d+)?(?:M|\s*tri[eệ]u|\s*VNĐ|\s*VND)?)\b`,
		`(?i)\b(up\s+to\s+\$?\d+(?:[,.]\d+)?(?:[,.]\d{3})*(?:\s*USD|\s*VND|\s*VNĐ|\s*tri[eệ]u)?)\b`,
		// từ X triệu
		`(?i)\b(t[ừu]\s+\d+(?:[,.]\d+)?(?:\s*đến\s+\d+(?:[,.]\d+)?)?\s*tri[eệ]u(?:\s*VNĐ|\s*VND)?)\b`,
		// $X,XXX - $Y,XXX
		`(\$\d{1,3}(?:,\d{3})*(?:\s*[-–]\s*\$\d{1,3}(?:,\d{3})*)?(?:\+)?(?:\s*USD|\s*VND|\s*VNĐ)?)`,
		// 10,000,000 VNĐ
		`\b(\d{1,3}(?:[,.]\d{3})+(?:\s*VNĐ|\s*VND|\s*đồng|đ)?)\b`,
		// lương thương lượng, cạnh tranh
		`(?i)\b(lương\s+(?:thương\s+lượng|cạnh\s+tranh|hấp\s+dẫn|theo\s+năng\s+lực|thoả\s+thuận|thỏa\s+thuận))\b`,
		`(?i)\b(thu\s+nhập\s+(?:cạnh\s+tranh|hấp\s+dẫn|theo\s+năng\s+lực))\b`,
		`(?i)\b(salary\s+(?:negotiable|competitive|attractive))\b`,
		`(?i)\b(competitive\s+salary(?:\s+range)?)\b`,
	}

	for _, p := range patterns {
		re, err := regexp.Compile(p)
		if err == nil {
			e.salaryPatterns = append(e.salaryPatterns, re)
		}
	}
}

func (e *Extractor) initJobRolePatterns() {
	e.jobRoleKeywords = []string{
		// Management
		"Chief Executive Officer", "Chief Technology Officer", "Chief Information Officer",
		"Chief Product Officer", "Chief Data Officer", "Chief Operating Officer",
		"Vice President", "General Manager", "Managing Director",
		"Giám đốc điều hành", "Giám đốc công nghệ", "Giám đốc kỹ thuật",
		"Giám đốc sản phẩm", "Giám đốc dữ liệu", "Giám đốc vận hành",
		"Tổng giám đốc", "Phó giám đốc", "Trưởng phòng", "Phó phòng",
		"Trưởng nhóm", "Trưởng bộ phận", "Quản lý dự án",

		// IT / Tech roles
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

		// Vietnamese roles
		"Kỹ sư phần mềm", "Lập trình viên", "Nhà phát triển phần mềm",
		"Kỹ sư dữ liệu", "Kỹ sư AI", "Kỹ sư học máy",
		"Kỹ sư hệ thống", "Kỹ sư mạng", "Kỹ sư bảo mật",
		"Kỹ sư DevOps", "Kỹ sư cloud", "Kỹ sư kiểm thử",
		"Chuyên viên phân tích dữ liệu", "Chuyên viên phân tích nghiệp vụ",
		"Chuyên viên phát triển phần mềm", "Chuyên viên IT",
		"Nhà khoa học dữ liệu", "Kiến trúc sư phần mềm",
		"Quản lý sản phẩm", "Quản lý dự án IT",
		"Nhà thiết kế UI", "Nhà thiết kế UX", "Nhà thiết kế giao diện",

		// Common roles
		"Penetration Tester", "Pentest Engineer",
		"VoIP Engineer", "Telephony Engineer", "Network Security Engineer",
		"Pre-Sale Engineer", "Pre-Sales Engineer",
		"Creative Designer", "Graphic Designer", "Art Designer",
		"UI/UX Researcher", "Motion Designer", "3D Designer",
		"IT Helpdesk", "IT Coordinator",
		"Senior AI Engineer", "Junior AI Engineer",
		"Manual Tester", "Automation Tester",
		"BrSE", "Fresher Developer", "Fresher Engineer",
		"DevOps/Cloud Engineer", "Cloud DevOps Engineer",
		"SAP Consultant", "ERP Consultant",
		"Data Lake Engineer", "MLOps Engineer",
		"Lập Trình Viên", "Kỹ Thuật Viên", "Chuyên Viên IT",
		"Nhân Viên IT", "Nhân Viên Triển Khai",

		// Abbreviations
		"CEO", "CTO", "CIO", "CPO", "CDO", "COO", "CFO",
		"VP", "GM", "PM", "PO", "BA", "SA", "DBA",
		"SDE", "SWE", "QA", "QC",
	}

	// Sort by length descending
	sort.Slice(e.jobRoleKeywords, func(i, j int) bool {
		return len(e.jobRoleKeywords[i]) > len(e.jobRoleKeywords[j])
	})

	// Build regex pattern
	escaped := make([]string, len(e.jobRoleKeywords))
	for i, kw := range e.jobRoleKeywords {
		escaped[i] = regexp.QuoteMeta(kw)
	}
	e.jobRolePattern = regexp.MustCompile(`(?i)\b(` + strings.Join(escaped, "|") + `)\b`)
}

func (e *Extractor) initLocationKeywords() {
	e.locationKeywords = []string{
		"Việt Nam", "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng",
		"TP.HCM", "TP HCM", "Sài Gòn", "Huế", "Cần Thơ",
		"Mỹ", "USA", "United States", "Canada", "UK", "Anh", "Nhật", "Japan",
		"Trung Quốc", "China", "Hàn Quốc", "Korea", "Singapore",
		"Thái Lan", "Thailand", "Ấn Độ", "India", "Châu Âu", "Europe",
		"Đồng Nai", "Bình Dương", "Long An", "Bà Rịa", "Vũng Tàu",
		"Nghệ An", "Thanh Hóa", "Thừa Thiên", "Quảng Ninh",
	}
}

// Connect establishes connections to Kafka
func (e *Extractor) Connect() {
	e.writer = &kafka.Writer{
		Addr:     kafka.TCP(e.config.Kafka.Brokers...),
		Balancer: &kafka.LeastBytes{},
	}
}

// Close closes all connections
func (e *Extractor) Close() {
	if e.writer != nil {
		e.writer.Close()
	}
}

// Entity represents a single extracted entity
type Entity struct {
	Text  string  `json:"entity"`
	Label string  `json:"label"`
	Score float64 `json:"score"`
}

// EntityGroups represents grouped entities by type
// Note: PER removed - person extraction disabled due to low accuracy with rule-based approach
type EntityGroups struct {
	ORG      []string `json:"ORG,omitempty"`
	LOC      []string `json:"LOC,omitempty"`
	DATE     []string `json:"DATE,omitempty"`
	TECH     []string `json:"TECH,omitempty"`
	JOB_ROLE []string `json:"JOB_ROLE,omitempty"`
	SALARY   []string `json:"SALARY,omitempty"`
}

// normalizeTechName chuẩn hóa tên công nghệ về dạng chính thức
// VD: "llm", "Llm", "LLM" → "LLM"; "python", "Python" → "Python"
func (e *Extractor) normalizeTechName(text string) string {
	textLower := strings.ToLower(text)
	
	// Kiểm tra case-sensitive abbreviations (AI, IT, GPU...)
	if e.techAbbrevCaseSensitive[text] {
		return text // Giữ nguyên nếu đúng case
	}
	
	// Kiểm tra case-insensitive abbreviations → uppercase
	for abbr := range e.techAbbrev {
		if abbr == textLower {
			return strings.ToUpper(abbr) // AWS, API, SQL...
		}
	}
	
	// Kiểm tra tech keywords → title case hoặc original form
	for _, kw := range e.techKeywords {
		if strings.ToLower(kw) == textLower {
			return kw // Trả về form chuẩn từ dictionary
		}
	}
	
	// Fallback: title case
	return strings.Title(text)
}

// extractTech extracts technology entities from text
// Tất cả entities được normalize NGAY khi trích xuất để tránh duplicate
func (e *Extractor) extractTech(text string) []Entity {
	seen := make(map[string]bool) // key là lowercase của normalized name
	var entities []Entity

	// Case-sensitive abbreviations (AI, IT, etc.) - giữ nguyên case
	if e.abbrevCasePattern != nil {
		matches := e.abbrevCasePattern.FindAllString(text, -1)
		for _, match := range matches {
			// Normalize ngay và dùng normalized làm key
			normalized := match // Case-sensitive giữ nguyên
			key := strings.ToLower(normalized)
			if !seen[key] {
				seen[key] = true
				entities = append(entities, Entity{Text: normalized, Label: "TECH", Score: 1.0})
			}
		}
	}

	// Case-insensitive abbreviations - chuẩn hóa thành UPPERCASE
	if e.abbrevPattern != nil {
		matches := e.abbrevPattern.FindAllString(text, -1)
		for _, match := range matches {
			// Normalize thành UPPERCASE
			normalized := strings.ToUpper(match)
			key := strings.ToLower(normalized)
			if !seen[key] {
				seen[key] = true
				entities = append(entities, Entity{Text: normalized, Label: "TECH", Score: 1.0})
			}
		}
	}

	// Tech keywords - chuẩn hóa theo dictionary
	if e.techPattern != nil {
		matches := e.techPattern.FindAllString(text, -1)
		for _, match := range matches {
			// Normalize theo dictionary
			normalized := e.normalizeTechName(match)
			key := strings.ToLower(normalized)
			if !seen[key] {
				seen[key] = true
				entities = append(entities, Entity{Text: normalized, Label: "TECH", Score: 1.0})
			}
		}
	}

	return entities
}

// extractDates extracts date entities from text
func (e *Extractor) extractDates(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity
	coveredSpans := make([][2]int, 0)

	for _, pattern := range e.datePatterns {
		matches := pattern.FindAllStringIndex(text, -1)
		for _, match := range matches {
			if len(match) >= 2 {
				start, end := match[0], match[1]
				// Check overlap
				overlaps := false
				for _, span := range coveredSpans {
					if start < span[1] && end > span[0] {
						overlaps = true
						break
					}
				}
				if !overlaps {
					coveredSpans = append(coveredSpans, [2]int{start, end})
					dateText := strings.TrimSpace(text[start:end])
					if !seen[strings.ToLower(dateText)] {
						seen[strings.ToLower(dateText)] = true
						entities = append(entities, Entity{Text: dateText, Label: "DATE", Score: 1.0})
					}
				}
			}
		}
	}

	return entities
}

// extractSalary extracts salary entities from text
func (e *Extractor) extractSalary(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity
	coveredSpans := make([][2]int, 0)

	for _, pattern := range e.salaryPatterns {
		matches := pattern.FindAllStringIndex(text, -1)
		for _, match := range matches {
			if len(match) >= 2 {
				start, end := match[0], match[1]
				// Check overlap
				overlaps := false
				for _, span := range coveredSpans {
					if start < span[1] && end > span[0] {
						overlaps = true
						break
					}
				}
				if !overlaps {
					coveredSpans = append(coveredSpans, [2]int{start, end})
					salaryText := strings.TrimSpace(text[start:end])
					if !seen[strings.ToLower(salaryText)] {
						seen[strings.ToLower(salaryText)] = true
						entities = append(entities, Entity{Text: salaryText, Label: "SALARY", Score: 1.0})
					}
				}
			}
		}
	}

	return entities
}

// extractJobRoles extracts job role entities from text
func (e *Extractor) extractJobRoles(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity

	if e.jobRolePattern != nil {
		matches := e.jobRolePattern.FindAllString(text, -1)
		for _, match := range matches {
			key := strings.ToLower(match)
			if !seen[key] {
				seen[key] = true
				entities = append(entities, Entity{Text: match, Label: "JOB_ROLE", Score: 1.0})
			}
		}
	}

	return entities
}

// extractLocation extracts location entities from text using word boundaries
func (e *Extractor) extractLocation(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity

	// Build location pattern - use word boundary instead of lookbehind
	// Go regexp (RE2) doesn't support lookbehind assertions
	escapedLocs := make([]string, len(e.locationKeywords))
	for i, loc := range e.locationKeywords {
		escapedLocs[i] = regexp.QuoteMeta(loc)
	}
	locPattern := regexp.MustCompile(`(?i)\b(` + strings.Join(escapedLocs, "|") + `)\b`)
	
	matches := locPattern.FindAllString(text, -1)
	for _, match := range matches {
		key := strings.ToLower(match)
		if !seen[key] {
			seen[key] = true
			entities = append(entities, Entity{Text: match, Label: "LOC", Score: 1.0})
		}
	}

	return entities
}

// extractOrg extracts organization entities from text using suffix patterns
func (e *Extractor) extractOrg(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity

	suffixes := []string{"Corp", "Inc", "Ltd", "LLC", "Company", "Group", "JSC", "Co.", "Corporation"}
	words := strings.Fields(text)

	for i, word := range words {
		for _, suffix := range suffixes {
			if strings.Contains(word, suffix) || strings.HasSuffix(word, suffix) {
				start := i - 2
				if start < 0 {
					start = 0
				}
				end := i + 2
				if end > len(words) {
					end = len(words)
				}
				orgName := strings.Join(words[start:end], " ")
				orgName = cleanEntity(orgName)
				if orgName != "" && !seen[strings.ToLower(orgName)] {
					seen[strings.ToLower(orgName)] = true
					entities = append(entities, Entity{Text: orgName, Label: "ORG", Score: 1.0})
				}
			}
		}
	}

	return entities
}

// isTechKeyword checks if a word is a tech keyword
func (e *Extractor) isTechKeyword(word string) bool {
	wordLower := strings.ToLower(word)
	// Check in abbrev maps
	if e.techAbbrevCaseSensitive[word] || e.techAbbrev[wordLower] {
		return true
	}
	// Check in keywords slice
	for _, kw := range e.techKeywords {
		if strings.ToLower(kw) == wordLower {
			return true
		}
	}
	return false
}

// extractPerson extracts person name entities from text
func (e *Extractor) extractPerson(text string) []Entity {
	seen := make(map[string]bool)
	var entities []Entity
	words := strings.Fields(text)

	for i, word := range words {
		// Check if word starts with uppercase and is not a tech keyword
		if len(word) > 2 && unicode.IsUpper(rune(word[0])) {
			// Skip if it's a tech keyword
			if e.isTechKeyword(word) {
				continue
			}

			// Look for consecutive capitalized words (potential names)
			if i+1 < len(words) {
				nextWord := words[i+1]
				if len(nextWord) > 1 && unicode.IsUpper(rune(nextWord[0])) {
					if !e.isTechKeyword(nextWord) {
						name := word + " " + nextWord
						name = cleanEntity(name)
						if name != "" && !seen[strings.ToLower(name)] {
							seen[strings.ToLower(name)] = true
							entities = append(entities, Entity{Text: name, Label: "PER", Score: 1.0})
						}
					}
				}
			}
		}
	}

	return entities
}

// cleanEntity normalizes entity text
func cleanEntity(text string) string {
	// Remove subword artifacts
	text = strings.ReplaceAll(text, "▁", "")
	text = strings.ReplaceAll(text, "\u2581", "")

	// Collapse whitespace
	text = strings.Join(strings.Fields(text), " ")

	// Strip punctuation from ends
	text = strings.Trim(text, ".,;:\"'()[]{}")

	return strings.TrimSpace(text)
}

// groupEntities groups entities by their label
func groupEntities(entities []Entity) EntityGroups {
	groups := EntityGroups{
		ORG:      make([]string, 0),
		LOC:      make([]string, 0),
		DATE:     make([]string, 0),
		TECH:     make([]string, 0),
		JOB_ROLE: make([]string, 0),
		SALARY:   make([]string, 0),
	}

	seen := make(map[string]map[string]bool)
	for _, label := range []string{"ORG", "LOC", "DATE", "TECH", "JOB_ROLE", "SALARY"} {
		seen[label] = make(map[string]bool)
	}

	for _, ent := range entities {
		text := cleanEntity(ent.Text)
		if text == "" {
			continue
		}

		label := ent.Label
		if seen[label] == nil {
			continue
		}

		key := strings.ToLower(text)
		if !seen[label][key] {
			seen[label][key] = true
			switch label {
			case "ORG":
				groups.ORG = append(groups.ORG, text)
			case "LOC":
				groups.LOC = append(groups.LOC, text)
			case "DATE":
				groups.DATE = append(groups.DATE, text)
			case "TECH":
				groups.TECH = append(groups.TECH, text)
			case "JOB_ROLE":
				groups.JOB_ROLE = append(groups.JOB_ROLE, text)
			case "SALARY":
				groups.SALARY = append(groups.SALARY, text)
			}
		}
	}

	return groups
}

// ExtractAll extracts all entity types from text and returns grouped entities
// Note: extractPerson is disabled because rule-based approach produces too many false positives
// Person name extraction should use NER model (like PhoBERT) for better accuracy
func (e *Extractor) ExtractAll(text string) EntityGroups {
	var allEntities []Entity

	// Extract each entity type
	allEntities = append(allEntities, e.extractTech(text)...)
	allEntities = append(allEntities, e.extractDates(text)...)
	allEntities = append(allEntities, e.extractSalary(text)...)
	allEntities = append(allEntities, e.extractJobRoles(text)...)
	allEntities = append(allEntities, e.extractLocation(text)...)
	allEntities = append(allEntities, e.extractOrg(text)...)
	// allEntities = append(allEntities, e.extractPerson(text)...) // Disabled: too many false positives

	return groupEntities(allEntities)
}

// ProcessArticle extracts entities from an article
func (e *Extractor) ProcessArticle(raw *models.RawArticle) *models.ExtractedArticle {
	fullText := raw.Data.Title + " " + raw.Data.Content
	groups := e.ExtractAll(fullText)

	entities := models.Entities{
		TECH:     groups.TECH,
		ORG:      groups.ORG,
		LOC:      groups.LOC,
		DATE:     groups.DATE,
		JOB_ROLE: groups.JOB_ROLE,
		SALARY:   groups.SALARY,
	}

	return &models.ExtractedArticle{
		MessageType:    "extracted_article",
		SourcePlatform: raw.SourcePlatform,
		CrawledAt:      raw.CrawledAt,
		ExtractedAt:    time.Now(),
		Data: models.ExtractedArticleData{
			Title:       raw.Data.Title,
			PublishDate: raw.Data.PublishDate,
			Content:     raw.Data.Content,
			SourceURL:   raw.Data.SourceURL,
			Entities:    entities,
		},
	}
}

// ProcessJob extracts entities from a job posting
func (e *Extractor) ProcessJob(raw *models.RawJob) *models.ExtractedJob {
	fullText := raw.Data.JobTitle + " " + raw.Data.Description + " " + raw.Data.Requirement
	groups := e.ExtractAll(fullText)

	// Merge extracted tech with provided skills
	techSet := make(map[string]bool)
	for _, tech := range groups.TECH {
		techSet[tech] = true
	}
	for _, skill := range raw.Data.Skills {
		techSet[skill] = true
	}
	technologies := make([]string, 0, len(techSet))
	for tech := range techSet {
		technologies = append(technologies, tech)
	}

	entities := models.Entities{
		TECH:     technologies,
		ORG:      groups.ORG,
		LOC:      groups.LOC,
		DATE:     groups.DATE,
		JOB_ROLE: groups.JOB_ROLE,
		SALARY:   groups.SALARY,
	}

	return &models.ExtractedJob{
		MessageType:    "extracted_job",
		SourcePlatform: raw.SourcePlatform,
		CrawledAt:      raw.CrawledAt,
		ExtractedAt:    time.Now(),
		Data: models.ExtractedJobData{
			Job: models.JobInfo{
				Title:       raw.Data.JobTitle,
				Description: raw.Data.Description,
				Requirement: raw.Data.Requirement,
				Benefit:     raw.Data.Benefit,
				Salary:      raw.Data.Salary,
				DueDate:     "",
				SourceURL:   raw.Data.SourceURL,
			},
			Company: models.CompanyInfo{
				Name:     raw.Data.CompanyName,
				Size:     "",
				Field:    "",
				Location: raw.Data.Location,
			},
			Skills:       raw.Data.Skills,
			Technologies: technologies,
			Entities:     entities,
		},
	}
}

// Run starts the entity extraction service
func (e *Extractor) Run(ctx context.Context) error {
	articleReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  e.config.Kafka.Brokers,
		Topic:    e.config.Kafka.TopicRawArticles,
		GroupID:  config.GroupEntityExtractor,
		MinBytes: 1,
		MaxBytes: 10e6,
	})
	defer articleReader.Close()

	jobReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  e.config.Kafka.Brokers,
		Topic:    e.config.Kafka.TopicRawJobs,
		GroupID:  config.GroupEntityExtractor,
		MinBytes: 1,
		MaxBytes: 10e6,
	})
	defer jobReader.Close()

	errChan := make(chan error, 2)

	// Process articles in a separate goroutine
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			default:
				msg, err := articleReader.ReadMessage(ctx)
				if err != nil {
					if ctx.Err() != nil {
						return
					}
					log.Printf("Error reading article message: %v", err)
					continue
				}
				e.processArticleMessage(ctx, msg)
			}
		}
	}()

	// Process jobs in a separate goroutine
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			default:
				msg, err := jobReader.ReadMessage(ctx)
				if err != nil {
					if ctx.Err() != nil {
						return
					}
					log.Printf("Error reading job message: %v", err)
					continue
				}
				e.processJobMessage(ctx, msg)
			}
		}
	}()

	// Wait for context cancellation or error
	select {
	case <-ctx.Done():
		return ctx.Err()
	case err := <-errChan:
		return err
	}
}

func (e *Extractor) processArticleMessage(ctx context.Context, msg kafka.Message) {
	var rawArticle models.RawArticle
	if err := json.Unmarshal(msg.Value, &rawArticle); err != nil {
		log.Printf("Error unmarshaling article: %v", err)
		return
	}
	extracted := e.ProcessArticle(&rawArticle)
	key := generateMD5(rawArticle.Data.SourceURL)
	data, _ := json.Marshal(extracted)
	err := e.writer.WriteMessages(ctx, kafka.Message{
		Topic: e.config.Kafka.TopicExtractedArticles,
		Key:   []byte(key),
		Value: data,
	})
	if err != nil {
		log.Printf("Error publishing extracted article: %v", err)
	} else {
		log.Printf("Extracted entities from article: %s", truncate(rawArticle.Data.Title, 50))
	}
}

func (e *Extractor) processJobMessage(ctx context.Context, msg kafka.Message) {
	var rawJob models.RawJob
	if err := json.Unmarshal(msg.Value, &rawJob); err != nil {
		log.Printf("Error unmarshaling job: %v", err)
		return
	}
	extracted := e.ProcessJob(&rawJob)
	key := generateMD5(rawJob.Data.SourceURL)
	data, _ := json.Marshal(extracted)
	err := e.writer.WriteMessages(ctx, kafka.Message{
		Topic: e.config.Kafka.TopicExtractedJobs,
		Key:   []byte(key),
		Value: data,
	})
	if err != nil {
		log.Printf("Error publishing extracted job: %v", err)
	} else {
		log.Printf("Extracted entities from job: %s", truncate(rawJob.Data.JobTitle, 50))
	}
}

func generateMD5(s string) string {
	hash := md5.Sum([]byte(s))
	return hex.EncodeToString(hash[:])
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}
