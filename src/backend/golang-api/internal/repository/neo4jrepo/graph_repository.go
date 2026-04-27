package neo4jrepo

import (
	"context"
	"fmt"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	"github.com/neo4j/neo4j-go-driver/v5/neo4j/dbtype"
	"github.com/techpulsevn/final-data-mining/golang-api/internal/database"
)

type GraphRepository struct {
	DB *database.Neo4jDB
}

func NewGraphRepository(db *database.Neo4jDB) *GraphRepository {
	return &GraphRepository{DB: db}
}

type RawNode struct {
	ID     int64
	Labels []string
	Props  map[string]interface{}
}

type RawEdge struct {
	ID       int64
	Type     string
	SourceID int64
	TargetID int64
	Props    map[string]interface{}
}

// FindCenterNodes returns one Technology or Skill node per keyword.
func (r *GraphRepository) FindCenterNodes(ctx context.Context, keywords []string) ([]RawNode, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		UNWIND $keywords AS kw
		MATCH (n)
		WHERE (n:Technology OR n:Skill) AND toLower(n.name) CONTAINS toLower(kw)
		WITH kw, collect(n)[0] AS n
		WHERE n IS NOT NULL
		RETURN n
	`
	result, err := session.Run(ctx, query, map[string]interface{}{"keywords": keywords})
	if err != nil {
		return nil, fmt.Errorf("neo4j find centers: %w", err)
	}

	var nodes []RawNode
	for result.Next(ctx) {
		rec := result.Record()
		val, _ := rec.Get("n")
		if node, ok := val.(dbtype.Node); ok {
			nodes = append(nodes, RawNode{
				ID:     node.Id,
				Labels: node.Labels,
				Props:  node.Props,
			})
		}
	}
	if err := result.Err(); err != nil {
		return nil, fmt.Errorf("neo4j find centers result: %w", err)
	}
	return nodes, nil
}

// ExploreByKeywordAndLocation finds a center Technology by keyword, then returns
// all Technologies used by Companies whose location matches any of the given searchTerms.
// Path: Technology(center) <-[USES]- Company(location~X) -[USES]-> Technology(other)
func (r *GraphRepository) ExploreByKeywordAndLocation(ctx context.Context, keyword string, searchTerms []string) (int64, []RawNode, []RawEdge, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		MATCH (center:Technology)
		WHERE toLower(center.name) CONTAINS toLower($keyword)
		WITH center LIMIT 1
		OPTIONAL MATCH (center)<-[r1:USES]-(c:Company)-[r2:USES]->(other:Technology)
		WHERE any(term IN $searchTerms WHERE toLower(c.location) CONTAINS term)
		RETURN center, c, other, r1, r2
		LIMIT 500
	`
	result, err := session.Run(ctx, query, map[string]interface{}{
		"keyword":     keyword,
		"searchTerms": searchTerms,
	})
	if err != nil {
		return 0, nil, nil, fmt.Errorf("neo4j explore by location: %w", err)
	}

	var centerID int64 = -1
	nodeMap := make(map[int64]RawNode)
	edgeSet := make(map[int64]RawEdge)

	for result.Next(ctx) {
		rec := result.Record()

		if cVal, _ := rec.Get("center"); cVal != nil {
			if node, ok := cVal.(dbtype.Node); ok && centerID == -1 {
				centerID = node.Id
				nodeMap[node.Id] = RawNode{ID: node.Id, Labels: node.Labels, Props: node.Props}
			}
		}
		if cVal, _ := rec.Get("c"); cVal != nil {
			if node, ok := cVal.(dbtype.Node); ok {
				if _, exists := nodeMap[node.Id]; !exists {
					nodeMap[node.Id] = RawNode{ID: node.Id, Labels: node.Labels, Props: node.Props}
				}
			}
		}
		if oVal, _ := rec.Get("other"); oVal != nil {
			if node, ok := oVal.(dbtype.Node); ok {
				if _, exists := nodeMap[node.Id]; !exists {
					nodeMap[node.Id] = RawNode{ID: node.Id, Labels: node.Labels, Props: node.Props}
				}
			}
		}
		if r1Val, _ := rec.Get("r1"); r1Val != nil {
			if rel, ok := r1Val.(dbtype.Relationship); ok {
				edgeSet[rel.Id] = RawEdge{ID: rel.Id, Type: rel.Type, SourceID: rel.StartId, TargetID: rel.EndId, Props: rel.Props}
			}
		}
		if r2Val, _ := rec.Get("r2"); r2Val != nil {
			if rel, ok := r2Val.(dbtype.Relationship); ok {
				edgeSet[rel.Id] = RawEdge{ID: rel.Id, Type: rel.Type, SourceID: rel.StartId, TargetID: rel.EndId, Props: rel.Props}
			}
		}
	}
	if err := result.Err(); err != nil {
		return 0, nil, nil, fmt.Errorf("neo4j explore by location result: %w", err)
	}

	nodes := make([]RawNode, 0, len(nodeMap))
	for _, n := range nodeMap {
		nodes = append(nodes, n)
	}
	edges := make([]RawEdge, 0, len(edgeSet))
	for _, e := range edgeSet {
		edges = append(edges, e)
	}
	return centerID, nodes, edges, nil
}

// GetNeighborhood returns up to 10 neighbors and their edges for each given node ID.
func (r *GraphRepository) GetNeighborhood(ctx context.Context, nodeIDs []int64) ([]RawNode, []RawEdge, error) {
	session := r.DB.Driver.NewSession(ctx, neo4j.SessionConfig{
		AccessMode:   neo4j.AccessModeRead,
		DatabaseName: r.DB.Database,
	})
	defer session.Close(ctx)

	query := `
		UNWIND $node_ids AS nid
		MATCH (center) WHERE id(center) = nid
		OPTIONAL MATCH (center)-[r]-(neighbor)
		WITH center, r, neighbor
		ORDER BY id(neighbor)
		WITH center, collect({r: r, n: neighbor})[..10] AS conns
		UNWIND conns AS conn
		WITH conn.r AS r, conn.n AS neighbor
		WHERE r IS NOT NULL AND neighbor IS NOT NULL
		RETURN neighbor, r
	`
	result, err := session.Run(ctx, query, map[string]interface{}{"node_ids": nodeIDs})
	if err != nil {
		return nil, nil, fmt.Errorf("neo4j get neighborhood: %w", err)
	}

	var nodes []RawNode
	var edges []RawEdge
	for result.Next(ctx) {
		rec := result.Record()

		nVal, _ := rec.Get("neighbor")
		rVal, _ := rec.Get("r")

		if node, ok := nVal.(dbtype.Node); ok {
			nodes = append(nodes, RawNode{
				ID:     node.Id,
				Labels: node.Labels,
				Props:  node.Props,
			})
		}
		if rel, ok := rVal.(dbtype.Relationship); ok {
			edges = append(edges, RawEdge{
				ID:       rel.Id,
				Type:     rel.Type,
				SourceID: rel.StartId,
				TargetID: rel.EndId,
				Props:    rel.Props,
			})
		}
	}
	if err := result.Err(); err != nil {
		return nil, nil, fmt.Errorf("neo4j neighborhood result: %w", err)
	}
	return nodes, edges, nil
}
