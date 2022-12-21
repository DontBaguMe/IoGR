import json
import os
import tkinter as tk
from tkinter import *
from tkinter import ttk
import random

from randomizer.iogr_rom import generate_filename
from randomizer.models.enums.difficulty import Difficulty
#from randomizer.models.enums.level import Level
from randomizer.models.enums.enemizer import Enemizer
from randomizer.models.enums.goal import Goal
from randomizer.models.enums.statue_req import StatueReq
from randomizer.models.enums.logic import Logic
from randomizer.models.enums.sprites import Sprite
from randomizer.models.enums.entrance_shuffle import EntranceShuffle
from randomizer.models.enums.start_location import StartLocation
from randomizer.iogr_rom import Randomizer, VERSION
from randomizer.models.randomizer_data import RandomizerData
from randomizer.errors import FileNotFoundError, OffsetError
from randomizer.classes import World


def find_ROM():
    ROM.delete(0, tk.END)
    ROM.insert(10, tk.filedialog.askopenfilename())

def find_json():
    plando.delete(0, tk.END)
    plando.insert(10, tk.filedialog.askopenfilename())

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
    seed.delete(0, tk.END)
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
        tk.messagebox.showinfo("ERROR", "Please enter or generate a valid seed")
        return

    try:
        plando_json = open(plando.get(), "rb").read()
    except:
        plando_json = ""

    try:
        seed_int = int(seed_str)
        settings = RandomizerData(seed_int, get_difficulty(), get_goal(), get_logic(), statues.get(), get_statue_req(), get_enemizer(), get_start_location(),
            firebird.get(), ohko.get(), red_jewel_madness.get(), glitches.get(), boss_shuffle.get(), open_mode.get(), z3_mode.get(),
            overworld_shuffle.get(), get_entrance_shuffle(), race_mode_toggle.get(), fluteless.get(), get_sprite(), False, plando_json)

        rom_filename = generate_filename(settings, "sfc")
        spoiler_filename = generate_filename(settings, "json")
        graph_viz_filename = generate_filename(settings, "png")

        randomizer = Randomizer(rompath)

        patch = randomizer.generate_rom(rom_filename, settings)

        write_patch(patch, rompath, rom_filename, settings)
        if not race_mode_toggle.get():
            spoiler = randomizer.generate_spoiler()
            write_spoiler(spoiler, spoiler_filename, rompath)
        if graph_viz_toggle.get():
            graph_viz = randomizer.generate_graph_visualization()
            write_graph_viz(graph_viz, graph_viz_filename, rompath)

        tk.messagebox.showinfo("Success!", rom_filename + " has been successfully created!")
    except OffsetError:
        tk.messagebox.showerror("ERROR", "This randomizer is only compatible with the (US) version of Illusion of Gaia")
    except FileNotFoundError:
        tk.messagebox.showerror("ERROR", "ROM file does not exist")
    except Exception as e:
        tk.messagebox.showerror("ERROR", e)


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


def write_patch(patch, rom_path, filename, settings):
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

    # Custom sprites
    if settings.sprite != Sprite.WILL:
        sprite_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"randomizer","randomizer","bin","plugins","sprites",settings.sprite.value,"")
        for binfile in os.listdir(sprite_dir):
            if binfile.endswith(".bin"):
                f = open(os.path.join(sprite_dir,binfile), "rb")
                randomized.seek(int(binfile.partition(".")[0], 16))
                randomized.write(f.read())
                f.close

    # Fluteless sprite work
    if settings.fluteless:
        flute_addrs = [
            [0x1a8540,0x60],
            [0x1a8740,0x60],
            [0x1aa120,0x40],
            [0x1aa560,0x20],
            [0x1aa720,0x60],
            [0x1aa8e0,0x80],
            [0x1aab00,0x20],
            [0x1aac60,0x40],
            [0x1aae60,0x40],
            [0x1ab400,0x80],
            [0x1ab600,0x80],
            [0x1ab800,0x40],
            [0x1aba00,0x40]
        ]
        for [addr,l] in flute_addrs:
            randomized.seek(addr)
            randomized.write(b"\x00"*l)

    randomized.close()


root = tk.Tk()
root.title("Illusion of Gaia Randomizer (v." + VERSION + ")")
# if os.name == 'nt':
#     root.wm_iconbitmap('iogr.ico')
# else:
#     root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=os.path.join(".",'iogr.png')))

# Variables
difficulty = tk.StringVar(root)
diff_choices = ["Easy", "Normal", "Hard", "Extreme"]
difficulty.set("Normal")

goal = tk.StringVar(root)
goal_choices = ["Dark Gaia", "Apocalypse Gaia", "Random Gaia", "Red Jewel Hunt"]
goal.set("Dark Gaia")

