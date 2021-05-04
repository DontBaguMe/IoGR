import json
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import random

from randomizer.iogr_rom import generate_filename
from randomizer.models.enums.difficulty import Difficulty
#from randomizer.models.enums.level import Level
from randomizer.models.enums.enemizer import Enemizer
from randomizer.models.enums.goal import Goal
from randomizer.models.enums.statue_req import StatueReq
from randomizer.models.enums.logic import Logic
#from randomizer.models.enums.sprites import Sprite
from randomizer.models.enums.entrance_shuffle import EntranceShuffle
from randomizer.models.enums.start_location import StartLocation
from randomizer.iogr_rom import Randomizer, VERSION
from randomizer.models.randomizer_data import RandomizerData
from randomizer.errors import FileNotFoundError, OffsetError


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

#    def get_level():
#        l = level.get()
#        if l == "Beginner":
#            return Level.BEGINNER
#        if l == "Intermediate":
#            return Level.INTERMEDIATE
#        if l == "Advanced":
#            return Level.ADVANCED
#        if l == "Expert":
#            return Level.EXPERT

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

    if not seed_str.isdigit():
        tkinter.messagebox.showinfo("ERROR", "Please enter or generate a valid seed")
        return

    try:
        seed_int = int(seed_str)
        settings = RandomizerData(seed_int, get_difficulty(), get_goal(), get_logic(), statues.get(), get_statue_req(), get_enemizer(), get_start_location(),
            firebird.get(), ohko.get(), red_jewel_madness.get(), glitches.get(), boss_shuffle.get(), open_mode.get(), z3_mode.get(),
            overworld_shuffle.get(), get_entrance_shuffle(), race_mode_toggle.get())#, get_level(), get_sprite())

        rom_filename = generate_filename(settings, "sfc")
        spoiler_filename = generate_filename(settings, "json")
        graph_viz_filename = generate_filename(settings, "png")

        randomizer = Randomizer(rompath)

        patch = randomizer.generate_rom(rom_filename, settings)

        write_patch(patch, rompath, rom_filename)
        if not race_mode_toggle.get():
            spoiler = randomizer.generate_spoiler()
            write_spoiler(spoiler, spoiler_filename, rompath)
        if graph_viz_toggle.get():
            graph_viz = randomizer.generate_graph_visualization()
            write_graph_viz(graph_viz, graph_viz_filename, rompath)

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


def write_graph_viz(graph_viz, filename, rom_path):
    import os
    if "Graphviz" in os.environ['PATH']:
        graph_viz.format = 'png'
        graph_viz.render(os.path.dirname(rom_path) + os.path.sep + filename, view="False")


def sort_patch(val):
    return val['index']


def write_patch(patch, rom_path, filename):
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


def diff_help():
    lines = ["Difficulty affects enemy strength as well as stat upgrades available to the player (HP/STR/DEF):", "",
             "EASY:", " - Enemies have 50% STR/DEF and 67% HP compared to Normal", " - Herbs restore HP to full", " - Player upgrades available: 10/7/7 (4 upgrades per boss)", "",
             "NORMAL:", " - Enemy stats roughly mirror a vanilla playthrough", " - Herbs restore 8 HP", " - Player upgrades available: 10/4/4 (3 upgrades per boss)", "",
             "HARD:", " - Enemies have roughly 2x STR/DEF compared to Normal", " - Herbs restore 4 HP", " - Player upgrades available: 8/2/2 (2 upgrades per boss)", "",
             "EXTREME:", " - Enemies have roughly 2x STR/DEF compared to Normal", " - Herbs restore 2 HP, item hints are removed", " - Player upgrades available: 6/0/0 (1 upgrade per boss)"]
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
             "COMPLETABLE:", " - All locations are accessible", " - Freedan abilities will only show up in dungeons", "",
             "BEATABLE:", " - Some non-essential items may be inaccessible", " - Freedan abilities will only show up in dungeons", "",
             "CHAOS:", " - Some non-essential items may be inaccessible", " - Freedan abilities may show up in towns"]
    tkinter.messagebox.showinfo("Logic Modes", "\n".join(lines))


def firebird_help():
    lines = ["Checking this box grants early access to the Firebird attack, when:", " - The Crystal Ring is equipped,", " - Kara is saved from her painting, and",
             " - Player is in Shadow's form."]
    tkinter.messagebox.showinfo("Firebird", "\n".join(lines))


def variant_help():
    lines = ["The following variants are currently available:", "", "OHKO:", " - Player starts with 1 HP", " - All HP upgrades are removed or negated"]
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

def entrance_shuffle_help():
    lines = ["This setting shuffles where doors and other exits take you.", "",
             "COUPLED:", " - Doors and exits act normally, i.e. if you backtrack through an exit you'll return to where you entered", "",
             "UNCOUPLED:", " - Doors and exits send you to different places, depending on which direction you go through them"]
    tkinter.messagebox.showinfo("Start Location", "\n".join(lines))


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

tkinter.Label(mainframe, text="ROM File").grid(row=0, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Seed").grid(row=1, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Difficulty").grid(row=2, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Goal").grid(row=3, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Logic").grid(row=4, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Early Firebird").grid(row=5, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Start Location").grid(row=6, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="One Hit KO").grid(row=7, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Red Jewel Madness").grid(row=8, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Enemizer (beta)").grid(row=9, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Statues").grid(row=10, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Allow Glitches").grid(row=12, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Boss Shuffle").grid(row=13, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Open Mode").grid(row=14, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Z3 Mode").grid(row=15, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Overworld Shuffle").grid(row=16, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Entrance Shuffle").grid(row=17, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Generate graph").grid(row=18, column=0, sticky=tkinter.W)
tkinter.Label(mainframe, text="Race seed").grid(row=19, column=0, sticky=tkinter.W)
#tkinter.Label(mainframe, text="Sprite").grid(row=14, column=0, sticky=tkinter.W)
#tkinter.Label(mainframe, text="Player Level").grid(row=15, column=0, sticky=tkinter.W)

