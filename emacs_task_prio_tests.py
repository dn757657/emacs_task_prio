import datetime

import orgparse.date

from PyOrgMode.PyOrgMode import PyOrgMode
import orgparse.date as orgd
import re
import org_parse_util

TASKS_FILE_IN = "C:/Users/Daniel/emacs_x29hm-v4p65/org/Tasks_test.org"


def standard_tests(nodes):
    """ standard tests for org parse util layer """

    test_results = dict()
    test_node = nodes.children[1].children[0]
    test_orgdate = orgparse.date.OrgDate.list_from_str('<2006-11-01 Wed 19:15>')[0]

    test_results['update_scheduled'] = test_set_node_prop(test_node, 'scheduled', test_orgdate.__str__())
    test_results['update_deadline'] = test_set_node_prop(test_node, 'deadline', test_orgdate.__str__())
    test_results['update_existing_property'] = test_set_node_prop(test_node, 'effort', '5')

    return test_results


def test_set_node_prop(node, prop, new_val):
    """ working """

    root = org_parse_util.set_node_property(node, prop, new_val)

    snode = None
    for snode in root[1:]:
        if snode.linenumber == node.linenumber:
            break
    
    new_node = snode  # snode is search node not an insult

    if not snode:
        return False
    else:
        if hasattr(new_node, prop):
            if getattr(new_node, prop).__str__() == new_val:
                return True
        if prop.lower() in [x.lower() for x in new_node.properties.keys()]:
            for i, cprop in enumerate(new_node.properties.keys()):
                if cprop.lower() == prop.lower():
                    break
            actual_prop = list(new_node.properties.keys())[i]

            # remember that update only has str as intake as were updating root lines!
            if str(new_node.properties[actual_prop]) == new_val:
                return True
        else:
            return False


def test_duplicate(nodes, node_to_duplicate):
    """ check if node is actually duplicated
    currently fails because node count returns 0 in second count, not sure why

    can probably fix using line number comparison? (should probably fix)
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