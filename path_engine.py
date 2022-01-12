"""
Script that take coordinates of two point and determine the shortest path to go from the first to the second point
using the metro in Paris
It will return the name and line of the stations and the time needed for the trip

Example usage: python3 path_engine.py 651949.77 6865656.88 649449.32 6863156.51
"""
import argparse
from neo4j import GraphDatabase

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse coordinates")
    parser.add_argument(
        "x_start",
        type=float,
        help="latitude starting point in m",
    )

    parser.add_argument(
        "y_start",
        type=float,
        help="longitude starting point in m",
    )

    parser.add_argument(
        "x_end",
        type=float,
        help="latitude ending point in m",
    )

    parser.add_argument(
        "y_end",
        type=float,
        help="longitude ending point in m",
    )

    args = parser.parse_args()

    print(args)

    FOOT_SPEED = 66.6  # m/min

    driver = GraphDatabase.driver(
        "bolt://0.0.0.0:7687", auth=("neo4j", "neo4j")
    )

    # Create nodes in the graph
    create_start_node = f"""create (s:Disposable {{name: 'START', x: toFloat({args.x_start}), y: toFloat({args.y_start})}})
    """

    create_end_node = f"""create (e:Disposable {{name: 'END', x: toFloat({args.x_end}), y: toFloat({args.y_end})}})
    """

    # Create relations between starting and ending points with nearby metro stations
    create_disposable_relations_start = f"""match(n)
    match(s:Disposable) where distance(point({{x: s.x, y:s.y}}), point({{x:n.x, y:n.y}})) <= 1000 and s.name<>n.name
    merge (n)-[:Onfoot {{time: distance(point({{x: s.x, y:s.y}}), point({{x:n.x, y:n.y}}))/{FOOT_SPEED}}}]->(s)
    merge (n)<-[:Onfoot {{time: distance(point({{x: s.x, y:s.y}}), point({{x:n.x, y:n.y}}))/{FOOT_SPEED}}}]-(s);
    """

    # Create a relation between starting and ending point in case
    # it is quicker to go only on foot
    create_foot_relation = f"""
    match (s:Disposable {{name: 'START'}})
    match (e:Disposable {{name: 'END'}})
    merge (s)-[:Onfoot {{time: distance(point({{x: s.x, y:s.y}}), point({{x:e.x, y:e.y}}))/{FOOT_SPEED}}}]->(e)
    merge (s)<-[:Onfoot {{time: distance(point({{x: s.x, y:s.y}}), point({{x:e.x, y:e.y}}))/{FOOT_SPEED}}}]-(e)
    """

    # Query to get the shortest path using time attribute as weight
    query = """
        MATCH (start:Disposable {name: 'START'})
        MATCH (end:Disposable {name: 'END'})
        CALL gds.alpha.shortestPath.stream({
          nodeQuery: 'MATCH (n) RETURN id(n) as id',
          relationshipQuery: 'MATCH (n1)-[r]-(n2) RETURN id(r) as id, id(n1) as source, id(n2) as target, r.time as time',
          startNode: start,
          endNode: end,
          relationshipWeightProperty: 'time'
        })
        YIELD nodeId, cost
        RETURN gds.util.asNode(nodeId), cost
    """

    with driver.session() as session:

        session.run(create_start_node)
        session.run(create_end_node)
        session.run(create_disposable_relations_start)
        session.run(create_foot_relation)

        data = session.run(query).data()

        for dat in data:
            if dat["gds.util.asNode(nodeId)"]["name"].lower() not in [
                "start",
                "end",
            ]:
                print(
                    f'Station: {dat["gds.util.asNode(nodeId)"]["name"]: <35} Ligne: {dat["gds.util.asNode(nodeId)"]["line"]: <10} Temps:{dat["cost"]:.2f}'
                )
            else:
                print(
                    f'Station: {dat["gds.util.asNode(nodeId)"]["name"]: <35} Ligne: {"/": <10} Temps:{dat["cost"]:.2f}'
                )
        # Remove disposable nodes and relations from database to avoid polluting the graph
        session.run("match(n:Disposable) detach delete n")
