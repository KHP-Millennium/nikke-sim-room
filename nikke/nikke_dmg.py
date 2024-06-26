"""Module nikke_dmg for computing the DPS of various NIKKE combinations."""

import copy
import time
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# pylint: disable=import-error
from nikke.nikke_config import NIKKEConfig, NIKKEUtil, BuffWindow

class Graphs:
    """Graphing namespace for creating charts."""
    class ColorPlot:
        """Create a color plot with a 2D axis."""
        def __init__(self, title: str):
            plt.style.use('dark_background')
            self.fig, self.axes = plt.subplots(nrows=1, ncols=1)
            self.fig.set_figwidth(30.0)
            self.fig.set_figheight(16.875)
            self.fig.set_dpi(72)
            self.axes.minorticks_on()
            self.axes.grid(visible=True,
                which='major',
                linestyle='-',
                linewidth='0.5',
                color='red')
            self.axes.grid(visible=True,
                which='minor',
                linestyle=':',
                linewidth='0.5',
                color='black')
            self.set_title(title)
            self.set_xlabel('X-Axis')
            self.set_ylabel('Y-Axis')
            # axis.set_title(title, fontdict={"weight": "bold", "size": 20})
            #     axis.set_xlabel(xlabel, fontdict={"weight": "bold", "size": 20})
            #     axis.set_ylabel(
            #         f"{keyword} Speed Buffer Utilization (%)",
            #         fontdict={"weight": "bold", "size": 20},
            #     )
            #     for item in axis.get_xticklabels() + axis.get_yticklabels():
            #         item.set_fontsize(24)
            self.extent = None
            self.pos = None

        def load_data(self, data: np.array, x_vals: np.array, y_vals: np.array, style: str='turbo'):
            """Plots the specified data table as a color map, using specified color map style.

            'data' must be a MxN numpy array of floats for this function to plot.
            """
            color_scheme = matplotlib.colormaps[style]
            self.extent = [x_vals[0], x_vals[-1], y_vals[0], y_vals[-1]]
            self.pos = self.axes.imshow(data,
                interpolation='none',\
                cmap=color_scheme,
                origin='lower',
                extent=self.extent,
                aspect='auto')
            self.fig.colorbar(self.pos, ax=self.axes)

        def draw_line(self, data: np.array, color: str='r'):
            """Draws a line in the color plot, using a Nx2 numpy array."""
            self.axes.plot(data[:,0], data[:,1], color=color)

        def set_title(self, title: str):
            """Sets the title of this plot."""
            self.title = title
            self.axes.set_title(self.title, fontdict={'weight': 'bold', 'size': 20})

        def set_xlabel(self, label: str):
            """Sets the name of the x-axis for this plot."""
            self.axes.set_xlabel(label, fontdict={'weight': 'bold', 'size': 20})

        def set_ylabel(self, label: str):
            """Sets the name of the y-axis for this plot."""
            self.axes.set_ylabel(label, fontdict={'weight': 'bold', 'size': 20})

        def set_bounds(self, min_x: float, max_x: float, min_y: float, max_y: float):
            """Sets the maximum value of the x-axis for this plot."""
            self.extent = [min_x, max_x, min_y, max_y]

    class ScatterPlot:
        """Create a scatter plot with a line through it."""
        def __init__(self, title: str):
            plt.style.use('classic')
            self.fig, self.axes = plt.subplots(nrows=1, ncols=1)
            self.axes.minorticks_on()
            self.axes.grid(visible=True,
                which='major',
                linestyle='-',
                linewidth='0.5',
                color='red')
            self.axes.grid(visible=True,
                which='minor',
                linestyle=':',
                linewidth='0.5',
                color='black')
            self.set_title(title)
            self.set_xlabel('X-Axis')
            self.set_ylabel('Y-Axis')
            self.extent = None
            self.pos = None

        def draw_line(self, data: np.array, color: str='g'):
            """Draws a line in the color plot, using a Nx2 numpy array."""
            self.axes.plot(data[:,0], data[:,1], color=color)

        def set_title(self, title: str):
            """Sets the title of this plot."""
            self.title = title
            self.axes.set_title(self.title)

        def set_xlabel(self, label: str):
            """Sets the name of the x-axis for this plot."""
            self.axes.set_xlabel(label)

        def set_ylabel(self, label: str):
            """Sets the name of the y-axis for this plot."""
            self.axes.set_ylabel(label)

        def set_bounds(self, min_x: float, max_x: float, min_y: float, max_y: float):
            """Sets the maximum value of the x-axis for this plot."""
            self.extent = [min_x, max_x, min_y, max_y]

    class Histogram:
        """Create a histogram."""
        def __init__(self):
            plt.style.use('dark_background')

        def abc(self):
            """abc"""


