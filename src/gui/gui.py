import json
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import random
import zipfile

from randomizer.iogr_rom import generate_filename
#from randomizer.models.enums.difficulty import Difficulty
#from randomizer.models.enums.enemizer import Enemizer
#from randomizer.models.enums.goal import Goal
#from randomizer.models.enums.statue_req import StatueReq
#from randomizer.models.enums.logic import Logic
#from randomizer.models.enums.sprites import Sprite
#from randomizer.models.enums.entrance_shuffle import EntranceShuffle
##from randomizer.models.enums.dungeon_shuffle import DungeonShuffle
#from randomizer.models.enums.orb_rando import OrbRando
#from randomizer.models.enums.darkrooms import DarkRooms
#from randomizer.models.enums.start_location import StartLocation
#from randomizer.models.enums.flute import FluteOpt
from randomizer.iogr_rom import Randomizer, VERSION
from randomizer.models.randomizer_data import RandomizerData
from randomizer.errors import FileNotFoundError, OffsetError
from randomizer.models.enums import *


def find_ROM():
    ROM.delete(0, tkinter.END)
    ROM.insert(10, tkinter.filedialog.askopenfilename())


def load_ROM():
    try:
        f = open("rompath.txt")
        return f.read()
    except:
        return ""


def save_ROM(rompath):
    with open("rompath.txt","w") as f:
        f.write(rompath)


def generate_seed():
    seed.delete(0, tkinter.END)
    seed.insert(10, random.randint(0, 99999999))


