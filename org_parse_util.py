import orgparse
import orgparse.node
from util import ensure_datetime


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


def dump_nodes(root):
    """ returns list of lists, sublist are lines of each dumped node
    the lines contain everything known about the node, therefore it is comprehensive
    """

    lines = []
    for node in root[0:]:
        lines.append(node._lines)

    # flatted_lines = flatten(lines)

    return lines


def duplicate_node(root, node):
    """ i think we need the entire tree, hence pass root
        - get both the root and node as lines
        - get the start and end of node_lines to duplicate within root_lines
        - insert the node_lines after root_lines

        returns nodes with duplicated
    """

    # root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # split root_lines at end of node_lines and insert new duplicated node there
    root_lines_before_new_node = root_lines[:node_end_location+1]
    root_lines_after_new_node = root_lines[node_end_location+1:]
    root_lines = root_lines_before_new_node + node_lines + root_lines_after_new_node

    return lines_2_nodes(root_lines)


def locate_node_in_root(root_lines, node_lines, node_line_number):
    """
    to find where to insert duplicate we need to indentify node from potential duplicates
    in the root_lines list,
    each node as a linenumber property indicating its location in the root._lines structure
    if it is flat, therefore by using the lengths of the individual lists in root_lines
    we can find its location and insert appropriately
    """

    # find location in root_nodes where node_lines are using node.linenumber
    lines = 0  # lines in org mode start at 1
    i = 0
    while lines != node_line_number-1:
        lines += len(root_lines[i])
        # debug
        y = len(node_lines)
        x = lines
        # if lines <= node_line_number:
        i += 1

    # get start and end of node_lines in root_lines
    node_start_location = i  # inclusive (index is first line)
    node_end_location = node_start_location + len(node_lines) - 1  # inclusive (index is last line)

    # debugging
    found = root_lines[node_start_location][0]
    seeking = node_lines[0][0]

    if root_lines[node_start_location][0] != node_lines[0][0]:
        print()

    return node_start_location, node_end_location


def update_node_line(node, old_val, new_val=""):
    """ default new_val is blank, will be replaced with nothing up no new_val passed

    presently this is only going to replace the first item it finds, which is really quite poor, although
    I cannto presenyl conceive a better way of doing this, might just work out ok
    """

    root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # since we only want to change scheduled in the node passed, use [0] from node_lines
    line_to_update = root_lines[node_start_location]

    # find which line contains property name, case insensitive!
    i = None
    for i, line in enumerate(line_to_update):
        if old_val.lower() in line.lower():
            break

    old_start_idx = line_to_update[i].find(old_val)  # must be exact match
    old_end_idx = old_start_idx + len(old_val)

    old_root_line_pref = root_lines[node_start_location][i][:old_start_idx]
    old_root_line_suff = root_lines[node_start_location][i][old_end_idx:]

    root_lines[node_start_location][i] = old_root_line_pref + new_val + old_root_line_suff
    root_lines[node_start_location][i] = root_lines[node_start_location][i].strip()

    x = root_lines[node_start_location][i]
    ly = len(x)

    # delete line if blank
    if root_lines[node_start_location][i].isspace() or len(root_lines[node_start_location][i]) == 0:
        del root_lines[node_start_location][i]

    return lines_2_nodes(root_lines)


def del_node_property(node, prop):

    action = 'del'

    root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # since we only want to change scheduled in the node passed, use [0] from node_lines
    line_to_update = root_lines[node_start_location]

    # find which line contains property name, case insensitive!
    i = None
    for i, line in enumerate(line_to_update):
        if prop.lower() in line.lower():
            break

    if i:  # must find property
        if prop.lower() in [x.lower() for x in node.properties.keys()]:
            root_lines = update_property(root_lines=root_lines,
                                         node_index=node_start_location,
                                         node_line_index=i,
                                         action=action
                                         )
        elif prop.lower() == 'scheduled' or prop.lower() == 'deadline':
            root_lines = update_org_date(root_lines=root_lines,
                                         node_index=node_start_location,
                                         node_line_index=i,
                                         prop=prop,
                                         action=action,
                                         )
    else:
        print('property not found')

    return lines_2_nodes(root_lines)


