# rudimentary node class which can represent an undirected graph
# this may later be replaced by a proper external library for graphs
class Node:
    def __init__(self, parent, data, delimiter='/'):
        self._delimiter = delimiter
        self.parent = parent
        self.children = []
        self.data = data
        if self.parent:
            self.parent.children.append(self)

    # does not work for graphs with cycles yet, todo: use DFS
    def __str__(self):
        s = str(self.data)
        p = self.parent
        while p:
            s = str(p.data) + self._delimiter + s
            p = p.parent
        return "Node(" + self._delimiter + s + ")"

    def __repr__(self):
        return str(self)

    def print_graph(self, short=False):
        self._print_recursive(0, short)

    # does not work for graphs with cycles yet, todo: use DFS
    def _print_recursive(self, level, short=False):
        if short:
            print(level * "   " + "-" + str(self.data))
        else:
            print(level * "   " + "-" + str(self))
        for child in self.children:
            child._print_recursive(level + 1, short)

    # does not work for graphs with cycles yet, todo: use DFS
    def get_all_nodes(self):
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes


# this function shall return all connected subgraphs of a specific size
# where size is the total amount of nodes that the subgraph must have
def get_all_subgraphs(graph, start_node, size):
    if size == 1:
        return [[start_node]]

    if size == 2:
        sub_graphs = []
        if start_node.parent:
            sub_graphs.append([start_node.parent, start_node])
        for child in start_node.children:
            sub_graphs.append([start_node, child])
        return sub_graphs

    # todo: to be continued


def test_main():
    s = Node(None, "s")
    n1 = Node(s, "1")
    n2 = Node(s, "2")
    n3 = Node(n1, "3")
    n4 = Node(n2, "4")
    n5 = Node(n2, "5")
    n6 = Node(n4, "6")

    s.print_graph(True)
    all_nodes = s.get_all_nodes()
    print(all_nodes)

    sub_graphs = get_all_subgraphs(s, n2, 2)
    for sg in sub_graphs:
        print(sg)


if __name__ == '__main__':
    test_main()
