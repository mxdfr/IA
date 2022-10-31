from trust_scores import all, agent

def create_trust_network(scores, agent):
    '''
    Creating agents trust network based on combining beliefs:

    total_belief_x_z = b_x_y * b_y_z
    total_disbelief_x_z = d_x_y * d_y_z
    uncertainty: d_x_y + u_x_y + b_x_y*u_y_z

    r, s = (2*b/u, 2*d/u)

    trust scores are saved and returned as a distionary, where:
        * keys are tweeter account ids,
        * and values are tuples of e, r, and s
    '''
    graph_connections = []

    for i, node in enumerate(scores):
        for key in node:
            graph_connections.append([i, key])

    agents_total_trust = {1: {},
                          2: {},
                          3: {},
                          4: {},
                          5: {},
                          6: {},
                          7: {},
                          8: {},
                          9: {},
                          10: {},
                          11: {},
                          12: {},
                          13: {},
                          14: {},
                          15: {}
                          }

    checked_nodes = []
    for key in agent:
        b = agent[key]["b"]
        d = agent[key]["d"]
        u = agent[key]["u"]

        r, s = (2 * float(b) / float(u), 2 * float(d) / float(u))
        agents_total_trust[key]["e"] = (r + 1) / (r + s + 2)
        agents_total_trust[key]["r"] = r
        agents_total_trust[key]["s"] = s
        checked_nodes.append(key)

    while True:
        new_checked_nodes = []
        for node in checked_nodes:
            vals = scores[node]
            for key in vals:
                b = vals[key]["b"]
                d = vals[key]["d"]
                u = vals[key]["u"]

                r, s = (2 * float(b) / float(u), 2 * float(d) / float(u))
                agents_total_trust[key]["e"] = (r + 1) / (r + s + 2)
                agents_total_trust[key]["r"] = r
                agents_total_trust[key]["s"] = s
                new_checked_nodes.append(key)

        checked_nodes = new_checked_nodes.copy()
        if bool(checked_nodes) == False:
            break

    return agents_total_trust


if __name__ == "__main__":
    scores = create_trust_network(all, agent)
    print(scores)
