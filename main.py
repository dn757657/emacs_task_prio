import numpy as np
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


# def get_scheduled(task):
#     """ to determine the time status of the task, possible outcomes:
#             - task has deadline
#                 - could be date object
#                 - could also be datetime object
#             - parent or ancestor has deadline (nearest deadline)
#             - task is scheduled already (pull effort from this?) -> move to other func!
#     """
#     scheduled = None
#
#     if task.scheduled:
#         scheduled = task.scheduled
#
#     elif task.parent:
#         level = task.level
#
#         while level >= 2 and not scheduled:
#             parent = task.get_parent()
#             if parent.scheduled:
#                 scheduled = parent.scheduled
#                 # break
#             else:
#                 level += -1
#                 task = parent
#
#     if scheduled:
#         # convert ord node date object to datetime
#         scheduled_str = scheduled.start.strftime("%Y-%m-%d %H:%M")
#         scheduled_datetime = datetime.datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")
#
#         if scheduled_datetime.time() == datetime.time.min:
#             # set to end of day
#             scheduled_datetime = scheduled_datetime + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
#
#         scheduled = scheduled_datetime
#
#     return scheduled


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

    # tree traversal reverse
    for child in nodes.children:
        node_stats = process(child, node_stats)

    # get deadline if exists
    # get scheduled if exists
    # process rangelist (stores dates in a time range)
    # process datelist (stores date stamps not in scheduled)
    # get calc effort
    # get repeating stats

    # do stuff with tree as it is traversed
    if nodes.level >= min_real_tasks_level:
        deadline = get_nearest_datetype_property(nodes, 'deadline')
        scheduled = get_nearest_datetype_property(nodes, 'scheduled')
        # checks 1) if scheduled before deadline

        effort = get_effort(nodes)

        datelist = nodes.datelist  # any dates assigned
        rangelist = nodes.rangelist  # any dates assigned as a range or including a time range

        created = None

        node_stats_new = pd.DataFrame(data=[[nodes.heading,
                                             deadline,
                                             effort,
                                             scheduled,
                                             datelist,
                                             rangelist]],
                                      columns=node_stats.columns.tolist())

        node_stats = pd.concat([node_stats_new, node_stats], ignore_index=True)

    return node_stats


def remove_created_dates(nodes_df):
    """ remove created dates from datelist and move to own column """

    if 'created' not in nodes_df.columns:
        nodes_df['created'] = np.nan

    for index in range(len(nodes_df)):
        datelist = nodes_df.loc[index, 'datelist']

        if len(datelist) > 0:
            for org_date in datelist:
                if convert_org_parse_date_2_datetime(org_date) < datetime.datetime.today() and not org_date._repeater:
                    nodes_df.loc[index, 'created'] = org_date  # put created in created col
                    nodes_df.loc[index, 'datelist'].remove(org_date)  # remove created from datelist

    return nodes_df


def expand_lists(nodes_df, cols):
    """ expand datelist (create new entries) """

    nodes_df_expanded = pd.DataFrame(columns=nodes_df.columns.tolist())

    for col in cols:
        for index in range(len(nodes_df)):
            col_list = nodes_df.loc[index, col]

            if len(col_list) > 0:
                for org_date in col_list:
                    # copy node to new node, ignore means it goes to max (next)
                    nodes_df_expanded = pd.concat([nodes_df_expanded, nodes_df.loc[[index]]],
                                                  ignore_index=True)
                    # change new node scheduled to
                    nodes_df_expanded.loc[max(nodes_df_expanded.index), 'scheduled'] = org_date
                    nodes_df_expanded.loc[max(nodes_df_expanded.index), col] = None

    # add in old nodes that did not get expanded
    nodes_df_expanded = pd.concat([nodes_df_expanded,
                                   nodes_df[~nodes_df.node_heading.isin(nodes_df_expanded.node_heading)]],
                                  ignore_index=True)

    return nodes_df_expanded


