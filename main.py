import orgparse
import orgparse.node
import pandas as pd
import datetime

TASKS_FILE_IN = "C://Users//Daniel//emacs//org//Tasks_test.org"
TASKS_FILE_OUT = "C://Users//Daniel//emacs//org//Tasks_testout.org"


def read_tasks(tasks_file_path):
    tasks = orgparse.load(tasks_file_path)

    return tasks


def parse_scheduled_from_task(task):
    """ there are different ways to determine if task is scheduled other than scheduled prop
     - scheduled can be multiple, make list
     """

    scheduled = None
    if task.scheduled:
        scheduled = task.scheduled

    # elif len(task.rangelist) > 0:
    #     for scheduled


def get_scheduled(task):
    """ to determine the time status of the task, possible outcomes:
            - task has deadline
                - could be date object
                - could also be datetime object
            - parent or ancestor has deadline (nearest deadline)
            - task is scheduled already (pull effort from this?) -> move to other func!
    """
    scheduled = None

    if task.scheduled:
        scheduled = task.scheduled

    elif task.parent:
        level = task.level

        while level >= 2 and not scheduled:
            parent = task.get_parent()
            if parent.scheduled:
                scheduled = parent.scheduled
                # break
            else:
                level += -1
                task = parent

    if scheduled:
        # convert ord node date object to datetime
        scheduled_str = scheduled.start.strftime("%Y-%m-%d %H:%M")
        scheduled_datetime = datetime.datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")

        if scheduled_datetime.time() == datetime.time.min:
            # set to end of day
            scheduled_datetime = scheduled_datetime + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

        scheduled = scheduled_datetime

    return scheduled


def get_effort(node):
    """ fetch a property, if property not found get from nearest_parent
    """
    effort = node.get_property("Effort")

    if node.parent:
        level = node.level

        while level >= 2:
            parent = node.get_parent()
            parent_effort = parent.get_property('Effort')
            if parent_effort:
                effort += parent_effort
            else:
                node = parent
            level += -1

    return effort


def get_nearest_datetype_property(node, node_property_str):
    """ fetch a property, if property not found get from nearest_parent
    """
    property_found = None
    node_property = getattr(node, node_property_str)

    if node_property:
        property_found = node_property

    elif node.parent:
        level = node.level

        while level >= 2 and not property_found:
            parent = node.get_parent()
            parent_property = getattr(parent, node_property_str)

            if parent_property:
                property_found = parent_property
                # break
            else:
                level += -1
                node = parent


    # property_found = property_found._repeater

    # if property_found:
    #     # property_found = property_found._repeater
    #     property_datetime = convert_org_parse_date_2_datetime(property_found)
    #
    #     if property_datetime.time() == datetime.time.min and node_property_str == 'deadline':
    #         property_datetime = set_datetime_eod(property_datetime)
    #
    #     property_found = property_datetime

    return property_found


def process_tree(tree, min_real_tasks_level=2):
    """
    :param tree: orgparse node
    :param min_real_tasks_level: minimum level at which real tasks exist (not headings)
    :return:
    """

    print(f'task: {tree.heading}')  # this is the bottom of the subtree, will progress down list top to bottom
    print(f'level: {tree.level}')

    if tree.level >= min_real_tasks_level:
        # need to parse effort also since multiple ways of determining effort

        deadline = get_deadline(tree)
        print(f'deadline: {deadline}')

        scheduled = get_scheduled(tree)
        print(f'deadline: {scheduled}')


    print()
    return


