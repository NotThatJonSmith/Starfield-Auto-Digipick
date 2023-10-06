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
        for num_rotations in legal_rotations(lock_ring, key_rings[i]):
            yield (i, num_rotations)

# Given the game situation and a move,
# Return the game situation after the move
def apply_move(lock_rings, key_rings, key_index, num_rotations):
    lock_rings[0] &= ~rotate_key(key_rings[key_index], num_rotations)
    key_rings[key_index] = 0xffffffff
    if lock_rings[0] == 0:
        lock_rings = lock_rings[1:]
    return (lock_rings, key_rings)

# Given a list of lock rings and a list of key rings,
# Return a solution as a list of key ring indices and rotation counts
def solve(lock_rings, key_rings, moves_list=[]):
    if len(lock_rings) == 0:
        return moves_list
    lock_ring = lock_rings[0]
    for (key_index, num_rotations) in legal_moves(lock_ring, key_rings):
        (new_lock_rings, new_key_rings) = apply_move(lock_rings, key_rings, key_index, num_rotations)
        solution = solve(new_lock_rings, new_key_rings, moves_list + [(key_index, num_rotations)])
        if solution:
            return solution
    return None