def post_process(nodes_df):
    """ pull repeater tuples out of scheduled data and store in repeater col """

    for index in range(len(nodes_df)):
        get_repeater(nodes_df, index)
        get_effort_from_scheduled_ranges(nodes_df, index)

        deadline = nodes_df.loc[index, 'deadline']
        if deadline:
            deadline = convert_org_parse_date_2_datetime(deadline)

            p = deadline.time()
            k = datetime.time.min

            if deadline.time() == datetime.time.min:
                deadline = set_datetime_eod(deadline)  # set to eod since deadline

            nodes_df.loc[index, 'deadline'] = deadline

        scheduled = nodes_df.loc[index, 'scheduled']
        if scheduled:
            scheduled = convert_org_parse_date_2_datetime(scheduled)
            nodes_df.loc[index, 'scheduled'] = scheduled

    return nodes_df


def get_repeater(nodes_df, index):

    if 'repeater_val' not in nodes_df.columns:
        nodes_df['repeater_val'] = np.nan
        nodes_df['repeater_unit'] = np.nan

    # test = nodes_df.loc[0, 'repeater_val']

    scheduled = nodes_df.loc[index, 'scheduled']

    if scheduled:
        if scheduled._repeater:
            repeater_tup = scheduled._repeater
            repeat_delay = int(repeater_tup[1])

            if repeater_tup[0] == '-':
                repeat_delay = repeat_delay * -1

            # repeater = dict()
            # repeater[timedelta_org_mapping(repeater_tup[2])] = repeat_delay

            nodes_df.loc[index, 'repeater_val'] = repeat_delay
            nodes_df.loc[index, 'repeater_unit'] = timedelta_org_mapping(repeater_tup[2])

    return


def timedelta_org_mapping(org_repeat_window):
    """ map org repeaters to timedelta windows """

    mapped = dict()
    mapped['d'] = 'days'
    mapped['w'] = 'weeks'

    return mapped[org_repeat_window]


def get_effort_from_scheduled_ranges(nodes_df, index):
    """ range item have min and max datetime objects indicating time assigned by user, convert to effort """

    scheduled = nodes_df.loc[index, 'scheduled']

    if scheduled:
        if scheduled.start and scheduled.end:
            effort = scheduled.end - scheduled.start
            effort_sec = effort.total_seconds()
            effort_min = effort_sec/60

            nodes_df.loc[index, 'effort'] = int(effort_min)

    return


def fill_recurring_to_max(nodes_df):
    """ fill reoccuring nodes using repeaters up to max scheduled or deadline"""
    max_deadline = nodes_df['deadline'].max()
    max_schedule = nodes_df['scheduled'].max()

    if max_deadline > max_schedule:
        max_date = max_deadline
    else:
        max_date = max_schedule

    recurring_nodes = nodes_df[nodes_df['repeater_unit'].notnull()]
    expanded_nodes = pd.DataFrame(columns=recurring_nodes.columns.tolist())

    for index in range(len(nodes_df)):
        expanded_nodes = pd.concat([expanded_nodes, nodes_df.loc[[index]]], ignore_index=True)  # add original

        # scheduled = nodes_df.loc[index, 'scheduled']
        repeater_unit = nodes_df.loc[index, 'repeater_unit']
        repeater_val = nodes_df.loc[index, 'repeater_val']

        repeater = dict()
        repeater[repeater_unit] = repeater_val

        time_add = datetime.timedelta(**repeater)

        while nodes_df.loc[index, 'scheduled'] + time_add < max_date:
            nodes_df.loc[index, 'scheduled'] = nodes_df.loc[index, 'scheduled'] + time_add
            nodes_df.loc[index, 'deadline'] = nodes_df.loc[index, 'deadline'] + time_add

            expanded_nodes = pd.concat([expanded_nodes, nodes_df.loc[[index]]], ignore_index=True)

    return nodes_df


def remove_headings(nodes_df):
    """ any nodes with no deadline, effort or scheduled date are considered headings """
    nodes_df.dropna(subset=['effort'], how='all', inplace=True)
    return nodes_df


