package service

import (
	"context"
	"fmt"
	"strconv"
	"strings"

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

	enrichNodeProps(result)
	return result, nil
}

func (s *GraphService) RoadAnalysis(ctx context.Context, keyword1, keyword2 string) (*domain.RoadAnalysisResult, error) {
	if s.graphRepo == nil {
		return nil, fmt.Errorf("neo4j unavailable")
	}

	rawPath, err := s.graphRepo.FindRoadPath(ctx, keyword1, keyword2)
	if err != nil {
		return nil, err
	}
	if rawPath == nil {
		return &domain.RoadAnalysisResult{Found: false, Nodes: []domain.GraphNode{}, Edges: []domain.GraphEdge{}}, nil
	}

	nodes := make([]domain.GraphNode, 0, len(rawPath.Nodes))
	for _, n := range rawPath.Nodes {
		nodes = append(nodes, domain.GraphNode{
			ID:         strconv.FormatInt(n.ID, 10),
			Labels:     n.Labels,
			Properties: sanitizeNodeProps(n.Labels, n.Props),
		})
	}
	edges := make([]domain.GraphEdge, 0, len(rawPath.Edges))
	for _, e := range rawPath.Edges {
		edges = append(edges, domain.GraphEdge{
			ID:         strconv.FormatInt(e.ID, 10),
			Type:       e.Type,
			Source:     strconv.FormatInt(e.SourceID, 10),
			Target:     strconv.FormatInt(e.TargetID, 10),
			Properties: e.Props,
		})
	}

	return &domain.RoadAnalysisResult{
		Found:  true,
		Length: len(rawPath.Edges),
		Nodes:  nodes,
		Edges:  edges,
	}, nil
}

func (s *GraphService) ExploreByLocation(ctx context.Context, keyword, location string) (*domain.GraphResult, error) {
	if s.graphRepo == nil {
		return nil, fmt.Errorf("neo4j unavailable")
	}

	searchTerms := ExpandLocationSearchTerms(location)
	centerID, rawNodes, rawEdges, err := s.graphRepo.ExploreByKeywordAndLocation(ctx, keyword, searchTerms)
	if err != nil {
		return nil, err
	}

	if centerID == -1 {
		return &domain.GraphResult{Centers: []string{}, Nodes: []domain.GraphNode{}, Edges: []domain.GraphEdge{}}, nil
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

	for _, n := range rawNodes {
		addNode(n)
	}
	for _, e := range rawEdges {
		addEdge(e)
	}

	result := &domain.GraphResult{
		Centers: []string{strconv.FormatInt(centerID, 10)},
		Nodes:   make([]domain.GraphNode, 0, len(nodeMap)),
		Edges:   make([]domain.GraphEdge, 0, len(edgeMap)),
	}
	for _, n := range nodeMap {
		result.Nodes = append(result.Nodes, *n)
	}
	for _, e := range edgeMap {
		result.Edges = append(result.Edges, *e)
	}
	enrichNodeProps(result)
	return result, nil
}

// parseSalaryMin extracts the lower bound from Vietnamese salary strings.
// "Từ X triệu" → X  |  "X-Y triệu" → X
func parseSalaryMin(s string) (float64, bool) {
	if idx := strings.Index(s, "triệu"); idx >= 0 {
		s = strings.TrimSpace(s[:idx])
	}
	s = strings.TrimPrefix(strings.TrimPrefix(s, "Từ "), "từ ")
	s = strings.TrimSpace(s)
	if idx := strings.Index(s, "-"); idx > 0 {
		if v, err := strconv.ParseFloat(strings.TrimSpace(s[:idx]), 64); err == nil {
			return v, true
		}
	}
	if v, err := strconv.ParseFloat(s, 64); err == nil {
		return v, true
	}
	return 0, false
}

// enrichNodeProps adds computed fields to nodes for client-side filtering:
// - Job nodes: min_salary (float, lower bound from salary string) and location (from connected Company via HIRES_FOR)
func enrichNodeProps(result *domain.GraphResult) {
	companyLoc := map[string]string{}
	for _, node := range result.Nodes {
		for _, l := range node.Labels {
			if l == "Company" {
				if loc, _ := node.Properties["location"].(string); loc != "" {
					companyLoc[node.ID] = loc
				}
				break
			}
		}
	}
	jobCompany := map[string]string{}
	for _, e := range result.Edges {
		if e.Type == "HIRES_FOR" {
			jobCompany[e.Source] = e.Target
		}
	}
	for i, node := range result.Nodes {
		for _, l := range node.Labels {
			if l == "Job" {
				sal, _ := node.Properties["salary"].(string)
				if v, ok := parseSalaryMin(sal); ok {
					result.Nodes[i].Properties["min_salary"] = v
				}
				if cid, ok := jobCompany[node.ID]; ok {
					if loc, ok := companyLoc[cid]; ok {
						result.Nodes[i].Properties["location"] = loc
					}
				}
				break
			}
		}
	}
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
