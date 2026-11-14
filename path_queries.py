"""Cypher path-query workflow: neighbors, N-hop nodes, paths, shortestPath vs BFS."""


class PathQueryExplorer:
    def __init__(self, explorer):
        # Reuse the existing GraphExplorer driver and database name
        self.explorer = explorer
        self.driver = explorer.driver
        self.database = explorer.DATABASE_INSTANCE

    # Immediate undirected neighbors via MATCH
    def immediate_neighbors(self, node_id):
        query = """
        MATCH (n:MockEntity {id: $node_id})-[r]-(m:MockEntity)
        RETURN
            n.name AS source,
            type(r) AS relationship,
            m.id AS neighbor_id,
            m.name AS neighbor_name,
            startNode(r) = n AS outgoing
        ORDER BY relationship, neighbor_name
        """

        records, _, _ = self.driver.execute_query(
            query,
            node_id=node_id,
            database_=self.database,
        )
        return [record.data() for record in records]

    # Distinct nodes reachable within 1..max_hops (variable-length path)
    def nodes_within_hops(self, start_id, max_hops):
        # Hop bounds cannot be parameters in Cypher; max_hops is validated as int
        query = f"""
        MATCH (n:MockEntity {{id: $start_id}})-[*1..{max_hops}]-(m:MockEntity)
        WHERE m.id <> n.id
        RETURN DISTINCT m.id AS id, m.name AS name
        ORDER BY name
        """

        records, _, _ = self.driver.execute_query(
            query,
            start_id=start_id,
            database_=self.database,
        )
        return [record.data() for record in records]

    # Up to 20 undirected paths between two entities (hop-bounded)
    def paths_between(self, start_id, end_id, max_hops):
        query = f"""
        MATCH (a:MockEntity {{id: $start_id}}), (b:MockEntity {{id: $end_id}})
        MATCH path = (a)-[*1..{max_hops}]-(b)
        RETURN
            [n IN nodes(path) | {{id: n.id, name: n.name}}] AS nodes,
            [r IN relationships(path) | type(r)] AS relationships,
            length(path) AS hops
        LIMIT 20
        """

        records, _, _ = self.driver.execute_query(
            query,
            start_id=start_id,
            end_id=end_id,
            database_=self.database,
        )
        return [record.data() for record in records]

    # Native Cypher shortestPath between two entities
    def cypher_shortest_path(self, start_id, end_id):
        query = """
        MATCH (a:MockEntity {id: $start_id}), (b:MockEntity {id: $end_id})
        MATCH path = shortestPath((a)-[*]-(b))
        RETURN
            [n IN nodes(path) | {id: n.id, name: n.name}] AS nodes,
            [r IN relationships(path) | type(r)] AS relationships,
            length(path) AS hops
        """

        records, _, _ = self.driver.execute_query(
            query,
            start_id=start_id,
            end_id=end_id,
            database_=self.database,
        )
        if not records:
            return None
        return records[0].data()


def _prompt_max_hops(default=3):
    raw = input(f"Enter max hops (default {default}): ").strip()
    if not raw:
        return default
    try:
        hops = int(raw)
    except ValueError:
        print("Max hops must be an integer.")
        return None
    if hops < 1:
        print("Max hops must be at least 1.")
        return None
    return hops


def _prompt_optional_max_depth():
    raw = input(
        "Enter max depth for Python BFS (Enter for uncapped): "
    ).strip()
    if not raw:
        return None
    try:
        depth = int(raw)
    except ValueError:
        print("Max depth must be an integer.")
        return False
    if depth < 0:
        print("Max depth must be non-negative.")
        return False
    return depth


def _format_path_nodes(nodes, relationships=None):
    # e.g. P0 (Alice) -[WORKS_AT]-> C0 (Company 0)
    if not nodes:
        return ""

    parts = [f"{nodes[0]['id']} ({nodes[0]['name']})"]
    for i in range(1, len(nodes)):
        node = nodes[i]
        if relationships and i - 1 < len(relationships):
            rel = relationships[i - 1]
            parts.append(f"-[{rel}]-> {node['id']} ({node['name']})")
        else:
            parts.append(f"-> {node['id']} ({node['name']})")
    return " ".join(parts)


def _print_path(label, nodes, hops=None, relationships=None):
    if not nodes:
        print(f"{label}: no path found.")
        return
    if hops is None:
        hops = max(len(nodes) - 1, 0)
    print(f"{label} ({hops} hop(s)):")
    print(f"  {_format_path_nodes(nodes, relationships)}")


