from collections import deque
from neo4j import GraphDatabase
import constants

class GraphExplorer:
    DATABASE_INSTANCE = constants.NEO4J_INSTANCE_ID

    def __init__(self):
        # Open a Neo4j driver connection using Aura credentials
        self.driver = GraphDatabase.driver(
            constants.NEO4J_URI,
            auth=(
                constants.NEO4J_USERNAME,
                constants.NEO4J_PASSWORD
            )
        )

    # Look up a single MockEntity by id
    def get_node(self, node_id):
        query = """
        MATCH (n:MockEntity {id: $node_id})
        RETURN n.id AS id, n.name AS name
        """

        # Run the lookup against the configured database
        records, _, _ = self.driver.execute_query(
            query,
            node_id=node_id,
            database_=self.DATABASE_INSTANCE
        )

        # Missing id means the node does not exist
        if not records:
            return None

        return records[0].data()

    # Fetch undirected neighbors and relationship metadata for a node
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

        # Run the adjacency query against Neo4j
        records, _, _ = self.driver.execute_query(
            query,
            node_id=node_id,
            database_=self.DATABASE_INSTANCE
        )

        # Convert Neo4j records into plain dicts for the CLI
        return [record.data() for record in records]

    # Case-insensitive substring search over node names
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

        # Run the name search and cap results at 20
        records, _, _ = self.driver.execute_query(
            query,
            name=name,
            database_=self.DATABASE_INSTANCE
        )

        return [record.data() for record in records]

    # Breadth-first traversal visit order
    def bfs(self, start_id, max_depth):
        # Resolve the start node; abort if it is missing
        start = self.get_node(start_id)
        if start is None:
            return []

        # Seed visit order, visited set, and FIFO queue at depth 0
        visit_order = [{"id": start["id"], "name": start["name"], "depth": 0}]
        visited = {start_id}
        queue = deque([(start_id, 0)])

        while queue:
            # Dequeue next node in level order
            node_id, depth = queue.popleft()
            # Do not expand nodes already at the depth limit
            if depth >= max_depth:
                continue

            # Enqueue each unseen neighbor one level deeper
            for row in self.get_neighbors(node_id):
                neighbor_id = row["neighbor_id"]
                if neighbor_id in visited:
                    continue

                visited.add(neighbor_id)
                next_depth = depth + 1
                visit_order.append({
                    "id": neighbor_id,
                    "name": row["neighbor_name"],
                    "depth": next_depth,
                })
                queue.append((neighbor_id, next_depth))

        return visit_order

    # Depth-first traversal visit order
    def dfs(self, start_id, max_depth):
        # Resolve the start node; abort if it is missing
        start = self.get_node(start_id)
        if start is None:
            return []

        visit_order = []
        visited = set()
        # Stack holds (node_id, name, depth); push neighbors in reverse
        # so relationship/name order is preserved when popping.
        stack = [(start_id, start["name"], 0)]

        while stack:
            # Pop next node (LIFO) for depth-first order
            node_id, name, depth = stack.pop()
            if node_id in visited:
                continue

            # Record first visit, then stop expanding at max depth
            visited.add(node_id)
            visit_order.append({"id": node_id, "name": name, "depth": depth})

            if depth >= max_depth:
                continue

            # Push unseen neighbors so the first listed is explored next
            neighbors = self.get_neighbors(node_id)
            for row in reversed(neighbors):
                neighbor_id = row["neighbor_id"]
                if neighbor_id not in visited:
                    stack.append((
                        neighbor_id,
                        row["neighbor_name"],
                        depth + 1,
                    ))

        return visit_order

    # Shortest path via BFS with parent pointers
    def bfs_shortest_path(self, start_id, end_id, max_depth=None):
        # Resolve endpoints; abort if either is missing
        start = self.get_node(start_id)
        end = self.get_node(end_id)
        if start is None or end is None:
            return []

        # Trivial path when start and end are the same node
        if start_id == end_id:
            return [{"id": start["id"], "name": start["name"]}]

        # parent maps child_id -> (parent_id, child_name, relationship)
        parent = {start_id: (None, start["name"], None)}
        queue = deque([(start_id, 0)])

        found = False
        while queue:
            node_id, depth = queue.popleft()
            # Optional hop cap for fair comparison with bounded Cypher walks
            if max_depth is not None and depth >= max_depth:
                continue

            for row in self.get_neighbors(node_id):
                neighbor_id = row["neighbor_id"]
                if neighbor_id in parent:
                    continue

                parent[neighbor_id] = (
                    node_id,
                    row["neighbor_name"],
                    row["relationship"],
                )
                if neighbor_id == end_id:
                    found = True
                    break

                queue.append((neighbor_id, depth + 1))

            if found:
                break

        if end_id not in parent:
            return []

        # Walk parent links from end back to start, then reverse
        path = []
        current = end_id
        while current is not None:
            parent_id, name, relationship = parent[current]
            entry = {"id": current, "name": name}
            if relationship is not None:
                entry["relationship"] = relationship
            path.append(entry)
            current = parent_id

        path.reverse()
        return path

    def close(self):
        # Release the Neo4j driver connection
        self.driver.close()
