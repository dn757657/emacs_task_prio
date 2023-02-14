import orgparse
import orgparse.node
import org_parse_util
import emacs_task_prio_tests

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


def main():
    """ rules:
        1)  rangelist children only have effort if they need to be done prior to rangelist item
            examples:
                - often rangelist is used for meetings or recurring tasks, children of the meeting may be meeting
                  items, but if they occur within the meeting time they should not have effort
                - if they need be accomplished prior to the meeting they should have effort assigned
    """
    tasks = orgparse.load(TASKS_FILE_IN)
    # test = pre_order_traversal(tasks.root)

    test_node = tasks.children[1].children[0]
    test = emacs_task_prio_tests.test_update_scheduled(test_node)

    org_parse_util.nodes_to_file(tasks, TASKS_FILE_OUT)

    print()


if __name__ == "__main__":
    main()
