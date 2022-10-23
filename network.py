## belief, disbelief and uncertainty values for each of the agents:

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pprint

agent = {1:{"b":0.3, "d":0.2, "u":0.5},
		  5:{"b":0.7, "d":0.2, "u":0.1},
		  9:{"b":0.6, "d":0.2, "u":0.2},
		  12:{"b":0.5, "d":0.2, "u":0.3}}

user_1 = {2:{"b":0.5, "d":0, "u":0.5},
		  8:{"b":0.0, "d":0.9, "u":0.1}}

user_2 = {7:{"b":0.2, "d":0.7, "u":0.1},}

user_3 = {}

user_4 = {3:{"b":0.9, "d":0.05, "u":0.05},}

user_5 = {4:{"b":0.7, "d":0, "u":0.3},
		  6:{"b":0.98, "d":0, "u":0.02}}

user_6 = {}

user_7 = {}

user_8 = {}

user_9 = {10:{"b":0, "d":0.9, "u":0.1}}

user_10 = {}

user_11 = {15:{"b":0.9, "d":0, "u":0.1}}

user_12 = {11:{"b":0.83, "d":0.07, "u":0.1},
		  13:{"b":0.75, "d":0, "u":0.25}}

user_13 = {14:{"b":0.6, "d":0.1, "u":0.3}}

user_14 = {}
user_15 = {}

all = [agent, user_1, 
			  user_2,
			  user_3,
			  user_4,
			  user_5,
			  user_6,
			  user_7,
			  user_8,
			  user_9,
			  user_10,
			  user_11,
			  user_12,
			  user_13,
			  user_14,
			  user_15
			  ]

'''
G = nx.Graph()

for i, node in enumerate(all):
	for key in node:
		G.add_edge(i, key, weight=node[key]["b"]*node[key]["u"]*2)
		#G.add_edge(i, key)



pos = nx.spring_layout(G)
nx.draw(G, pos, node_color='lawngreen', with_labels = True)
#nx.draw_spectral(G)
plt.axis('equal')
plt.show()
'''

graph_connections = []

for i, node in enumerate(all):
	for key in node:
		graph_connections.append([i, key])

for edge in graph_connections:
	print(f"{edge[0]}-->{edge[1]}")


## Combining beliefs:

#total_belief_x_z = b_x_y * b_y_z
#total_disbelief_x_z = d_x_y * d_y_z
# uncertainty: d_x_y + u_x_y + b_x_y*u_y_z

# r, s = (2*b/u, 2*d/u)

agents_total_trust = {1:{},
						2:{},
						3:{},
						4:{},
						5:{},
						6:{},
						7:{},
						8:{},
						9:{},
						10:{},
						11:{},
						12:{},
						13:{},
						14:{},
						15:{}
						}

checked_nodes = []
for key in agent:
	b = agent[key]["b"]
	d = agent[key]["d"]
	u = agent[key]["u"]
	
	r, s = (2*float(b)/float(u), 2*float(d)/float(u))
	agents_total_trust[key]["e"] = (r+1)/(r+s+2)
	agents_total_trust[key]["r"] = r
	agents_total_trust[key]["s"] = s
	checked_nodes.append(key)


while True:
	print(checked_nodes)
	new_checked_nodes = []
	for node in checked_nodes:
		vals = all[node]
		for key in vals:
			print(key)
			b = vals[key]["b"]
			d = vals[key]["d"]
			u = vals[key]["u"]
			
			print(b,d,u)
			r, s = (2*float(b)/float(u), 2*float(d)/float(u))
			agents_total_trust[key]["e"] = (r+1)/(r+s+2)
			agents_total_trust[key]["r"] = r
			agents_total_trust[key]["s"] = s
			new_checked_nodes.append(key)
		
	checked_nodes = new_checked_nodes.copy()
	if bool(checked_nodes) == False:
		break

#print(agents_total_trust)
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(agents_total_trust)