logic = tk.StringVar(root)
logic_choices = ["Completable", "Beatable", "Chaos"]
logic.set("Completable")

firebird = tk.IntVar(root)
firebird.set(0)

start = tk.StringVar(root)
start_choices = ["South Cape", "Safe", "Unsafe", "Forced Unsafe"]
start.set("South Cape")

ohko = tk.IntVar(root)
ohko.set(0)

red_jewel_madness = tk.IntVar(root)
red_jewel_madness.set(0)

glitches = tk.IntVar(root)
glitches.set(0)

open_mode = tk.IntVar(root)
open_mode.set(0)

z3_mode = tk.IntVar(root)
z3_mode.set(0)

entrance_shuffle = tk.StringVar(root)
entrance_shuffle_choices = ["None", "Coupled", "Uncoupled"]
entrance_shuffle.set("None")

race_mode_toggle = tk.IntVar(root)
race_mode_toggle.set(0)

fluteless = tk.IntVar(root)
fluteless.set(0)

enemizer = tk.StringVar(root)
enemizer_choices = ["None", "Limited", "Balanced", "Full", "Insane"]
enemizer.set("None")

sprite = tk.StringVar(root)
sprite_choices = ["Will", "Bagu", "Invisible"]#, "Freet", "Solar", "Sye"]
sprite.set("Will")

statue_req = tk.StringVar(root)
statue_req_choices = ["Game Choice", "Player Choice"]
statue_req.set("Game Choice")

statues = tk.StringVar(root)
statue_choices = ["0", "1", "2", "3", "4", "5", "6"]
statues.set("4")

st1 = tk.IntVar(root)
st1.set(0)
st2 = tk.IntVar(root)
st2.set(0)
st3 = tk.IntVar(root)
st3.set(0)
st4 = tk.IntVar(root)
st4.set(0)
st5 = tk.IntVar(root)
st5.set(0)
st6 = tk.IntVar(root)
st6.set(0)

# Create tabs
tabControl = ttk.Notebook(root)
tab1 = ttk.Frame(tabControl)
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)

tabControl.add(tab1, text ='1. General')
tabControl.add(tab2, text ='2. Game Settings')
tabControl.add(tab3, text ='3. Items')
tabControl.pack(expand = 1, fill ="both")

tab1frame = tk.Frame(tab1)
tab1frame.grid(column=2, row=9, sticky=(tk.N, tk.W, tk.E, tk.S))
tab1frame.columnconfigure(0, weight=1)
tab1frame.rowconfigure(0, weight=1)
tab1frame.pack(pady=20, padx=20)

tab2frame = tk.Frame(tab2)
tab2frame.grid(column=2, row=9, sticky=(tk.N, tk.W, tk.E, tk.S))
tab2frame.columnconfigure(0, weight=1)
tab2frame.rowconfigure(0, weight=1)
tab2frame.pack(pady=20, padx=20)

# Tab 1: General
tk.Label(tab1frame, text="ROM File").grid(row=0, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Plando JSON").grid(row=1, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Seed").grid(row=2, column=0, sticky=tk.W)

ROM = tk.Entry(tab1frame, width="40")
ROM.grid(row=0, column=1)
ROM.insert(0,load_ROM())

plando = tk.Entry(tab1frame, width="40")
plando.grid(row=1, column=1)

seed = tk.Entry(tab1frame)
seed.grid(row=2, column=1)
seed.insert(10, random.randint(0, 999999))

tk.Button(tab1frame, text='Browse...', command=find_ROM).grid(row=0, column=2)
tk.Button(tab1frame, text='Browse...', command=find_json).grid(row=1, column=2)
tk.Button(tab1frame, text='Generate Seed', command=generate_seed).grid(row=2, column=2)

