"""
Complete pipeline: Import data and create relationships
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from multi_source_import_v3 import RelationshipBuilder, main

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 COMPLETE PIPELINE: Import Data + Create Relationships")
    print("="*70 + "\n")

    # Define data paths
    base_path = Path(__file__).parent.parent.parent.parent
    data_dir = base_path / "src" / "data-pipeline"
    extracted_dir = data_dir / "extracted_data_phobert"

    news_paths = [
        str(extracted_dir / "extracted_data_phobert_VN-EP.json"),
        str(extracted_dir / "extracted_data_phobert_DT.json")
    ]

    # Support directory-based TopCV data sourcing
    topcv_dir = data_dir / "extracted_data" / "topCV"
    topcv_path = None
    
    if topcv_dir.exists() and topcv_dir.is_dir():
        # Find all JSON files (YYYY_MM_DD.json)
        json_files = list(topcv_dir.glob("*.json"))
        if json_files:
            # Sort by filename (which is YYYY_MM_DD.json) to get the latest
            latest_file = sorted(json_files)[-1]
            topcv_path = str(latest_file)
            print(f"📂 Found latest TopCV data: {latest_file.name}")
        else:
            # Fallback to old path
            topcv_path = str(data_dir / "extracted_data_topCV" / "extracted_data_topCV.json")
    else:
        # Fallback to old path
        topcv_path = str(data_dir / "extracted_data_topCV" / "extracted_data_topCV.json")

    # Run import pipeline
    importer = RelationshipBuilder()
    stats = importer.run_import_pipeline(news_paths, topcv_path)

    # Create relationships
    print("\n" + "="*70)
    print("🚀 Creating Relationships in Neo4j")
    print("="*70 + "\n")

    from neo4j import GraphDatabase
    from neo4j_config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            print("1. Creating Job → Company relationships (HIRES_FOR)...")
            result = session.run("""
                MATCH (j:Job)
                WHERE j.company_name IS NOT NULL AND j.company_name <> ''
                MATCH (c:Company {name: j.company_name})
                MERGE (j)-[:HIRES_FOR]->(c)
                RETURN count(j) as rel_count
            """)
            record = result.single()
            rel_count = record['rel_count'] if record else 0
            print(f"   ✅ Created {rel_count} HIRES_FOR relationships")

            print("\n2. Creating Job → Technology relationships (REQUIRES)...")
            result = session.run("""
                MATCH (j:Job)
                MATCH (t:Technology)
                WHERE t.name IN ['Python', 'Java', 'React', 'Node.js', 'Go', 'C#', 'SQL', 'MongoDB']
                MERGE (j)-[:REQUIRES {is_mandatory: true, frequency: 1}]->(t)
                RETURN count(j) as rel_count
            """)
            record = result.single()
            rel_count = record['rel_count'] if record else 0
            print(f"   ✅ Created {rel_count} REQUIRES relationships")

            print("\n3. Creating Job → Skill relationships (REQUIRES)...")
            result = session.run("""
                MATCH (j:Job)
                MATCH (s:Skill)
                WHERE s.name IN ['Python', 'Java', 'React', 'JavaScript', 'SQL', 'Git']
                MERGE (j)-[:REQUIRES {is_mandatory: true, frequency: 1}]->(s)
                RETURN count(j) as rel_count
            """)
            record = result.single()
            rel_count = record['rel_count'] if record else 0
            print(f"   ✅ Created {rel_count} REQUIRES relationships")

            print("\n4. Creating Company → Technology relationships (USES)...")
            result = session.run("""
                MATCH (c:Company)
                MATCH (t:Technology)
                WHERE t.name IN ['Python', 'Java', 'React', 'Node.js', 'AWS', 'Azure']
                MERGE (c)-[:USES {frequency: 1}]->(t)
                RETURN count(c) as rel_count
            """)
            record = result.single()
            rel_count = record['rel_count'] if record else 0
            print(f"   ✅ Created {rel_count} USES relationships")

            print("\n5. Creating Article → Technology relationships (MENTIONS)...")
            result = session.run("""
                MATCH (a:Article)
                MATCH (t:Technology)
                WHERE t.name IN ['AI', 'Machine Learning', 'GPT', 'Docker', 'Kubernetes']
                MERGE (a)-[:MENTIONS]->(t)
                RETURN count(a) as rel_count
            """)
            record = result.single()
            rel_count = record['rel_count'] if record else 0
            print(f"   ✅ Created {rel_count} MENTIONS relationships")

        print("\n✅ All relationships created successfully!")

    finally:
        driver.close()

    # Print final statistics
    print("\n" + "="*70)
    print("📊 FINAL DATABASE STATISTICS")
    print("="*70 + "\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            stats = {}

            node_types = ['Article', 'Technology', 'Company', 'Skill', 'Person', 'Job']
            for node_type in node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                record = result.single()
                stats[node_type] = record['count'] if record else 0

            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = result.single()
            stats['Relationships'] = record['count'] if record else 0

            for node_type, count in stats.items():
                label = node_type if node_type == 'Relationships' else node_type
                print(f"   {label:15s}: {count:5d}")

    finally:
        driver.close()

    print("\n" + "="*70)
    print("✅ COMPLETE PIPELINE FINISHED!")
    print("="*70 + "\n")
