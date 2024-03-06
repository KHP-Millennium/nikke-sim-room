"""TODO"""
import copy
import os
import time
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


# The probability table for the list of substats
SUBSTAT_TABLE = {
    'element_dmg': 0.10,
    'hit_rate': 0.12,
    'ammo': 0.12,
    'attack': 0.10,
    'charge_dmg': 0.12,
    'charge_spd': 0.12,
    'crit_rate': 0.12,
    'crit_dmg': 0.10,
    'defense': 0.10,
}
LINE_TABLE = [
    1.00,
    0.50,
    0.30
]
assert math.isclose(sum(SUBSTAT_TABLE.values()), 1),\
    f'Substat probabilities must sum to 1 (actual: {sum(SUBSTAT_TABLE.values())}).'


# Cache file names
CACHED_RAW_ROLLS_FNAME = os.path.join(os.getcwd(), '.cache', 'raw_substat_cache.npy')


def generate_raw_lines(n_iter: int) -> np.array:
    """Generates a list of n_iter substats, with no locking."""
    ret = []
    for _ in range(n_iter):
        sub_copy = copy.deepcopy(SUBSTAT_TABLE)
        substats = np.array(list(sub_copy.keys()))

        rolls = ['1', '2', '3']

        for i, _ in enumerate(rolls):
            if np.random.uniform(0.0, 1.0) <= LINE_TABLE[i]:
                p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
                rolls[i] = np.random.choice(substats, 1, p=p_vals)[0]
                if rolls[i] not in sub_copy.keys():
                    raise ValueError('Error updating probability table.')
                sub_copy[rolls[i]] = 0

        if rolls[0] == rolls[1] or rolls[0] == rolls[2] or rolls[1] == rolls[2]:
            result_str = - f'{rolls[0]}\n\t- {rolls[1]}\n\t- {rolls[2]}'
            raise ValueError(f'This is not possible: \n\t- {result_str}')
        ret.append(rolls)

    return ret


def generated_lock_second_lines(n_iter: int, locked: str) -> np.array:
    """Generates a list of n_iter substats, with no locking."""
    assert locked in SUBSTAT_TABLE, f'{locked} is not a valid substat.'
    ret = np.zeros(shape=(n_iter,3),dtype=str)
    for i in range(n_iter):
        sub_copy = copy.deepcopy(SUBSTAT_TABLE)
        sub_copy[locked] = 0
        substats = np.array(list(sub_copy.keys()))

        ret[i][0] = '1'
        ret[i][1] = locked
        ret[i][2] = '3'

        # First substat
        p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
        ret[i][0] = np.random.choice(substats, 1, p=p_vals)[0]
        sub_copy[ret[i][0]] = 0

        # Third substat
        if np.random.uniform(0.0, 1.0) <= LINE_TABLE[2]:
            p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
            ret[i][2] = np.random.choice(substats, 1, p=p_vals)[0]
            sub_copy[ret[i][2]] = 0

        if ret[i][0] == ret[i][1] \
                or ret[i][0] == ret[i][2] or ret[i][1] == ret[i][2]:
            result_str = - f'{ret[i][0]}\n\t- {ret[i][1]}\n\t- {ret[i][2]}'
            print(f'This is not possible: \n\t- {result_str}')
            return 1

    return ret

