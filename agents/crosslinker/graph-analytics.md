# Graph Analytics Logic

## Metrics to compute

### Node-level
- **Degree centrality**: count of connections (in + out)
- **Betweenness centrality**: how often a node sits on the shortest path between two other nodes
- **Domain**: from frontmatter `domain:` field

### Graph-level
- **Total nodes**: count of notes
- **Total edges**: count of unique connections
- **Density**: edges / (nodes * (nodes-1) / 2)
- **Connected components**: how many isolated subgraphs exist
- **Average degree**: mean connections per note

### Domain-level
- **Intra-domain density**: connections within a domain
- **Inter-domain bridges**: connections between domains
- **Domain size**: note count per domain

## Implementation approach

For small vaults (<500 notes): in-memory adjacency list, brute-force analytics.
For larger vaults: use networkx (Python) or similar graph library via script.

The `scripts/vault-stats.py` script can compute these metrics from the vault filesystem by parsing frontmatter and wikilinks.