def generate_ROM():
    rompath = ROM.get()
    save_ROM(rompath)
    seed_str = seed.get()

    def get_difficulty():
        d = difficulty.get()
        if d == "Easy":
            return Difficulty.EASY
        if d == "Normal":
            return Difficulty.NORMAL
        if d == "Hard":
            return Difficulty.HARD
        if d == "Extreme":
            return Difficulty.EXTREME

    def get_goal():
        g = goal.get()
        if g == "Dark Gaia":
            return Goal.DARK_GAIA
        if g == "Apocalypse Gaia":
            return Goal.APO_GAIA
        if g == "Random Gaia":
            return Goal.RANDOM_GAIA
        if g == "Red Jewel Hunt":
            return Goal.RED_JEWEL_HUNT

    def get_statue_req():
        s = statue_req.get()
        if s == "Player Choice":
            return StatueReq.PLAYER_CHOICE
        if s == "Random Choice":
            return StatueReq.RANDOM_CHOICE
        else:
            return StatueReq.GAME_CHOICE

    def get_logic():
        l = logic.get()
        if l == "Completable":
            return Logic.COMPLETABLE
        if l == "Beatable":
            return Logic.BEATABLE
        if l == "Chaos":
            return Logic.CHAOS
    
    def get_flute_opt():
        f = flute_opt.get()
        if f == "Shuffle Flute":
            return FluteOpt.SHUFFLE
        if f == "Fluteless":
            return FluteOpt.FLUTELESS
        return FluteOpt.START

    def get_enemizer():
        e = enemizer.get()
        if e == "None":
            return Enemizer.NONE
        if e == "Limited":
            return Enemizer.LIMITED
        if e == "Balanced":
            return Enemizer.BALANCED
        if e == "Full":
            return Enemizer.FULL
        if e == "Insane":
            return Enemizer.INSANE

    def get_entrance_shuffle():
        g = entrance_shuffle.get()
        if g == "None":
            return EntranceShuffle.NONE
        if g == "Coupled":
            return EntranceShuffle.COUPLED
        if g == "Uncoupled":
            return EntranceShuffle.UNCOUPLED
 
    def get_dungeon_shuffle():
        g = dungeon_shuffle.get()
        if g == "None":
            return DungeonShuffle.NONE
        if g == "Basic":
            return DungeonShuffle.BASIC
        if g == "Chaos":
            return DungeonShuffle.CHAOS
        if g == "Clustered":
            return DungeonShuffle.CLUSTERED

    def get_orb_rando():
        g = orb_rando.get()
        if g == "None":
            return OrbRando.NONE
        if g == "Basic":
            return OrbRando.BASIC
        if g == "Orbsanity":
            return OrbRando.ORBSANITY
    
    def get_darkrooms():
        l = darkrooms_level.get()
        c = darkrooms_cursed.get()
        if l == "None":
            return DarkRooms.NONE
        if l == "All":
            return DarkRooms.ALL
        if l == "Few":
            if c:
                return DarkRooms.FEWCURSED
            return DarkRooms.FEW
        if l == "Some":
            if c:
                return DarkRooms.SOMECURSED
            return DarkRooms.SOME
        if l == "Many":
            if c:
                return DarkRooms.MANYCURSED
            return DarkRooms.MANY

    def get_start_location():
        g = start.get()
        if g == "South Cape":
            return StartLocation.SOUTH_CAPE
        if g == "Safe":
            return StartLocation.SAFE
        if g == "Unsafe":
            return StartLocation.UNSAFE
        if g == "Forced Unsafe":
            return StartLocation.FORCED_UNSAFE

    def get_sprite():
        sp = sprite.get()
        if sp == "Will":
            return Sprite.WILL
        if sp == "Bagu":
            return Sprite.BAGU
        if sp == "Freet":
            return Sprite.FREET
        if sp == "Invisible":
            return Sprite.INVISIBLE
        if sp == "Solar":
            return Sprite.SOLAR
        if sp == "Sye":
            return Sprite.SYE

    def get_printlevel():
        m = printlevel.get()
        if m == "Error":
            return PrintLevel.ERROR
        if m == "Warn":
            return PrintLevel.WARN
        if m == "Info":
            return PrintLevel.INFO
        if m == "Verbose":
            return PrintLevel.VERBOSE
        return PrintLevel.SILENT

    if not seed_str.isdigit():
        tkinter.messagebox.showinfo("ERROR", "Please enter or generate a valid seed")
        return

    try:
        seed_int = int(seed_str)
        settings = RandomizerData(
            seed = seed_int, 
            difficulty = get_difficulty(), 
            goal = get_goal(), 
            logic = get_logic(), 
            statues = statues.get(), 
            statue_req = get_statue_req(), 
            start_location = get_start_location(),
            enemizer = get_enemizer(), 
            firebird = firebird.get(), 
            ohko = ohko.get(), 
            red_jewel_madness = red_jewel_madness.get(), 
            allow_glitches = glitches.get(), 
            boss_shuffle = boss_shuffle.get(), 
            open_mode = open_mode.get(), 
            z3 = z3_mode.get(),
            coupled_exits = coupled_exits.get(),
            town_shuffle = town_shuffle.get(),
            dungeon_shuffle = dungeon_shuffle.get(), 
            overworld_shuffle = overworld_shuffle.get(), 
            race_mode = race_mode_toggle.get(), 
            flute = get_flute_opt(), 
            sprite = get_sprite(),
            orb_rando = get_orb_rando(), 
            darkrooms = get_darkrooms(),
            printlevel = get_printlevel(),
            break_on_error = break_on_error.get(),
            break_on_init = break_on_init.get(),
            ingame_debug = ingame_debug.get()
            )

        base_filename = generate_filename(settings, "")
        rom_filename = base_filename + ".sfc"
        asm_filename = base_filename + ".asr"
        spoiler_filename = base_filename + ".json"
        randomizer = Randomizer(rompath)
        if do_profile.get():
            random.seed(seed_int)
            import cProfile, pstats, io
            profiling_path = os.path.dirname(rompath) + os.path.sep + "iogr" + os.path.sep + base_filename + os.path.sep
            if not os.path.exists(os.path.dirname(profiling_path)):
                os.makedirs(os.path.dirname(profiling_path))
            profile = cProfile.Profile()
            profile.enable()
            test_number = 1
            while test_number <= 20:
                settings.seed = random.randint(0, 99999999)
                patch = randomizer.generate_rom("", settings, profiling_path + "Test" + format(test_number,"02"))
                test_number += 1
            profile.disable()
            #statstream = io.StringIO()
            statfile = open(profiling_path + os.path.sep + "profile.txt","w")
            runstats = pstats.Stats(profile, stream=statfile)
            runstats.strip_dirs()
            runstats.sort_stats('time')
            runstats.print_stats()
            #statfile.write(statstream.read())
            statfile.close()
            tkinter.messagebox.showinfo("Success","Profiling complete; results in ./iogr/"+base_filename+"/")
        else:
            patch = randomizer.generate_rom(rom_filename, settings)
            if not patch[0]:
                tkinter.messagebox.showerror("Error", "Assembling failed. The first error was:" + str(patch[1][0]) )
            else:
                write_patch(patch, rompath, rom_filename, settings)
                if not race_mode_toggle.get():
                    spoiler = randomizer.generate_spoiler()
                    write_spoiler(spoiler, spoiler_filename, rompath)
                    asm_dump = randomizer.generate_asm_dump()
                    write_asm_dump(asm_dump, asm_filename, rompath)
                tkinter.messagebox.showinfo("Success!", rom_filename + " has been successfully created!")
    except OffsetError:
        tkinter.messagebox.showerror("ERROR", "This randomizer is only compatible with the (US) version of Illusion of Gaia")
    except FileNotFoundError:
        tkinter.messagebox.showerror("ERROR", "ROM file does not exist")
    except Exception as e:
        tkinter.messagebox.showerror("ERROR", e)


