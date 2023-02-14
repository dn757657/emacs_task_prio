import orgparse
import orgparse.node


def dump_nodes(root):
    """ returns list of lists, sublist are lines of each dumped node
    the lines contain everything known about the node, therefore it is comprehensive
    """

    lines = []
    for node in root[0:]:
        lines.append(node._lines)

    # flatted_lines = flatten(lines)

    return lines


def duplicate_node(node):
    """ i think we need the entire tree, hence pass root
        - get both the root and node as lines
        - get the start and end of node_lines to duplicate within root_lines
        - insert the node_lines after root_lines

        returns nodes with duplicated
    """

    root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # split root_lines at end of node_lines and insert new duplicated node there
    root_lines_before_new_node = root_lines[:node_end_location+1]
    root_lines_after_new_node = root_lines[node_end_location+1:]
    root_lines = root_lines_before_new_node + node_lines + root_lines_after_new_node

    return lines_2_nodes(root_lines)


def locate_node_in_root(root_lines, node_lines, node_line_number):
    """
    to find where to insert duplicate we need to indentify node from potential duplicates
    in the root_lines list,
    each node as a linenumber property indicating its location in the root._lines structure
    if it is flat, therefore by using the lengths of the individual lists in root_lines
    we can find its location and insert appropriately
    """

    # find location in root_nodes where node_lines are using node.linenumber
    lines = 0
    i = 0
    while lines < node_line_number:
        lines += len(root_lines[i])
        i += 1

    # get start and end of node_lines in root_lines
    node_start_location = i - 1  # inclusive (index is first line)
    node_end_location = node_start_location + len(node_lines) - 1  # inclusive (index is last line)

    return node_start_location, node_end_location


def update_date_kwd(node, kwd, new_date):
    """ for when orgparse.OrgNode.kwd cannot be set (scheduled and deadline), therefore:
        - dump lines
        - update schedule in lines
            - convert orgDate to string
            - find scheduled keyword
            - replace date component
        - turn lines back into a node

    :param new_date is orgparse.OrgDate
    :return root
    """

    root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # since we only want to change scheduled in the node passed, use [0] from node_lines
    test = root_lines
    line_to_update = root_lines[node_start_location]

    i = None
    for i, line in enumerate(node_lines):
        if kwd in line:  # find which line contains keyword
            break

    if i:
        date_start_idx = line_to_update[i].find("<")
        date_end_idx = line_to_update[i].find(">")

        root_lines[node_start_location][i] = line_to_update[i][:date_start_idx] \
                                             + new_date.__str__() \
                                             + line_to_update[i][date_end_idx+1:]

    return lines_2_nodes(root_lines)


def lines_2_nodes(lines):
    """ turn lines back to a node tree
    :param lines: list of lines
    :return: orgparse node env
    """

    flatted_list = flatten(lines)
    flatted_str = '\n'.join(flatted_list)

    nodes = orgparse.loads(flatted_str)

    return nodes


def flatten(lst):
    """ flatten a list of unknown depth to a single list of no depth """
    result = []
    for item in lst:
        if type(item) == list:
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def nodes_to_file(nodes, outfile):
    """ write node tree out to file
    :param nodes: orgparse node env
    :param outfile: string filepath
    :return: nothing
    """

    lines = dump_nodes(nodes)
    flatted_list = flatten(lines)
    flatted_str = '\n'.join(flatted_list)

    with open(outfile, 'w') as file:
        file.write(flatted_str)

    return
