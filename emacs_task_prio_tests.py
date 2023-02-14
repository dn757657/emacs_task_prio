import datetime
from PyOrgMode.PyOrgMode import PyOrgMode
import orgparse.date as orgd
import re
import org_parse_util

TASKS_FILE_IN = "C:/Users/Daniel/emacs_x29hm-v4p65/org/Tasks_test.org"


def test_duplicate(nodes, node_to_duplicate):
    """ check if node is actually duplicated
    currently fails because node count returns 0 in second count, not sure why
    """

    node_count_pre = count_nodes_in_tree(nodes, node_to_duplicate)

    nodes_w_duplicate = org_parse_util.duplicate_node(nodes, node_to_duplicate)

    node_count_post = count_nodes_in_tree(nodes_w_duplicate, node_to_duplicate)

    if node_count_pre == node_count_post-1:
        return True
    else:
        return False


def count_nodes_in_tree(nodes, node_to_count):

    node_count = 0
    for node in nodes[0:]:
        if node == node_to_count:
            node_count += 1

    return node_count


def main():

    dateorg = '<2006-11-01 Wed 19:15 +1w>'
    dateorg_ranged = '<2004-08-23 Mon>--<2004-08-26 Thu>'

    date_pyorgmode = PyOrgMode.OrgDate(dateorg_ranged)
    date_org = date_pyorgmode.get_value()

    orgparse_date = orgd.OrgDate.list_from_str(dateorg)[0]
    orgparse_date_str = orgparse_date.__str__()

    print()

if __name__ == "__main__":
    main()