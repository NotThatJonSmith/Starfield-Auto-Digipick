
def decrement_selected_key(selected_key_index, key_rings):
    i = selected_key_index
    if i == 0:
        i = 11
    else:
        i -= 1
    while key_rings[i] == 0:
        if i == 0:
            i = 11
        else:
            i -= 1
    return i

def increment_selected_key(selected_key_index, key_rings):
    i = selected_key_index
    i += 1
    if i == 12:
        i = 0
    while key_rings[i] == 0:
        i += 1
        if i == 12:
            i = 0
    return i

# Given a sequence of key indices and rotation counts,
# Return a sequence of control motions that performs those actions
def inputs_for_solution(move_list, key_rings):
    selected_key_index = 0
    inputs = ''
    for key_index, num_rotations in move_list:
        while selected_key_index != key_index:
            inputs += 'q'
            selected_key_index = decrement_selected_key(selected_key_index, key_rings)
        if num_rotations >= 16:
            inputs += 'a'*(32-num_rotations)
        else:
            inputs += 'd'*num_rotations
        inputs += 'e'
        if key_index != move_list[-1][0]:
            key_rings[selected_key_index] = 0
            selected_key_index = increment_selected_key(selected_key_index, key_rings)
    return inputs