class NIKKE:
    """API for computing various NIKKE calculations."""
    # Table for elements that counter one another
    element_table = {
        'water': 'fire',
        'fire': 'wind',
        'wind': 'iron',
        'iron': 'electric',
        'electric': 'water'
    }

    # Emperical value for weapons
    weapon_table = {
        'AR': {
            'attack_speed': 12,
            'wind_up_seconds': 0.0,
            'wind_up_ammo': 0
        },
        'SMG': {
            'attack_speed': 20,
            'wind_up_seconds': 0.0,
            'wind_up_ammo': 0
        },
        'SR': {
            'attack_speed': 4.4,
            'wind_up_seconds': 0,
            'wind_up_ammo': 0
        },
        'RL': {
            'attack_speed': 4.4,
            'wind_up_seconds': 0,
            'wind_up_ammo': 0
        },
        'MG': {
            'attack_speed': 59,
            'wind_up_seconds': 2,
            'wind_up_ammo': 43
        },
        'SG': {
            'attack_speed': 1.5,
            'wind_up_seconds': 0.0,
            'wind_up_ammo': 0
        },
    }

    # Reference values for cubes, calls resilience 'reload' because it's easier to type...
    cube_table = {
        'reload': [0.0, 14.84, 22.27, 29.69],
        'bastion': [0.0, 0.1, 0.2, 0.3],
        'adjutant': [0.0, 1.06, 1.59, 2.12],
        'wingman': [0.0, 14.84, 22.27, 29.69],
        'onslaught': [0.0, 2.54, 3.81, 5.09],
        'assault': [0.0, 2.54, 3.81, 5.09],
    }

    class Exceptions:
        """Exceptions namespace for NIKKE calculator."""
        class BadElement(Exception):
            """Signifies that a non-existent element was used for comparison."""

    class ModifierCache:
        """Caches calculations which do not remove buffs from the buff list.

        Do not manually generate this class. Instead, call NIKKE.generate_cache
        instead to get properly initialized default values.
        """
        def __init__(
                self,
                modifiers: np.array,
                crit_rate: float = 15,
                crit_dmg: float = 50,
                core_dmg: float = 100,
                range_dmg: float = 30,
                full_burst_dmg: float = 50,
                core_hit: int = 0,
                range_bonus: int = 0,
                full_burst: int = 0,
                element_bonus: int = 0):
            # Total ATK (0)
            # Charge Damage (1)
            # Damage Taken (2)
            # Elemental Damage (3)
            # Damage Up (4)
            # Total DEF (5)
            self.attack = modifiers[0]
            self.charge_dmg = modifiers[1]
            self.damage_taken = modifiers[2]
            self.element_dmg = modifiers[3]
            self.damage_up = modifiers[4]
            self.defense = modifiers[5]
            self.flat_atk = modifiers[6]

            # Full burst frame modifiers
            self.crit_rate = crit_rate
            self.crit_dmg = crit_dmg
            self.core_dmg = core_dmg
            self.range_dmg = range_dmg
            self.full_burst_dmg = full_burst_dmg

            # Flag counters
            self.core_hit = core_hit
            self.range_bonus = range_bonus
            self.full_burst = full_burst
            self.element_bonus = element_bonus

        def add_buff(self, buff: dict):
            """Updates a modifier self using a single buff.

            This function is forwarded to by the add_buffs function.
            """
            stacks = int(buff.get('stacks', 1))
            if 'attack' in buff:
                self.attack += buff['attack'] * stacks
            if 'charge_dmg' in buff:
                self.charge_dmg += buff['charge_dmg'] * stacks
            if 'full_charge_dmg' in buff:
                self.charge_dmg += (buff['full_charge_dmg'] - 100) * stacks
            if 'damage_taken' in buff:
                self.damage_taken += buff['damage_taken'] * stacks
            if 'element_dmg' in buff:
                self.element_dmg += buff['element_dmg'] * stacks
            if 'damage_up' in buff:
                self.damage_up += buff['damage_up'] * stacks
            if 'defense' in buff:
                self.defense += buff['defense'] * stacks
            if 'flat_atk' in buff:
                self.flat_atk += buff['flat_atk'] * stacks
            if 'crit_rate' in buff:
                self.crit_rate += buff['crit_rate'] * stacks
            if 'crit_dmg' in buff:
                self.crit_dmg += buff['crit_dmg'] * stacks
            if 'core_dmg' in buff:
                self.crit_dmg += buff['core_dmg'] * stacks
            if 'range_dmg' in buff:
                self.crit_dmg += buff['range_dmg'] * stacks
            if 'full_burst_dmg' in buff:
                self.crit_dmg += buff['full_burst_dmg'] * stacks
            # Bonus override flags
            if 'core_hit' in buff:
                val = buff['core_hit']
                self.core_hit += val if isinstance(val, int) else 1
            if 'range_bonus' in buff:
                val = buff['range_bonus']
                self.range_bonus += val if isinstance(val, int) else 1
            if 'full_burst' in buff:
                val = buff['full_burst']
                self.full_burst += val if isinstance(val, int) else 1
            if 'element_bonus' in buff:
                val = buff['element_bonus']
                self.element_bonus += val if isinstance(val, int) else 1

        def add_buffs(self, buffs: list or dict, start: int = None, end: int = None):
            """Updates the cache using the list of buffs."""
            if isinstance(buffs, dict):
                self.add_buff(buffs)
            elif isinstance(buffs, list):
                if start is not None and end is not None:
                    for i in range(start, end):
                        self.add_buff(buffs[i])
                else:
                    for buff in buffs:
                        self.add_buff(buff)

        def remove_buff(self, buff: dict):
            """Updates a modifier self by removing a single buff.

            This function is forwarded to by the remove_buffs function.
            """
            stacks = int(buff.get('stacks', 1))
            if 'attack' in buff:
                self.attack -= buff['attack'] * stacks
            if 'charge_dmg' in buff:
                self.charge_dmg -= buff['charge_dmg'] * stacks
            if 'full_charge_dmg' in buff:
                self.charge_dmg -= (buff['full_charge_dmg'] - 100) * stacks
            if 'damage_taken' in buff:
                self.damage_taken -= buff['damage_taken'] * stacks
            if 'element_dmg' in buff:
                self.element_dmg -= buff['element_dmg'] * stacks
            if 'damage_up' in buff:
                self.damage_up -= buff['damage_up'] * stacks
            if 'defense' in buff:
                self.defense -= buff['defense'] * stacks
            if 'flat_atk' in buff:
                self.flat_atk -= buff['flat_atk'] * stacks
            if 'crit_rate' in buff:
                self.crit_rate -= buff['crit_rate'] * stacks
            if 'crit_dmg' in buff:
                self.crit_dmg -= buff['crit_dmg'] * stacks
            if 'core_dmg' in buff:
                self.crit_dmg -= buff['core_dmg'] * stacks
            if 'range_dmg' in buff:
                self.crit_dmg -= buff['range_dmg'] * stacks
            if 'full_burst_dmg' in buff:
                self.crit_dmg -= buff['full_burst_dmg'] * stacks
            # Bonus override flags
            if 'core_hit' in buff:
                val = buff['core_hit']
                self.core_hit -= val if isinstance(val, int) else 1
            if 'range_bonus' in buff:
                val = buff['range_bonus']
                self.range_bonus -= val if isinstance(val, int) else 1
            if 'full_burst' in buff:
                val = buff['full_burst']
                self.full_burst -= val if isinstance(val, int) else 1
            if 'element_bonus' in buff:
                val = buff['element_bonus']
                self.element_bonus -= val if isinstance(val, int) else 1

        def remove_buffs(self, buffs: list or dict, start: int = None, end: int = None):
            """Updates the cache using the list of buffs.

            Undos the buff by calling remove_buff.
            """
            if isinstance(buffs, dict):
                self.remove_buff(buffs)
            else:
                if start is not None and end is not None:
                    for i in range(start, end):
                        self.remove_buff(buffs[i])
                else:
                    for buff in buffs:
                        self.remove_buff(buff)

    @staticmethod
    def compute_normal_dps(
        damage: float,
        ammo: int,
        reload: float,
        weapon: str) -> float:
        """Computes the normal attack DPS of a character as multiplier/second.

        - damage: The damage multiplier of each normal attack.
        - ammo: The actual ammo of the character, after ammo percentage and bastion cube.
        - reload: The actual reload time of the character, after reload speed.
        - weapon: The key specifying what weapon this character uses.
        """
        if reload <= 0:
            return NIKKE.compute_peak_normal_dps(damage, weapon)

        speed = NIKKE.weapon_table[weapon]['attack_speed']
        wind_up_seconds = NIKKE.weapon_table[weapon]['wind_up_seconds']
        wind_up_ammo = NIKKE.weapon_table[weapon]['wind_up_ammo']
        return damage * (ammo - wind_up_ammo) \
            / ((ammo - wind_up_ammo) / speed + wind_up_seconds + reload)

    @staticmethod
    def compute_peak_normal_dps(damage: float, weapon: str) -> float:
        """Returns the maximum achievable multiplier/second for a
        character's normal attack, in other words the infinite ammo case.
        """
        return damage * NIKKE.weapon_table[weapon]['attack_speed']

    @staticmethod
    def compute_damage(
            damage: float,
            attack: float,
            defense: float,
            buffs: list = None,
            core_hit: bool = False,
            range_bonus: bool = False,
            full_burst: bool = False,
            element_bonus: bool = False,
            cache: ModifierCache = None) -> np.array:
        """Computes the damage dealt by source to target.

        Returns a 1x3 numpy array contain the no-crit, crit, and average damage.

        Currently does not take into account weakpoint damage due to confusion
        on how and when that triggers.
        """
        # Total ATK (0)
        # Charge Damage (1)
        # Damage Taken (2)
        # Elemental Damage (3)
        # Unique Modifiers (4)
        # Total DEF (5)
        if buffs is None:
            buffs = []
        if cache is not None:
            calc = copy.deepcopy(cache)
            calc.add_buffs(buffs)
        else:
            calc = NIKKE.generate_cache(buffs)
        final_atk = attack * calc.attack / 100.0
        target_def = - defense * calc.defense / 100.0
        calc.charge_dmg /= 100.0
        calc.damage_taken /= 100.0
        calc.element_dmg = 1.0 if not element_bonus and calc.element_bonus <= 0 \
            else calc.element_dmg / 100.0
        calc.damage_up /= 100.0

        base_dmg = (final_atk - target_def + calc.flat_atk) \
            * calc.charge_dmg \
            * calc.damage_taken \
            * calc.element_dmg \
            * calc.damage_up \
            * damage / 100.0

        base_mod = 1.0
        if core_hit or calc.core_hit > 0:
            base_mod += calc.core_dmg / 100.0
        if range_bonus or calc.range_bonus > 0:
            base_mod += calc.range_bonus / 100.0
        if full_burst or calc.full_burst > 0:
            base_mod += calc.full_burst_dmg / 100.0

        crit_rate_p = min(1.0, calc.crit_rate / 100.0)
        crit_dmg_p = max(0.0, calc.crit_dmg / 100.0)
        crit_mod = base_mod + crit_dmg_p
        avg_mod = base_mod * (1.0 - crit_rate_p) + crit_mod * crit_rate_p

        return base_dmg * np.array([base_mod, crit_mod, avg_mod])

    @staticmethod
    def generate_cache(buffs: list,
                       crit_rate: float = 15,
                       crit_dmg: float = 50,
                       core_dmg: float = 100,
                       range_dmg: float = 30,
                       full_burst_dmg: float = 50) -> ModifierCache:
        """Caches the modifier values and returns them in a dictionary.

        Use this function when looping to reduce the number of redundant
        computations from calling compute_damage() on a large buff list.
        """
        cache = NIKKE.ModifierCache(
            np.array([100.0, 100.0, 100.0, 110.0, 100.0, 100.0, 0.0]),
                crit_rate=crit_rate,
                crit_dmg=crit_dmg,
                core_dmg=core_dmg,
                range_dmg=range_dmg,
                full_burst_dmg=full_burst_dmg)
        cache.add_buffs(buffs)
        return cache

    @staticmethod
    def get_bonus_tag(
            core_hit: bool = False,
            range_bonus: bool = False,
            full_burst: bool = False,
            element_bonus: bool = False) -> str:
        """Returns the tag corresponding to the flags."""
        tag = ''
        if core_hit:
            tag += 'core_'
        if range_bonus:
            tag += 'range_'
        if full_burst:
            tag += 'fb_'
        if element_bonus:
            tag += 'elem_'
        return tag[:-1] if tag != '' else 'base'

    @staticmethod
    def compute_damage_matrix(
            damage: float,
            attack: float,
            defense: float,
            buffs: list = None,
            cache: ModifierCache = None) -> dict:
        """Computes the matrix of damage dealt by source to target for
        all possibilities of core hit, range bonus, and

        Returns a 1x3 numpy array contain the no-crit, crit, and average damage.

        Currently does not take into account weakpoint damage due to confusion
        on how and when that triggers.
        """
        if cache is not None:
            cache.add_buffs(buffs)
        else:
            cache = NIKKE.generate_cache(buffs)
        ret = {
            'matrix': np.zeros((16,3))
        }
        index = 0
        flags = [False, True]
        for core_hit in flags:
            for range_bonus in flags:
                for full_burst in flags:
                    for element_bonus in flags:
                        tag = NIKKE.get_bonus_tag(
                            core_hit=core_hit,
                            range_bonus=range_bonus,
                            full_burst=full_burst,
                            element_bonus=element_bonus)
                        total_dmg = NIKKE.compute_damage(
                            damage,
                            attack,
                            defense,
                            core_hit=core_hit,
                            range_bonus=range_bonus,
                            full_burst=full_burst,
                            element_bonus=element_bonus,
                            cache=cache)
                        ret[tag] = {
                            'index': index,
                            'base': total_dmg[0],
                            'crit': total_dmg[1],
                            'avg': total_dmg[2]
                        }
                        ret['matrix'][index] = total_dmg

                        index += 1
        return ret

    @staticmethod
    def matrix_avg_dmg(matrix: dict, tags: dict, normalize: bool = True) -> float:
        """Sums damage from the damage matrix according to tags."""
        total_dmg = 0.0
        total_ratio = 0.0
        for tag, ratio in tags.items():
            total_dmg += matrix[tag]['avg'] * ratio
            total_ratio += ratio
        if normalize and total_ratio != 0:
            total_dmg /= total_ratio
        return total_dmg

    @staticmethod
    def accumulate_avg_dmg(
            damage: float,
            attack: float,
            defense: float,
            buffs: list,
            tags: dict,
            normalize: bool = True,
            cache: ModifierCache = None) -> float:
        """Sums damage from the damage matrix according to tags."""
        matrix = NIKKE.compute_damage_matrix(damage, attack, defense, buffs=buffs, cache=cache)
        return NIKKE.matrix_avg_dmg(matrix, tags, normalize=normalize)

    @staticmethod
    def get_unique_times(buffs, window_start, window_end):
        """Returns the complete timeline of unique buff windows and time points."""
        unique_times = []
        if not math.isinf(window_start):
            unique_times.append(window_start)
        if not math.isinf(window_end):
            unique_times.append(window_end)
        for buff in buffs:
            start = buff['start']
            end = buff['end']
            if not math.isinf(start) \
                    and window_start < start < window_end \
                    and start not in unique_times:
                unique_times.append(start)
            if not math.isinf(end) \
                    and window_start < end < window_end \
                    and end not in unique_times:
                unique_times.append(end)
        return np.array(unique_times, dtype=float)

    @staticmethod
    def compute_dps_window_nlogn(
            damage_tags: list,
            attack: float,
            defense: float,
            buffs: list,
            window_start: float = -math.inf,
            window_end: float = math.inf,
            accumulate: bool = True,
            normalize: bool = True) -> float:
        """Uses start and end times in the buff iist to estimate damage.

        damage_tags specifies the damage to sum over and the associated
        bonuses from core hits, full burst, etc., and in what duration
        window they apply.

        normalize is passed to the accumulate function.

        accumulate when True will sum the final result as a single float.

        window_start manually specifies the minimum time to analyaze from.

        window_end manually specifies the maximum time to analyze towards.

        This is the O(NlogN) variant of the algorithm, which tends to
        perform better at N >= 800.
        """
        # Buffs to add sorted in chronological order
        add_buffs = sorted(buffs, key=lambda d: d['start'])
        # Buffs to remove sorted in chronological order
        sub_buffs = sorted(buffs, key=lambda d: d['end'])

        # Start by searching through the buff list to determine timeline
        time_points = NIKKE.get_unique_times(add_buffs, window_start, window_end)

        # Sort the timeline in chronological order
        time_points = np.sort(time_points)

        # Preinitialize the list of time point windows
        time_windows = np.zeros((len(time_points) - 1, 2), dtype=float)
        buff_windows = np.zeros((len(time_points) - 1, 4), dtype=int)
        add_index = 0
        sub_index = 0
        prev_time = time_points[0]
        for i in range(1, len(time_points)):
            index = i - 1
            curr_time = time_points[i]
            # As this loop can only be ran a maximum of N times, it is O(N)
            time_windows[index] = [prev_time, curr_time]
            buff_windows[index][0] = add_index
            buff_windows[index][2] = sub_index
            if add_index < len(add_buffs):
                while prev_time >= add_buffs[add_index]['start']:
                    add_index += 1
            if sub_index < len(sub_buffs):
                while prev_time >= sub_buffs[sub_index]['end']:
                    sub_index += 1
            buff_windows[index][1] = add_index
            buff_windows[index][3] = sub_index
            prev_time = curr_time
        #print(np.concatenate((time_windows, buff_windows), axis=1))

        results = np.zeros(len(damage_tags))
        cache = NIKKE.generate_cache([])
        for (t_0, t_1), (add_s, add_e, sub_s, sub_e) in zip(time_windows, buff_windows):
            # This operation can only occur O(N) times in total
            if add_e > add_s:
                cache.add_buffs(add_buffs, add_s, add_e)
            if sub_e > sub_s:
                cache.remove_buffs(sub_buffs, sub_s, sub_e)

            # Loop over all damage tags and begin accumulating the damage per window
            for i, dmg_tag in enumerate(damage_tags):
                damage = dmg_tag['damage']
                tags = dmg_tag['tags']
                start = dmg_tag['start']
                duration = dmg_tag.get('duration', 0)
                end = dmg_tag.get('end', start + duration if not math.isinf(duration) else math.inf)

                # Shift the window until we are in a valid start time
                if start >= t_1 or end < t_0:
                    continue

                total_dmg = NIKKE.accumulate_avg_dmg(
                    damage,
                    attack,
                    defense,
                    None,
                    tags,
                    normalize=normalize,
                    cache=cache
                )

                # Determine, based on duration, whether or not to multiply
                duration = min(end, t_1) - max(start, t_0) if duration != 0 else 0
                if duration > 0:
                    results[i] += total_dmg * duration
                else:
                    results[i] += total_dmg
        return np.sum(results) if accumulate else results

    @staticmethod
    def compute_dps_window_n2(
            damage_tags: list,
            attack: float,
            defense: float,
            buffs: list,
            window_start: float = -math.inf,
            window_end: float = math.inf,
            accumulate: bool = True,
            normalize: bool = True) -> float:
        """Uses start and end times in the buff iist to estimate damage.

        damage_tags specifies the damage to sum over and the associated
        bonuses from core hits, full burst, etc., and in what duration
        window they apply.

        normalize is passed to the accumulate function.

        accumulate when True will sum the final result as a single float.

        window_start manually specifies the minimum time to analyaze from.

        window_end manually specifies the maximum time to analyze towards.

        This is the O(N^2) variant of the algorithm, which tends to
        perform better at N < 800.
        """
        # Start by searching through the buff list to determine timeline
        time_points = NIKKE.get_unique_times(buffs, window_start, window_end)

        # Sort the timeline in chronological order
        time_points = np.sort(time_points)

        # Preinitialize the list of time point windows
        buff_windows = []
        t_0 = time_points[0]
        for t_1 in time_points:
            if t_0 >= t_1:
                continue
            buff_windows.append([t_0, t_1])
            t_0 = t_1
        buff_windows = np.array(buff_windows)

        # Loop over all damage tags and begin accumulating the damage per window
        results = np.zeros(len(damage_tags))
        # Timeline loop - t0 is the inclusive current time and t1 is non-inclusive the end time
        for t_0, t_1 in buff_windows:
            window = []
            for buff in buffs:
                if t_0 >= buff['start'] and t_0 < buff['end']:
                    window.append(buff)
            cache = NIKKE.generate_cache(window)
            for i, dmg_tag in enumerate(damage_tags):
                damage = dmg_tag['damage']
                tags = dmg_tag['tags']
                start = dmg_tag['start']
                duration = dmg_tag.get('duration', 0)
                end = dmg_tag.get('end', start + duration if not math.isinf(duration) else math.inf)
                # Shift the window until we are in a valid start time
                if start >= t_1 or end < t_0:
                    continue

                total_dmg = NIKKE.accumulate_avg_dmg(
                    damage,
                    attack,
                    defense,
                    None,
                    tags,
                    normalize=normalize,
                    cache=cache
                )

                # Determine, based on duration, whether or not to multiply
                duration = min(end, t_1) - max(start, t_0) if duration != 0 else 0
                if duration > 0:
                    results[i] += total_dmg * duration
                else:
                    results[i] += total_dmg
        return np.sum(results) if accumulate else results

    @staticmethod
    def compute_dps_window(
            damage_tags: list,
            attack: float,
            defense: float,
            buffs: list,
            window_start: float = -math.inf,
            window_end: float = math.inf,
            accumulate: bool = True,
            normalize: bool = True) -> float:
        """Forwards the DPS computation parameters to the O(NlogN) or the
        O(N^2) algorithm based on the length of buffs.

        The O(N^2) algorithm tends to perform more consistently and better
        at N < 800, so even though the O(NlogN) algorithm has a better
        runtime analysis, in practice the O(N^2) algorithm is preferred.
        """
        if len(buffs) >= 800:
            return NIKKE.compute_dps_window_nlogn(damage_tags, attack, defense, buffs,
                window_start, window_end, accumulate, normalize)
        return NIKKE.compute_dps_window_n2(damage_tags, attack, defense, buffs,
            window_start, window_end, accumulate, normalize)


    @staticmethod
    def compare_dps_window_alg(
            damage_tags: list,
            attack: float,
            defense: float,
            buffs: list,
            window_start: float = -math.inf,
            window_end: float = math.inf,
            accumulate: bool = True,
            normalize: bool = True) -> float:
        """Compares the performance of the O(N^2) algorithm versus the
        O(NlogN) algorithm for the given parameters.
        """
        logger = NIKKEUtil.get_logger('NIKKE_logger')
        start_nlogn = time.time()
        result_nlogn = NIKKE.compute_dps_window_nlogn(damage_tags, attack, defense, buffs,
                 window_start, window_end, accumulate, normalize)
        nlogn_time = (time.time() - start_nlogn) * 1000

        start_n2 = time.time()
        result_n2 = NIKKE.compute_dps_window_n2(damage_tags, attack, defense, buffs,
            window_start, window_end, accumulate, normalize)
        n2_time = (time.time() - start_n2) * 1000

        if not math.isclose(result_nlogn, result_n2):
            logger.error('O(N^2) and O(NlogN) algorithms did not return the same reuslt!')

        diff = abs(nlogn_time - n2_time)
        name = 'n2' if n2_time < nlogn_time else 'nlogn'
        logger.debug(f'{n2_time=:.3f} ms vs {nlogn_time=:.3f} ms ({name} faster by {diff:.3f} ms)')
        return result_n2

    @staticmethod
    def compare_element(source: str, target: str) -> bool:
        """Checks if the source element is strong against the target element.

        Returns True if the source element is strong against the target. False otherwise.
        """
        if not source in NIKKE.element_table:
            raise NIKKE.Exceptions.BadElement(f'"{source}" is not an element.')
        if not target in NIKKE.element_table:
            raise NIKKE.Exceptions.BadElement(f'"{target}" is not an element.')
        return NIKKE.element_table[source] == target