def main() -> int:
    """Main function."""
    forced_subs = [
        ['attack', 'ammo', 'element_dmg'],
        ['charge_spd', 'ammo', 'attack'],
        ['charge_spd', 'ammo', 'element_dmg'],
    ]
    for r in forced_subs:
        forced_prob = [SUBSTAT_TABLE[x] for x in r]
        sub_p = 0

        # Subs are on lines 1 and 2, line 3 is empty
        sub_p = forced_prob[0] * forced_prob[1] *\
            LINE_TABLE[1] * (1-LINE_TABLE[2]) *\
            (1 / (1-forced_prob[0]) + 1 / (1-forced_prob[1]))

        # Subs are on lines 1 and 3, line 2 is empty
        sub_p += forced_prob[0] * (1 - LINE_TABLE[1]) *\
            forced_prob[1] * LINE_TABLE[2] *\
            (1 / (1-forced_prob[0]) + 1 / (1-forced_prob[1]))

        # Subs are any of lines 1-3, all lines are present
        for random_sub, random_p in SUBSTAT_TABLE.items():
            if random_sub in r:
                continue
            sub_p += forced_prob[0] * forced_prob[1] * random_p *\
                LINE_TABLE[1] * LINE_TABLE[2] * 6

        print(f'Probability of getting both subs in a roll: {sub_p*100:0.2f}%')

    # Monte carlo comparison
    n_iter = 1000000
    success = 0

    # Cache operation
    if os.path.exists(CACHED_RAW_ROLLS_FNAME):
        with open(CACHED_RAW_ROLLS_FNAME, 'rb') as f:
            rolled_list = np.load(f)
    else:
        rolled_list = generate_raw_lines(n_iter)
        if not os.path.isdir(os.path.dirname(CACHED_RAW_ROLLS_FNAME)):
            os.makedirs(os.path.dirname(CACHED_RAW_ROLLS_FNAME))
        np.save(CACHED_RAW_ROLLS_FNAME, rolled_list)

    for r_list in rolled_list:
        for sub_list in forced_subs:
            if all(x in [r_list[0], r_list[1], r_list[2]] for x in sub_list):
                success += 1
                break
    prob = success / n_iter
    print(f'Monte Carlo Result: {prob*100:0.2f}% ({success} out of {n_iter})')
    print(f'Average required rolls: {1/prob}')

    # Monte carlo comparison for ammo on line two
    n_iter = 1000000
    success = 0
    for _ in range(n_iter):
        sub_copy = copy.deepcopy(SUBSTAT_TABLE)
        sub_copy['ammo'] = 0
        substats = np.array(list(sub_copy.keys()))

        first = '1'
        second = 'ammo'
        third = '3'

        # First substat
        p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
        first = np.random.choice(substats, 1, p=p_vals)[0]
        sub_copy[first] = 0

        # Third substat
        if np.random.uniform(0.0, 1.0) <= LINE_TABLE[2]:
            p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
            third = np.random.choice(substats, 1, p=p_vals)[0]
            sub_copy[third] = 0

        if first == second or first == third or second == third:
            result_str = - f'{first}\n\t- {second}\n\t- {third}'
            print(f'This is not possible: \n\t- {result_str}')
            return 1

        # for sub_list in forced_subs:
        #     if all(x in [first, second, third] for x in sub_list):
        #         success += 1
        #         break
        if second == 'ammo' and third in ['attack', 'charge_spd', 'element_dmg']:
            success += 1

    # Monte carlo comparison for ammo on lines one and three
    n_iter = 1000000
    success = 0
    for _ in range(n_iter):
        sub_copy = copy.deepcopy(SUBSTAT_TABLE)
        sub_copy['ammo'] = 0
        sub_copy['attack'] = 0
        substats = np.array(list(sub_copy.keys()))

        first = 'ammo'
        second = '2'
        third = 'attack'

        # Second substat
        if np.random.uniform(0.0, 1.0) <= LINE_TABLE[1]:
            p_vals = np.array(list(sub_copy.values())) / sum(sub_copy.values())
            second = np.random.choice(substats, 1, p=p_vals)[0]
            sub_copy[second] = 0

        if first == second or first == third or second == third:
            result_str = - f'{first}\n\t- {second}\n\t- {third}'
            print(f'This is not possible: \n\t- {result_str}')
            return 1

        # for sub_list in forced_subs:
        #     if all(x in [first, second, third] for x in sub_list):
        #         success += 1
        #         break
        if second in ['charge_spd', 'element_dmg']:
            success += 1

    prob = success / n_iter
    print(f'Monte Carlo Result for locked ammo: {prob*100:0.2f}% ({success} out of {n_iter})')
    print(f'Average required rolls: {1/prob}')

    return 0


if __name__ == '__main__':
    main()
