import datetime
import orgparse.date
from orgdate_utils import orgdate_2_dt, push_repeated_2_present, expand_repeated_2_window
from org_parse_util import set_node_property
from node_util import generate_uid, is_node_task, get_deadline, get_active_orgdates, is_task_scoreable, \
    is_task_scheduled, get_node_status, get_property_key, find_node_idx
from tabulate import tabulate


def inherit_deadlines(root):
    """ inherit soonest deadline of schedule of ancestors

    important to note that we cannot traverse root and modify root simultaneously, hence the significant
    numbers of traversals (slow)

    """
    deadline_updates = dict()
    for node in root[1:]:
        # only score task nodes
        if is_node_task(node):
            inherited_deadline_od = find_ancestor_deadline(node)
            node_uid = generate_uid(node)

            # no updates needed if inherited deadline is deadline
            if node.deadline != inherited_deadline_od and inherited_deadline_od:
                deadline_updates[node_uid] = inherited_deadline_od

    # update deadlines in root
    for key in deadline_updates.keys():
        for node in root[1:]:
            if is_node_task(node):
                if key == generate_uid(node):
                    root = set_node_property(node, 'deadline', deadline_updates[key].__str__())

    return root


def find_ancestor_deadline(node):
    """ get the soonest (worst case scenario) for deadline out of ancestor props
        lowest value of:
            - ancestor scheduled dates (including active)
            - ancestor deadlines

    :return soonest deadline to inherit, None if no deadline to inherit
    """

    # get deadline as orgdate
    node_deadline = get_deadline(node)
    if not node_deadline:
        node_deadline = []
    else:
        node_deadline = [node_deadline]

    # get ancestor scheduled, active and deadline as org dates
    ancestral_scheduled_dates = get_ancestor_scheduled_dates(node)
    ancestral_deadline_dates = get_ancestor_deadlines(node)

    # convert fetched dates to datetime
    node_deadline_dt = orgdate_2_dt(node_deadline)
    ancestral_scheduled_dates_dt = orgdate_2_dt(ancestral_scheduled_dates)
    ancestral_deadline_dates_dt = orgdate_2_dt(ancestral_deadline_dates)

    # aggregate lists
    potential_deadlines = node_deadline + \
                          ancestral_scheduled_dates + \
                          ancestral_deadline_dates

    potential_deadlines_dt = node_deadline_dt + \
                             ancestral_scheduled_dates_dt + \
                             ancestral_deadline_dates_dt

    # find soonest deadline
    adjusted_deadline_orgdate = None
    if len(potential_deadlines) != 0:
        # we need to know the index of the sorted list prior to sorting
        # such that we can tie it back to the all active dates list
        # and assign the proper org date to node.deadline
        sort_index = [i for i, x in sorted(enumerate(potential_deadlines_dt), key=lambda x: x[1])]

        potential_deadlines_dt.sort()
        adjusted_deadline_orgdate = potential_deadlines[sort_index[0]]

        # checks
        # if range object is being inherited, only inherit start as the deadline
        if adjusted_deadline_orgdate.start and adjusted_deadline_orgdate.end:
            # cant just set to start because start is a datetime object
            adjusted_deadline_orgdate = orgparse.date.OrgDate(start=adjusted_deadline_orgdate.start,
                                                              end=None,
                                                              active=adjusted_deadline_orgdate._active,
                                                              repeater=adjusted_deadline_orgdate._repeater,
                                                              warning=adjusted_deadline_orgdate._warning)

        if len(node_deadline) > 0:
            # nothing to inherit, keep original deadline
            if adjusted_deadline_orgdate == node_deadline:
                return None

        # date is repeated and likely set in the past, adjust to present
        if adjusted_deadline_orgdate._repeater:
            adjusted_deadline_orgdate = push_repeated_2_present(adjusted_deadline_orgdate)

    return adjusted_deadline_orgdate


def get_ancestor_deadlines(node):

    all_deadlines = []

    while node != node.root:
        node = node.parent
        parent_deadline = get_deadline(node)
        if parent_deadline:
            all_deadlines += [parent_deadline]

    return all_deadlines


def get_ancestor_scheduled_dates(node):
    """ trace branch back to root via parents """

    all_active_dates = []

    while node != node.root:
        node = node.parent
        all_active_dates += get_active_orgdates(node,
                                                scheduled=True,
                                                deadline=False)

    return all_active_dates


def get_ancestor_cum_effort(node):
    """ trace branch back to root via parents """

    inherited_effort = 0

    while node != node.root:
        node = node.parent
        if node.get_property("Effort"):
            inherited_effort += node.get_property('Effort')

    return inherited_effort


