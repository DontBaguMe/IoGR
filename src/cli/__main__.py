import os
import sys
import random
import argparse

from randomizer.models.enums.difficulty import Difficulty
from randomizer.models.enums.enemizer import Enemizer
from randomizer.models.enums.goal import Goal
from randomizer.models.enums.logic import Logic
from randomizer.models.enums.start_location import StartLocation
from randomizer.models.randomizer_data import RandomizerData
from src.randomizer.iogr_rom import Randomizer

parser = argparse.ArgumentParser(description="Generate a randomly seeded ROM")
parser.add_argument('-s', '--seed', dest="seed", type=int, required=False, default=random.randint(0, 999999999))
parser.add_argument('-d', '--difficulty', dest="difficulty", type=Difficulty, required=False, default=Difficulty.NORMAL)
parser.add_argument('-g', '--goal', dest="goal", type=Goal, required=False, default=Goal.DARK_GAIA)
parser.add_argument('-l', '--logic', dest="logic", type=Logic, required=False, default=Logic.COMPLETABLE)
parser.add_argument('-e', '--enemizer', dest="enemizer", type=Enemizer, required=False, default=Enemizer.NONE)
parser.add_argument('--start-pos', dest="start", type=StartLocation, required=False, default=StartLocation.SOUTH_CAPE)
parser.add_argument('--statues', dest="statues", type=str, required=False, default="4")
parser.add_argument('--firebird', dest="firebird", type=bool, required=False, default=False)
parser.add_argument('--allow-glitches', dest="allow_glitches", type=bool, required=False, default=False)
parser.add_argument('--boss-shuffle', dest="boss_shuffle", type=bool, required=False, default=False)
parser.add_argument('--overworld-shuffle', dest="overworld_shuffle", type=bool, required=False, default=False)
parser.add_argument('--dungeon-shuffle', dest="dungeon_shuffle", type=bool, required=False, default=False)

modeParser = parser.add_mutually_exclusive_group(required=False)
modeParser.add_argument('--ohko', dest="ohko", action='store_true')
modeParser.add_argument('--red-jewel-madness', dest="red_jewel_madness", action='store_true')

parser.set_defaults(ohko=False)
parser.set_defaults(red_jewel_madness=False)


def main(argv):
    args = parser.parse_args(argv)
    settings = RandomizerData(args.seed, args.difficulty, args.goal, args.logic, args.statues, args.enemizer, args.start, args.firebird, args.ohko, args.red_jewel_madness,
                              args.allow_glitches, args.boss_shuffle, args.overworld_shuffle, args.dungeon_shuffle)
    randomizer = Randomizer(settings)

    filename = randomizer.generate_filename()
    randomizer.generate_rom(filename)

    print("File created: " + filename)


if __name__ == "__main__":
    main(sys.argv[1:])
