// Package neo4j_writer handles writing data to Neo4j
package neo4j_writer

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	"github.com/segmentio/kafka-go"
	"github.com/techpulse/graph_database/pkg/config"
	"github.com/techpulse/graph_database/pkg/models"
)

// Writer handles writing data to Neo4j
type Writer struct {
	config *config.Config
	driver neo4j.DriverWithContext
}

// NewWriter creates a new Neo4j writer
func NewWriter(cfg *config.Config) *Writer {
	return &Writer{config: cfg}
}

// Connect establishes connection to Neo4j
func (w *Writer) Connect(ctx context.Context) error {
	var err error
	w.driver, err = neo4j.NewDriverWithContext(
		w.config.Neo4j.URI,
		neo4j.BasicAuth(w.config.Neo4j.Username, w.config.Neo4j.Password, ""),
	)
	if err != nil {
		return fmt.Errorf("failed to create Neo4j driver: %w", err)
	}

	err = w.driver.VerifyConnectivity(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to Neo4j: %w", err)
	}

	log.Printf("Connected to Neo4j at %s", w.config.Neo4j.URI)
	return nil
}

// CreateConstraints creates unique constraints in Neo4j
func (w *Writer) CreateConstraints(ctx context.Context) error {
	session := w.driver.NewSession(ctx, neo4j.SessionConfig{})
	defer session.Close(ctx)

	constraints := []string{
		"CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
		"CREATE CONSTRAINT IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE",
		"CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE",
		"CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
		"CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
		// Person constraint removed - no longer extracting Person entities
		"CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
	}

	for _, constraint := range constraints {
		_, err := session.Run(ctx, constraint, nil)
		if err != nil {
			log.Printf("Warning creating constraint: %v", err)
		}
	}

	log.Println("Neo4j constraints created/verified")
	return nil
}

// Close closes the Neo4j connection
func (w *Writer) Close() {
	if w.driver != nil {
		w.driver.Close(context.Background())
	}
}

// WriteArticle writes an article and its entities to Neo4j
func (w *Writer) WriteArticle(ctx context.Context, article *models.ExtractedArticle) error {
	session := w.driver.NewSession(ctx, neo4j.SessionConfig{})
	defer session.Close(ctx)

	articleID := generateMD5(article.Data.SourceURL)

	_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
		// Create Article node
		_, err := tx.Run(ctx, `
			MERGE (a:Article {id: $id})
			SET a.title = $title,
			    a.content = $content,
			    a.url = $source_url,
			    a.source_platform = $source_platform,
			    a.published_date = $publish_date
		`, map[string]any{
			"id":              articleID,
			"title":           article.Data.Title,
			"content":         article.Data.Content,
			"source_url":      article.Data.SourceURL,
			"source_platform": article.SourcePlatform,
			"publish_date":    article.Data.PublishDate,
		})
		if err != nil {
			return nil, err
		}

		// Create Technology nodes and relationships (normalized to uppercase for consistency)
		for _, tech := range article.Data.Entities.TECH {
			normalizedTech := normalizeTechName(tech)
			if normalizedTech == "" {
				continue
			}
			_, err = tx.Run(ctx, `
				MERGE (t:Technology {name: $tech})
				SET t.mention_count = COALESCE(t.mention_count, 0) + 1
				WITH t
				MATCH (a:Article {id: $article_id})
				MERGE (a)-[:MENTIONS]->(t)
			`, map[string]any{
				"tech":        normalizedTech,
				"article_id":  articleID,
			})
			if err != nil {
				log.Printf("Error creating tech relationship: %v", err)
			}
		}

		// Create Organization/Company nodes and relationships
		// ORG entities are treated as Company nodes
		for _, org := range article.Data.Entities.ORG {
			cleanedOrg := cleanEntity(org)
			if cleanedOrg == "" {
				continue
			}
			companyID := slugify(cleanedOrg)
			_, err = tx.Run(ctx, `
				MERGE (c:Company {id: $company_id})
				SET c.name = $company_name
				WITH c
				MATCH (a:Article {id: $article_id})
				MERGE (a)-[:MENTIONS]->(c)
			`, map[string]any{
				"company_id":   companyID,
				"company_name": cleanedOrg,
				"article_id":   articleID,
			})
			if err != nil {
				log.Printf("Error creating company relationship: %v", err)
			}
		}

		// Create Location nodes and relationships
		for _, loc := range article.Data.Entities.LOC {
			_, err = tx.Run(ctx, `
				MERGE (l:Location {name: $location})
				WITH l
				MATCH (a:Article {id: $article_id})
				MERGE (a)-[:MENTIONS]->(l)
			`, map[string]any{
				"location":    loc,
				"article_id":  articleID,
			})
			if err != nil {
				log.Printf("Error creating location relationship: %v", err)
			}
		}

		return nil, nil
	})

	return err
}

