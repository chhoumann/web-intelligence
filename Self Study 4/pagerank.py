import networkx as nx

# TODO: Implement the PageRank algorithm using lecture slides method

# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html
def pagerank(graph: nx.DiGraph, alpha=0.85, max_iter=100, tolerance=1.0e-6):
    """
    Returns a dictionary of page ranks for each page in the graph

    alpha is the dampening parameter for PageRank.
    """
    if len(graph) == 0:
        return {}

    # Graph needs directed edges. If it is undirected, we convert it to directed.
    # During conversion, each edge is replaced by two edges, i.e. (v, u) and (u, v).
    if not graph.is_directed():
        digraph = graph.to_directed()
    else:
        digraph = graph

    # weights is a right-stochastic representation of the graph.
    # A right-stochastic graph is a weighted directed graph in which for each node,
    # the sum of the weights of all the out-edges of that node is 1.
    # Basically, the surfer has an equal probability of choosing any of the out-links.
    weighted_graph = nx.stochastic_graph(digraph, weight="weight")
    num_nodes = weighted_graph.number_of_nodes()

    # Starting value for PageRank iteration for all nodes
    iter_val = dict.fromkeys(weighted_graph, 1.0 / num_nodes)  # uniform probability

    # Assign uniform personalization vector
    personalization_vec = dict.fromkeys(weighted_graph, 1.0 / num_nodes)

    # we don't want to have any dangling pages,
    # which would mean to have a page with no outgoing links
    # the solution is to add outgoing edges from dangling pages into a transition probability
    # matrix, with a probability of 1/N
    dangling_weights = personalization_vec
    dangling_nodes = [
        n
        for n in weighted_graph
        if weighted_graph.out_degree(n, weight="weight") == 0.0
    ]

    # power iteration: make up to max_iter iterations
    # https://en.wikipedia.org/wiki/Power_iteration
    for _ in range(max_iter):
        last_iter_val = iter_val
        iter_val = dict.fromkeys(last_iter_val.keys(), 0)

        danglesum = alpha * sum(last_iter_val[node] for node in dangling_nodes)

        for node in iter_val:
            # left multiply: x^T=xlast^T*W
            for _, nbr, weight in weighted_graph.edges(node, data="weight"):
                iter_val[nbr] += alpha * last_iter_val[node] * weight

            iter_val[node] += danglesum * dangling_weights.get(node, 0) + (
                1.0 - alpha
            ) * personalization_vec.get(node, 0)

        err = sum([abs(iter_val[n] - last_iter_val[n]) for n in iter_val])

        # While we want to reach the stationary distribution for the markov chain,
        # we still have to set a threshold for the error. If it can't converge, we stop.
        if err < num_nodes * tolerance:
            return iter_val

    raise Exception(
        f"Pagerank: power iteration failed to converge in {max_iter} iterations. Err: {err}."
    )
