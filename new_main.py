import numpy as np
import orgparse
import orgparse.node
from orgparse import date as orgdate
import pandas as pd
import datetime
import PyOrgMode

TASKS_FILE_IN = "C:/Users/Daniel/emacs_x29hm-v4p65/org/Tasks_test.org"
TASKS_FILE_OUT = "C:/Users/Daniel/emacs_x29hm-v4p65/org/Tasks_test_out.org"


def read_tasks(tasks_file_path):
    tasks = orgparse.load(tasks_file_path)

    return tasks


def score_task(node):
    """ score and return node with score property added """

    return node


def pre_order_traversal(node):
    """ root -> left node -> right node

    node must have children property
    node must have heading property
    """
    # score node
    print(f'scoring: {node.heading}')
    parent_traversal(node)  # get properties of parents

    for child in node.children:
        pre_order_traversal(child)

    return node


def parent_traversal(node):
    """ trace branch back to root via parents """

    while node != node.root:
        node = node.parent
        print(f'parent: {node.heading}')


def dump_nodes(root):
    """ returns list of lists, sublist are lines of each dumped node
    the lines contain everything known about the node, therefore it is comprehensive
    """

    lines = []
    for node in root[0:]:
        lines.append(node._lines)

    return lines


def duplicate_node(root, node):
    """ i think we need the entire tree, hence pass root
        - get both the root and node as lines
        - get the start and end of node_lines to duplicate within root_lines
        - insert the node_lines after root_lines

        returns nodes with duplicated
    """
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    end_idx = root_lines.index(node_lines[-1])  # find where the node_lines block ends in root_lines

    root_lines_start = root_lines[:end_idx + 1]
    root_lines_end = root_lines[end_idx + 1:]

    root_lines = root_lines_start + node_lines + root_lines_end

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


def main():
    """ rules:
        1)  rangelist children only have effort if they need to be done prior to rangelist item
            examples:
                - often rangelist is used for meetings or recurring tasks, children of the meeting may be meeting
                  items, but if they occur within the meeting time they should not have effort
                - if they need be accomplished prior to the meeting they should have effort assigned
    """
    tasks = orgparse.load(TASKS_FILE_IN)
    test = pre_order_traversal(tasks.root)

    # test to see if lines are updated with properties
    # lines are NOT updated if random property is added - could write a func to do this, might need to
    node_lines_changed = False

    test_node = tasks.children[1].children[0]
    test_node.properties['urgency'] = 10  # simulate urgency addition
    lines_ini = test_node._lines

    # NODE dumping?
    from inorganic_karlicross import asorgoutline
    test = asorgoutline(heading=test_node.heading,
                        todo=test_node.todo,
                        tags=test_node.tags,
                        # scheduled=test_node.scheduled,
                        properties=test_node.properties,
                        body=test_node.body,
                        )
    print(test)

    # testing syncs-------------------------------
    # # update.sync deadline
    # new_dead = orgdate.OrgDate.from_str('2012-02-10 Fri')
    # test_node.deadline = new_dead
    #
    # # update.sync scheduled
    # new_sched = orgdate.OrgDate.from_str('2012-02-10 Fri')
    # test_node.scheduled = new_sched

    # # update.sync a property
    # test_node.properties['Effort'] = 5
    #
    # lines_post = test_node._lines
    #
    # if lines_ini != lines_post:
    #     node_lines_changed = True
    #
    # nodes_to_file(tasks, TASKS_FILE_OUT)  # out to file (check)

    print()


if __name__ == "__main__":
    main()
