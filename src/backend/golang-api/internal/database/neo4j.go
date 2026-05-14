package database

import (
	"context"
	"fmt"
	"time"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

type Neo4jDB struct {
	Driver   neo4j.DriverWithContext
	Database string
}

// NewNeo4j creates a Neo4j driver and verifies connectivity.
// Returns (nil, err) if connection fails — caller decides whether to fatal or warn.
func NewNeo4j(ctx context.Context, uri, username, password, database string) (*Neo4jDB, error) {
	auth := neo4j.BasicAuth(username, password, "")

	driver, err := neo4j.NewDriverWithContext(uri, auth)
	if err != nil {
		return nil, fmt.Errorf("create neo4j driver: %w", err)
	}

	pingCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	if err := driver.VerifyConnectivity(pingCtx); err != nil {
		driver.Close(ctx)
		return nil, fmt.Errorf("verify neo4j connectivity: %w", err)
	}

	return &Neo4jDB{Driver: driver, Database: database}, nil
}

func (n *Neo4jDB) Close(ctx context.Context) {
	if n != nil {
		n.Driver.Close(ctx)
	}
}
