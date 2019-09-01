import sys
import random
import argparse
from randomizer.iogr_rom import Randomizer


parser = argparse.ArgumentParser(description="Generate a randomly seeded ROM")
parser.add_argument('-s', '--seed', dest="seed", type=int, required=False, default=random.randint(0, 999999999))
parser.add_argument('-p', '--path', dest="path", type=str, required=True)
parser.add_argument('-d', '--difficulty', dest="difficulty", type=str, required=False, default="Normal")
parser.add_argument('-g', '--goal', dest="goal", type=str, required=False, default="Dark Gaia")
parser.add_argument('-l', '--logic', dest="logic", type=str, required=False, default="Completable")
parser.add_argument('-e', '--enemizer', dest="enemizer", type=str, required=False, default="None")
parser.add_argument('--start-pos', dest="start", type=str, required=False, default="South Cape")
parser.add_argument('--statues', dest="statues", type=str, required=False, default="4")
parser.add_argument('--variant', dest="variant", type=str, required=False, default="None")

firebirdParser = parser.add_mutually_exclusive_group(required=False)
firebirdParser.add_argument('--firebird', dest="firebird", action='store_true')
firebirdParser.add_argument('--no-firebird', dest="firebird", action='store_false')

parser.set_defaults(firebird=False)

def main(argv):
    args = parser.parse_args(argv)
    randomizer = Randomizer()
    
    filename = randomizer.generate_filename(args.seed, args.difficulty, args.goal, args.logic, args.statues, args.variant, args.start, args.enemizer, args.firebird)
    randomizer.generate_rom(filename, args.path, args.seed, args.difficulty, args.goal, args.logic, args.statues, args.start, args.variant, args.enemizer, args.firebird)
    
    print("File created: " + filename)


if __name__ == "__main__":
    main(sys.argv[1:])