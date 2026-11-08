from neo4j import GraphDatabase
import os
import constants

class GraphExplorer:
    DATABASE_INSTANCE = constants.NEO4J_INSTANCE_ID

    def __init__(self):
        self.driver = GraphDatabase.driver(
            constants.NEO4J_URI,
            auth=(
                constants.NEO4J_USERNAME,
                constants.NEO4J_PASSWORD
            )
        )

    # Get neighbors of a node
    def get_neighbors(self, node_id):
        query = """
        MATCH (n:MockEntity {id: $node_id})-[r]-(neighbor)
        RETURN
            n.name AS source,
            type(r) AS relationship,
            neighbor.id AS neighbor_id,
            neighbor.name AS neighbor_name,
            labels(neighbor) AS neighbor_labels,
            startNode(r) = n AS outgoing
        ORDER BY relationship, neighbor_name
        """

        records, _, _ = self.driver.execute_query(
            query,
            node_id=node_id,
            database_=self.DATABASE_INSTANCE
        )

        return [record.data() for record in records]

    # Find nodes by name
    def find_nodes_by_name(self, name):
        query = """
        MATCH (n:MockEntity)
        WHERE toLower(n.name) CONTAINS toLower($name)
        RETURN
            n.id AS id,
            n.name AS name,
            labels(n) AS labels
        ORDER BY name
        LIMIT 20
    """

        records, _, _ = self.driver.execute_query(
            query,
            name=name,
            database_=self.DATABASE_INSTANCE
        )

        return [record.data() for record in records]

    def close(self):
        self.driver.close()