difficulty = tkinter.StringVar(root)
diff_choices = ["Easy", "Normal", "Hard", "Extreme"]
difficulty.set("Normal")

#level = tkinter.StringVar(root)
#level_choices = ["Beginner", "Intermediate", "Advanced", "Expert"]
#level.set("Intermediate")

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

entrance_shuffle = tkinter.StringVar(root)
entrance_shuffle_choices = ["None", "Coupled", "Uncoupled"]
entrance_shuffle.set("None")

graph_viz_toggle = tkinter.IntVar(root)
graph_viz_toggle.set(0)

race_mode_toggle = tkinter.IntVar(root)
race_mode_toggle.set(0)

enemizer = tkinter.StringVar(root)
enemizer_choices = ["None", "Limited", "Balanced", "Full", "Insane"]
enemizer.set("None")

sprite = tkinter.StringVar(root)
sprite_choices = ["Will", "Bagu", "Freet", "Invisible", "Solar", "Sye"]
sprite.set("Will")

statues = tkinter.StringVar(root)
statue_choices = ["0", "1", "2", "3", "4", "5", "6", "Random"]
statues.set("4")

statue_req = tkinter.StringVar(root)
statue_req_choices = ["Game Choice", "Player Choice", "Random Choice"]
statue_req.set("Game Choice")

ROM = tkinter.Entry(mainframe, width="40")
ROM.grid(row=0, column=1)
ROM.insert(0,load_ROM())

seed = tkinter.Entry(mainframe)
seed.grid(row=1, column=1)
seed.insert(10, random.randint(0, 999999))

diff_menu = tkinter.OptionMenu(mainframe, difficulty, *diff_choices).grid(row=2, column=1)
goal_menu = tkinter.OptionMenu(mainframe, goal, *goal_choices).grid(row=3, column=1)
logic_menu = tkinter.OptionMenu(mainframe, logic, *logic_choices).grid(row=4, column=1)
firebird_checkbox = tkinter.Checkbutton(mainframe, variable=firebird, onvalue=1, offvalue=0).grid(row=5, column=1)
start_menu = tkinter.OptionMenu(mainframe, start, *start_choices).grid(row=6, column=1)
ohko_checkbox = tkinter.Checkbutton(mainframe, variable=ohko, onvalue=1, offvalue=0).grid(row=7, column=1)
rjm_checkbox = tkinter.Checkbutton(mainframe, variable=red_jewel_madness, onvalue=1, offvalue=0).grid(row=8, column=1)
enemizer_menu = tkinter.OptionMenu(mainframe, enemizer, *enemizer_choices).grid(row=9, column=1)
statues_menu = tkinter.OptionMenu(mainframe, statues, *statue_choices).grid(row=10, column=1)
statue_req_menu = tkinter.OptionMenu(mainframe, statue_req, *statue_req_choices).grid(row=11, column=1)
glitches_checkbox = tkinter.Checkbutton(mainframe, variable=glitches, onvalue=1, offvalue=0).grid(row=12, column=1)
boss_shuffle_checkbox = tkinter.Checkbutton(mainframe, variable=boss_shuffle, onvalue=1, offvalue=0).grid(row=13, column=1)
open_mode_checkbox = tkinter.Checkbutton(mainframe, variable=open_mode, onvalue=1, offvalue=0).grid(row=14, column=1)
z3_mode_checkbox = tkinter.Checkbutton(mainframe, variable=z3_mode, onvalue=1, offvalue=0).grid(row=15, column=1)
overworld_shuffle_checkbox = tkinter.Checkbutton(mainframe, variable=overworld_shuffle, onvalue=1, offvalue=0).grid(row=16, column=1)
entrance_shuffle_menu = tkinter.OptionMenu(mainframe, entrance_shuffle, *entrance_shuffle_choices).grid(row=17, column=1)
graph_viz_toggle_checkbox = tkinter.Checkbutton(mainframe, variable=graph_viz_toggle, onvalue=1, offvalue=0).grid(row=18, column=1)
race_mode_toggle_checkbox = tkinter.Checkbutton(mainframe, variable=race_mode_toggle, onvalue=1, offvalue=0).grid(row=19, column=1)
#sprite_menu = tkinter.OptionMenu(mainframe, sprite, *sprite_choices).grid(row=14, column=1)
#level_menu = tkinter.OptionMenu(mainframe, level, *level_choices).grid(row=15, column=1)

tkinter.Button(mainframe, text='Browse...', command=find_ROM).grid(row=0, column=2)
tkinter.Button(mainframe, text='Generate Seed', command=generate_seed).grid(row=1, column=2)
tkinter.Button(mainframe, text='Generate ROM', command=generate_ROM).grid(row=10, column=2)

tkinter.Button(mainframe, text='?', command=diff_help).grid(row=2, column=2)
tkinter.Button(mainframe, text='?', command=goal_help).grid(row=3, column=2)
tkinter.Button(mainframe, text='?', command=logic_help).grid(row=4, column=2)
tkinter.Button(mainframe, text='?', command=firebird_help).grid(row=5, column=2)
tkinter.Button(mainframe, text='?', command=start_help).grid(row=6, column=2)
tkinter.Button(mainframe, text='?', command=variant_help).grid(row=7, column=2)
tkinter.Button(mainframe, text='?', command=enemizer_help).grid(row=9, column=2)
tkinter.Button(mainframe, text='?', command=entrance_shuffle_help).grid(row=17, column=2)

root.mainloop()
