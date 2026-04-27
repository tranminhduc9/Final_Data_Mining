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

type RoadAnalysisResult struct {
	Found  bool        `json:"found"`
	Length int         `json:"length"` // number of hops (edges)
	Nodes  []GraphNode `json:"nodes"`  // ordered from start to end
	Edges  []GraphEdge `json:"edges"`  // ordered, with actual relationship direction
}
