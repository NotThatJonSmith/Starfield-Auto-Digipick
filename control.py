import pyautogui

# Given a sequence of key indices and rotation counts,
# Return a sequence of control motions that performs those actions
def inputs_for_solution(move_list):
    spent_keys = []
    selected_key_index = 0
    for key_index, num_rotations in move_list:
        while selected_key_index != key_index:
                
            pass