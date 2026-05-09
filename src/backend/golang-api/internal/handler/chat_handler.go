package handler

import (
	"crypto/rand"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/middleware"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/service"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/sse"
)

type ChatHandler struct {
	AI *service.AIClient
}

func NewChatHandler(ai *service.AIClient) *ChatHandler {
	return &ChatHandler{AI: ai}
}

// ── DTOs ──────────────────────────────────────────────────────────────────────

// CreateSessionResponse là body trả về khi client tạo session mới.
type CreateSessionResponse struct {
	SessionID string    `json:"session_id"`
	CreatedAt time.Time `json:"created_at"`
}

// PostMessageRequest là body cho post message / stream.
type PostMessageRequest struct {
	Query string `json:"query" binding:"required,min=1,max=2000"`
}

// IndexResponse là body của GET /chat (health proxy).
type IndexResponse struct {
	Status string `json:"status"`
	RAG    string `json:"rag"`
	Neo4j  bool   `json:"neo4j"`
}

// ── Handlers ──────────────────────────────────────────────────────────────────

// Index godoc
// @Summary  Health check của RAG service (proxy)
// @Tags     chatbot
// @Security BearerAuth
// @Produce  json
// @Success  200 {object} IndexResponse
// @Failure  502 {object} map[string]string
// @Router   /chat [get]
func (h *ChatHandler) Index(c *gin.Context) {
	hr, err := h.AI.Health(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"status": "degraded", "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, IndexResponse{Status: "ok", RAG: hr.Status, Neo4j: hr.Neo4j})
}

// CreateSession godoc
// @Summary  Tạo session chat mới
// @Description  Generate UUIDv4 cho session. RAG service sẽ tự upsert vào DB khi nhận message đầu tiên.
// @Tags     chatbot
// @Security BearerAuth
// @Produce  json
// @Success  200 {object} CreateSessionResponse
// @Failure  500 {object} map[string]string
// @Router   /chat/session [post]
func (h *ChatHandler) CreateSession(c *gin.Context) {
	id, err := newUUIDv4()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, CreateSessionResponse{
		SessionID: id,
		CreatedAt: time.Now().UTC(),
	})
}

// GetMessages godoc
// @Summary  Lấy lịch sử message của 1 session
// @Tags     chatbot
// @Security BearerAuth
// @Produce  json
// @Param    session_id path string true "Session UUID"
// @Success  200 {array}  service.ChatMessageItem
// @Failure  502 {object} map[string]string
// @Router   /chat/session/{session_id}/messages [get]
func (h *ChatHandler) GetMessages(c *gin.Context) {
	sessionID := c.Param("session_id")
	if sessionID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing session_id"})
		return
	}
	msgs, err := h.AI.ListMessages(c.Request.Context(), sessionID)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, msgs)
}

// PostMessage godoc
// @Summary  Gửi message (non-stream)
// @Description  Proxy POST /chat sang RAG service. Trả full response (không stream).
// @Tags     chatbot
// @Security BearerAuth
// @Accept   json
// @Produce  json
// @Param    session_id path string true "Session UUID"
// @Param    body body PostMessageRequest true "Câu hỏi"
// @Success  200 {object} service.ChatResponse
// @Failure  400 {object} map[string]string
// @Failure  502 {object} map[string]string
// @Router   /chat/session/{session_id}/messages [post]
func (h *ChatHandler) PostMessage(c *gin.Context) {
	sessionID := c.Param("session_id")
	if sessionID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing session_id"})
		return
	}
	var body PostMessageRequest
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	userID := userIDFromContext(c)
	resp, err := h.AI.Chat(c.Request.Context(), service.ChatRequest{
		Query:     body.Query,
		SessionID: &sessionID,
		UserID:    userID,
	})
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, resp)
}

// PostMessageStream godoc
// @Summary  Gửi message và stream câu trả lời (SSE)
// @Description  Proxy POST /chat/stream sang RAG. SSE events: `token` (data=text chunk), `done` (data=JSON metadata: answer, session_id, sources, entities, job_titles, query).
// @Tags     chatbot
// @Security BearerAuth
// @Accept   json
// @Produce  text/event-stream
// @Param    session_id path string true "Session UUID"
// @Param    body body PostMessageRequest true "Câu hỏi"
// @Success  200 {string} string "SSE stream"
// @Failure  400 {object} map[string]string
// @Failure  502 {object} map[string]string
// @Router   /chat/session/{session_id}/messages/stream [post]
func (h *ChatHandler) PostMessageStream(c *gin.Context) {
	sessionID := c.Param("session_id")
	if sessionID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing session_id"})
		return
	}
	var body PostMessageRequest
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	flusher, ok := c.Writer.(http.Flusher)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "streaming unsupported"})
		return
	}
	sse.SetHeaders(c)
	c.Writer.WriteHeader(http.StatusOK)
	flusher.Flush()

	userID := userIDFromContext(c)
	err := h.AI.ChatStream(c.Request.Context(), service.ChatRequest{
		Query:     body.Query,
		SessionID: &sessionID,
		UserID:    userID,
	}, c.Writer, flusher)

	if err != nil && !errors.Is(err, c.Request.Context().Err()) {
		// Stream đã start → ghi error event thay vì JSON
		_, _ = fmt.Fprintf(c.Writer, "event: error\ndata: %q\n\n", err.Error())
		flusher.Flush()
	}
}

// ── helpers ───────────────────────────────────────────────────────────────────

// userIDFromContext lấy user_id (UUID string) từ JWT middleware.
// Trả nil nếu không có để RAG xử lý ẩn danh.
func userIDFromContext(c *gin.Context) *string {
	v, ok := c.Get(middleware.ContextUserIDKey)
	if !ok {
		return nil
	}
	s, ok := v.(string)
	if !ok || s == "" {
		return nil
	}
	return &s
}

func newUUIDv4() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant 10
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:]), nil
}