def checks(nodes_df):
    """ check for any stupid (dysfunctional) user inputs """

    nodes_df = remove_scheduled_before_deadline(nodes_df)

    return nodes_df


def remove_scheduled_before_deadline(nodes_df):
    """ if scheduled after deadline remove scheduled """

    issue_indices = nodes_df[nodes_df['deadline']<nodes_df['scheduled']]
    nodes_df.loc[issue_indices.index, 'scheduled'] = np.nan
    return nodes_df


def return_node_props_df():
    """ centralize creation for concatenation consistency """
    columns = ['node_heading',
               'cascaded_efforts',
               'efforts',
               'deadline',
               'scheduled',
               'urg_score']

    # TODO seperate efforts and cascaded_efforts for analytics later

    return pd.DataFrame(columns=columns)


def preorder_traversal(root,
                       node_props_df=None,
                       processed=None,
                       node_df=None):
    """ traverse nodes and extract the required properties to calculate score criteria,
    also propagate parent node props to children as required

    this traversal traces each branch from top to bottom, when root.root is passed to self it signifies the
    start of a new branch

    it is essential that non task nodes be filtered out LATER? could likely incorporate here but easier not to
    because i have a little brain
    """

    if node_props_df is None:
        node_props_df = return_node_props_df()

    if node_df is None:
        node_df = return_node_props_df()

    if not processed:
        processed = list()

    if not root:  # do not delete lol, dont know why anymore
        return

    # if no children, or no unprocessed children
    if not root.children or (root.children and set(root.children).issubset(processed)):
        if root.root == root:
            # stop when done (root has no unprocessed children)
            return node_props_df, processed, node_df

        else:
            # process root (all children done at this point)
            print(f'process {root.heading}')

            # concat node_df to main props df
            node_df.loc[0, 'node_heading'] = root.heading  # only update heading before appending
            node_props_df = pd.concat([node_props_df, node_df], ignore_index=True)  # add new node to props

            processed.append(root)
            # pass root, start over
            # starting over means resetting the node properties
            # therefore no node_df is passed, creating a new blank node_df from function defaults
            # recur
            node_props_df, processed, node_df = preorder_traversal(root.root, node_props_df, processed)

    else:
        for child in root.children:
            if child not in processed:
                print(f'pass {child.heading}')

                # update the node with cascaded properties
                node_df = update_node(node=child, node_df=node_df)
                node_df.loc[0, 'node_heading'] = child.heading
                # recur
                node_props_df, processed, node_df = preorder_traversal(root=child,
                                                                       node_props_df=node_props_df,
                                                                       processed=processed,
                                                                       node_df=node_df)

    return node_props_df, processed, node_df


def update_node(node, node_df):
    """ extract properties from node, update or add if necessary """
    node_df = update_cascaded_effort(node, node_df)
    node_df.loc[0, 'efforts'] = get_effort(node)
    node_df = update_deadline(node=node, node_df=node_df)
    node_df = update_scheduled(node=node, node_df=node_df)

    return node_df


def get_effort(node):
    """ get effort from either source
            - effort prop
            - rangelist
            - scheduled with range props?
        can only be one of the other
        effort should be a list because of rangelist
    """

    # get effort from node
    efforts = list()
    efforts_prop = node.get_property("Effort")

    if efforts_prop:
        efforts.append(efforts_prop)

    elif node.rangelist:
        efforts = efforts + get_effort_from_org_rangedates(node.rangelist)

    elif node.scheduled:
        efforts = efforts + get_effort_from_org_rangedates(node.scheduled)

    return efforts


def get_effort_from_org_rangedates(range_dates):
    """ range item have min and max datetime objects indicating time assigned by user, convert to effort """

    if not isinstance(range_dates, list):
        range_dates = [range_dates]

    range_efforts = list()

    for rdate in range_dates:
        if rdate.start and rdate.end:
            effort = rdate.end - rdate.start
            effort_sec = effort.total_seconds()
            effort_min = effort_sec/60

            range_efforts.append(int(effort_min))

    return range_efforts