def post_order_traversal(tree, func=None):
    """ return tasks starting """

    # task_scores = pd.DataFrame(columns=['task_heading', 'score', 'scheduled', 'deadline'])  # might move to main

    for branch in tree.children:
        post_order_traversal(branch, func)
    if func:
        func(tree)

    return

    # maybe first flatten the tasks within the range, so all can be processed more or less the same, takes care of repeated tasks
    # check if scheduled, has time already assigned
    # get time scheduled or deadline
    # get adjusted effort
    # get score

    # need to process bottom up (not really, just need to unpack trees)
    # therefore seeking only tasks with no children (only process bottom)
    # heading that are not tasks (organizational) have no effort
    # if not tree.children and tree.get_property('Effort'):
    #     process_tree(tree)

        # if tree.level >= 2:
        #     deadline = get_deadline_or_scheduled(tree)
        #     print(deadline)


        # if tree.level == 2:  # tree level 2 indicates a task without parents given current setup
        #     deadline = tree.deadline.start  # start can return date or datetime?
        #     if type(deadline) == datetime.date:
        #         deadline = datetime.datetime.combine(deadline, datetime.time())
        #
        #     effort_minutes = tree.get_property("Effort")
        #     effort_datetime = datetime.timedelta(minutes=effort_minutes)
        #
        #     adjusted_deadline = deadline - effort_datetime
        #     score = adjusted_deadline - datetime.datetime.today()  # this is how long until you actually need ot start
        #
        #     print(score)


def convert_org_parse_date_2_datetime(org_parse_date):
    """
    :param org_parse_date: org prase date object (annoying)
    :return:
    """

    org_date_str = org_parse_date.start.strftime("%Y-%m-%d %H:%M")
    org_date_datetime = datetime.datetime.strptime(org_date_str, "%Y-%m-%d %H:%M")
    datetime_obj = org_date_datetime
    return datetime_obj


def set_datetime_eod(datetime_obj):
    """ set datetime object time to end of day"""
    datetime_obj = datetime_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
    return datetime_obj


def process(nodes, node_stats, min_real_tasks_level=2):
    """ need to define a window upper bound in tree of nodes """

    # populate node stats as we go
    # can find upper bound in populated stats
    # expand nodes in stats once processed initially (upper date bound is known)
    # node_stats = pd.DataFrame(columns=['node_heading', 'deadline', 'effort', 'scheduled', 'repeat', 'repeat_unit', 'repeat_freq'])

    for child in nodes.children:
        node_stats = process(child, node_stats)

    # get deadline if exists
    # get scheduled if exists
    # process rangelist (stores dates in a time range)
    # process datelist (stores date stamps not in scheduled)
    # get calc effort
    # get repeating stats

    if nodes.level >= min_real_tasks_level:
        deadline = get_nearest_datetype_property(nodes, 'deadline')
        scheduled = get_nearest_datetype_property(nodes, 'scheduled')
        effort = get_effort(nodes)

        datelist = nodes.datelist  # any dates assigned
        rangelist = nodes.rangelist  # any dates assigned as a range or including a time range

        created = None

        node_stats_new = pd.DataFrame(data=[[nodes.heading,
                                             deadline,
                                             effort,
                                             scheduled,
                                             datelist,
                                             rangelist,
                                             created]],
                                      columns=node_stats.columns.tolist())

        node_stats = pd.concat([node_stats_new, node_stats], ignore_index=True)

    return node_stats


def remove_created_dates(nodes_df):
    """ expand datelist (create new entries) """

    # cant change index while iterating
    delete_nodes = list()
    insert_nodes = list()

    # parse datelist - past dates in the past are always created date? not sure
    # get node by index as df
    # create new entries based on datelist
    # delete original entry

    for index in range(len(nodes_df)):
        # node = nodes_df.loc[[index]]
        datelist = nodes_df.loc[index, 'datelist']

        # drop old node
        # delete_nodes.append(index)

        if len(datelist) > 0:
            for org_date in datelist:

                # new_node = node

                # if in the past and not repeated then its created date?
                if convert_org_parse_date_2_datetime(org_date) < datetime.datetime.today() and not org_date._repeater:
                    # set up new node
                    nodes_df.loc[index, 'created'] = org_date

                    # datelist.remove(org_date)
                    nodes_df.loc[index, 'datelist'].remove(org_date)
                    # new_node.loc[index, 'datelist'] = None

                # else:
                #     # make new entry from org_date as scheduled
                #     new_node.loc[index, 'scheduled'] = org_date

                # insert new node
                # nodes_df = pd.concat([nodes_df, node], ignore_index=True)
                # new_node.loc[index, 'datelist'] = None
                # insert_nodes.append(new_node)
                # datelist.remove(org_date)

    # nodes_df.drop(delete_nodes, inplace=True)
    # insert_nodes.append(nodes_df)
    # nodes_df = pd.concat(insert_nodes, ignore_index=True)  # good god why

    return nodes_df


