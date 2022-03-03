# Neo4j Metro Paris

The goal of the project is to create a graph database of subway stations in Paris.
The data comes from RATP.

## Neo4j instance
The project use a specific docker image of Neo4j which can be retrieved with this command:
`docker container run -p 7474:7474 -p 7687:7687 datascientest/neo4j`.

## Usage
When the instance is up and running open a browser to `localhost:7474`.
Enter commands from `cypher_create_graph` in the Neo4j terminal to create the graph with the data.
The script `path_engine.py` return subway stations on the shortest path between to points.
`commandes_questions` contains queries which can executed in the terminal to answer the given question.