def set_node_property(node, prop, new_val):
    """ for when orgparse.OrgNode.kwd cannot be set (scheduled and deadline), therefore:
        - dump lines
        - update schedule in lines
            - convert orgDate to string
            - find scheduled keyword
            - replace date component
        - turn lines back into a node

    :return root
    """

    action = 'set'

    root = node.root
    root_lines = dump_nodes(root)
    node_lines = dump_nodes(node)

    # TODO misidentifying nodes!
    node_start_location, node_end_location = locate_node_in_root(root_lines=root_lines,
                                                                 node_lines=node_lines,
                                                                 node_line_number=node.linenumber)

    # since we only want to change scheduled in the node passed, use [0] from node_lines
    x = node.heading
    line_to_update = root_lines[node_start_location]

    # find which line contains property name, case insensitive!
    i = find_in_lines(line_to_update, prop)

    if i:
        if prop.lower() in [x.lower() for x in node.properties.keys()]:
            root_lines = update_property(root_lines=root_lines,
                                         node_index=node_start_location,
                                         node_line_index=i,
                                         new_prop=new_val,
                                         action=action
                                         )
        elif prop.lower() == 'scheduled' or prop.lower() == 'deadline':
            root_lines = update_org_date(root_lines=root_lines,
                                         node_index=node_start_location,
                                         node_line_index=i,
                                         action=action,
                                         prop=prop,
                                         new_date=new_val,
                                         )
    else:
        if prop.lower() == 'scheduled' or prop.lower() == 'deadline':
            # scheduled and deadline must be on the same line per org mode
            # therefore if either exists we use that line to add in non existant
            # deadline or scheduled
            scheduled_line_idx = find_in_lines(line_to_update, 'scheduled')
            deadline_line_idx = find_in_lines(line_to_update, 'deadline')

            if scheduled_line_idx:
                i = scheduled_line_idx
            elif deadline_line_idx:
                i = deadline_line_idx
            else:
                # if no scheduled/deadline line, always after heading
                i = find_in_lines(line_to_update, node.heading) + 1
                # blank line when niether is present
                root_lines[node_start_location].insert(i, "")

            root_lines = add_org_date(root_lines=root_lines,
                                      node_index=node_start_location,
                                      node_line_index=i,
                                      prop=prop,
                                      new_date=new_val,)

        else:
            # TODO add new property
            pass

    return lines_2_nodes(root_lines)


def find_in_lines(lines, prop):
    idx = None
    for i, line in enumerate(lines):
        if prop.lower() in line.lower():
            idx = i
            break

    return idx


def update_property(root_lines, node_index, node_line_index, action, new_prop=None):
    """ need to """
    # TODO insert property that doesnt exist already (may need to change parent func)

    if action == 'set' and new_prop:
        line_to_update = root_lines[node_index][node_line_index]
        line_to_update = line_to_update.split(":")

        len_prev_val = len(line_to_update[-1])  # match length of previous value for display
        len_diff = len(line_to_update[-1].replace(" ", "")) - len(new_prop)
        len_whitespace = len_prev_val-len_diff

        # update the line
        line_to_update[-1] = " "*len_whitespace + new_prop
        line_to_update = ":".join(line_to_update)
        root_lines[node_index][node_line_index] = line_to_update

    elif action == 'del':  # remove entire line since property drawer only allows one property per line
        del root_lines[node_index][node_line_index]

    return root_lines


def update_org_date(root_lines, node_index, node_line_index, action, prop, new_date=None):
    """ scheduled and deadline are treated differently
        - they are on same line therefore deleting is different
        - they are their own node properties?

    """
    line_to_update = root_lines[node_index][node_line_index]

    prop_start_idx = line_to_update.lower().find(prop.lower())  # inclusive

    # should prevent from finding the wrong < or > since there may be two on same line
    # bcause it always find the first instance of the find arg, since the search string is limited
    # to after the property argument (prop)

    # adding back in prop_idx to match indx with original full string index
    date_start_idx = line_to_update[prop_start_idx:].find("<") + prop_start_idx
    date_end_idx = line_to_update[prop_start_idx:].find(">") + prop_start_idx

    # set to new date by cuting out old and adding in new
    if action == 'set' and new_date:
        root_lines[node_index][node_line_index] = line_to_update[:date_start_idx] \
                                                  + new_date \
                                                  + line_to_update[date_end_idx+1:]
    elif action == 'del':
        # removes from start of property to end of date inclusive
        root_lines[node_index][node_line_index] = line_to_update[:prop_start_idx] + line_to_update[date_end_idx+1:]

        # delete line if blank
        if root_lines[node_index][node_line_index].isspace or len(root_lines[node_index][node_line_index]) == 0:
            del root_lines[node_index][node_line_index]

    return root_lines


def add_org_date(root_lines, node_index, node_line_index, prop, new_date=None):
    """ add scheduled or deadline property to node that does not have one already """

    new_str = prop.upper() + ": " + new_date

    # can always add on the end because i dont think org mode forces the order of scheduled and deadline
    root_lines[node_index][node_line_index] = root_lines[node_index][node_line_index] + new_str

    return root_lines


def lines_2_nodes(lines):
    """ turn lines back to a node tree
    :param lines: list of lines
    :return: orgparse node env
    """

    flatted_list = flatten(lines)
    flatted_str = '\n'.join(flatted_list)

    nodes = orgparse.loads(flatted_str)

    return nodes


def orgdate_2_dt(dates):
    """ get datetime object from orgdate """

    dates_dt = []

    if not isinstance(dates, list):
        dates = [dates]

    # pull date times objects out of orgdate objects from ancestral
    for date in dates:
        # start is preferred because it is soner (worst case) for scoring
        if date.start:
            dates_dt.append(ensure_datetime(date.start))
        elif date.end:
            dates_dt.append(ensure_datetime(date.end))

    return dates_dt


def flatten(lst):
    """ flatten a list of unknown depth to a single list of no depth """
    result = []
    for item in lst:
        if type(item) == list:
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def nodes_to_file(nodes, outfile):
    """ write node tree out to file
    :param nodes: orgparse node env
    :param outfile: string filepath
    :return: nothing
    """

    lines = dump_nodes(nodes)
    flatted_list = flatten(lines)
    flatted_str = '\n'.join(flatted_list)

    with open(outfile, 'w') as file:
        file.write(flatted_str)

    return
