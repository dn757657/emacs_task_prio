from orgparse.node import parse_heading_todos


def get_effort(node):
    """ effort can come from multiple sources, return effort if present in any source

     :return integer effort in minutes (orgparse deals in minutes)
     """

    prop_effort = None
    date_effort = None
    effort = None
    active_orgdates = get_active_orgdates(node, scheduled=True)

    # get effort from properties if present
    effort_key = get_property_key('effort', node)
    prop_effort = node.get_property(effort_key)

    # get effort from active dates
    for orgdate in active_orgdates:
        if len(active_orgdates) == 1:  # only works if single active date, otherwise ambig
            if orgdate.start and orgdate.end:
                date_effort = orgdate.end - orgdate.start
                date_effort = int(date_effort.seconds/60)

    if prop_effort and date_effort:
        effort = date_effort  # date effort trumps effort
    elif prop_effort:
        effort = prop_effort
    elif date_effort:
        effort = date_effort

    return effort


def get_property_key(try_key, node):
    """ match passed key to actual property in properties
        - allows for fuzzy matching to node properties in case they change

    :return key if found, none otherwise
    """

    for key in node.properties.keys():
        if try_key.lower() == key.lower():
            return key

    return None


def get_active_orgdates(node, scheduled=None, deadline=None):
    """ get all scheduled in node, ignores scheduled and deadline by defualt babyyyyyy

    really just an orgparse.get_timestamps func with defaults? elim?

    can include scheudled or deadline since not normally included by get_timestamps
    """

    all_active_orgdates = node.get_timestamps(active=True,
                                              inactive=False,
                                              range=True,
                                              point=True)

    if scheduled:
        if hasattr(node, 'scheduled'):
            # node.scheduled is never none so we need to check start
            if node.scheduled.start:
                all_active_orgdates += [node.scheduled]  # only adding scheduled

    if deadline:
        if hasattr(node, 'deadline'):
            # node.deadline is never none so we need to check start and end? not so sure if both needed
            if node.deadline.start or node.deadline.end:
                all_active_orgdates += [node.deadline]

    return all_active_orgdates


def is_node_task(node):

    if node.get_property('Effort'):
        return True
    else:
        return False


def is_task_scoreable(node):

    deadline = get_deadline(node)

    # node must first be a task to be scorable
    if is_node_task(node):
        if deadline:
            return True
        else:
            return False


def is_task_scheduled(node):

    if len(get_active_orgdates(node, scheduled=True)) != 0:
        return True
    else:
        return False


def get_node_status(node):
    """ get the str status of the node
        - todos must match available in .emacs config
    """

    todos = ["BACKLOG",
             "PLAN",
             "READY",
             "ACTIVE",
             "REVIEW",
             "WAIT",
             "HOLD",
             "COMPLETED",
             "CANC",
             "TODO"]
    full_heading = node._lines[0]
    full_heading = full_heading.replace("*", "")  # strip * chars
    full_heading = full_heading.strip()

    status = parse_heading_todos(full_heading, todos)[1]

    return status


def generate_uid(node):
    """ generate unique id for each unscheduled task
        - since the root is flattened each node can only have one active date other than deadline
            which is interpreted as scheduled
            - these nodes obviously do not need to scheduled
        - therefore generate unique ID using heading and created?
        - scheduled added to discern duplicates

    ISSUES:
        - possible issue with using scheduled, comparing uid generated before or after scheduled updated
    """

    heading = node.heading.lower()

    if 'CREATED' in node.properties.keys():
        created = node.get_property("CREATED").lower()
    else:
        created = ""

    scheduled = get_active_orgdates(node, scheduled=True)

    if len(scheduled) > 1:
        scheduled = ""
    elif len(scheduled) == 1:
        scheduled = scheduled[0].__str__()
    else:
        scheduled = ""

    uid = heading + created + scheduled
    uid = uid.strip()
    uid = uid.replace(" ", "")

    return uid


def find_node_idx(uid, root):
    """ find node in root using uid """

    i = 1
    node_to_duplicate_idx = None
    for node in root[i:]:
        if uid == generate_uid(node):
            node_to_duplicate_idx = i
            break
        i += 1  # sketchy?

    return node_to_duplicate_idx


def get_deadline(node):

    if hasattr(node, 'deadline'):
        if node.deadline:
            # node can have a deadline property with an orgdate object in it but still not have a deadline
            if len(node.deadline.__str__()) != 0:
                return node.deadline
            else:
                return None
