package service

import (
	"context"
	"fmt"
	"strconv"

	"github.com/techpulsevn/final-data-mining/golang-api/internal/domain"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/repository/neo4jrepo"
)

type GraphService struct {
	graphRepo *neo4jrepo.GraphRepository
}

func NewGraphService(graphRepo *neo4jrepo.GraphRepository) *GraphService {
	return &GraphService{graphRepo: graphRepo}
}

func (s *GraphService) Explore(ctx context.Context, keywords []string, depth int) (*domain.GraphResult, error) {
	if s.graphRepo == nil {
		return nil, fmt.Errorf("neo4j unavailable")
	}

	nodeMap := make(map[int64]*domain.GraphNode)
	edgeMap := make(map[int64]*domain.GraphEdge)

	addNode := func(raw neo4jrepo.RawNode) {
		if _, exists := nodeMap[raw.ID]; exists {
			return
		}
		nodeMap[raw.ID] = &domain.GraphNode{
			ID:         strconv.FormatInt(raw.ID, 10),
			Labels:     raw.Labels,
			Properties: sanitizeNodeProps(raw.Labels, raw.Props),
		}
	}

	addEdge := func(raw neo4jrepo.RawEdge) {
		if _, exists := edgeMap[raw.ID]; exists {
			return
		}
		edgeMap[raw.ID] = &domain.GraphEdge{
			ID:         strconv.FormatInt(raw.ID, 10),
			Type:       raw.Type,
			Source:     strconv.FormatInt(raw.SourceID, 10),
			Target:     strconv.FormatInt(raw.TargetID, 10),
			Properties: raw.Props,
		}
	}

	// Find center nodes (one per keyword)
	centers, err := s.graphRepo.FindCenterNodes(ctx, keywords)
	if err != nil {
		return nil, err
	}
	centerIDs := make([]string, 0, len(centers))
	depth1IDs := make([]int64, 0, len(centers))
	for _, c := range centers {
		addNode(c)
		centerIDs = append(centerIDs, strconv.FormatInt(c.ID, 10))
		depth1IDs = append(depth1IDs, c.ID)
	}

	// Depth 1: neighbors of center nodes
	d1Nodes, d1Edges, err := s.graphRepo.GetNeighborhood(ctx, depth1IDs)
	if err != nil {
		return nil, err
	}
	depth2IDs := make([]int64, 0, len(d1Nodes))
	for _, n := range d1Nodes {
		if _, exists := nodeMap[n.ID]; !exists {
			depth2IDs = append(depth2IDs, n.ID)
		}
		addNode(n)
	}
	for _, e := range d1Edges {
		addEdge(e)
	}

	// Depth 2: neighbors of depth-1 nodes (only new nodes not yet seen)
	if depth >= 2 && len(depth2IDs) > 0 {
		d2Nodes, d2Edges, err := s.graphRepo.GetNeighborhood(ctx, depth2IDs)
		if err != nil {
			return nil, err
		}
		for _, n := range d2Nodes {
			addNode(n)
		}
		for _, e := range d2Edges {
			addEdge(e)
		}
	}

	result := &domain.GraphResult{
		Centers: centerIDs,
		Nodes:   make([]domain.GraphNode, 0, len(nodeMap)),
		Edges:   make([]domain.GraphEdge, 0, len(edgeMap)),
	}
	for _, n := range nodeMap {
		result.Nodes = append(result.Nodes, *n)
	}
	for _, e := range edgeMap {
		result.Edges = append(result.Edges, *e)
	}

	return result, nil
}

// sanitizeNodeProps removes heavy fields (e.g. Article.content) to keep the response lean.
func sanitizeNodeProps(labels []string, props map[string]interface{}) map[string]interface{} {
	if props == nil {
		return map[string]interface{}{}
	}
	for _, l := range labels {
		if l == "Article" {
			delete(props, "content")
			break
		}
	}
	return props
}