class Examples:
    """Namespace for helper functions specific to this script."""
    @staticmethod
    def compute_normal_attack_dps(
            config: NIKKEConfig,
            nikke_name: str,
            damage: float = None,
            ammo: float = 0.0,
            reload: float = NIKKE.cube_table['reload'][3],
            log: bool = True,
            graph: bool = False,
            atk_name: str = 'Normal Attack') -> float:
        """Graphs the normal attack DPS for the given NIKKE and logs it."""
        params = config.get_normal_params(nikke_name)
        if damage is not None:
            params['damage'] = damage
        base_ammo = params['ammo']
        params['ammo'] = int(base_ammo * (1 + ammo / 100.0))
        params['reload'] *= (1 - reload / 100.0)
        dps = NIKKE.compute_normal_dps(**params)
        peak = NIKKE.compute_peak_normal_dps(params['damage'], params['weapon'])
        ratio = dps / peak * 100
        message = f'{nikke_name} {atk_name} DPS: {dps:,.2f} / {peak:,.2f} ({ratio:,.2f}%)'

        if log:
            NIKKEUtil.get_logger('NIKKE_Logger').info(message)

        # Add a plot for this graph
        if graph:
            iterations = 25
            data = np.zeros((iterations, 2))
            for i in range(iterations):
                data[i][0] = 1 + 0.1 * i + ammo / 100
                params['ammo'] = int(base_ammo * data[i][0])
                data[i][0] = (data[i][0] - 1) * 100
                data[i][1] = ((NIKKE.compute_normal_dps(**params) / dps) - 1) * 100
            plot = Graphs.ScatterPlot(f'{nikke_name} {atk_name} DPS vs Ammo (Lv2 Reload Cube)')
            plot.draw_line(data)
            plot.set_xlabel('Ammo Capacity Up (%)')
            plot.set_ylabel('Damage Increase (%)')
            plt.show()

        return dps

    @staticmethod
    def compute_actual_damage(
            damage: float,
            attack: float,
            defense: float,
            buffs: list,
            log: bool = True,
            core_hit: bool = False,
            range_bonus: bool = False,
            full_burst: bool = False,
            element_bonus: bool = False,
            name: str = 'Attack',
            show_stats:bool = True,
            show_base: bool = True,
            show_crit: bool = True,
            show_avg: bool = True) -> np.array:
        """Returns the damage a single hit does under burst and logs it."""
        dmg_cache = NIKKE.generate_cache(buffs)
        values = NIKKE.compute_damage(damage, attack, defense, cache=dmg_cache,
                                      core_hit=core_hit, range_bonus=range_bonus,
                                      full_burst=full_burst, element_bonus=element_bonus)
        if log:
            logger = NIKKEUtil.get_logger('NIKKE_Logger')
            msg = f'{name} damage'

            if show_stats:
                msg += f' based on the following stats:\
                    \n  - ATK: {attack}\
                    \n  - Enemy DEF: {defense}\
                    \n  - Skill Multiplier: {damage:.2f}'
            else:
                msg += ':'
            logger.info(msg)
            if show_base:
                logger.info('Base Damage: %s', f'{values[0]:,.2f}')
            if show_crit:
                logger.info('Crit Damage: %s', f'{values[1]:,.2f}')
            if show_avg:
                logger.info('Average Damage: %s', f'{values[2]:,.2f}')
        return values

    @staticmethod
    def compute_nikke_dps(
            damage_tags: list,
            attack: float,
            defense: float,
            buffs: list,
            window_start: float,
            window_end: float,
            name: str = 'NIKKE',
            relative_dps: float = None,
            relative_name: str = None,
            verbose=False) -> float:
        """Returns the average DPS of a NIKKE."""
        logger = NIKKEUtil.get_logger('NIKKE_Logger')
        total_avg_dmg = NIKKE.compute_dps_window(
            damage_tags=damage_tags,
            attack=attack,
            defense=defense,
            buffs=buffs,
            window_start=window_start,
            window_end=window_end)
        dps = total_avg_dmg / (window_end - window_start)

        if verbose:
            duration = window_end - window_start
            msg = f'{name} Average DPS based on the following stats:\
                \n  - ATK: {attack}\
                \n  - Enemy DEF: {defense}\
                \n  - Duration: {duration:.2f}'
            logger.debug(msg)

        msg = f'{name} Average Damage = {total_avg_dmg:,.2f} ({dps:,.2f} damage/s)'
        if relative_dps is not None:
            ratio = dps / relative_dps * 100.0
            msg += f' ({ratio:,.2f}% of {relative_name})' \
                if relative_name is not None else f' ({ratio:,.2f}%)'
        logger.info(msg)
        return dps


