# This script generated mock data and loads it into the Neo4j database
import os
import random
from faker import Faker
from neo4j import GraphDatabase
import constants

def generate_graph():
    # Configuration
    fake = Faker()
    fake.seed_instance(42)
    random.seed(42)

    URI = constants.NEO4J_URI
    USERNAME = constants.NEO4J_USERNAME
    PASSWORD = constants.NEO4J_PASSWORD
    DATABASE_INSTANCE = constants.NEO4J_INSTANCE_ID
    
    NUM_PEOPLE = 200
    NUM_COMPANIES = 15
    NUM_PROJECTS = 40

    # Generate companies
    companies = [
        {"id": f"C{i}", "name": f"Company {i}"}
        for i in range(NUM_COMPANIES)
    ]

    # Generate people
    people = [
        {
            "id": f"P{i}",
            "name": fake.name(),
            "age": random.randint(22, 60),
            "department": random.choice(
                ["Engineering", "Marketing", "Finance", "HR"]
            ),
            "company_id": random.choice(companies)["id"]
        }
        for i in range(NUM_PEOPLE)
    ]

    # Generate projects, each owned by a company
    projects = [
        {
            "id": f"PR{i}",
            "name": f"Project {i}",
            "company_id": random.choice(companies)["id"]
        }
        for i in range(NUM_PROJECTS)
    ]

    relationships = []

    # Every person works at one company
    for person in people:
        relationships.append({
            "source": person["id"],
            "target": person["company_id"],
            "type": "WORKS_AT"
        })

    # Company owns its projects
    for project in projects:
        relationships.append({
            "source": project["company_id"],
            "target": project["id"],
            "type": "OWNS"
        })

    # Random social connections
    for person in people:
        friends = random.sample(
            [p for p in people if p["id"] != person["id"]],
            5
        )

        for friend in friends:
            relationships.append({
                "source": person["id"],
                "target": friend["id"],
                "type": "KNOWS"
            })

    # Assign people to projects belonging to their company
    projects_by_company = {}

    for project in projects:
        projects_by_company.setdefault(
            project["company_id"], []
        ).append(project["id"])

    for person in people:
        possible = projects_by_company.get(
            person["company_id"], []
        )

        for project_id in random.sample(
            possible, min(2, len(possible))
        ):
            relationships.append({
                "source": person["id"],
                "target": project_id,
                "type": "WORKS_ON"
            })

    # Add manager relationships within companies
    for company in companies:
        employees = [
            p for p in people
            if p["company_id"] == company["id"]
        ]

        if len(employees) < 2:
            continue

        manager = employees[0]

        for employee in employees[1:6]:
            relationships.append({
                "source": manager["id"],
                "target": employee["id"],
                "type": "MANAGES"
            })

    # Remove duplicate relationships
    unique = {
        (r["source"], r["target"], r["type"]): r
        for r in relationships
    }
    relationships = list(unique.values())

    # Import into Neo4j
    driver = GraphDatabase.driver(
        URI, auth=(USERNAME, PASSWORD)
    )

    def run(query, **params):
        driver.execute_query(
            query,
            parameters_=params,
            database_=DATABASE_INSTANCE
        )

    try:
        driver.verify_connectivity()

        # Unique IDs across all mock nodes
        run("""
            CREATE CONSTRAINT mock_entity_id IF NOT EXISTS
            FOR (n:MockEntity)
            REQUIRE n.id IS UNIQUE
        """)

        # Create nodes
        for label, rows in [
            ("Person", people),
            ("Company", companies),
            ("Project", projects)
        ]:
            run(f"""
                UNWIND $rows AS row
                MERGE (n:MockEntity:{label} {{id: row.id}})
                SET n += row
            """, rows=rows)

        # Create relationships by type
        # Relationship types are fixed, trusted strings
        for rel_type in [
            "WORKS_AT", "KNOWS", "WORKS_ON",
            "MANAGES", "OWNS"
        ]:
            rows = [
                r for r in relationships
                if r["type"] == rel_type
            ]

            run(f"""
                UNWIND $rows AS row
                MATCH (a:MockEntity {{id: row.source}})
                MATCH (b:MockEntity {{id: row.target}})
                MERGE (a)-[:{rel_type}]->(b)
            """, rows=rows)

        print(f"Created {len(people) + len(companies) + len(projects)} nodes")
        print(f"Generated {len(relationships)} unique relationships")

    finally:
        driver.close()