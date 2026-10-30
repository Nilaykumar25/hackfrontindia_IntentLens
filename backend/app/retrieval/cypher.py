"""All Cypher used at question time. Parameterised templates only: the LLM never writes Cypher."""

_DECISION_RETURN = """
OPTIONAL MATCH (d)-[ev:EVIDENCED_BY]->(x)
OPTIONAL MATCH (d)-[:MADE_BY]->(p:Person)
OPTIONAL MATCH (n:Decision)-[sr:SUPERSEDES|REVERTS]->(d)
OPTIONAL MATCH (d)-[:SUPERSEDES|REVERTS]->(o:Decision)
RETURN d{.id,.title,.summary,.rationale,.decided_on,.status,.explicit_rationale,.agreement,.alternatives_rejected} AS decision,
  collect(DISTINCT e.id) AS entity_ids,
  collect(DISTINCT {id:x.id, kind:labels(x)[0], url:x.url, date:x.date, author:x.author,
                    snippet:left(coalesce(x.text,''),400), quote:ev.quote}) AS evidence,
  collect(DISTINCT p.id) AS people,
  collect(DISTINCT n{.id,.title,.summary,.decided_on, reason:sr.reason, confidence:sr.confidence, review_flag:sr.review_flag}) AS superseded_by,
  collect(DISTINCT o{.id,.title,.decided_on}) AS supersedes
"""

DECISIONS_BY_ENTITY = """
MATCH (e:Entity) WHERE e.id IN $entity_ids
MATCH (d:Decision)-[:GOVERNS]->(e)
""" + _DECISION_RETURN

DECISIONS_BY_IDS = """
MATCH (d:Decision) WHERE d.id IN $ids
OPTIONAL MATCH (d)-[:GOVERNS]->(e:Entity)
""" + _DECISION_RETURN

ENTITY_EXACT = """
MATCH (e:Entity) WHERE toLower(e.name) IN $names OR toLower(e.path) IN $names
RETURN e.id AS id, e.name AS name, labels(e) AS labels, 10.0 AS score LIMIT 5
"""

ENTITY_FULLTEXT = """
CALL db.index.fulltext.queryNodes('entity_names', $q) YIELD node, score
RETURN node.id AS id, node.name AS name, labels(node) AS labels, score
ORDER BY score DESC LIMIT $k
"""

DECISION_VECTOR = """
CALL db.index.vector.queryNodes('decision_embedding', $k, $embedding) YIELD node, score
OPTIONAL MATCH (node)-[:GOVERNS]->(e:Entity)
RETURN node.id AS id, collect(e.id) AS entity_ids, score
"""

LAST_CHANGERS = """
MATCH (c:Commit)-[:MODIFIES]->(e:Entity) WHERE e.id IN $entity_ids
RETURN DISTINCT c.id AS id, left(c.message, 200) AS message, c.date AS date, c.author AS author, c.url AS url
ORDER BY c.date DESC LIMIT 5
"""

TOP_CONTRIBUTOR = """
MATCH (p:Person)-[:AUTHORED]->(c:Commit)-[:MODIFIES]->(e:Entity) WHERE e.id IN $entity_ids
RETURN p.id AS id, p.name AS name, count(DISTINCT c) AS commits, max(c.date) AS last_active
ORDER BY commits DESC LIMIT 1
"""

DRIFT_COUNT = """
MATCH (c:Commit)-[:MODIFIES]->(e:Entity) WHERE e.id IN $entity_ids
  AND $after IS NOT NULL AND $after <> '' AND c.date > $after
  AND NOT EXISTS { MATCH (c)<-[:EVIDENCED_BY]-(:Decision) }
  AND NOT EXISTS { MATCH (c)-[:PART_OF]->()<-[:EVIDENCED_BY]-(:Decision) }
RETURN count(DISTINCT c) AS n
"""

RELATED_DISCUSSIONS = """
CALL db.index.vector.queryNodes('comment_embedding', $k, $embedding) YIELD node, score
RETURN node.id AS id, node.url AS url, node.date AS date, node.author AS author, left(node.text, 300) AS snippet, score
"""

NEIGHBOURHOOD = """
MATCH (e:Entity {id:$id})<-[:GOVERNS]-(d:Decision)
OPTIONAL MATCH (d)-[r:EVIDENCED_BY|MADE_BY|SUPERSEDES|REVERTS|REFINES]-(x)
RETURN e.id AS eid, e.name AS ename, d{.id,.title,.status} AS d, type(r) AS rtype,
       (startNode(r) = d) AS outgoing, x.id AS xid, labels(x)[0] AS xlabel,
       coalesce(x.title, x.name, left(x.text, 60), x.id) AS xname
"""