tk.Label(tab1frame, text="Difficulty").grid(row=3, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Goal").grid(row=4, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Logic").grid(row=5, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Enemizer (beta)").grid(row=6, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Entrance Shuffle").grid(row=7, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Sprite").grid(row=8, column=0, sticky=tk.W)

diff_menu = tk.OptionMenu(tab1frame, difficulty, *diff_choices).grid(row=3, column=1)
goal_menu = tk.OptionMenu(tab1frame, goal, *goal_choices).grid(row=4, column=1)
logic_menu = tk.OptionMenu(tab1frame, logic, *logic_choices).grid(row=5, column=1)
enemizer_menu = tk.OptionMenu(tab1frame, enemizer, *enemizer_choices).grid(row=6, column=1)
entrance_shuffle_menu = tk.OptionMenu(tab1frame, entrance_shuffle, *entrance_shuffle_choices).grid(row=7, column=1)
sprite_menu = tk.OptionMenu(tab1frame, sprite, *sprite_choices).grid(row=8, column=1)

tk.Label(tab1frame, text="Early Firebird").grid(row=3, column=2, sticky=tk.W)
tk.Label(tab1frame, text="One Hit KO").grid(row=4, column=2, sticky=tk.W)
tk.Label(tab1frame, text="Red Jewel Madness").grid(row=5, column=2, sticky=tk.W)
tk.Label(tab1frame, text="Allow Glitches").grid(row=6, column=2, sticky=tk.W)
tk.Label(tab1frame, text="Open Mode").grid(row=7, column=2, sticky=tk.W)
tk.Label(tab1frame, text="Z3 Mode").grid(row=8, column=2, sticky=tk.W)
tk.Label(tab1frame, text="Fluteless").grid(row=9, column=2, sticky=tk.W)

firebird_checkbox = tk.Checkbutton(tab1frame, variable=firebird, onvalue=1, offvalue=0).grid(row=3, column=3)
ohko_checkbox = tk.Checkbutton(tab1frame, variable=ohko, onvalue=1, offvalue=0).grid(row=4, column=3)
rjm_checkbox = tk.Checkbutton(tab1frame, variable=red_jewel_madness, onvalue=1, offvalue=0).grid(row=5, column=3)
glitches_checkbox = tk.Checkbutton(tab1frame, variable=glitches, onvalue=1, offvalue=0).grid(row=6, column=3)
open_mode_checkbox = tk.Checkbutton(tab1frame, variable=open_mode, onvalue=1, offvalue=0).grid(row=7, column=3)
z3_mode_checkbox = tk.Checkbutton(tab1frame, variable=z3_mode, onvalue=1, offvalue=0).grid(row=8, column=3)
fluteless_checkbox = tk.Checkbutton(tab1frame, variable=fluteless, onvalue=1, offvalue=0).grid(row=9, column=3)

# Tab 2: Game Settings
gamechoiceframe = tk.Frame(tab2)
tk.Label(gamechoiceframe, text="1").grid(row=0, column=0, sticky=tk.W)
tk.Label(gamechoiceframe, text="2").grid(row=0, column=2, sticky=tk.W)
tk.Label(gamechoiceframe, text="3").grid(row=0, column=4, sticky=tk.W)
tk.Label(gamechoiceframe, text="4").grid(row=0, column=6, sticky=tk.W)
tk.Label(gamechoiceframe, text="5").grid(row=0, column=8, sticky=tk.W)
tk.Label(gamechoiceframe, text="6").grid(row=0, column=10, sticky=tk.W)
st1_checkbox = tk.Checkbutton(gamechoiceframe, variable=st1, onvalue=1, offvalue=0).grid(row=0, column=1)
st2_checkbox = tk.Checkbutton(gamechoiceframe, variable=st2, onvalue=1, offvalue=0).grid(row=0, column=3)
st3_checkbox = tk.Checkbutton(gamechoiceframe, variable=st3, onvalue=1, offvalue=0).grid(row=0, column=5)
st4_checkbox = tk.Checkbutton(gamechoiceframe, variable=st4, onvalue=1, offvalue=0).grid(row=0, column=7)
st5_checkbox = tk.Checkbutton(gamechoiceframe, variable=st5, onvalue=1, offvalue=0).grid(row=0, column=9)
st6_checkbox = tk.Checkbutton(gamechoiceframe, variable=st6, onvalue=1, offvalue=0).grid(row=0, column=11)

playerchoiceframe = tk.Frame(tab2)
tk.Label(playerchoiceframe, text="# statues").grid(row=0, column=0, sticky=tk.W)
statues_menu = tk.OptionMenu(playerchoiceframe, statues, *statue_choices).grid(row=0, column=1)

def statue_req_toggle(var, index, mode):
    if statue_req.get() == "Player Choice":
        gamechoiceframe.pack_forget()
        playerchoiceframe.pack()
    else:
        playerchoiceframe.pack_forget()
        gamechoiceframe.pack()

statue_req.trace_add(['read','write'], statue_req_toggle)
tk.Label(tab2frame, text="Statues Required").grid(row=0, column=0, sticky=tk.W)

statue_req_menu = tk.OptionMenu(tab2frame, statue_req, *statue_req_choices).grid(row=0, column=1)
#tk.Button(root, text=statue_req, command=statue_req_toggle).grid(row=0, column=1)




    #tk.Label(tab2frame, text="2").grid(row=1, column=0)#, sticky=tk.W)

# Generate ROM buttom at bottom
tk.Button(root, text='Generate ROM', command=generate_ROM).pack(pady=20, padx=20)

root.mainloop()
