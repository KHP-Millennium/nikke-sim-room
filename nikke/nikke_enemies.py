"""Calculates the damage inflicted by various enemies."""

import copy
import json
import time
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# pylint: disable=import-error
import nikke_dmg


def get_multiplier(damage: float, attack: float, defense: float) -> float:
    """Reverse engineers the attack multiplier from the damage taken."""
    return damage / (attack - defense)

def alteisen() -> int:
    """Main function."""
    si_boss_params = {'attack': 65613, 'defense': 5740}
    ur_train_params = {'attack': 57602, 'defense': 8580} # 11522 enemy defense
    modernia_laser_m = 100 * get_multiplier(**si_boss_params, damage=438622)
    # source: https://www.youtube.com/watch?v=sKkNz1TuF8I
    missile_m = 100 * get_multiplier(**si_boss_params, damage=583821) # 515677 to cover w/Noah S2 Lv4,
    # where did 593008 come from???
    # source: Neppity screenshot of Maxwell getting hit
    turret_m = 100 * get_multiplier(**si_boss_params, damage=108395) # 95743 to cover w/Noah S2 Lv4
    num_shots = 18 #- 3

    si_boss_params['attack'] *= 1 - 0.1065
    # source: my own vod
    noah_missile_m = 100 * get_multiplier(**si_boss_params, damage=515677) # 510391 taking it directly
    # source: my own vod
    noah_turret_m = 100 * get_multiplier(**si_boss_params, damage=95743) # 94762 taking it directly
    print(f'{modernia_laser_m=:.2f} {missile_m=:.2f}, {turret_m=:.2f}, {noah_missile_m=:.2f}, {noah_turret_m=:.2f}')

    nikke_dmg.Examples.compute_actual_damage(
        damage=missile_m,
        attack=ur_train_params['attack'] * (1 - 0.1065),
        defense=ur_train_params['defense'],
        buffs=[],
        name='Alteisen Missile Turret',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=turret_m*7,#*num_shots,
        attack=ur_train_params['attack'] * (1 - 0.1065),
        defense=ur_train_params['defense']*2.0378,
        buffs=[],
        name='Alteisen Turret',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=499.5*10,
        attack=60000,
        defense=ur_train_params['defense'],
        buffs=[{
            'attack': 7.72+40.4+90.75+16.16,
            'crit_dmg': 13.22+32.99+56.23,#13.22+10.77+12.46+14.42,
            'crit_rate': 4.21+14.64+26.1,#26.1+4.21+31.9,
            'damage_taken': 11.85,#39.96,
        }],
        range_bonus=False,
        full_burst=True,
        core_hit=True,
        name='Snow White Burst'
    )

    def_range = range(6500, 12000, 20)
    hp_range = range(900000, 2000000, 100)
    data = np.zeros((len(def_range), len(hp_range)))
    breakpoint_data = np.zeros((len(def_range), 2))
    for i, defense in enumerate(def_range):
        damage = nikke_dmg.Examples.compute_actual_damage(
            damage=turret_m*num_shots,
            attack=ur_train_params['attack'],# * (1 - 0.1065),
            defense=defense,#*2.0378,
            buffs=[],
            name='Alteisen Turret',
            log=False
        )
        prev = math.inf
        for j, health in enumerate(hp_range):
            data[i][j] = damage[0] / health * 100

            if prev > 100 and data[i][j] <= 100:
                breakpoint_data[i] = [health, defense]
            prev = data[i][j]

    plot = nikke_dmg.Graphs.ColorPlot(f'Alteisen Turret Damage (x{num_shots} Shots)')
    plot.load_data(data, hp_range, def_range)
    plot.draw_line(breakpoint_data)
    plot.set_xlabel('Max Health (in millions of HP)')
    plot.set_ylabel('Defense')

    return 0


