from org_parse_util import get_active_orgdates
from node_util import generate_uid, is_node_task


class SchedNodeProxy:
    def __init__(self,
                 node,):
        """ can have multiple scheduled dates (scheduleds), must match efforts
            just indicates that task has been split into multiple days
        """

        uid = generate_uid(node)
        score = node.get_property('time_remaining_to_complete')
        efforts = node.get_property('Effort')
        scheduleds = get_active_orgdates(node,
                                         scheduled=True,
                                         deadline=False)

        if not isinstance(efforts, list):
            efforts = [efforts]
        if not isinstance(scheduleds, list):
            scheduleds = [scheduleds]

        self.uid = uid
        self.score = score
        self.efforts = efforts
        self.scheduleds = scheduleds

        return


def nodes_2_dict(flat_root):
    """ pull required params out of node tree for scheduling """

    sched_nodes = list()

    for node in flat_root[1:]:
        if is_node_task(node):
            # if not already scheduled!
            if len(get_active_orgdates(node,
                                       scheduled=True,
                                       deadline=False)) == 0:
                sched_nodes.append(SchedNodeProxy(node))

    # sort sched_nodes by score
    sched_nodes.sort(key=lambda x: x.score, reverse=False)

    for proxy in sched_nodes:
        print(f'{proxy.score}:{proxy.uid}')

    return sched_nodes


def schedule_tasks(flat_root):
    """ schedule them tasks bb """

    proxy_node_objs = nodes_2_dict(flat_root)

    return flat_root