// WriteJob writes a job and its entities to Neo4j
func (w *Writer) WriteJob(ctx context.Context, job *models.ExtractedJob) error {
	session := w.driver.NewSession(ctx, neo4j.SessionConfig{})
	defer session.Close(ctx)

	jobID := generateMD5(job.Data.Job.SourceURL)
	companyID := slugify(job.Data.Company.Name)

	_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
		// Create Job node
		_, err := tx.Run(ctx, `
			MERGE (j:Job {id: $id})
			SET j.name = $title,
			    j.description = $description,
			    j.requirement = $requirement,
			    j.benefit = $benefit,
			    j.salary = $salary,
			    j.url = $source_url,
			    j.source_platform = $source_platform
		`, map[string]any{
			"id":              jobID,
			"title":           job.Data.Job.Title,
			"description":     job.Data.Job.Description,
			"requirement":     job.Data.Job.Requirement,
			"benefit":         job.Data.Job.Benefit,
			"salary":          job.Data.Job.Salary,
			"source_url":      job.Data.Job.SourceURL,
			"source_platform": job.SourcePlatform,
		})
		if err != nil {
			return nil, err
		}

		// Create Company node and relationship
		if job.Data.Company.Name != "" {
			_, err = tx.Run(ctx, `
				MERGE (c:Company {id: $company_id})
				SET c.name = $company_name,
				    c.location = $company_location
				WITH c
				MATCH (j:Job {id: $job_id})
				MERGE (j)-[:POSTED_BY]->(c)
			`, map[string]any{
				"company_id":       companyID,
				"company_name":     job.Data.Company.Name,
				"company_location": job.Data.Company.Location,
				"job_id":           jobID,
			})
			if err != nil {
				log.Printf("Error creating company relationship: %v", err)
			}
		}

		// Create Technology nodes and relationships (normalized to avoid duplicates)
		for _, tech := range job.Data.Technologies {
			normalizedTech := normalizeTechName(tech)
			if normalizedTech == "" {
				continue
			}
			_, err = tx.Run(ctx, `
				MERGE (t:Technology {name: $tech})
				SET t.mention_count = COALESCE(t.mention_count, 0) + 1
				WITH t
				MATCH (j:Job {id: $job_id})
				MERGE (j)-[:REQUIRES]->(t)
			`, map[string]any{
				"tech":    normalizedTech,
				"job_id": jobID,
			})
			if err != nil {
				log.Printf("Error creating tech relationship: %v", err)
			}
		}

		// Create Skill nodes and relationships
		for _, skill := range job.Data.Skills {
			_, err = tx.Run(ctx, `
				MERGE (s:Skill {name: $skill})
				SET s.mention_count = COALESCE(s.mention_count, 0) + 1
				WITH s
				MATCH (j:Job {id: $job_id})
				MERGE (j)-[:REQUIRES]->(s)
			`, map[string]any{
				"skill":  skill,
				"job_id": jobID,
			})
			if err != nil {
				log.Printf("Error creating skill relationship: %v", err)
			}
		}

		return nil, nil
	})

	return err
}