def run_path_query_menu(explorer):
    pq = PathQueryExplorer(explorer)

    while True:
        choice = input(
            "\nCypher path queries:\n"
            "1) Immediate neighbors (MATCH)\n"
            "2) Nodes within N hops\n"
            "3) Paths between two entities\n"
            "4) Shortest path vs Python BFS\n"
            "5) Back to main menu\n\n"
            "Select a number: "
        ).strip() or "5"

        if choice == "1":
            node_id = input(
                "\nEnter node ID (e.g. P0, C0, PR0): "
            ).strip()
            if not node_id:
                continue

            results = pq.immediate_neighbors(node_id)
            if not results:
                print("No neighbors found (or node doesn't exist).")
                continue

            source = results[0]["source"]
            print(f"\nImmediate neighbors of {source} ({node_id}):")
            print("-" * 60)
            for row in results:
                direction = "->" if row["outgoing"] else "<-"
                print(
                    f"{node_id} {direction} "
                    f"[{row['relationship']}] {direction} "
                    f"{row['neighbor_name']} ({row['neighbor_id']})"
                )

        elif choice == "2":
            start_id = input(
                "\nEnter start node ID (e.g. P0): "
            ).strip()
            if not start_id:
                continue

            max_hops = _prompt_max_hops()
            if max_hops is None:
                continue

            results = pq.nodes_within_hops(start_id, max_hops)
            print(
                f"\nNodes within {max_hops} hop(s) of {start_id} "
                f"({len(results)} found):"
            )
            print("-" * 60)
            if not results:
                print("No nodes found (or start node doesn't exist).")
            else:
                for row in results:
                    print(f"{row['id']} - {row['name']}")

        elif choice == "3":
            start_id = input(
                "\nEnter start node ID (e.g. P0): "
            ).strip()
            end_id = input("Enter end node ID (e.g. P1): ").strip()
            if not start_id or not end_id:
                continue

            max_hops = _prompt_max_hops()
            if max_hops is None:
                continue

            results = pq.paths_between(start_id, end_id, max_hops)
            print(
                f"\nPaths from {start_id} to {end_id} "
                f"(max {max_hops} hops, up to 20):"
            )
            print("-" * 60)
            if not results:
                print("No paths found.")
            else:
                for i, row in enumerate(results, start=1):
                    print(f"{i}. ({row['hops']} hop(s))")
                    print(
                        f"   {_format_path_nodes(row['nodes'], row.get('relationships'))}"
                    )

        elif choice == "4":
            start_id = input(
                "\nEnter start node ID (e.g. P0): "
            ).strip()
            end_id = input("Enter end node ID (e.g. P1): ").strip()
            if not start_id or not end_id:
                continue

            max_depth = _prompt_optional_max_depth()
            if max_depth is False:
                continue

            cypher = pq.cypher_shortest_path(start_id, end_id)
            python_path = explorer.bfs_shortest_path(
                start_id, end_id, max_depth=max_depth
            )

            print(f"\nShortest path comparison: {start_id} -> {end_id}")
            print("-" * 60)

            cypher_nodes = cypher["nodes"] if cypher else []
            cypher_hops = cypher["hops"] if cypher else None
            cypher_rels = cypher.get("relationships") if cypher else None
            _print_path(
                "Cypher shortestPath",
                cypher_nodes,
                cypher_hops,
                cypher_rels,
            )
            python_rels = [
                n["relationship"]
                for n in python_path[1:]
                if "relationship" in n
            ]
            _print_path(
                "Python BFS",
                python_path,
                relationships=python_rels or None,
            )

            cypher_ids = [n["id"] for n in cypher_nodes]
            python_ids = [n["id"] for n in python_path]
            cypher_len = len(cypher_ids)
            python_len = len(python_ids)

            print("\nComparison:")
            if not cypher_ids and not python_ids:
                print("  Neither method found a path.")
            elif not cypher_ids:
                print("  Cypher found no path; Python BFS did.")
            elif not python_ids:
                print(
                    "  Python BFS found no path; Cypher did "
                    "(check max depth if set)."
                )
            else:
                same_length = cypher_len == python_len
                same_sequence = cypher_ids == python_ids
                print(
                    f"  Same length: {same_length} "
                    f"(Cypher={cypher_len - 1} hops, "
                    f"BFS={python_len - 1} hops)"
                )
                print(f"  Same node sequence: {same_sequence}")
                if same_length and not same_sequence:
                    print(
                        "  Both are shortest; alternate routes of equal length."
                    )

        elif choice == "5":
            break
        else:
            print("Unknown option; choose 1–5.")