def write_spoiler(spoiler, filename, rom_path):
    f = open(os.path.dirname(rom_path) + os.path.sep + filename, "w+")
    f.write(spoiler)
    f.close()


def write_asm_dump(asm_dump, filename, rom_path):
    f = open(os.path.dirname(rom_path) + os.path.sep + filename, "w+")
    f.write(asm_dump)
    f.close()


def sort_patch(val):
    return val['index']


def write_patch(patch, rom_path, filename, settings):
    original = open(rom_path, "rb")

    randomized = open(os.path.dirname(rom_path) + os.path.sep + filename, "wb")
    randomized.write(patch[1])

    original.close()

    randomized.close()


def diff_help():
    lines = ["Increased difficulty generally places required items deeper in dungeons, so more of the game has to be completed.",
             "",
             "Extreme difficulty additionally removes in-game spoilers, and may require difficult tasks like defeating Solid Arm."]
    tkinter.messagebox.showinfo("Difficulties", "\n".join(lines))


def goal_help():
    lines = ["Goal determines the required conditions to beat the game:", "",
             "[DARK/APOCALYPSE/RANDOM] GAIA:", " - Collect the required Mystic Statues (if any)", " - Rescue Kara from her portrait using the Magic Dust",
             " - Acquire and use the Aura to gain Shadow's form", " - Talk to Gaia in any Dark Space to face and defeat the Gaia of your choice", "",
             "RED JEWEL HUNT:", "Collect the appropriate number of Red Jewels, by difficulty, and turn them into the Jeweler:",
             " - Easy: 35 Red Jewels", " - Normal: 40 Red Jewels", " - Hard/Extreme: 50 Red Jewels"]
    tkinter.messagebox.showinfo("Goal", "\n".join(lines))


def logic_help():
    lines = ["Logic determines how items and abilities are placed:", "",
             "COMPLETABLE:", " - All items and locations are accessible", " - Freedan abilities will only show up in dungeons", "",
             "BEATABLE:", " - Some non-essential items may be inaccessible", " - Freedan abilities will only show up in dungeons", "",
             "CHAOS:", " - Some non-essential items may be inaccessible", " - Freedan abilities may show up in towns"]
    tkinter.messagebox.showinfo("Logic Modes", "\n".join(lines))


