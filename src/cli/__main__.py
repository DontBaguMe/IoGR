import json
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
from randomizer.iogr_rom import Randomizer, generate_filename

parser = argparse.ArgumentParser(description="Generate a randomly seeded ROM")
parser.add_argument('-p', '--path', dest="path", type=str, required=True)
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
parser.add_argument('--open-mode', dest="open_mode", type=bool, required=False, default=False)

modeParser = parser.add_mutually_exclusive_group(required=False)
modeParser.add_argument('--ohko', dest="ohko", action='store_true')
modeParser.add_argument('--red-jewel-madness', dest="red_jewel_madness", action='store_true')

parser.set_defaults(ohko=False)
parser.set_defaults(red_jewel_madness=False)


def main(argv):
    args = parser.parse_args(argv)

    settings = RandomizerData(args.seed, args.difficulty, args.goal, args.logic, args.statues, args.enemizer, args.start, args.firebird, args.ohko, args.red_jewel_madness,
                              args.allow_glitches, args.boss_shuffle, args.open_mode, args.overworld_shuffle, args.dungeon_shuffle)

    rom_filename = generate_filename(settings, "sfc")
    spoiler_filename = generate_filename(settings, "json")

    randomizer = Randomizer(args.path)
    patch = randomizer.generate_rom(rom_filename, settings)
    spoiler = randomizer.generate_spoiler()

    write_patch(patch, rom_filename, args.path)
    write_spoiler(spoiler, spoiler_filename, args.path)


def write_spoiler(spoiler, filename, rom_path):
    f = open(os.path.dirname(rom_path) + os.path.sep + filename, "w+")
    f.write(spoiler)
    f.close()
    print("Spoiler created: " + filename)


def sort_patch(val):
    return val['index']


def write_patch(patch, filename, rom_path):
    original = open(rom_path, "rb")
    randomized = open(os.path.dirname(rom_path) + os.path.sep + filename, "wb")
    randomized.write(original.read())

    original.close()
    data = json.loads(patch)
    data.sort(key=sort_patch)

    for k in data:
        address = int(k['address'])
        value = bytes(k['data'])

        randomized.seek(address)
        randomized.write(value)
    randomized.close()
    print("Patch created: " + filename)


if __name__ == "__main__":
    main(sys.argv[1:])
