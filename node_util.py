from org_parse_util import get_active_orgdates


def is_node_task(node):

    if node.get_property('Effort'):
        return True
    else:
        return False


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