def variant_help():
    lines = ["OHKO: You always have 1 HP and perish in one hit.","",
             "Red Jewel Madness: Start with 40 HP. Each Red Jewel given to the Jeweler reduces HP by 1.","",
             "Fluteless: Will has no primary weapon, and can only do damage via abilities or as Freedan/Shadow.","",
             "Z3 Mode: HP and damage values are adjusted to make combat faster and more dangerous. STR and DEF upgrades double/halve damage.","",
             "Glitches: To beat the game, you may be required to take advantage of bugs or other unintended mechanics.","",
             "Early Firebird: As Shadow, you gain the Firebird attack after using the Crystal Ring and rescuing Kara.","",
             "Open Mode: Intercontinental travel via Lola's Letter, the Teapot, the Memory Melody, the Will, and the Large Roast is accessible from the start of the game.","",
             "Race Seed: A spoiler log is not generated, and the chosen seed is transformed to a new secret seed. Useful for racing if exchanging files isn't possible.",""]
    tkinter.messagebox.showinfo("Variants", "\n".join(lines))


def enemizer_help():
    lines = ["The following enemy shuffle modes are available:", "",
             "LIMITED:", " - Enemies only appear within their own dungeons", "",
             "BALANCED:", " - Enemies can show up in any dungeon, but retain the stats of the enemies they replace", "",
             "FULL:", " - Enemies can show up in any dungeon with their normal stats", "", "INSANE:", " - Same as Full, but enemy stats are shuffled"]
    tkinter.messagebox.showinfo("Enemizer", "\n".join(lines))


def start_help():
    lines = ["You can change this setting to affect where you start the game.", "Where you start the game is also where Gaia sends you when you warp to start.", "",
             "SOUTH CAPE:", " - You start the game in South Cape, as normal", "",
             "SAFE:", " - You start the game in a random town, in front of a Dark Space", "",
             "UNSAFE:", " - You start the game in front of a random Dark Space, could be in a town or a dungeon", "",
             "FORCED UNSAFE:", " - You're guaranteed to start the game in the middle of a dungeon"]
    tkinter.messagebox.showinfo("Start Location", "\n".join(lines))
    
def overworld_shuffle_help():
    lines = ["Overworld Shuffle randomizes which overworld-connected rooms are on each continent for overworld travel."]
    tkinter.messagebox.showinfo("Overworld Shuffle", "\n".join(lines))

def entrance_shuffle_help():
    lines = ["Town Shuffle randomizes doors and other transitions outside of dungeons.",
             "Dungeon Shuffle randomizes transitions within dungeons.",
             "",
             "Coupled transitions are reversible: after taking an exit, you can backtrack through the paired exit on the other side.",
             "If coupling is turned off, backtracking generally won't return you to the room you came from."]
    tkinter.messagebox.showinfo("Transition Shuffles", "\n".join(lines))
    
def orb_rando_help():
    lines = ["Randomizes the orbs that open doors and barriers, that are produced when some monsters are destroyed.",
             " - Basic: Orb-generating monsters open a random door instead of their intended one.",
             " - Orbsanity: Orbs are shuffled with all other items. Orb-generating monsters grant a random item when they're destroyed."]
    tkinter.messagebox.showinfo("Orb Rando", "\n".join(lines))
    
def darkrooms_help():
    lines = ["Random dungeon rooms are made dark, generally in clusters on side branches or near the dungeon end.",
             "",
             "The Dark Glasses and the Crystal Ring let you see in darkness. The game won't require you to enter a dark room without both of these items, unless you choose Cursed Darkness.",
             "",
             "If Cursed, you may have to traverse dark rooms without a light source. Darkness may spread out of side branches into central dungeon rooms."]
    tkinter.messagebox.showinfo("Dark Rooms", "\n".join(lines))
    
def dr_maybe_set_cursed(drlevel):
    if darkrooms_level.get() == "All":
        darkrooms_cursed_checkbox.config(state='disabled')
        darkrooms_cursed.set(1)
    else:
        darkrooms_cursed_checkbox.config(state='normal')