// Run starts the Neo4j writer service
func (w *Writer) Run(ctx context.Context) error {
	articleReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  w.config.Kafka.Brokers,
		Topic:    w.config.Kafka.TopicExtractedArticles,
		GroupID:  config.GroupNeo4jWriter,
		MinBytes: 1,
		MaxBytes: 10e6,
	})
	defer articleReader.Close()

	jobReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  w.config.Kafka.Brokers,
		Topic:    w.config.Kafka.TopicExtractedJobs,
		GroupID:  config.GroupNeo4jWriter,
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
					log.Printf("Error reading extracted article message: %v", err)
					continue
				}
				w.processArticleMessage(ctx, msg)
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
					log.Printf("Error reading extracted job message: %v", err)
					continue
				}
				w.processJobMessage(ctx, msg)
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

func (w *Writer) processArticleMessage(ctx context.Context, msg kafka.Message) {
	var article models.ExtractedArticle
	if err := json.Unmarshal(msg.Value, &article); err != nil {
		log.Printf("Error unmarshaling article: %v", err)
		return
	}

	if err := w.WriteArticle(ctx, &article); err != nil {
		log.Printf("Error writing article to Neo4j: %v", err)
	} else {
		log.Printf("Written article to Neo4j: %s", truncate(article.Data.Title, 50))
	}
}

func (w *Writer) processJobMessage(ctx context.Context, msg kafka.Message) {
	var job models.ExtractedJob
	if err := json.Unmarshal(msg.Value, &job); err != nil {
		log.Printf("Error unmarshaling job: %v", err)
		return
	}

	if err := w.WriteJob(ctx, &job); err != nil {
		log.Printf("Error writing job to Neo4j: %v", err)
	} else {
		log.Printf("Written job to Neo4j: %s", truncate(job.Data.Job.Title, 50))
	}
}

func generateMD5(s string) string {
	// Simple hash for demo - use crypto/md5 in production
	hash := uint32(0)
	for _, c := range s {
		hash = hash*31 + uint32(c)
	}
	return fmt.Sprintf("%x", hash)
}

func slugify(s string) string {
	s = strings.ToLower(s)
	s = strings.ReplaceAll(s, " ", "-")
	s = strings.ReplaceAll(s, "_", "-")
	for _, c := range s {
		if (c < 'a' || c > 'z') && (c < '0' || c > '9') && c != '-' {
			s = strings.ReplaceAll(s, string(c), "")
		}
	}
	return s
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}

