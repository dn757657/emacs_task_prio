import datetime
from org_parse_util import set_node_property, get_active_orgdates, orgdate_2_dt
from node_util import generate_uid, is_node_task, get_deadline


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
    """

    node_deadline = get_deadline(node)
    if not node_deadline:
        node_deadline = []
    else:
        node_deadline = [node_deadline]

    ancestral_scheduled_dates = get_ancestor_scheduled_dates(node)
    ancestral_deadline_dates = get_ancestor_deadlines(node)

    node_deadline_dt = orgdate_2_dt(node_deadline)
    ancestral_scheduled_dates_dt = orgdate_2_dt(ancestral_scheduled_dates)
    ancestral_deadline_dates_dt = orgdate_2_dt(ancestral_deadline_dates)

    potential_deadlines = node_deadline + \
                          ancestral_scheduled_dates + \
                          ancestral_deadline_dates

    potential_deadlines_dt = node_deadline_dt + \
                             ancestral_scheduled_dates_dt + \
                             ancestral_deadline_dates_dt

    adjusted_deadline_orgdate = None
    if len(potential_deadlines) != 0:
        # we need to know the index of the sorted list prior to sorting
        # such that we can tie it back to the all active dates list
        # and assign the proper org date to node.deadline
        sort_index = [i for i, x in sorted(enumerate(potential_deadlines_dt), key=lambda x: x[1])]

        potential_deadlines_dt.sort()
        adjusted_deadline_orgdate = potential_deadlines[sort_index[0]]

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


def get_node_score(node):
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

    """
    # score nodes
    if len(get_active_orgdates(node, scheduled=True)) == 0:
        if is_node_task(node):
            # get all efforts
            inherited_effort = get_ancestor_cum_effort(node)
            node_effort = node.get_property('Effort')
            deadline = orgdate_2_dt(node.deadline)[0]

            raw_time_remaining_tdelta = deadline - datetime.datetime.today()
            raw_time_remaining_secs = raw_time_remaining_tdelta.seconds

            if raw_time_remaining_tdelta < datetime.timedelta(0):
                raw_time_remaining_secs = raw_time_remaining_secs * -1

            raw_time_remaining_mins = raw_time_remaining_secs/60

            # score calc
            time_remaining_mins = raw_time_remaining_mins - node_effort - inherited_effort
            node.properties['time_remaining_to_complete'] = time_remaining_mins

            return time_remaining_mins
    else:
        return None


def score_tasks(flat_root):
    """ schedule them tasks bb """

    inherited_tasks = inherit_deadlines(flat_root)

    for node in inherited_tasks[1:]:
        score = get_node_score(node)
        if score:
            node.properties['time_remaining_to_complete'] = score

    return inherited_tasks
