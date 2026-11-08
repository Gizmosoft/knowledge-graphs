import argparse
from data.dataset_generator import generate_graph
from graph_explorer import GraphExplorer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a mock dataset in Neo4j",
    )
    args = parser.parse_args()

    # Generate mock dataset in Neo4j if --generate is provided
    if args.generate:
        print("Generating mock employee relationship dataset in Neo4j...\n")
        generate_graph()
        print("Mock employee relationship dataset generated successfully!\n")
    
    # Explore the graph data 
    explorer = GraphExplorer()
    try:
        while True:
            # prompt user what they want to do
            workflow_decision = input(
                "Select a workflow:\n"
                "1) Find nodes by name (Default)\n"
                "2) Find neighbors of a node\n"
                "3) Exit\n\n"
                "Select a number to select a workflow: "
            ).strip() or "1"

            if workflow_decision == "1":
                name = input("Enter a name to find nodes by: ")
                results = explorer.find_nodes_by_name(name)
                print(f"\nNodes found for '{name}':")
                print("-" * 60)
                for row in results:
                    print(f"{row['id']} - {row['name']} ({', '.join(row['labels'])})")
            elif workflow_decision == "2":
                node_id = input("\nEnter node ID (e.g. P0, C0, PR0) or 'exit': ").strip()

                if node_id.lower() == "exit":
                    break

                if not node_id:
                    continue

                results = explorer.get_neighbors(node_id)

                if not results:
                    print("No connections found (or node doesn't exist).")
                    continue

                node_name = results[0]["source"]
                print(f"\nNode: {node_name} ({node_id})")
                print(f"Connections for {node_name}:")
                print("-" * 60)

                for row in results:
                    name = row["neighbor_name"]
                    relationship = row["relationship"]
                    neighbor_id = row["neighbor_id"]

                    direction = "->" if row["outgoing"] else "<-"

                    print(
                        f"{node_id} {direction} "
                        f"[{relationship}] {direction} "
                        f"{name} ({neighbor_id})"
                    )
            elif workflow_decision == "3":
                print("Exiting...")
                break
    finally:
        explorer.close()

if __name__ == "__main__":
    main()