def update_cascaded_effort(node, node_df):
    """ checks and updates cascaded effort """
    if not node_df.empty:
        current_cas_efforts = node_df.loc[0, 'cascaded_efforts']
    else:
        current_cas_efforts = []

    new_efforts = get_effort(node=node)
    updated_cas_efforts = list()

    if len(current_cas_efforts) > 1:  # greater len would indicate multiple efforts from rangelist
        # multiple efforts means children cannot also have a rangelist of efforts
        if len(new_efforts) > 1:
            print(f'cannot process child and parent with multiple range scheduled')
            return

    if len(current_cas_efforts) > 0:
        for c_effort in current_cas_efforts:
            for n_effort in new_efforts:
                updated_cas_efforts.append(c_effort + n_effort)
    else:
        updated_cas_efforts = new_efforts

    node_df.loc[0, 'cascaded_efforts'] = updated_cas_efforts
    return node_df


def update_deadline(node, node_df):
    """ dont need deadline since it only comes from one source
        check for cascaded deadline
        check for self deadline
        if self deadline is before cascaded, then use that one
    """
    node_deadline = node.deadline
    df_deadline = node_df.loc[0, 'deadline']

    if node_deadline.start:  # check if deadline set for node is before deadline set for cascaded
        node_deadline_dt = convert_org_parse_date_2_datetime(node_deadline)
        if hasattr(df_deadline, 'start'):
            df_deadline_dt = convert_org_parse_date_2_datetime(df_deadline)

            if node_deadline_dt < df_deadline_dt:  # if node deadline is sooner than cascaded
                node_df.loc[0, 'deadline'] = node_deadline
            else:
                node_df.loc[0, 'deadline'] = df_deadline
        else:
            node_df.loc[0, 'deadline'] = node_deadline

    return node_df


def update_scheduled(node, node_df):
    """ update scheduled
            - can scheduled be inherited?
            - no, parent schedule becomes child deadline
    """

    node_scheduled = get_scheduled(node)
    df_scheduled = node_df.loc[0, 'scheduled']

    if len(node_scheduled) == 0:  # if cascaded scheduled, and no node scheduled, cascaded becomes deadline
        if df_scheduled != np.nan:  # TODO not working start here
            node_df.loc[0, 'deadline'] = df_scheduled
    else:
        node_df.loc[0, 'scheduled'] = node_scheduled

    return node_df


def is_task(node):
    """ determine if a node is a task """
    task = False

    # node has deadline or scheduled, then is task**
    if node.deadline or get_scheduled(node):
        task = True

    return task


def get_scheduled(node):
    """ there are three ways a task can be scheduled
            - node has .scheduled prop
            - node has datelist item(s) that is not the created date
            - node has rangelist item(s)
        can have all three? likely
    """
    scheduled = []

    if node.scheduled:
        scheduled.append(node.scheduled)

    if node.datelist:
        # created date shows up in datelist, kinda wanted to keep it so pulling out created best i can
        for org_date in node.datelist:
            if not is_created_date(org_date):
                scheduled.append(org_date)

    if node.rangelist:
        scheduled = scheduled + node.rangelist

    return scheduled


def is_created_date(org_date):
    """ if a date has no repeater (user did not intend to repeat, and occurs prior to present date,
     this is likely** the creation date"""
    if convert_org_parse_date_2_datetime(org_date) < datetime.datetime.today() and not org_date._repeater:
        return True
    else:
        return False


def main():
    """ rules:
        1)  rangelist children only have effort if they need to be done prior to rangelist item
            examples:
                - often rangelist is used for meetings or recurring tasks, children of the meeting may be meeting
                  items, but if they occur within the meeting time they should not have effort
                - if they need be accomplished prior to the meeting they should have effort assigned
    """
    tasks = read_tasks(TASKS_FILE_IN)
    node_props_df, stuff, stuff1 = preorder_traversal(tasks)

    print()


if __name__ == "__main__":
    main()