// normalizeTechName chuẩn hóa tên công nghệ để tránh duplicate nodes
// VD: "ai", "Ai", "AI" -> "AI"; "llm", "Llm" -> "LLM"
func normalizeTechName(tech string) string {
	// Clean entity first
	tech = cleanEntity(tech)
	if tech == "" {
		return ""
	}
	
	techLower := strings.ToLower(tech)
	
	// Danh sách các abbreviations cần viết hoa toàn bộ
	upperCaseTech := map[string]string{
		"ai": "AI", "llm": "LLM", "gpt": "GPT", "nlp": "NLP",
		"api": "API", "sdk": "SDK", "ide": "IDE", "orm": "ORM",
		"jwt": "JWT", "ssh": "SSH", "http": "HTTP", "https": "HTTPS",
		"rest": "REST", "soap": "SOAP", "html": "HTML", "xml": "XML",
		"json": "JSON", "yaml": "YAML", "grpc": "gRPC", "rag": "RAG",
		"iot": "IoT", "waf": "WAF", "sip": "SIP", "rtp": "RTP",
		"vpn": "VPN", "etl": "ETL", "erp": "ERP", "crm": "CRM",
		"mes": "MES", "olap": "OLAP", "dwh": "DWH", "siem": "SIEM",
		"edr": "EDR", "hsm": "HSM", "ids": "IDS", "ips": "IPS",
		"sse": "SSE", "ddos": "DDoS", "mpc": "MPC", "kyc": "KYC",
		"soc": "SOC", "nvr": "NVR", "vms": "VMS", "otp": "OTP",
		"2fa": "2FA", "apk": "APK", "nfc": "NFC", "adb": "ADB",
		"ipv4": "IPv4", "ipv6": "IPv6", "5g": "5G", "4g": "4G",
		"esim": "eSIM", "rom": "ROM", "moe": "MoE", "lpu": "LPU",
		"ici": "ICI", "sram": "SRAM", "hbm": "HBM", "eeg": "EEG",
		"c2pa": "C2PA", "gdpr": "GDPR", "fcc": "FCC", "ciso": "CISO",
		"mau": "MAU", "dau": "DAU", "gpu": "GPU", "tpu": "TPU",
		"npu": "NPU", "rpa": "RPA", "agi": "AGI", "it": "IT",
		"aws": "AWS", "gcp": "GCP", "css": "CSS", "php": "PHP",
		"sql": "SQL", "vba": "VBA", "sas": "SAS", "elk": "ELK",
		"svn": "SVN", "tcp": "TCP", "udp": "UDP", "dns": "DNS",
		"dhcp": "DHCP", "vlan": "VLAN", "nat": "NAT", "bgp": "BGP",
		"ospf": "OSPF", "ocr": "OCR", "stt": "STT", "tts": "TTS",
		"ml": "ML", "mlops": "MLOps",
	}
	
	// Kiểm tra xem có trong danh sách không
	if normalized, ok := upperCaseTech[techLower]; ok {
		return normalized
	}
	
	// Kiểm tra tên công nghệ phổ biến (title case)
	techKeywords := []string{
		"Python", "Java", "JavaScript", "TypeScript", "Golang", "Rust",
		"Kotlin", "Swift", "Scala", "Ruby", "Perl", "Dart", "Lua",
		"React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte",
		"Node.js", "Express", "Django", "Flask", "FastAPI", "Spring",
		"Docker", "Kubernetes", "Git", "GitHub", "GitLab",
		"TensorFlow", "PyTorch", "Keras", "Pandas", "NumPy",
		"MongoDB", "PostgreSQL", "MySQL", "Redis", "Neo4j",
		"Azure", "Firebase", "Heroku", "Vercel",
		"ChatGPT", "Claude", "Gemini", "Copilot", "OpenAI", "Anthropic",
		"Android", "iOS", "Windows", "Linux", "macOS",
		"NVIDIA", "Intel", "AMD", "Apple", "Google", "Microsoft", "Meta",
		"DeepSeek", "Mistral", "Llama", "HuggingFace",
	}
	
	for _, kw := range techKeywords {
		if strings.ToLower(kw) == techLower {
			return kw
		}
	}
	
	// Fallback: nếu toàn bộ là chữ hoa, giữ nguyên
	// Nếu toàn bộ là chữ thường, viết hoa chữ cái đầu
	if tech == strings.ToUpper(tech) {
		return tech
	}
	return strings.Title(tech)
}

// cleanEntity làm sạch entity trước khi lưu vào database
// Loại bỏ dấu câu, khoảng trắng thừa, và các ký tự không hợp lệ
func cleanEntity(entity string) string {
	// Remove subword artifacts
	entity = strings.ReplaceAll(entity, "▁", "")
	entity = strings.ReplaceAll(entity, "\u2581", "")
	
	// Collapse whitespace
	entity = strings.Join(strings.Fields(entity), " ")
	
	// Strip punctuation from ends (nhưng giữ lại dấu trong tiếng Việt)
	entity = strings.Trim(entity, ".,;:!?'\"()[]{}<>«»")
	
	// Remove trailing/leading dots and commas
	entity = strings.Trim(entity, ".,")
	
	// Nếu entity quá ngắn hoặc rỗng, bỏ qua
	if len(entity) < 2 {
		return ""
	}
	
	// Nếu entity chứa các từ không hợp lệ như "Cuối", "Quy", "Phía" ở cuối
	// (đây là các từ bị cắt sai từ văn bản)
	invalidEnds := []string{" Cuối", " Quy", " Phía", " Store", " YouTube"}
	for _, invalid := range invalidEnds {
		if strings.HasSuffix(entity, invalid) {
			entity = strings.TrimSuffix(entity, invalid)
		}
	}
	
	return strings.TrimSpace(entity)
}