def main() -> int:
    """Main function."""
    logger = NIKKEUtil.get_logger('NIKKE_Logger')
    config = NIKKEConfig()
    params = {
        'damage': config.config['nikkes']['Scarlet']['burst']['effect'][1]['damage'],
        'attack': config.get_nikke_attack('Modernia'),
        'defense': config.get_enemy_defense('union_raid_7'),
    }

    # Attack stat override
    config.config['nikkes']['Modernia']['attack'] = 119089
    config.config['nikkes']['Liter']['attack'] = 99855
    config.config['nikkes']['2B']['attack'] = 76377

    # Conditionals
    use_list = {
        'B1': {
            'Liter': False,
            'Volume': True,
        },
        'B2': {
            'Blanc': False,
            'Mast': True,
            'Novel': False,
            'Rupee': False,
        },
        'B3': {
            'Noir': True,
            'Maxwell': False,
            'Privaty': False,
            'Helm': True,
            'Anis: Sparkling Summer': True
        },
    }
    burst_times = np.array([0, 15, 30])
    ammo = (64.81 + 68.93 + 60.71)# / 0.7 + 100 / 0.7 - 100
    ammo = ammo * (1.3988 if use_list['B3']['Noir'] else 1.0)
    priv_reload = (NIKKE.cube_table['reload'][2]
        + config.config['nikkes']['Privaty']['skill_1']['effect']['reload'])
    priv_ammo = (ammo
        + config.config['nikkes']['Privaty']['skill_1']['effect']['ammo'])

    # Base buffs
    base_buffs = config.convert_to_buffs({
        'Nikkes': {
            'Liter': BuffWindow.timeline(['s1_3', 'b'], burst_times-0.5) \
                if use_list['B1']['Liter'] else [],
            'Volume': BuffWindow.timeline(['s2_3', 'b'], burst_times-0.5) \
                if use_list['B1']['Volume'] else [],
            'Blanc': BuffWindow.timeline('b', burst_times-0.25) \
                if use_list['B2']['Blanc'] else [],
            'Mast': BuffWindow.timeline(['s1', 'b'], burst_times-0.25) \
                if use_list['B2']['Mast'] else [],
            'Novel': BuffWindow.timeline('b', burst_times+1.5) \
                if use_list['B2']['Novel'] else [],
            'Rupee': BuffWindow.timeline('b', burst_times-0.25) \
                if use_list['B2']['Rupee'] else [],
            # 'Noir': BuffWindow.timeline('s1', burst_times) \
            #     if use_list['B3']['Noir'] else [],
            'Maxwell': BuffWindow.timeline('s1', burst_times) \
                if use_list['B3']['Maxwell'] else [],
            'Privaty': BuffWindow.timeline('s1', burst_times) \
                if use_list['B3']['Privaty'] else [],
            'Helm': BuffWindow.timeline('s2', burst_times) \
                if use_list['B3']['Helm'] else [],
        },
        'Modifiers': BuffWindow.full_burst_uniform(burst_times, 10),
    }) + [{
        'type': 'buff',
        'flat_atk': (115513 * 0.1408) if use_list['B3']['Noir'] else 0,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }] + [{
        'type': 'buff',
        'attack': 15 if use_list['B2']['Mast'] else 0,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    if use_list['B3']['Helm']:
        base_buffs = base_buffs + config.convert_nikke_buffs({
            'Helm': [
                BuffWindow.inf_buff('s1'),
            ],
        })

    # Scarlet buffs
    scar_buffs = base_buffs + config.convert_nikke_buffs({
        'Scarlet': [
            BuffWindow.inf_buff('s1', 5),
            BuffWindow.inf_buff('s2'),
            # BuffWindow('b', burst_times[0]),
        ],
    }) + [{
        'type': 'buff',
        'attack': 11.81,
        'flat_atk': config.config['nikkes']['2B']['attack'] * 0.5531 \
            if use_list['B3']['Anis: Sparkling Summer'] else 0,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    # Modernia buffs
    mod_buffs = base_buffs + config.convert_nikke_buffs({
        'Modernia': [
            BuffWindow.inf_buff('s1', 5),
            BuffWindow.inf_buff('s2'),
        ],
    }) + [{
        'type': 'buff',
        'attack': 10.40+6.18+5.47,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]

    logger.info('=======================================================')
    Examples.compute_actual_damage(**params, buffs=scar_buffs, name='Scarlet burst')
    Examples.compute_actual_damage(
        damage=499.5*10,
        attack=119161,
        defense=config.get_enemy_defense('union_raid_7'),
        buffs=base_buffs+[{'attack': 11.81+9.00, 'damage_up': 10.23}],
        full_burst=True,
        core_hit=True,
        range_bonus=True,
        name='Snow White burst (with range bonus)'
    )
    logger.info('=======================================================')

    scar_n = Examples.compute_normal_attack_dps(
        config, 'Scarlet', ammo=ammo, graph=False)
    scar_priv_n = Examples.compute_normal_attack_dps(
        config, 'Scarlet', ammo=priv_ammo, reload=priv_reload,
        atk_name='Normal Attack (w/Privaty)', graph=False)
    sw_n = Examples.compute_normal_attack_dps(
        config, 'Snow White', ammo=0, graph=False)
    mod_n = Examples.compute_normal_attack_dps(
        config, 'Modernia', graph=False,
        ammo=config.config['nikkes']['Modernia']['skill_1']['effect']['ammo']*5+ammo)
    mod_s1 = Examples.compute_normal_attack_dps(
        config, 'Modernia', graph=False, atk_name='S1',
        damage=config.config['nikkes']['Modernia']['skill_1']['effect']['damage'],
        ammo=config.config['nikkes']['Modernia']['skill_1']['effect']['ammo']*5+ammo)
    peak_mod_n = Examples.compute_normal_attack_dps(
        config, 'Modernia', graph=False, reload=110)
    peak_mod_s1 = Examples.compute_normal_attack_dps(
        config, 'Modernia', graph=False, reload=110, atk_name='S1',
        damage=config.config['nikkes']['Modernia']['skill_1']['effect']['damage'])
    max_n = Examples.compute_normal_attack_dps(
        config, 'Maxwell', ammo=ammo, graph=False)
    alice_n = Examples.compute_normal_attack_dps(
        config, 'Alice', ammo=ammo, graph=False)
    rupee_n = Examples.compute_normal_attack_dps(
        config, 'Rupee', ammo=ammo, graph=False)
    guil_n = Examples.compute_normal_attack_dps(
        config, 'Guillotine', ammo=ammo, graph=False)
    soline_n = Examples.compute_normal_attack_dps(
        config, 'Soline', ammo=ammo, graph=False)
    two_b_n = Examples.compute_normal_attack_dps(
        config, '2B', ammo=0, graph=False)

    logger.info('=======================================================')

    # Set up weapon tags
    ar_range_bonus = False
    mg_range_bonus = False
    sr_range_bonus = False
    core_hit = True
    core_tag = NIKKE.get_bonus_tag(core_hit=core_hit)
    ar_base_tag = NIKKE.get_bonus_tag(range_bonus=ar_range_bonus)
    ar_core_tag = NIKKE.get_bonus_tag(range_bonus=ar_range_bonus, core_hit=core_hit)
    mg_core_tag = NIKKE.get_bonus_tag(range_bonus=mg_range_bonus, core_hit=core_hit)
    sr_base_tag = NIKKE.get_bonus_tag(range_bonus=sr_range_bonus)
    sr_core_tag = NIKKE.get_bonus_tag(range_bonus=sr_range_bonus, core_hit=core_hit)
    mod_s1_tag = NIKKE.get_bonus_tag(range_bonus=False)
    ar_tag_profile = {
        ar_base_tag: 0.833,
        # 61px AR spread vs 25 px Blacksmith turret is about 1 in 6
        ar_core_tag: 0.167
    }
    mg_tag_profile = {mg_core_tag: 1.0}
    sr_tag_profile = {
        sr_base_tag: 0.2,
        sr_core_tag: 0.8,
    }
    smg_tag_profile = {
        ar_base_tag: 0.95,
        ar_core_tag: 0.05
    }

    # Scarlet attack dps calculation
    scar_dmg_tags = [
        {
            'damage': config.config['nikkes']['Scarlet']['burst']['effect'][1]['damage'],
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {'base': 1.0},
        },
        {
            'damage': scar_n,
            'start': -math.inf,
            'duration': math.inf,
            'tags': ar_tag_profile,
        },
    ]
    if use_list['B3']['Privaty']:
        scar_priv_diff = scar_priv_n - scar_n
        for start in burst_times:
            scar_dmg_tags.append({
                'damage': scar_priv_diff,
                'start': start,
                'duration': 10,
                'tags': ar_tag_profile
            })
    scar_avg_dps = Examples.compute_nikke_dps(
        damage_tags=scar_dmg_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=scar_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Scarlet (Self Burst)',
        verbose=False
    )

    # Modernia attack dps calculation
    Examples.compute_nikke_dps(
        damage_tags=[
            {
                'damage': mod_n,
                'start': -math.inf,
                'duration': math.inf,
                'tags': mg_tag_profile,
            },
            {
                'damage': mod_s1,
                'start': -math.inf,
                'duration': math.inf,
                'tags': {mod_s1_tag: 1.0},
            },
        ],
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=mod_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Modernia',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Modernia attack dps calculation
    Examples.compute_nikke_dps(
        damage_tags=[
            {
                'damage': peak_mod_n,
                'start': -math.inf,
                'duration': math.inf,
                'tags': mg_tag_profile,
            },
            {
                'damage': peak_mod_s1,
                'start': -math.inf,
                'duration': math.inf,
                'tags': {mod_s1_tag: 1.0},
            },
        ],
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=mod_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Peak Modernia',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Rupee
    rupee_buffs = base_buffs + config.convert_nikke_buffs({
        'Rupee': [BuffWindow.inf_buff('s2', 5)],
    })
    Examples.compute_nikke_dps(
        damage_tags=[
            {
                'damage': rupee_n,
                'start': -math.inf,
                'duration': math.inf,
                'tags': ar_tag_profile,
            },
            {
                'damage': config.config['nikkes']['Rupee']['burst']['effect'][0]['damage'],
                'start': burst_times[-1] - 0.1,
                'duration': 0,
                'tags': {mod_s1_tag: 1.0},
            },
        ],
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=rupee_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Rupee',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Dorothy Calculation
    doro_tags = [
        {
            'damage': 13.65 * 60 / (5 + (1 - NIKKE.cube_table['reload'][3] / 100.0)),
            'start': -math.inf,
            'duration': math.inf,
            'tags': ar_tag_profile,
        },
        {
            'damage': 8900.83 * (config.get_nikke_attack('Liter') \
                                 + config.get_enemy_defense('special_interception')) \
                                    / config.get_nikke_attack('Liter'),
            'start': burst_times[1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
        {
            'damage': 8900.83 * (config.get_nikke_attack('Liter') \
                                 + config.get_enemy_defense('special_interception')) \
                                    / config.get_nikke_attack('Liter'),
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
    ] + [
        {
            'damage': 216,
            'start': burst_times[j] + (i+1) * 2,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0}
        } for i in range(5) for j in range(len(burst_times))]
    Examples.compute_nikke_dps(
        damage_tags=doro_tags,
        attack=config.get_nikke_attack('Liter'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=base_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Dorothy',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Snow White, Maxwell, and Alice Calculation
    alice_dmg_tags = [
        {
            'damage': 69.04 * 3.57 * 36 / 10,
            'start': burst_times[0],
            'duration': 10,
            'tags': sr_tag_profile
        },
        {
            'damage': alice_n * (1 + 2.5 / (NIKKE.weapon_table['SR']['attack_speed'] * 1.5)),
            'start': burst_times[0] + 10,
            'duration': math.inf,
            'tags': sr_tag_profile
        }
    ]
    alice_buffs = base_buffs + config.convert_nikke_buffs({
        'Alice': [BuffWindow('b', burst_times[0])],
    })

    reload_t = 1.5*(1 - NIKKE.cube_table['reload'][3] / 100.0)
    b_fire_t = burst_times[0] + 4.0
    s1_trigger_req = 30 / NIKKE.weapon_table['AR']['attack_speed']
    restart_t = b_fire_t + reload_t
    s1_trigger_t = restart_t + s1_trigger_req
    sw_buffs = base_buffs + config.convert_nikke_buffs({
        'Snow White': [BuffWindow('s1', s1_trigger_t, math.inf)]
            + BuffWindow.timeline('s2', [burst_times[0]+2, burst_times[0]+17]),
    })

    sw_dmg_tags = [
        {
            'damage': 499.5 * 10,
            'start': b_fire_t,
            'duration': 0,
            'tags': {ar_core_tag: 1.0},
        },
        {
            'damage': sw_n,
            'start': restart_t,
            'duration': math.inf,
            'tags': ar_tag_profile,
        },
        {
            'damage': 126.64,
            'start': 2.0,
            'duration': 0,
            'tags': {'base': 1.0},
        },
        {
            'damage': 126.64,
            'start': 17.0,
            'duration': 0,
            'tags': {'base': 1.0},
        }
    ]
    sw_dmg_tags += [{
        'damage': 65.55,
        'start': s1_trigger_t + s1_trigger_req * i,
        'duration': 0,
        'tags': {'base': 1.0},
    } for i in range(10)]
    Examples.compute_nikke_dps(
        damage_tags=sw_dmg_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=sw_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Snow White',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet',
        verbose=False
    )
    Examples.compute_nikke_dps(
        damage_tags=[
            {
                'damage': 813.42 * 3,
                'start': 3.0,
                'duration': 0,
                'tags': {sr_core_tag: 1.0},
            },
            {
                'damage': max_n * (1 + 1.5 / (NIKKE.weapon_table['SR']['attack_speed'] * 1)),
                'start': 2,
                'duration': math.inf,
                'tags': sr_tag_profile,
            },
        ],
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=base_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Maxwell',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet',
        verbose=False
    )
    Examples.compute_nikke_dps(
        damage_tags=alice_dmg_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=alice_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Alice',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet',
        verbose=False
    )

    # Power calculation - not accurate, lowball estimate
    power_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'attack': 5.52 * 5,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    power_cycle_time = 12+2*(1-NIKKE.cube_table['reload'][3]/100)
    Examples.compute_nikke_dps(
        damage_tags=[
            {
                'damage': (61.3*2.5*12) / power_cycle_time,
                'start': -math.inf,
                'duration': math.inf,
                'tags': {core_tag: 1.0},
            },
            {
                'damage': 1368,
                'start': burst_times[-1] - 0.1,
                'duration': 0,
                'tags': {mod_s1_tag: 1.0},
            },
            {
                'damage': 1368,
                'start': burst_times[0],
                'duration': 0,
                'tags': {mod_s1_tag: 1.0},
            },
        ],
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=power_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Power',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet',
        verbose=False
    )

    # Sugar Calculation
    sugar_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'crit_rate': 10.65,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    sugar_tags = [
        {
            'damage': 231.6 * 22 / (22/2.4+2.03*(1-NIKKE.cube_table['reload'][3]/100)),
            'start': burst_times[0],
            'duration': 15,
            'tags': smg_tag_profile,
        },
        {
            'damage': 231.6 * 18 / (18/1.5+2.03*(1-NIKKE.cube_table['reload'][3]/100)),
            'start': 15,
            'duration': math.inf,
            'tags': smg_tag_profile,
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=sugar_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=sugar_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Sugar',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Noir
    noir_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'attack': 14.08,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    noir_tags = [
        {
            'damage': 204.6 * 20 / (20/1.5+0.67*(1-NIKKE.cube_table['reload'][3]/100)),
            'start': -math.inf,
            'duration': math.inf,
            'tags': smg_tag_profile,
        },
        {
            'damage': 303.69,
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=noir_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=noir_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Noir',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Guilty Calculation
    guilty_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'attack': 8.81 * 5 + 2.75,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    guilty_tags = [
        {
            'damage': 231.4 * 0.8 * 9 / (9/1.5+2.67*(1-NIKKE.cube_table['reload'][3]/100)),
            'start': -math.inf,
            'duration': math.inf,
            'tags': smg_tag_profile,
        },
        {
            'damage': 189.55,
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
        {
            'damage': 185.14,
            'start': burst_times[0],
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=guilty_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=guilty_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Guilty',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )


    # Soline Calculation
    soline_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        "crit_rate": 21.62,
        "crit_dmg": 62.27,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    soline_tags = [
        {
            'damage': soline_n * 1.0726,
            'start': -math.inf,
            'duration': math.inf,
            'tags': smg_tag_profile,
        },
        {
            'damage': 396,
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
        {
            'damage': 924*3,
            'start': burst_times[0],
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=soline_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=soline_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Soline',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # Guillotine Calculation
    guil_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'attack': 96,#48,
        'crit_rate': 8.28,
        'crit_dmg': 14.69,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    guil_tags = [
        {
            'damage': guil_n,
            'start': -math.inf,
            'duration': math.inf,
            'tags': mg_tag_profile,
        },
        {
            'damage': 1068.75,
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
        {
            'damage': 1068.75,
            'start': burst_times[0],
            'duration': 0,
            'tags': {mod_s1_tag: 1.0},
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=guil_tags,
        attack=config.get_nikke_attack('Modernia'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=guil_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='Guillotine',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    # 2B Calculations
    two_b_buffs = base_buffs + [{
        'type': 'buff',
        'element_bonus': False,
        'element_dmg': 8.49,
        'attack': 11.81,
        'flat_atk': (config.config['nikkes']['2B']['max_health'] * (1 + 0.1003 + 0.2006 + 0.5776) \
                     + (0 if not use_list['B2']['Mast'] else \
                        config.config['nikkes']['Mast']['max_health'] * 0.862)) * 0.0616,
        'start': -math.inf,
        'end': math.inf,
        'duration': math.inf
    }]
    two_b_tags = [
        {
            'damage': two_b_n,
            'start': -math.inf,
            'duration': math.inf,
            'tags': ar_tag_profile,
        },
        {
            'damage': config.config['nikkes']['2B']['burst']['effect'][0]['damage'],
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {'base': 1.0},
        },
        {
            'damage': config.config['nikkes']['2B']['burst']['effect'][1]['damage'],
            'start': burst_times[-1] - 0.1,
            'duration': 0,
            'tags': {'fb': 1.0},
        },
    ]
    Examples.compute_nikke_dps(
        damage_tags=two_b_tags,
        attack=config.get_nikke_attack('2B'),
        defense=config.get_enemy_defense('special_interception'),
        buffs=two_b_buffs,
        window_start=0,
        window_end=burst_times[-1],
        name='2B',
        relative_dps=scar_avg_dps,
        relative_name='Scarlet'
    )

    return 0

if __name__ == '__main__':
    main()
