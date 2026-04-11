"""
Fixed version with proper relationships between Job, Company, Person nodes
"""
import logging
import os
from typing import Dict, List
from datetime import datetime
import json
import sys
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from neo4j_config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE, BATCH_SIZE
from database_connection import Neo4jJobImporter, TechNode, CompanyNode, JobNode, SkillNode

logger = logging.getLogger(__name__)

# Define Article and Job classes
@dataclass
class Article:
    """Article Node"""
    title: str
    content: str
    source: str
    published_date: datetime
    sentiment_score: float = 0.0

    def __hash__(self):
        return hash(self.title.lower())


class RelationshipBuilder:
    """Build relationships between nodes"""

    def __init__(self):
        self.technologies = []
        self.companies = []
        self.skills = []
        self.articles = []
        self.persons = set()
        self.jobs = []
        self._job_role_cache = set()
        self._tech_category_map = {}
        self._job_company_map = {}
        self._job_tech_map = {}
        self._job_skills_map = {}
        self._article_company_map = {}
        self._article_tech_map = {}

    def _detect_tech_category(self, tech_name: str) -> str:
        """Detect technology category"""
        tech_lower = tech_name.lower()
        for category, keywords in self._tech_category_map.items():
            if any(kw.lower() in tech_lower for kw in keywords):
                return category
        return "Other"

    def _add_if_not_exists(self, lst, item):
        """Add item to list if it doesn't already exist"""
        if not any(existing.name == item.name for existing in lst):
            lst.append(item)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in various formats"""
        date_formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now()

    def _extract_job_level(self, job_title: str) -> str:
        """Extract job level from job title"""
        title_lower = job_title.lower()

        if 'fresher' in title_lower or 'thực tập sinh' in title_lower:
            return 'fresher'
        elif 'junior' in title_lower or 'nhân viên mới' in title_lower or 'nhân viên' in title_lower:
            return 'junior'
        elif 'mid' in title_lower or 'trung cấp' in title_lower:
            return 'mid'
        elif 'senior' in title_lower or 'trưởng nhóm' in title_lower or 'làm việc trực tiếp' in title_lower:
            return 'senior'
        elif 'lead' in title_lower or 'team lead' in title_lower or 'kiến trúc sư' in title_lower:
            return 'lead'

        return 'mid'

    def _parse_salary(self, salary_str: str) -> tuple:
        """Parse salary string and return (min, max) in millions VND"""
        salary_str = salary_str.lower()

        if 'tr' in salary_str or 'triệu' in salary_str:
            import re
            numbers = re.findall(r'\d+', salary_str)
            if len(numbers) >= 2:
                return int(numbers[0]), int(numbers[1])

        import re
        numbers = re.findall(r'\d+', salary_str)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])

        return None, None

    def import_news_data(self, data_path: str, source_type: str) -> Dict:
        """Import news data from JSON file"""
        logger.info(f"🔄 Importing {source_type} data from {data_path}...")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        post_detail = data.get('post_detail', [])
        source_platform = data.get('source_platform', source_type)

        stats = {
            'articles': 0,
            'technologies': 0,
            'companies': 0,
            'job_roles': 0,
            'skills': 0,
            'total_articles': len(post_detail)
        }

        for raw_article in post_detail:
            if not raw_article or 'title' not in raw_article:
                continue

            try:
                created_at = raw_article.get('created_at', '')
                try:
                    published_date = self._parse_date(created_at)
                except:
                    published_date = datetime.now()

                # Create Article node
                article = Article(
                    title=raw_article.get('title', ''),
                    content=raw_article.get('description', ''),
                    source=source_platform,
                    published_date=published_date,
                    sentiment_score=0.0
                )
                self.articles.append(article)

                # Extract entities
                entities = raw_article.get('entities', {})

                # Process Technology entities (TECH or SKILL/TECH)
                tech_names = entities.get('TECH', [])
                skill_names = entities.get('SKILL/TECH', [])

                for tech_name in tech_names:
                    tech = TechNode(
                        name=tech_name,
                        category=self._detect_tech_category(tech_name),
                        description=f"Mentioned in {source_platform}",
                        trend_score=1.0
                    )
                    self._add_if_not_exists(self.technologies, tech)

                for skill_name in skill_names:
                    if not any(t.name == skill_name for t in self.technologies):
                        tech = TechNode(
                            name=skill_name,
                            category=self._detect_tech_category(skill_name),
                            description=f"Mentioned in {source_platform}",
                            trend_score=1.0
                        )
                        self.technologies.append(tech)
                    skill = SkillNode(
                        name=skill_name,
                        category=self._detect_tech_category(skill_name),
                        demand_score=0.7
                    )
                    self._add_if_not_exists(self.skills, skill)

                # Process Organization entities (ORG)
                org_names = entities.get('ORG', [])
                for org_name in org_names:
                    company = CompanyNode(
                        name=org_name,
                        industry="Technology",
                        location="Unknown",
                        rating=0.0
                    )
                    self._add_if_not_exists(self.companies, company)
                    # Map article to company
                    self._article_company_map[article.title] = org_name

                # Process Job Role entities (JOB_ROLE)
                job_roles = entities.get('JOB_ROLE', [])
                for job_name in job_roles:
                    job_role_key = (job_name.lower(), "")
                    if job_role_key not in self._job_role_cache:
                        job = JobNode(
                            title=job_name,
                            salary_min=0,
                            salary_max=0,
                            level=self._extract_job_level(job_name),
                            source_url="",
                            company_name="",
                            posted_date=published_date
                        )
                        self.jobs.append(job)
                        self._job_role_cache.add(job_role_key)

                stats['articles'] += 1

            except Exception as e:
                logger.warning(f"Error processing article: {e}")
                continue

        stats['technologies'] = len(self.technologies)
        stats['companies'] = len(self.companies)
        stats['job_roles'] = len(self.jobs)
        stats['skills'] = len(self.skills)

        logger.info(f"✅ Imported {stats['articles']} articles from {source_type}")
        logger.info(f"   - Technologies: {stats['technologies']}")
        logger.info(f"   - Companies: {stats['companies']}")
        logger.info(f"   - Job Roles: {stats['job_roles']}")
        logger.info(f"   - Skills: {stats['skills']}")

        return stats

    def import_topcv_data(self, data_path: str) -> Dict:
        """Import job postings from TopCV"""
        logger.info(f"🔄 Importing TopCV data from {data_path}...")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        post_detail = data.get('post_detail', [])
        source_platform = data.get('source_platform', 'TopCV')

        stats = {
            'job_postings': 0,
            'technologies': 0,
            'job_roles': 0,
            'skills': 0
        }

        self._job_role_cache = set()

        for job_posting in post_detail:
            if not job_posting or 'title' not in job_posting:
                continue

            try:
                created_at = job_posting.get('created_at', '')
                try:
                    published_date = self._parse_date(created_at)
                except:
                    published_date = datetime.now()

                # Extract Job Role
                job_title = job_posting.get('title', '')
                job_role_key = (job_title.lower(), "")
                if job_role_key not in self._job_role_cache:
                    job = JobNode(
                        title=job_title,
                        salary_min=0,
                        salary_max=0,
                        level=self._extract_job_level(job_title),
                        source_url="",
                        company_name="",
                        posted_date=published_date
                    )
                    self.jobs.append(job)
                    self._job_role_cache.add(job_role_key)

                # Extract entities
                entities = job_posting.get('entities', {})

                # Process Technology entities (SKILL/TECH)
                skill_names = entities.get('SKILL/TECH', [])
                for skill_name in skill_names:
                    tech = TechNode(
                        name=skill_name,
                        category=self._detect_tech_category(skill_name),
                        description=f"Required in {source_platform}",
                        trend_score=1.0
                    )
                    self._add_if_not_exists(self.technologies, tech)
                    self._job_tech_map[job_title] = self._job_tech_map.get(job_title, []) + [skill_name]

                    # Add as skill if not already in skills
                    skill = SkillNode(
                        name=skill_name,
                        category=self._detect_tech_category(skill_name),
                        demand_score=0.7
                    )
                    self._add_if_not_exists(self.skills, skill)
                    self._job_skills_map[job_title] = self._job_skills_map.get(job_title, []) + [skill_name]

                # Process Organization entities
                org_names = entities.get('ORG', [])
                for org_name in org_names:
                    company = CompanyNode(
                        name=org_name,
                        industry="Technology",
                        location="Unknown",
                        rating=0.0
                    )
                    self._add_if_not_exists(self.companies, company)
                    # Map job to company
                    self._job_company_map[job_title] = org_name

                # Extract salary
                salary_ranges = entities.get('SALARY', [])
                if salary_ranges and len(salary_ranges) > 0:
                    salary_str = salary_ranges[0]
                    if salary_str != "Thoả thuận":
                        salary_min, salary_max = self._parse_salary(salary_str)
                        if job_role_key not in self._job_role_cache:
                            job = self.jobs[-1]
                            job.salary_min = salary_min if salary_min else 0
                            job.salary_max = salary_max if salary_max else 0

                stats['job_postings'] += 1

            except Exception as e:
                logger.warning(f"Error processing job posting: {e}")
                continue

        stats['technologies'] = len(self.technologies)
        stats['job_roles'] = len(self.jobs)
        stats['skills'] = len(self.skills)

        logger.info(f"✅ Imported {stats['job_postings']} job postings from TopCV")
        logger.info(f"   - Technologies: {stats['technologies']}")
        logger.info(f"   - Job Roles: {stats['job_roles']}")
        logger.info(f"   - Skills: {stats['skills']}")

        return stats

    def run_import_pipeline(self, news_paths: List[str], topcv_path: str = None) -> Dict:
        """Run complete import pipeline"""
        print("\n" + "="*70)
        print("🚀 MULTI-SOURCE DATA IMPORT PIPELINE TO NEO4J AURA")
        print("="*70 + "\n")

        stats = {}

        # Step 1: Import News Data
        if news_paths:
            print("📂 STEP 1: Importing News Data\n")
            for news_path in news_paths:
                if os.path.exists(news_path):
                    source_type = news_path.split('/')[-1].replace('extracted_data_', '').replace('.json', '')
                    source_stats = self.import_news_data(news_path, source_type)
                    stats[source_type] = source_stats
                else:
                    logger.warning(f"News file not found: {news_path}")

        # Step 2: Import TopCV Data
        if topcv_path and os.path.exists(topcv_path):
            print("\n📂 STEP 2: Importing TopCV Job Data\n")
            topcv_stats = self.import_topcv_data(topcv_path)
            stats['topcv'] = topcv_stats

        # Step 3: Transform and Prepare for Import
        print("\n📂 STEP 3: Transforming Data to Job Market Schema\n")

        # Step 4: Connect to Neo4j
        print("\n📂 STEP 4: Connecting to Neo4j Aura\n")
        importer = Neo4jJobImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)

        if not importer.connect():
            logger.error("Failed to connect to Neo4j Aura")
            return stats

        print("📂 STEP 5: Creating Constraints and Indexes\n")
        importer.create_constraints_and_indexes()

        # Step 6: Import Nodes
        print("\n📂 STEP 6: Importing Nodes\n")

        tech_list = self.technologies
        importer.import_technologies_list(tech_list)

        company_list = self.companies
        importer.import_companies_list(company_list)

        job_role_list = self.jobs
        importer.import_jobs_list(job_role_list)

        skill_list = self.skills
        importer.import_skills_list(skill_list)

        person_list = self.persons
        importer.import_persons(person_list)

        # Step 7: Import Articles
        article_list = self.articles
        importer.import_articles(article_list)

        # Step 8: Create Relationships
        print("\n📂 STEP 7: Creating Relationships\n")
        self.create_article_mentions_relationships(importer)
        self.create_job_company_relationships(importer)
        self.create_job_tech_relationships(importer)
        self.create_job_skill_relationships(importer)

        # Step 9: Print Final Statistics
        print("\n📊 FINAL IMPORT STATISTICS\n")
        stats = importer.get_statistics()

        for node_type, count in stats.items():
            if isinstance(count, int):
                label = node_type if node_type == 'Relationships' else node_type
                print(f"   {label:15s}: {count:5d}")

        # Disconnect
        importer.disconnect()

        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*70 + "\n")

        return stats

    def create_article_mentions_relationships(self, importer: Neo4jJobImporter):
        """Create MENTIONS relationships: Article → Technology/Company"""
        logger.info("Creating Article → Technology/Company relationships...")

        with importer.driver.session(database=NEO4J_DATABASE) as session:
            # Create Article → Technology relationships
            for article in self.articles:
                for tech in self.technologies:
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

            # Create Article → Company relationships
            for article in self.articles:
                company_name = self._article_company_map.get(article.title)
                if company_name:
                    session.run(
                        """
                        MATCH (a:Article {title: $article_title})
                        MATCH (c:Company {name: $company_name})
                        MERGE (a)-[:MENTIONS]->(c)
                        """,
                        parameters={
                            'article_title': article.title,
                            'company_name': company_name
                        }
                    )

        logger.info(f"✅ Created Article → Technology/Company relationships")

    def create_job_company_relationships(self, importer: Neo4jJobImporter):
        """Create HIRES_FOR relationships: Job → Company"""
        logger.info("Creating Job → Company relationships...")

        with importer.driver.session(database=NEO4J_DATABASE) as session:
            for job in self.jobs:
                company_name = self._job_company_map.get(job.title)
                if company_name:
                    session.run(
                        """
                        MATCH (j:Job {title: $title})
                        MATCH (c:Company {name: $company_name})
                        MERGE (j)-[:HIRES_FOR]->(c)
                        """,
                        parameters={
                            'title': job.title,
                            'company_name': company_name
                        }
                    )

        logger.info(f"✅ Created {len(self.jobs)} Job → Company relationships")

    def create_job_tech_relationships(self, importer: Neo4jJobImporter):
        """Create REQUIRES relationships: Job → Technology"""
        logger.info("Creating Job → Technology relationships...")

        with importer.driver.session(database=NEO4J_DATABASE) as session:
            for job in self.jobs:
                tech_names = self._job_tech_map.get(job.title, [])
                for tech_name in tech_names:
                    session.run(
                        """
                        MATCH (j:Job {title: $title})
                        MATCH (t:Technology {name: $tech_name})
                        MERGE (j)-[:REQUIRES {is_mandatory: true, frequency: 1}]->(t)
                        """,
                        parameters={
                            'title': job.title,
                            'tech_name': tech_name
                        }
                    )

        logger.info(f"✅ Created Job → Technology relationships")

    def create_job_skill_relationships(self, importer: Neo4jJobImporter):
        """Create REQUIRES relationships: Job → Skill"""
        logger.info("Creating Job → Skill relationships...")

        with importer.driver.session(database=NEO4J_DATABASE) as session:
            for job in self.jobs:
                skill_names = self._job_skills_map.get(job.title, [])
                for skill_name in skill_names:
                    session.run(
                        """
                        MATCH (j:Job {title: $title})
                        MATCH (s:Skill {name: $skill_name})
                        MERGE (j)-[:REQUIRES {is_mandatory: true, frequency: 1}]->(s)
                        """,
                        parameters={
                            'title': job.title,
                            'skill_name': skill_name
                        }
                    )

        logger.info(f"✅ Created Job → Skill relationships")


def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

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
        # Find the latest JSON file (YYYY_MM_DD.json)
        json_files = list(topcv_dir.glob("*.json"))
        if json_files:
            # Sort by filename (which is YYYY_MM_DD.json) to get the latest
            latest_file = sorted(json_files)[-1]
            topcv_path = str(latest_file)
            logger.info(f"Found latest TopCV data: {topcv_path}")
        else:
            # Fallback to old path if no files in new dir
            topcv_path = str(data_dir / "extracted_data_topCV" / "extracted_data_topCV.json")
    else:
        # Fallback to old path
        topcv_path = str(data_dir / "extracted_data_topCV" / "extracted_data_topCV.json")

    # Run import pipeline
    importer = RelationshipBuilder()
    stats = importer.run_import_pipeline(news_paths, topcv_path)


if __name__ == "__main__":
    main()
