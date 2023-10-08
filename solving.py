# Given a key ring,
# Return the key ring rotated the specified amount, 0 to 31
def rotate_key(key_ring, num_rotations):
    return ((key_ring << num_rotations) | (key_ring >> (32-num_rotations))) & 0xffffffff

# Given a lock ring and a key ring,
# Return a list of num_rotations values that can work
def legal_rotations(lock_ring, key_ring):
    return [i for i in range(32) if (lock_ring | rotate_key(key_ring,i)) == lock_ring]

# Given a lock ring, a list of key rings, and a list of key availability
# Return a list of (key ring index, rotation count) tuples that can work
def legal_moves(lock_ring, key_rings):
    for i in range(len(key_rings)):
        if key_rings[i] == 0 or key_rings[i] == 0xffffffff:
            continue
        for num_rotations in legal_rotations(lock_ring, key_rings[i]):
            yield (i, num_rotations)

# Given the game situation and a move,
# Return the game situation after the move
def apply_move(lock_rings, key_rings, key_index, num_rotations):
    new_lock_rings = list(lock_rings)
    new_key_rings = list(key_rings)
    new_lock_rings[0] &= ~rotate_key(new_key_rings[key_index], num_rotations)
    new_key_rings[key_index] = 0xffffffff
    if new_lock_rings[0] == 0:
        new_lock_rings = new_lock_rings[1:]
    return (new_lock_rings, new_key_rings)

# Given a game state,
# Print a summary for debug
def print_state(lock_rings, key_rings, move_list):
    print('lock:', end=' ')
    for l in lock_rings: 
        print(hex(l), end=' ')
    print('keys:', end=' ')
    for k in key_rings:
        print(hex(k), end=' ')
    print('moves:', end=' ')
    for m in move_list:
        print(m, end=' ')
    print()

# Given a list of lock rings and a list of key rings,
# Return a solution as a list of key ring indices and rotation counts
def solve(lock_rings, key_rings, moves_list=[]):
    print_state(lock_rings, key_rings, moves_list)
    if len(lock_rings) == 0:
        return moves_list
    for key_index, num_rotations in legal_moves(lock_rings[0], key_rings):
        new_lock_rings, new_key_rings = apply_move(lock_rings, key_rings, key_index, num_rotations)
        solution = solve(new_lock_rings, new_key_rings, list(moves_list + [(key_index, num_rotations)]))
        if solution:
            return solution
    return None

# Given a sequence of key indices and rotation counts,
# Return a sequence of control motions that performs those actions
def moves_to_keystrokes(move_list, key_rings):
    sel = 0
    inputs = ''
    for key_index, num_rotations in move_list:
        while sel != key_index:
            inputs += 'q'
            sel = (sel - 1) % 12
            while key_rings[sel] == 0:
                sel = (sel - 1) % 12
        inputs += 'a'*(32-num_rotations) if num_rotations >= 16 else 'd'*num_rotations
        inputs += 'e'
        if key_index != move_list[-1][0]:
            key_rings[sel] = 0
            sel = (sel + 1) % 12
            while key_rings[sel] == 0:
                sel = (sel + 1) % 12
    return inputs