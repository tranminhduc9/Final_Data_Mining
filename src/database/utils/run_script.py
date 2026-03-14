"""
Main script: Transform news data and import to Neo4j with Job Market Schema
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from data_transform import DataTransformer
from database_connection import Neo4jJobImporter
from neo4j_config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE,
    DATA_PATH_VNEP, DATA_PATH_DT
)

def main():
    """Main pipeline"""
    
    logger.info("=" * 60)
    logger.info("DATA TRANSFORMATION & NEO4J IMPORT PIPELINE")
    logger.info("=" * 60)
    
    # Step 1: Transform data
    logger.info("\n📊 STEP 1: TRANSFORMING DATA")
    logger.info("-" * 60)
    
    transformer = DataTransformer()
    
    # Transform VN-Express
    stats_vnep = transformer.batch_transform(DATA_PATH_VNEP)
    logger.info(f"VN-Express: {stats_vnep['articles']} articles")
    
    # Transform Dân Trí
    stats_dt = transformer.batch_transform(DATA_PATH_DT)
    logger.info(f"Dân Trí: {stats_dt['articles']} articles")
    
    # Print summary
    logger.info(transformer.get_summary())
    
    # Export transformed data
    transformer.export_to_json()
    
    # Step 2: Import to Neo4j
    logger.info("\n🗄️ STEP 2: IMPORTING TO NEO4J")
    logger.info("-" * 60)
    
    importer = Neo4jJobImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)
    
    if not importer.connect():
        logger.error("Failed to connect to Neo4j. Exiting.")
        return
    
    try:
        # Create constraints
        importer.create_constraints_and_indexes()
        
        # Import nodes
        importer.import_articles(transformer.articles)
        importer.import_technologies(list(transformer.technologies))
        importer.import_companies(list(transformer.companies))
        importer.import_persons(list(transformer.persons))
        importer.import_skills(list(transformer.skills))
        
        # Create relationships
        importer.create_article_mentions_relationships(transformer)
        
        # Print statistics
        logger.info("\n📈 IMPORT STATISTICS")
        logger.info("-" * 60)
        stats = importer.get_statistics()
        for node_type, count in stats.items():
            logger.info(f"{node_type:20s}: {count:5d}")
        
        logger.info("\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    finally:
        importer.disconnect()

if __name__ == '__main__':
    main()