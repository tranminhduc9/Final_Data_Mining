"""
Import transformed data to Neo4j Aura using Job Market Schema
"""
import logging
from typing import Dict, List
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from schema_define import (
    Technology, Company, Job, Skill, Article, Person,
    RelationshipType
)

logger = logging.getLogger(__name__)

class Neo4jJobImporter:
    """Import Job Market data to Neo4j"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
    
    def connect(self) -> bool:
        """Connect to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self.driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j Aura")
            return True
        except ServiceUnavailable:
            logger.error("❌ Neo4j unavailable")
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def create_constraints_and_indexes(self) -> bool:
        """Create constraints and indexes for all node types"""
        try:
            with self.driver.session(database=self.database) as session:
                constraints = [
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.title IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (j:Job) REQUIRE j.title IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
                ]
                
                for constraint in constraints:
                    session.run(constraint)
                    logger.info(f"✅ {constraint.split('FOR')[1][:30]}...")
            
            logger.info("✅ All constraints and indexes created")
            return True
        except Exception as e:
            logger.error(f"✗ Error creating constraints: {e}")
            return False
    
    def import_articles(self, articles: List[Article]) -> int:
        """Import Article nodes"""
        try:
            with self.driver.session(database=self.database) as session:
                for article in articles:
                    session.run(
                        """
                        MERGE (a:Article {title: $title})
                        ON CREATE SET
                            a.content = $content,
                            a.source = $source,
                            a.published_date = $published_date,
                            a.sentiment_score = $sentiment_score
                        """,
                        parameters={
                            'title': article.title,
                            'content': article.content,
                            'source': article.source,
                            'published_date': article.published_date.isoformat(),
                            'sentiment_score': article.sentiment_score
                        }
                    )
            
            logger.info(f"✅ Imported {len(articles)} articles")
            return len(articles)
        except Exception as e:
            logger.error(f"✗ Error importing articles: {e}")
            return 0
    
    def import_technologies(self, technologies: List[Technology]) -> int:
        """Import Technology nodes"""
        try:
            with self.driver.session(database=self.database) as session:
                for tech in technologies:
                    session.run(
                        """
                        MERGE (t:Technology {name: $name})
                        ON CREATE SET
                            t.category = $category,
                            t.description = $description,
                            t.trend_score = $trend_score
                        """,
                        parameters={
                            'name': tech.name,
                            'category': tech.category,
                            'description': tech.description,
                            'trend_score': tech.trend_score
                        }
                    )
            
            logger.info(f"✅ Imported {len(technologies)} technologies")
            return len(technologies)
        except Exception as e:
            logger.error(f"✗ Error importing technologies: {e}")
            return 0
    
    def import_companies(self, companies: List[Company]) -> int:
        """Import Company nodes"""
        try:
            with self.driver.session(database=self.database) as session:
                for company in companies:
                    session.run(
                        """
                        MERGE (c:Company {name: $name})
                        ON CREATE SET
                            c.industry = $industry,
                            c.size = $size,
                            c.location = $location,
                            c.rating = $rating
                        """,
                        parameters={
                            'name': company.name,
                            'industry': company.industry,
                            'size': company.size,
                            'location': company.location,
                            'rating': company.rating
                        }
                    )
            
            logger.info(f"✅ Imported {len(companies)} companies")
            return len(companies)
        except Exception as e:
            logger.error(f"✗ Error importing companies: {e}")
            return 0
    
    def import_persons(self, persons: List[Person]) -> int:
        """Import Person nodes"""
        try:
            with self.driver.session(database=self.database) as session:
                for person in persons:
                    session.run(
                        """
                        MERGE (p:Person {name: $name})
                        ON CREATE SET
                            p.role = $role
                        """,
                        parameters={
                            'name': person.name,
                            'role': person.role
                        }
                    )
            
            logger.info(f"✅ Imported {len(persons)} persons")
            return len(persons)
        except Exception as e:
            logger.error(f"✗ Error importing persons: {e}")
            return 0
    
    def import_skills(self, skills: List[Skill]) -> int:
        """Import Skill nodes"""
        try:
            with self.driver.session(database=self.database) as session:
                for skill in skills:
                    session.run(
                        """
                        MERGE (s:Skill {name: $name})
                        ON CREATE SET
                            s.category = $category,
                            s.demand_score = $demand_score
                        """,
                        parameters={
                            'name': skill.name,
                            'category': skill.category,
                            'demand_score': skill.demand_score
                        }
                    )
            
            logger.info(f"✅ Imported {len(skills)} skills")
            return len(skills)
        except Exception as e:
            logger.error(f"✗ Error importing skills: {e}")
            return 0
    
    def create_article_mentions_relationships(self, data_transformer) -> int:
        """Create MENTIONS relationships: Article -> Technology/Company"""
        try:
            with self.driver.session(database=self.database) as session:
                rel_count = 0
                
                for article in data_transformer.articles:
                    # Article mentions Technologies
                    for tech in data_transformer.technologies:
                        if tech.name.lower() in article.content.lower() or \
                           tech.name.lower() in article.title.lower():
                            session.run(
                                """
                                MATCH (a:Article {title: $article_title})
                                MATCH (t:Technology {name: $tech_name})
                                MERGE (a)-[:MENTIONS]->(t)
                                """,
                                parameters={
                                    'article_title': article.title,
                                    'tech_name': tech.name
                                }
                            )
                            rel_count += 1
                    
                    # Article mentions Companies
                    for company in data_transformer.companies:
                        if company.name.lower() in article.content.lower() or \
                           company.name.lower() in article.title.lower():
                            session.run(
                                """
                                MATCH (a:Article {title: $article_title})
                                MATCH (c:Company {name: $company_name})
                                MERGE (a)-[:MENTIONS]->(c)
                                """,
                                parameters={
                                    'article_title': article.title,
                                    'company_name': company.name
                                }
                            )
                            rel_count += 1
            
            logger.info(f"✅ Created {rel_count} MENTIONS relationships")
            return rel_count
        except Exception as e:
            logger.error(f"✗ Error creating relationships: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            with self.driver.session(database=self.database) as session:
                stats = {}
                
                node_types = ['Article', 'Technology', 'Company', 'Skill', 'Person', 'Job']
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    record = result.single()
                    stats[node_type] = record['count'] if record else 0
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                record = result.single()
                stats['Relationships'] = record['count'] if record else 0
                
                return stats
        except Exception as e:
            logger.error(f"✗ Error getting statistics: {e}")
            return {}