def expand_lists(nodes_df, cols):
    """ expand datelist (create new entries) """

    # cant change index while iterating
    delete_nodes = list()
    insert_nodes = list()

    nodes_df_expanded = pd.DataFrame(columns=nodes_df.columns.tolist())

    # parse datelist - past dates in the past are always created date? not sure
    # get node by index as df
    # create new entries based on datelist
    # delete original entry
    for col in cols:
        for index in range(len(nodes_df)):
            # node = nodes_df.loc[[index]]
            col_list = nodes_df.loc[index, col]

            # drop old node
            # delete_nodes.append(index)

            if len(col_list) > 0:
                for org_date in col_list:
                    # copy node to new node, ignore means it goes to max (next)
                    nodes_df_expanded = pd.concat([nodes_df_expanded, nodes_df.loc[[index]]],
                                                  ignore_index=True)
                    # change new node scheduled to
                    nodes_df_expanded.loc[max(nodes_df_expanded.index), 'scheduled'] = org_date
                    nodes_df_expanded.loc[max(nodes_df_expanded.index), col] = None

    # nodes_df.drop(delete_nodes, inplace=True)
    # include nodes that were not expanded
    nodes_df_expanded = pd.concat([nodes_df_expanded,
                                   nodes_df[~nodes_df.node_heading.isin(nodes_df_expanded.node_heading)]],
                                  ignore_index=True)

    return nodes_df_expanded

def remove_headings(nodes_df):
    """ any nodes with no deadline, effort or scheduled date are considered headings """
    nodes_df.dropna(subset=['deadline', 'effort', 'scheduled'], thresh=3, inplace=True)
    return


def main():
    tasks = read_tasks(TASKS_FILE_IN)
    root = tasks.root

    # populate node stats as we go
    # can find upper bound in populated stats
    # expand nodes in stats once processed initially (upper date bound is known)
    # node_stats = pd.DataFrame(columns=['node_heading', 'deadline', 'effort', 'scheduled', 'repeat', 'repeat_unit', 'repeat_freq'])

    node_stats = pd.DataFrame(columns=['node_heading',
                                       'deadline',
                                       'effort',
                                       'scheduled',
                                       'datelist',
                                       'rangelist',
                                       'created'])

    node_stats = process(tasks, node_stats)
    node_stats = remove_created_dates(node_stats)
    node_stats = expand_lists(node_stats, ['datelist', 'rangelist'])
    # node_stats = expand_lists(node_stats, 'rangelist')

    # remove_headings(node_stats)
    print()

    # trees = tasks.children  # trees are all top level headings

    # for each tree we need to find the base child
    # for tree in trees:
    # post_order_traversal(tasks)

    # for tree in tasks.children:
    #     process_tree(tree)
    #
    # print()
    #
    # subtree = tasks.children[0]
    # while subtree.children:
    #     subtree = subtree.children

    # find_tree_min_level(tasks)

    # need to find the bottom of the tree and work way back up using existing neighbour capability of nodes?
    # root nodes have different rules than all others, they need deadline to be valid whereas others can meet other
    # conditions to be considered valid
    # while True:
    #     for subtree in tasks.children:
    #         if subtree.deadline:  # root task must have deadline to be valid
    #             if subtree.children:  # if children need to keep checking for children
    #                 tasks = subtree
    #                 break
    #             else:  # if no children process
    #                 print(f'start processing {subtree.heading}')


if __name__ == "__main__":
    main()
