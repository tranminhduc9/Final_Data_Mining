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