def nihilister() -> int:
    """Main function."""
    campaign_boss_params_c = {'attack': 31990, 'defense': 6150}
    campaign_boss_params_n = {'attack': 31990, 'defense': 23879450 / 6887} # approx 3467.3
    ur_boss_params = {'attack': 57602, 'defense': 8580} # 11522 enemy defense
    # source: https://www.youtube.com/watch?v=QQBDLxhdC6o
    turret_m = 100 * get_multiplier(**campaign_boss_params_c, damage=6887) # lv 206
    breath_p1_m = 100 * get_multiplier(**campaign_boss_params_c, damage=44949) # lv 206
    burning_p1_m = 100 * get_multiplier(**campaign_boss_params_c, damage=19264) # lv 206
    meteor_p1_m = 100 * get_multiplier(**campaign_boss_params_c, damage=166952) # lv 206
    breath_p2_m = 100 * get_multiplier(**campaign_boss_params_c, damage=57791) # lv 206
    spear_p2_m = 100 * get_multiplier(**campaign_boss_params_n, damage=99228) # lv 206

    burning_num_shots = 10
    turret_num_shots = 30
    breath_num_shots = 3

    nikke_dmg.Examples.compute_actual_damage(
        damage=turret_m * turret_num_shots,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name=f'Nihilister Turrets x{turret_num_shots} Shots (Phase 1)',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=burning_p1_m * burning_num_shots,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name=f'Nihilister <Burning Shot> x{burning_num_shots} Missiles (Phase 1)',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=breath_p1_m * breath_num_shots,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name='Nihilister <Megiddo Flame> Breath (Phase 1)',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=meteor_p1_m,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name='Nihilister <Mini Meteor> x1 (Phase 1)',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=breath_p2_m,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name='Nihilister <Burning Scourge> Breath (Phase 2)',
        show_crit=False,
        show_avg=False
    )
    nikke_dmg.Examples.compute_actual_damage(
        damage=spear_p2_m,
        attack=ur_boss_params['attack'],
        defense=ur_boss_params['defense'],
        buffs=[],
        name='Nihilister <Thunder Spear> x1 (Phase 2)',
        show_crit=False,
        show_avg=False
    )

    # def_range = range(6500, 9000, 10)
    # hp_range = range(900000, 2000000, 100)
    # data = np.zeros((len(def_range), len(hp_range)))
    # breakpoint_data = np.zeros((len(def_range), 2))
    # for i, defense in enumerate(def_range):
    #     damage = nikke_dmg.Examples.compute_actual_damage(
    #         damage=breath_m*num_shots,
    #         attack=ur_boss_params['attack'],
    #         defense=defense,
    #         buffs=[],
    #         name='Alteisen Turret',
    #         log=False
    #     )
    #     prev = math.inf
    #     for j, health in enumerate(hp_range):
    #         data[i][j] = damage[0] / health * 100

    #         if prev > 100 and data[i][j] <= 100:
    #             breakpoint_data[i] = [health, defense]
    #         prev = data[i][j]

    # plot = nikke_dmg.Graphs.ColorPlot(f'Alteisen Turret Damage (x{num_shots} Shots)')
    # plot.load_data(data, hp_range, def_range)
    # plot.draw_line(breakpoint_data)
    # plot.set_xlabel('Max Health (in millions of HP)')
    # plot.set_ylabel('Defense')

    return 0

def main():
    """Main function."""
    #ret = nihilister()
    ret = alteisen()

    with open('nikke/config/StaticData/CoverStatEnhanceTable.json', 'r', encoding='utf-8') as fp:
        cover = json.load(fp)['records']
        cover_list = np.zeros((len(cover), 3))
        for i, item in enumerate(cover):
            cover_list[i] = [item['lv'], item['level_hp'], item['level_defence']]
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.minorticks_on()
    ax.grid(visible=True,
        which='major',
        linestyle='-',
        linewidth='0.5',
        color='red')
    ax.grid(visible=True,
        which='minor',
        linestyle=':',
        linewidth='0.5',
        color='black')
    ax.plot(cover_list[200:300,0], cover_list[200:300,1])
    ax.set_title('Cover HP vs Nikke Level', fontdict={'size': 20})
    ax.set_xlabel('Nikke Level', fontdict={'size': 20})
    ax.set_ylabel('Cover Health', fontdict={'size': 20})
    plt.show()

    return ret

if __name__ == '__main__':
    main()