def er_maybe_force_coupled():
    if not dungeon_shuffle.get() and not town_shuffle.get():
        coupled_exits.set(1)
        coupled_exits_checkbox.config(state='disabled')
    else:
        coupled_exits_checkbox.config(state='normal')

def checkbox_clear_rjm():
    red_jewel_madness.set(0)
def checkbox_clear_ohko():
    ohko.set(0)

def goal_maybe_change_statues(goalchoice):
    if goal.get() == "Red Jewel Hunt":
        statues.set("0")
def statues_maybe_change_goal(statuechoice):
    if statues.get() != "0" and goal.get() == "Red Jewel Hunt":
        goal.set("Dark Gaia")


root = tkinter.Tk()
root.title("Illusion of Gaia Randomizer (v." + VERSION + ")")
# if os.name == 'nt':
#     root.wm_iconbitmap('iogr.ico')
# else:
#     root.tk.call('wm', 'iconphoto', root._w, tkinter.PhotoImage(file=os.path.join(".",'iogr.png')))

# Add a grid
mainframe = tkinter.Frame(root)
mainframe.grid(column=2, row=9, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
mainframe.pack(pady=20, padx=20)

tkinter.Label(mainframe, text="Base ROM File").grid(row=0, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Seed").grid(row=1, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Difficulty").grid(row=2, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Logic").grid(row=3, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Goal").grid(row=4, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Statues").grid(row=5, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Start Location").grid(row=6, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Gameplay Variants").grid(row=7, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Enemizer").grid(row=9, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Overworld Shuffle").grid(row=16, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Entrance Shuffle").grid(row=17, column=0, sticky=tkinter.W)
#tkinter.Label(mainframe, text="Dungeon Shuffle").grid(row=18, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Orb Rando").grid(row=20, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Dark Rooms").grid(row=22, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Dev Tools").grid(row=50, column=0, sticky=tkinter.W)

difficulty = tkinter.StringVar(root)
diff_choices = ["Easy", "Normal", "Hard", "Extreme"]
difficulty.set("Normal")

goal = tkinter.StringVar(root)
goal_choices = ["Dark Gaia", "Apocalypse Gaia", "Random Gaia", "Red Jewel Hunt"]
goal.set("Dark Gaia")

logic = tkinter.StringVar(root)
logic_choices = ["Completable", "Beatable", "Chaos"]
logic.set("Completable")

firebird = tkinter.IntVar(root)
firebird.set(0)

start = tkinter.StringVar(root)
start_choices = ["South Cape", "Safe", "Unsafe", "Forced Unsafe"]
start.set("South Cape")

ohko = tkinter.IntVar(root)
ohko.set(0)

red_jewel_madness = tkinter.IntVar(root)
red_jewel_madness.set(0)

glitches = tkinter.IntVar(root)
glitches.set(0)

boss_shuffle = tkinter.IntVar(root)
boss_shuffle.set(0)

open_mode = tkinter.IntVar(root)
open_mode.set(0)

z3_mode = tkinter.IntVar(root)
z3_mode.set(0)

overworld_shuffle = tkinter.IntVar(root)
overworld_shuffle.set(0)

coupled_exits = tkinter.IntVar(root)
coupled_exits.set(1)

town_shuffle = tkinter.IntVar(root)
town_shuffle.set(0)

dungeon_shuffle = tkinter.IntVar(root)
dungeon_shuffle.set(0)

orb_rando = tkinter.StringVar(root)
orb_rando_choices = ["None", "Basic", "Orbsanity"]
orb_rando.set("None")

darkrooms_level = tkinter.StringVar(root)
darkrooms_level_choices = ["None", "Few", "Some", "Many", "All"]
darkrooms_level.set("None")
darkrooms_cursed = tkinter.IntVar(root)
darkrooms_cursed.set(0)

race_mode_toggle = tkinter.IntVar(root)
race_mode_toggle.set(0)

flute_opt = tkinter.StringVar(root)
flute_opt_choices = ["Start with Flute", "Shuffle Flute", "Fluteless"]
flute_opt.set("Start with Flute")

enemizer = tkinter.StringVar(root)
enemizer_choices = ["None", "Limited", "Balanced", "Full", "Insane"]
enemizer.set("None")

sprite = tkinter.StringVar(root)
sprite_choices = ["Will"]#, "Bagu", "Invisible"]#, "Freet", "Solar", "Sye"]
sprite.set("Will")

statues = tkinter.StringVar(root)
statue_choices = ["0", "1", "2", "3", "4", "5", "6", "Random"]
statues.set("4")

statue_req = tkinter.StringVar(root)
statue_req_choices = ["Game Choice", "Player Choice", "Random Choice"]
statue_req.set("Game Choice")

printlevel = tkinter.StringVar(root)
printlevel_choices = ["Silent", "Error", "Warn", "Info", "Verbose"]
printlevel.set("Silent")
break_on_error = tkinter.IntVar(root)
break_on_error.set(0)
break_on_init = tkinter.IntVar(root)
break_on_init.set(0)
do_profile = tkinter.IntVar(root)
do_profile.set(0)
ingame_debug = tkinter.IntVar(root)
ingame_debug.set(0)

ROM = tkinter.Entry(mainframe, width="40")
ROM.grid(row=0, column=1)
ROM.insert(0,load_ROM())

seed_frame = tkinter.Frame(mainframe, borderwidth=1)
seed_frame.grid(row=1, column=1)
seed_frame.columnconfigure(0, weight=1)
seed_frame.rowconfigure(0, weight=1)
seed = tkinter.Entry(seed_frame)
seed.pack(side='left')
seed.insert(10, random.randint(0, 999999))

diff_menu = tkinter.OptionMenu(mainframe, difficulty, *diff_choices).grid(row=2, column=1)
logic_menu = tkinter.OptionMenu(mainframe, logic, *logic_choices).grid(row=3, column=1)
goal_menu = tkinter.OptionMenu(mainframe, goal, *goal_choices, command=goal_maybe_change_statues).grid(row=4, column=1)
statues_frame = tkinter.Frame(mainframe)
statues_frame.grid(row=5, column=1)
statues_menu = tkinter.OptionMenu(statues_frame, statues, *statue_choices, command=statues_maybe_change_goal).pack(side='left')
statue_req_menu = tkinter.OptionMenu(statues_frame, statue_req, *statue_req_choices).pack(side='left')
start_menu = tkinter.OptionMenu(mainframe, start, *start_choices).grid(row=6, column=1)

variants_frame = tkinter.Frame(mainframe, borderwidth=1, relief='sunken')
variants_frame.grid(row=7, column=1)
variants_frame.columnconfigure(0, weight=1)
variants_frame.rowconfigure(0, weight=1)
ohko_label = tkinter.Label(variants_frame, text="OHKO:").grid(row=0, column=0, sticky=tkinter.E)
ohko_checkbox = tkinter.Checkbutton(variants_frame, variable=ohko, onvalue=1, offvalue=0, command=checkbox_clear_rjm).grid(row=0, column=1)
#variants_col_split_label = tkinter.Label(variants_frame, text=" ").grid(row=0, column=2)
rjm_label = tkinter.Label(variants_frame, text="Red Jewel Madness:").grid(row=0, column=3, sticky=tkinter.E)
rjm_checkbox = tkinter.Checkbutton(variants_frame, variable=red_jewel_madness, onvalue=1, offvalue=0, command=checkbox_clear_ohko).grid(row=0, column=4)
#fluteless_label = tkinter.Label(variants_frame, text="Fluteless:").grid(row=1, column=0, sticky=tkinter.E)
#fluteless_checkbox = tkinter.Checkbutton(variants_frame, variable=fluteless, onvalue=1, offvalue=0).grid(row=1, column=1)
z3_mode_label = tkinter.Label(variants_frame, text="Z3 Mode:").grid(row=1, column=3, sticky=tkinter.E)
z3_mode_checkbox = tkinter.Checkbutton(variants_frame, variable=z3_mode, onvalue=1, offvalue=0).grid(row=1, column=4)
glitches_label = tkinter.Label(variants_frame, text="Glitches:").grid(row=2, column=0, sticky=tkinter.E)
glitches_checkbox = tkinter.Checkbutton(variants_frame, variable=glitches, onvalue=1, offvalue=0).grid(row=2, column=1)
firebird_label = tkinter.Label(variants_frame, text="Early Firebird:").grid(row=2, column=3, sticky=tkinter.E)
firebird_checkbox = tkinter.Checkbutton(variants_frame, variable=firebird, onvalue=1, offvalue=0).grid(row=2, column=4)
open_mode_label = tkinter.Label(variants_frame, text="Open:").grid(row=3, column=0, sticky=tkinter.E)
open_mode_checkbox = tkinter.Checkbutton(variants_frame, variable=open_mode, onvalue=1, offvalue=0).grid(row=3, column=1)
race_mode_label = tkinter.Label(variants_frame, text="Race Seed:").grid(row=3, column=3, sticky=tkinter.E)
race_mode_toggle_checkbox = tkinter.Checkbutton(variants_frame, variable=race_mode_toggle, onvalue=1, offvalue=0).grid(row=3, column=4)
flute_label = tkinter.Label(variants_frame, text="Flute:").grid(row=4, column=0, sticky=tkinter.E)
flute_menu = tkinter.OptionMenu(variants_frame, flute_opt, *flute_opt_choices).grid(row=4, column=1, columnspan=4, sticky=tkinter.W)

enemy_rando_frame = tkinter.Frame(mainframe, borderwidth=1)
enemy_rando_frame.grid(row=9, column=1)
enemy_rando_frame.columnconfigure(0, weight=1)
enemy_rando_frame.rowconfigure(0, weight=1)
enemizer_menu = tkinter.OptionMenu(enemy_rando_frame, enemizer, *enemizer_choices).pack(side='left')
boss_shuffle_label = tkinter.Label(enemy_rando_frame, text="Boss shuffle:").pack(side='left')
boss_shuffle_checkbox = tkinter.Checkbutton(enemy_rando_frame, variable=boss_shuffle, onvalue=1, offvalue=0).pack(side='left')

overworld_shuffle_checkbox = tkinter.Checkbutton(mainframe, variable=overworld_shuffle, onvalue=1, offvalue=0).grid(row=16, column=1)

er_frame = tkinter.Frame(mainframe, borderwidth=1, relief='sunken')
er_frame.grid(row=17, column=1)
er_frame.columnconfigure(0, weight=1)
er_frame.rowconfigure(0, weight=1)
town_shuffle_label = tkinter.Label(er_frame, text="Towns:").grid(row=0, column=0, sticky=tkinter.E)
town_shuffle_checkbox = tkinter.Checkbutton(er_frame, variable=town_shuffle, onvalue=1, offvalue=0, command=er_maybe_force_coupled).grid(row=0, column=1)
dungeon_shuffle_label = tkinter.Label(er_frame, text="Dungeons:").grid(row=1, column=0, sticky=tkinter.E)
dungeon_shuffle_checkbox = tkinter.Checkbutton(er_frame, variable=dungeon_shuffle, onvalue=1, offvalue=0, command=er_maybe_force_coupled).grid(row=1, column=1)
coupled_exits_label = tkinter.Label(er_frame, text="Coupled:").grid(row=0, column=3, rowspan=2, sticky=tkinter.E)
coupled_exits_checkbox = tkinter.Checkbutton(er_frame, variable=coupled_exits, onvalue=1, offvalue=0)
coupled_exits_checkbox.grid(row=0, column=4, rowspan=2, sticky=tkinter.W)
coupled_exits_checkbox.config(state='disabled')

orb_rando_menu = tkinter.OptionMenu(mainframe, orb_rando, *orb_rando_choices).grid(row=20, column=1)
darkrooms_frame = tkinter.Frame(mainframe, borderwidth=1)
darkrooms_frame.grid(row=22, column=1)
darkrooms_level_menu = tkinter.OptionMenu(darkrooms_frame, darkrooms_level, *darkrooms_level_choices, command=dr_maybe_set_cursed).pack(side='left')
darkrooms_label = tkinter.Label(darkrooms_frame, text="Cursed:").pack(side='left')
darkrooms_cursed_checkbox = tkinter.Checkbutton(darkrooms_frame, variable=darkrooms_cursed, onvalue=1, offvalue=0)
darkrooms_cursed_checkbox.pack(side='left')

devtools_frame = tkinter.Frame(mainframe, borderwidth=1, relief='sunken')
devtools_frame.grid(row=50, column=1)
devtools_frame.columnconfigure(0, weight=1)
devtools_frame.rowconfigure(0, weight=1)
printlevel_label = tkinter.Label(devtools_frame, text="Console:").grid(row=0, column=0, sticky=tkinter.E)
printlevel_menu = tkinter.OptionMenu(devtools_frame, printlevel, *printlevel_choices).grid(row=0, column=1, columnspan=4, sticky=tkinter.W)
break_on_error_label = tkinter.Label(devtools_frame, text="Break on Error:").grid(row=1, column=0, sticky=tkinter.E)
break_on_error_checkbox = tkinter.Checkbutton(devtools_frame, variable=break_on_error, onvalue=1, offvalue=0).grid(row=1, column=1)
break_on_init_label = tkinter.Label(devtools_frame, text="Break on Init:").grid(row=1, column=3, sticky=tkinter.E)
break_on_init_checkbox = tkinter.Checkbutton(devtools_frame, variable=break_on_init, onvalue=1, offvalue=0).grid(row=1, column=4)
ingame_debug_label = tkinter.Label(devtools_frame, text="In-Game Debug:").grid(row=2, column=0, sticky=tkinter.E)
ingame_debug_checkbox = tkinter.Checkbutton(devtools_frame, variable=ingame_debug, onvalue=1, offvalue=0).grid(row=2, column=1)
do_profile_label = tkinter.Label(devtools_frame, text="Profile:").grid(row=2, column=3, sticky=tkinter.E)
do_profile_checkbox = tkinter.Checkbutton(devtools_frame, variable=do_profile, onvalue=1, offvalue=0).grid(row=2, column=4)

tkinter.Button(mainframe, text='Browse...', command=find_ROM).grid(row=0, column=2)
tkinter.Button(seed_frame, text='Random Seed', command=generate_seed).pack(side='left')
tkinter.Button(mainframe, text='Generate ROM', command=generate_ROM).grid(row=1, column=2)

tkinter.Button(mainframe, text='?', command=diff_help).grid(row=2, column=2)
tkinter.Button(mainframe, text='?', command=logic_help).grid(row=3, column=2)
tkinter.Button(mainframe, text='?', command=goal_help).grid(row=4, column=2)
tkinter.Button(mainframe, text='?', command=start_help).grid(row=6, column=2)
tkinter.Button(mainframe, text='?', command=variant_help).grid(row=7, column=2)
tkinter.Button(mainframe, text='?', command=enemizer_help).grid(row=9, column=2)
tkinter.Button(mainframe, text='?', command=overworld_shuffle_help).grid(row=16, column=2)
tkinter.Button(mainframe, text='?', command=entrance_shuffle_help).grid(row=17, column=2)
tkinter.Button(mainframe, text='?', command=orb_rando_help).grid(row=20, column=2)
tkinter.Button(mainframe, text='?', command=darkrooms_help).grid(row=22, column=2)

root.mainloop()
