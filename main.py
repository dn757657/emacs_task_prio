import orgparse
import orgparse.node
from score import score_tasks, show_scores
from org_parse_util import duplicate_node, del_node_property, update_node_line, nodes_to_file
from node_util import generate_uid, find_node_idx, is_node_task, get_active_orgdates, get_effort, get_property_key

TASKS_FILE_IN = "C:/Users/Daniel/emacs/org/Tasks.org"
TASKS_FILE_OUT = "C:/Users/Daniel/emacs/org/Tasks_test_out.org"


def read_tasks(tasks_file_path):
    tasks = orgparse.load(tasks_file_path)

    return tasks


def flatten_root(root):
    """ return root where each entry only has a single active date other than deadline if present
        - get active org_dates
        - store heading, created date and times to duplicate in dictionary, cant duplicate (modify root) while iterating root!
            - i think heading and created can be used to identify uniquely
        - duplicate all marked nodes the amount of times needed
        - profit

    this thing is a real mess but it works
    """
    # determine to be flattened
    to_flatten = dict()
    for node in root[1:]:  # start at one to exclude root
        if is_node_task(node):
            node_active_orgdates = get_active_orgdates(node, scheduled=True)  # not including deadline

            date_count = len(node_active_orgdates)
            if date_count > 1:  # multiple active dates
                # minus one because one already exists
                to_flatten[generate_uid(node)] = date_count - 1

    # forgive me for my tree navigating sins lord
    # duplicate nodes as marked by to_duplicate
    for key in to_flatten.keys():

        times_to_duplicate = to_flatten[key]

        node_idx = find_node_idx(key, root)
        node_to_flatten = root[node_idx]
        node_active_orgdates = get_active_orgdates(node_to_flatten, scheduled=True)

        # duplicate all at once otherwise we duplicate a modified version of original node
        while times_to_duplicate > 0:
            root = duplicate_node(root, node_to_flatten)
            times_to_duplicate -= 1

        # delete until single active date for each node
        for i, keep_date in enumerate(node_active_orgdates):
            node_to_modify_idx = node_idx + i
            node_to_modify = root[node_to_modify_idx]

            for del_date in node_active_orgdates:
                if del_date != keep_date:
                    if del_date == node_to_modify.scheduled:
                        root = del_node_property(node_to_modify, 'scheduled')
                    else:
                        root = update_node_line(node_to_modify, del_date.__str__(), "")

    return root


def prep_nodes_for_analysis(root):
    """ sanitize and prepare nodes for scheduling or other analysis """

    # flatten node tree such that each node has single scheduled/active date
    prepped_nodes = flatten_root(root)

    # extract/asign node efforts
    for node in prepped_nodes[1:]:
        effort = get_effort(node)

        if effort:
            effort_key = get_property_key('effort', node)  # find effort key in properties
            node_effort = node.get_property(effort_key)  # get current effort if present
            if node_effort != effort:  # if effort found is different set to effort found
                node.properties[effort_key] = effort

    return prepped_nodes


def main():
    """ rules:
        1)  rangelist children only have effort if they need to be done prior to rangelist item
            examples:
                - often rangelist is used for meetings or recurring tasks, children of the meeting may be meeting
                  items, but if they occur within the meeting time they should not have effort
                - if they need be accomplished prior to the meeting they should have effort assigned
    """
    tasks = orgparse.load(TASKS_FILE_IN)
    prepped_tasks = prep_nodes_for_analysis(tasks)
    scores = score_tasks(prepped_tasks)

    # tasks = schedule_tasks(tasks)
    # tests = emacs_task_prio_tests.standard_tests(tasks)

    nodes_to_file(tasks, TASKS_FILE_OUT)

    print()


if __name__ == "__main__":
    main()