def get_node_score(node, expanded=False, wmin=None, wmax=None):
    """ score and return node with score property added

    score = adjusted_deadline - today - effort - inherited_effort
        - smaller is more urgent (score = time remaining to complete)
        - negative would indicate that you dont have time to do the chain of tasks prior to the deadline

    adjusted_deadline: nearest of any active date of ancestors
            - ancestors active dates indicate a date where that task is to be completed or commenced
            - therefore all children must be completed prior

    inherited_effort: cumulative effort required to complete all ancestor tasks
            - effort values are reported in minutes**

    important to note that we cannot traverse root and modify root simultaneously, hence the significant
    numbers of traversals (slow)

    :type expanded Bool
    :param expanded, will expand repeated dates to window if window provided
    :type wmin datetime.datetime
    :param wmin window lower bound for expanding repeated tasks
    :type wmax datetime.datetime
    :param wmax window upper bound for expanding repeated tasks
    """

    if expanded:
        if not wmin:
            return ValueError
        if not wmax:
            return ValueError

    # score nodes
    if not is_task_scheduled(node):  # already scheduled will not get scored
        if is_node_task(node):
            if is_task_scoreable(node):

                # get all efforts
                inherited_effort = get_ancestor_cum_effort(node)
                node_effort = node.get_property('Effort')
                orgdeadline = node.deadline

                if orgdeadline._repeater and expanded:
                    deadlines = expand_repeated_2_window(orgdeadline, wmin, wmax)
                    deadlines = orgdate_2_dt(deadlines)
                else:
                    deadlines = orgdate_2_dt(orgdeadline)

                scores = []
                for deadline in deadlines:

                    raw_time_remaining_tdelta = deadline - datetime.datetime.today()

                    # to get minutes we must compute days and minutes component
                    raw_time_remaining_secs = raw_time_remaining_tdelta.seconds
                    raw_time_remaining_days = raw_time_remaining_tdelta.days

                    if raw_time_remaining_tdelta < datetime.timedelta(0):
                        raw_time_remaining_secs = raw_time_remaining_secs * -1

                    raw_time_remaining_mins = (raw_time_remaining_secs/60) + (raw_time_remaining_days * 24 * 60)

                    # score calc
                    time_remaining_mins = raw_time_remaining_mins - node_effort - inherited_effort
                    # node.properties['time_remaining_to_complete'] = time_remaining_mins
                    scores.append(time_remaining_mins)

                return scores
    else:
        return None


def get_scoring_window(inherited_root):
    """ get final deadline in tree to denote window max, window min is today """

    window_min = datetime.datetime.today()
    window_max = None

    for node in inherited_root[1:]:
        if get_deadline(node):
            deadline_dt = orgdate_2_dt(node.deadline)[0]

            if window_max:
                if deadline_dt > window_max:
                    window_max = deadline_dt
            else:
                window_max = deadline_dt

    return window_min, window_max


def show_scores(all_scores, inherited_root, to_sort=True):
    """ print scored nodes to console

    TODO add options for displaying remaining in something other than hours
    """

    # if to_sort:
    #     scores = {k: v for k, v in sorted(all_scores.items(), key=lambda item: item[1])}

    node_uids = []
    scores = []

    # gotta do this because cant sort lists nested in dict
    for node_uid in all_scores.keys():
        sub_scores = (all_scores[node_uid])
        for score in sub_scores:
            scores.append(score)
            node_uids.append(node_uid)

    if to_sort:
        # reorder both lists
        order = sorted(range(len(scores)), key=lambda i: scores[i])  # base list indexs on scores
        node_uids = [node_uids[i] for i in order]
        scores = [scores[i] for i in order]

    # header for tabulate
    tab_columns = ['Prio', 'Task', 'Effort [hrs]', 'Remaining [hrs]', 'Status']
    tab_data = []
    i = 1

    # generate table data
    for i, node_uid in enumerate(node_uids):
        node_data = []
        node = inherited_root[find_node_idx(node_uid, inherited_root)]

        score = scores[i]

        node_data.append(i)  # assign prio
        node_data.append(node.heading)

        effort = node.get_property(get_property_key('effort', node))
        node_data.append(effort/60)  # assign effort
        # score + effort is time until deadline because score is technically time remaining to START
        node_data.append((score + effort)/60)
        node_data.append(get_node_status(node))

        i += 1

        tab_data.append(node_data)

    print(tabulate(tab_data, headers=tab_columns))

    return


def score_tasks(flat_root, show=True):
    """ inherit -> score """

    inherited_tasks = inherit_deadlines(flat_root)
    window_min, window_max = get_scoring_window(inherited_tasks)  # will need later

    all_scores = dict()
    for node in inherited_tasks[1:]:
        scores = get_node_score(node)
        if scores:
            node_uid = generate_uid(node)
            all_scores[node_uid] = scores

    if show:
        show_scores(all_scores, inherited_tasks)

    return all_scores

