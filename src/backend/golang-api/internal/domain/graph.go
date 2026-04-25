package domain

type GraphNode struct {
	ID         string                 `json:"id"`
	Labels     []string               `json:"labels"`
	Properties map[string]interface{} `json:"properties"`
}

type GraphEdge struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	Source     string                 `json:"source"`
	Target     string                 `json:"target"`
	Properties map[string]interface{} `json:"properties"`
}

type GraphResult struct {
	Centers []string    `json:"centers"` // IDs of center nodes (matching keywords)
	Nodes   []GraphNode `json:"nodes"`
	Edges   []GraphEdge `json:"edges"`
}
