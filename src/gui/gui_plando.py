import json
import os
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
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
        if statue_req.get() == "Player Choice":
            return StatueReq.PLAYER_CHOICE
        else:
            return StatueReq.GAME_CHOICE

    def get_boss_shuffle():
        if boss_order.get() == "Vanilla":
            return False
        else:
            return True

    def get_overworld_shuffle():
        if ow_shuffle.get() == "Vanilla":
            return False
        else:
            return True

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
        s = start_loc.get()
        if s == "South Cape":
            return StartLocation.SOUTH_CAPE
        else:
            return StartLocation.UNSAFE

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

    def is_integer(val):
        try:
            float(val)
        except:
            return False
        return float(val).is_integer()

    def validate_settings():
        # Check for non-integer seed
        if not seed_str.isdigit():
            tk.messagebox.showinfo("ERROR", "Please enter or generate a valid seed")
            return False

        # Check Kara location
        if not kara_loc.get():
            tk.messagebox.showinfo("ERROR", "Please set Kara's location")
            return False

        # Check boss order
        if boss_order.get() == "Custom":
            bosses = boss_choices[:]
            bosses.remove("")
            try:
                bosses.remove(boss1.get())
                bosses.remove(boss2.get())
                bosses.remove(boss3.get())
                bosses.remove(boss4.get())
                bosses.remove(boss5.get())
                bosses.remove(boss6.get())
                bosses.remove(boss7.get())
            except:
                tk.messagebox.showinfo("ERROR", "Invalid boss configuration")
                return False

        # Check start location
        if start_loc.get()[0] == "-":
            tk.messagebox.showinfo("ERROR", "Please choose a valid start location")
            return False

        # Check overworld configuration
        regions = ow_choices_all[:]
        if ow_shuffle.get() == "Custom":
            try:
                regions.remove(ow_sw1.get())
                regions.remove(ow_sw2.get())
                regions.remove(ow_sw3.get())
                regions.remove(ow_sw4.get())
                regions.remove(ow_sw5.get())
                regions.remove(ow_se1.get())
                regions.remove(ow_se2.get())
                regions.remove(ow_se3.get())
                regions.remove(ow_se4.get())
                regions.remove(ow_se5.get())
                regions.remove(ow_ne1.get())
                regions.remove(ow_ne2.get())
                regions.remove(ow_ne3.get())
                regions.remove(ow_n1.get())
                regions.remove(ow_n2.get())
                regions.remove(ow_n3.get())
                regions.remove(ow_n4.get())
                regions.remove(ow_nw1.get())
                regions.remove(ow_nw2.get())
            except:
                tk.messagebox.showinfo("ERROR", "Invalid overworld configuration")
                return False

        # Check jeweler rewards
        if (not is_integer(gem1.get()) or not is_integer(gem2.get()) or not is_integer(gem3.get()) or not is_integer(gem4.get()) or
                not is_integer(gem5.get()) or not is_integer(gem6.get()) or not is_integer(gem7.get())):
            tk.messagebox.showinfo("ERROR", "Invalid jeweler reward amounts")
            return False
        if not (0 < float(gem1.get()) < float(gem2.get()) < float(gem3.get()) < float(gem4.get()) < float(gem5.get()) < float(gem6.get()) < float(gem7.get()) <= 50):
            tk.messagebox.showinfo("ERROR", "Jeweler rewards must be in ascending order between 1 and 50")
            return False

        # Check ability placement
        try:
            ability_name_list = ability_choices[:]
            ability_name_list.remove("-- WILL ONLY --")
            ability_name_list.remove("-- FREEDAN OKAY --")
            if ability1.get():
                ability_name_list.remove(ability1.get())
            if ability2.get():
                ability_name_list.remove(ability2.get())
            if ability3.get():
                ability_name_list.remove(ability3.get())
            if ability4.get():
                ability_name_list.remove(ability4.get())
            if ability5.get():
                ability_name_list.remove(ability5.get())
            if ability6.get():
                ability_name_list.remove(ability6.get())
        except:
            tk.messagebox.showinfo("ERROR", "Invalid ability location(s)")
            return False

        # Check item placement
        this_item = ""
        try:
            item_name_list = item_names_all[:]
            for var in item_vars:
                this_item = var.get()
                if this_item:
                    item_name_list.remove(this_item)
        except:
            tk.messagebox.showinfo("ERROR", "Too many items: " + this_item)
            return False

        # Check item

        return True

    def generate_json():
        plando_json = '{'

        # Start location
        plando_json += '"start_location": "' + start_loc.get() + '"'

        # Statue retuirement
        if goal.get() != "Red Jewel Hunt":
            plando_json += ', "statues_required": '
            if statue_req.get() == "Player Choice":
                plando_json += statues.get()
            else:
                statue_list = []
                if st1.get():
                    statue_list.append('1')
                if st2.get():
                    statue_list.append('2')
                if st3.get():
                    statue_list.append('3')
                if st4.get():
                    statue_list.append('4')
                if st5.get():
                    statue_list.append('5')
                if st6.get():
                    statue_list.append('6')
                plando_json += '[' + ','.join(statue_list) + ']'

        # Boss order
        if boss_order.get() == "Custom":
            plando_json += ', "boss_order":'
            boss_list = []
            boss_list_txt = [boss1.get(),boss2.get(),boss3.get(),boss4.get(),boss5.get(),boss6.get(),boss7.get()]
            while boss_list_txt:
                boss = boss_list_txt.pop(0)
                if boss == "Castoth":
                    boss_list.append('1')
                elif boss == "Viper":
                    boss_list.append('2')
                elif boss == "Vampires":
                    boss_list.append('3')
                elif boss == "Sand Fanger":
                    boss_list.append('4')
                elif boss == "Mummy Queen":
                    boss_list.append('5')
                elif boss == "Babel Queen":
                    boss_list.append('6')
                elif boss == "Solid Arm":
                    boss_list.append('7')

            plando_json += '[' + ','.join(boss_list) + ']'

        # Kara location
        plando_json += ', "kara_location": "' + kara_loc.get() + '"'

        # Jeweler rewards
        plando_json += ', "jeweler_amounts": [' + ','.join([gem1.get(),gem2.get(),gem3.get(),gem4.get(),gem5.get(),gem6.get(),gem7.get()]) + ']'

        # Items and abilities
        plando_json += ', "items": ['
        if ability1.get():
            plando_json += '{"location": "' + ability1.get() + '", "name": "Psycho Dash"}, '
        if ability2.get():
            plando_json += '{"location": "' + ability2.get() + '", "name": "Psycho Slider"}, '
        if ability3.get():
            plando_json += '{"location": "' + ability3.get() + '", "name": "Spin Dash"}, '
        if ability4.get():
            plando_json += '{"location": "' + ability4.get() + '", "name": "Dark Friar"}, '
        if ability5.get():
            plando_json += '{"location": "' + ability5.get() + '", "name": "Aura Barrier"}, '
        if ability6.get():
            plando_json += '{"location": "' + ability6.get() + '", "name": "Earthquaker"}, '

        for i in range(len(loc_names)):
            item_var = item_vars[i].get()
            if item_var:
                plando_json += '{"location": "' + loc_names[i] + '", "name": "' + item_var + '"}, '

        plando_json = plando_json[:-2]
        plando_json += ']'

        # Overworld shuffle
        if ow_shuffle.get() == "Custom":
            plando_json += ', "overworld_entrances": [{"region": "' + ow_sw1.get() + '", "continent": "SW Continent"}'
            plando_json += ', {"region": "' + ow_sw2.get() + '", "continent": "SW Continent"}'
            plando_json += ', {"region": "' + ow_sw3.get() + '", "continent": "SW Continent"}'
            plando_json += ', {"region": "' + ow_sw4.get() + '", "continent": "SW Continent"}'
            plando_json += ', {"region": "' + ow_sw5.get() + '", "continent": "SW Continent"}'
            plando_json += ', {"region": "' + ow_se1.get() + '", "continent": "SE Continent"}'
            plando_json += ', {"region": "' + ow_se2.get() + '", "continent": "SE Continent"}'
            plando_json += ', {"region": "' + ow_se3.get() + '", "continent": "SE Continent"}'
            plando_json += ', {"region": "' + ow_se4.get() + '", "continent": "SE Continent"}'
            plando_json += ', {"region": "' + ow_se5.get() + '", "continent": "SE Continent"}'
            plando_json += ', {"region": "' + ow_ne1.get() + '", "continent": "NE Continent"}'
            plando_json += ', {"region": "' + ow_ne2.get() + '", "continent": "NE Continent"}'
            plando_json += ', {"region": "' + ow_ne3.get() + '", "continent": "NE Continent"}'
            plando_json += ', {"region": "' + ow_n1.get() + '", "continent": "N Continent"}'
            plando_json += ', {"region": "' + ow_n2.get() + '", "continent": "N Continent"}'
            plando_json += ', {"region": "' + ow_n3.get() + '", "continent": "N Continent"}'
            plando_json += ', {"region": "' + ow_n4.get() + '", "continent": "N Continent"}'
            plando_json += ', {"region": "' + ow_nw1.get() + '", "continent": "NW Continent"}'
            plando_json += ', {"region": "' + ow_nw2.get() + '", "continent": "NW Continent"}]'

        # Wrap it up
        plando_json += '}'

        #tk.messagebox.showinfo("JSON", plando_json)

        return plando_json

    # Generate ROM code
    if not validate_settings():
        tk.messagebox.showinfo("ERROR", "Could not validate settings, ROM not generated")
        return

    plando_json = generate_json()
    if not plando_json:
        tk.messagebox.showinfo("ERROR", "Could not generate JSON input, ROM not generated")
        return

    try:
        seed_int = int(seed_str)
        #settings = RandomizerData(seed_int, get_difficulty(), get_goal(), get_logic(), statues.get(), get_statue_req(), get_enemizer(), get_start_location(),
        #    firebird.get(), ohko.get(), red_jewel_madness.get(), glitches.get(), boss_shuffle.get(), open_mode.get(), z3_mode.get(),
        #    overworld_shuffle.get(), get_entrance_shuffle(), race_mode_toggle.get(), fluteless.get(), get_sprite(), False, plando_json)
        settings = RandomizerData(seed_int, get_difficulty(), get_goal(), get_logic(), statues.get(), get_statue_req(), get_enemizer(), get_start_location(),
            firebird.get(), ohko.get(), red_jewel_madness.get(), glitches.get(), get_boss_shuffle(), open_mode.get(), z3_mode.get(),
            get_overworld_shuffle(), get_entrance_shuffle(), False, fluteless.get(), get_sprite(), False, plando_json)

        filename = plando_name.get().replace(" ", "") + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        rom_filename = filename + ".sfc"
        spoiler_filename = filename + ".json"
        #graph_viz_filename = generate_filename(settings, "png")

        randomizer = Randomizer(rompath)

        patch = randomizer.generate_rom(rom_filename, settings)

        write_patch(patch, rompath, rom_filename, settings)
        spoiler = randomizer.generate_spoiler()
        write_spoiler(spoiler, spoiler_filename, rompath)
        #if graph_viz_toggle.get():
        #    graph_viz = randomizer.generate_graph_visualization()
        #    write_graph_viz(graph_viz, graph_viz_filename, rompath)

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

w = World(RandomizerData())

item_list = w.list_item_pool(1)
item_names = []
item_names_all = []
for item in item_list:
    item_name = w.item_pool[item][3].strip()
    item_names_all.append(item_name)
    if item_name not in item_names:
        item_names.append(item_name)

ability_list = w.list_item_pool(2)
ability_names = []
for ability in ability_list:
    ability_name = w.item_pool[ability][3].strip()
    if ability_name not in ability_names:
        ability_names.append(ability_name)

loc_list = w.list_item_locations(1)
loc_names = []
for loc in loc_list:
    loc_name = w.item_locations[loc][9].strip()
    if loc_name not in loc_names:
        loc_names.append(loc_name)

ds_list = w.list_item_locations(2)
ds_will = []
ds_freedan = []
for ds in ds_list:
    ds_name = w.item_locations[ds][9].strip()
    if w.item_locations[ds][4]:
        if ds_name not in ds_will:
            ds_will.append(ds_name)
    else:
        if ds_name not in ds_freedan:
            ds_freedan.append(ds_name)

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

boss_order = tk.StringVar(root)
boss_order_choices = ["Vanilla", "Custom"]
boss_order.set("Vanilla")

boss_choices = ["","Castoth", "Viper", "Vampires", "Sand Fanger", "Mummy Queen", "Babel Queen", "Solid Arm"]

boss1 = tk.StringVar(root)
boss1.set("")
boss2 = tk.StringVar(root)
boss2.set("")
boss3 = tk.StringVar(root)
boss3.set("")
boss4 = tk.StringVar(root)
boss4.set("")
boss5 = tk.StringVar(root)
boss5.set("")
boss6 = tk.StringVar(root)
boss6.set("")
boss7 = tk.StringVar(root)
boss7.set("")

kara_loc = tk.StringVar(root)
kara_loc_choices = ["","Edward's Castle","Diamond Mine","Angel Dungeon","Mt. Kress","Ankor Wat"]
kara_loc.set("")

start_loc = tk.StringVar(root)
safe_loc_choices = ["-- SAFE --"]
unsafe_loc_choices = ["-- UNSAFE --"]
for ds in ds_list:
    if w.item_locations[ds][6] == "Safe":
        safe_loc_choices.append(w.item_locations[ds][9].strip())
    elif w.item_locations[ds][6] == "Unsafe":
        unsafe_loc_choices.append(w.item_locations[ds][9].strip())

#safe_loc_choices = [
#    "-- SAFE --",
#    "South Cape: Dark Space",
#    "Itory Village: Dark Space",
#    "Freejia: Dark Space",
#    "Sky Garden: Dark Space (Foyer)",
#    "Seaside Palace: Dark Space",
#    "Angel Village: Dark Space",
#    "Watermia: Dark Space",
#    "Euro: Dark Space",
#    "Natives' Village: Dark Space",
#    "Dao: Dark Space",
#    "Babel: Dark Space Top"
#]
#unsafe_loc_choices = [
#    "-- UNSAFE --",
#    "Underground Tunnel: Dark Space",
#    "Inca Ruins: Dark Space 1",
#    "Inca Ruins: Dark Space 2",
#    "Diamond Mine: Appearing Dark Space",
#    "Diamond Mine: Dark Space at Wall",
#    "Diamond Mine: Dark Space behind Wall",
#    "Sky Garden: Dark Space (SE)",
#    "Sky Garden: Dark Space (SW)",
#    "Sky Garden: Dark Space (NW)",
#    "Great Wall: Archer Dark Space",
#    "Great Wall: Platform Dark Space",
#    "Great Wall: Appearing Dark Space",
#    "Mt. Temple: Dark Space 1",
#    "Mt. Temple: Dark Space 2",
#    "Mt. Temple: Dark Space 3",
#    "Ankor Wat: Garden Dark Space",
#    "Ankor Wat: Drop Down Dark Space",
#    "Pyramid: Dark Space Bottom",
#    "Babel: Dark Space Bottom"
#]
start_loc_choices = safe_loc_choices+unsafe_loc_choices
start_loc.set("South Cape")

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

ow_shuffle = tk.StringVar(root)
ow_shuffle_choices = ["Vanilla", "Custom"]
ow_shuffle.set("Vanilla")

ow_choices_all = []
for region in w.overworld_menus:
    ow_choices_all.append(w.overworld_menus[region][8].strip())
#ow_choices_all = [
#    "South Cape",
#    "Edward's",
#    "Itory",
#    "Moon Tribe",
#    "Inca",
#    "Diamond Coast",
#    "Freejia",
#    "Diamond Mine",
#    "Neil's",
#    "Nazca",
#    "Angel Village",
#    "Watermia",
#    "Great Wall",
#    "Euro",
#    "Mt. Temple",
#    "Native's Village",
#    "Ankor Wat",
#    "Dao",
#    "Pyramid"
#]
ow_choices = ow_choices_all[:]

ow_sw1 = tk.StringVar(root)
ow_sw1.set("")
ow_sw2 = tk.StringVar(root)
ow_sw2.set("")
ow_sw3 = tk.StringVar(root)
ow_sw3.set("")
ow_sw4 = tk.StringVar(root)
ow_sw4.set("")
ow_sw5 = tk.StringVar(root)
ow_sw5.set("")
ow_se1 = tk.StringVar(root)
ow_se1.set("")
ow_se2 = tk.StringVar(root)
ow_se2.set("")
ow_se3 = tk.StringVar(root)
ow_se3.set("")
ow_se4 = tk.StringVar(root)
ow_se4.set("")
ow_se5 = tk.StringVar(root)
ow_se5.set("")
ow_ne1 = tk.StringVar(root)
ow_ne1.set("")
ow_ne2 = tk.StringVar(root)
ow_ne2.set("")
ow_ne3 = tk.StringVar(root)
ow_ne3.set("")
ow_n1 = tk.StringVar(root)
ow_n1.set("")
ow_n2 = tk.StringVar(root)
ow_n2.set("")
ow_n3 = tk.StringVar(root)
ow_n3.set("")
ow_n4 = tk.StringVar(root)
ow_n4.set("")
ow_nw1 = tk.StringVar(root)
ow_nw1.set("")
ow_nw2 = tk.StringVar(root)
ow_nw2.set("")

item_choices = [""] + item_names
ability_choices = ["","-- WILL ONLY --"] + ds_will + ["-- FREEDAN OKAY --"] + ds_freedan

ability1 = tk.StringVar(root)
ability1.set("")
ability2 = tk.StringVar(root)
ability2.set("")
ability3 = tk.StringVar(root)
ability3.set("")
ability4 = tk.StringVar(root)
ability4.set("")
ability5 = tk.StringVar(root)
ability5.set("")
ability6 = tk.StringVar(root)
ability6.set("")

# Create tabs
tabControl = ttk.Notebook(root)
tab1 = ttk.Frame(tabControl)
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)
tab4 = ttk.Frame(tabControl)

tabControl.add(tab1, text ='General')
tabControl.add(tab2, text ='Game Settings')
tabControl.add(tab3, text ='Abilities & Items')
tabControl.add(tab4, text ='Items (cont)')
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

tab3frame = tk.Frame(tab3)
tab3frame.grid(column=2, row=9, sticky=(tk.N, tk.W, tk.E, tk.S))
tab3frame.columnconfigure(0, weight=1)
tab3frame.rowconfigure(0, weight=1)
tab3frame.pack(pady=20, padx=20)

tab4frame = tk.Frame(tab4)
tab4frame.grid(column=2, row=9, sticky=(tk.N, tk.W, tk.E, tk.S))
tab4frame.columnconfigure(0, weight=1)
tab4frame.rowconfigure(0, weight=1)
tab4frame.pack(pady=20, padx=20)

# Tab 1: General
tk.Label(tab1frame, text="ROM File").grid(row=0, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Plando Creator").grid(row=1, column=0, sticky=tk.W)
tk.Label(tab1frame, text="Seed").grid(row=2, column=0, sticky=tk.W)

ROM = tk.Entry(tab1frame, width="40")
ROM.grid(row=0, column=1)
ROM.insert(0,load_ROM())

plando_name = tk.Entry(tab1frame, width="40")
plando_name.grid(row=1, column=1)

seed = tk.Entry(tab1frame)
seed.grid(row=2, column=1)
seed.insert(10, random.randint(0, 999999))

tk.Button(tab1frame, text='Browse...', command=find_ROM).grid(row=0, column=2)
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
#   Setting 1: Statue Requirement
statue_frame1 = tk.Frame(tab2frame)
statue_frame1.pack()
statue_frame2 = tk.Frame(tab2frame)
statue_frame2.pack()

gamechoiceframe = tk.Frame(statue_frame2)
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

playerchoiceframe = tk.Frame(statue_frame2)
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

tk.Label(statue_frame1, text="Statues Required").grid(row=0, column=0, sticky=tk.W)
statue_req_menu = tk.OptionMenu(statue_frame1, statue_req, *statue_req_choices).grid(row=0, column=1, sticky=tk.W)

#   Setting 2: Kara Location
kara_frame = tk.Frame(tab2frame)
kara_frame.pack(pady=15)

tk.Label(kara_frame, text="Kara Location").grid(row=0, column=0, sticky=tk.W)
kara_loc_menu = tk.OptionMenu(kara_frame, kara_loc, *kara_loc_choices).grid(row=0, column=1)

#   Setting 3: Boss Order
boss_frame1 = tk.Frame(tab2frame)
boss_frame1.pack(pady=15)
boss_frame2 = tk.Frame(tab2frame)
boss_frame2.pack()

def refresh_boss():
    boss1_menu['menu'].delete(1,'end')
    boss2_menu['menu'].delete(1,'end')
    boss3_menu['menu'].delete(1,'end')
    boss4_menu['menu'].delete(1,'end')
    boss5_menu['menu'].delete(1,'end')
    boss6_menu['menu'].delete(1,'end')
    boss7_menu['menu'].delete(1,'end')

    new_choices = boss_choices[:]
    if boss1 and boss1 in new_choices:
        new_choices.remove(boss1)
    if boss2 and boss2 in new_choices:
        new_choices.remove(boss2)
    if boss3 and boss3 in new_choices:
        new_choices.remove(boss3)
    if boss4 and boss4 in new_choices:
        new_choices.remove(boss4)
    if boss5 and boss5 in new_choices:
        new_choices.remove(boss5)
    if boss6 and boss6 in new_choices:
        new_choices.remove(boss6)
    if boss7 and boss7 in new_choices:
        new_choices.remove(boss7)

    #for choice in new_choices:
    #    boss1_menu['menu'].add_command(label=choice, command=tk._setit(options, choice))


#boss1.trace_add(['write'], refresh_boss)
#boss2.trace_add(['write'], refresh_boss)
#boss3.trace_add(['write'], refresh_boss)
#boss4.trace_add(['write'], refresh_boss)
#boss5.trace_add(['write'], refresh_boss)
#boss6.trace_add(['write'], refresh_boss)
#boss7.trace_add(['write'], refresh_boss)

boss_order_frame = tk.Frame(boss_frame2)
tk.Label(boss_order_frame, text="Inca").grid(row=0, column=0, sticky=tk.W)
tk.Label(boss_order_frame, text="Sky Garden").grid(row=0, column=1, sticky=tk.W)
tk.Label(boss_order_frame, text="Mu").grid(row=0, column=2, sticky=tk.W)
tk.Label(boss_order_frame, text="Great Wall").grid(row=0, column=3, sticky=tk.W)
tk.Label(boss_order_frame, text="Pyramid").grid(row=0, column=4, sticky=tk.W)
tk.Label(boss_order_frame, text="Babel").grid(row=0, column=5, sticky=tk.W)
tk.Label(boss_order_frame, text="Mansion").grid(row=0, column=6, sticky=tk.W)
boss1_menu = tk.OptionMenu(boss_order_frame, boss1, *boss_choices).grid(row=1, column=0)
boss2_menu = tk.OptionMenu(boss_order_frame, boss2, *boss_choices).grid(row=1, column=1)
boss3_menu = tk.OptionMenu(boss_order_frame, boss3, *boss_choices).grid(row=1, column=2)
boss4_menu = tk.OptionMenu(boss_order_frame, boss4, *boss_choices).grid(row=1, column=3)
boss5_menu = tk.OptionMenu(boss_order_frame, boss5, *boss_choices).grid(row=1, column=4)
boss6_menu = tk.OptionMenu(boss_order_frame, boss6, *boss_choices).grid(row=1, column=5)
boss7_menu = tk.OptionMenu(boss_order_frame, boss7, *boss_choices).grid(row=1, column=6)

def boss_order_toggle(var, index, mode):
    if boss_order.get() == "Vanilla":
        boss_order_frame.pack_forget()
    else:
        boss_order_frame.pack()

boss_order.trace_add(['write'], boss_order_toggle)

tk.Label(boss_frame1, text="Boss Order").grid(row=0, column=0, sticky=tk.W)
boss_menu = tk.OptionMenu(boss_frame1, boss_order, *boss_order_choices).grid(row=0, column=1)

#   Setting 4: Start Location
start_frame = tk.Frame(tab2frame)
start_frame.pack(pady=15)

tk.Label(start_frame, text="Start Location").grid(row=0, column=0, sticky=tk.W)
start_loc_menu = tk.OptionMenu(start_frame, start_loc, *start_loc_choices).grid(row=0, column=1)

#   Setting 5: Overworld Shuffle
ow_frame1 = tk.Frame(tab2frame)
ow_frame1.pack(pady=15)
ow_frame2 = tk.Frame(tab2frame)
ow_frame2.pack()

ow_shuffle_frame = tk.Frame(ow_frame2)
tk.Label(ow_shuffle_frame, text="SW Continent").grid(row=0, column=0, sticky=tk.W)
tk.Label(ow_shuffle_frame, text="SE Continent").grid(row=0, column=1, sticky=tk.W)
tk.Label(ow_shuffle_frame, text="NE Continent").grid(row=0, column=2, sticky=tk.W)
tk.Label(ow_shuffle_frame, text="N Continent").grid(row=0, column=3, sticky=tk.W)
tk.Label(ow_shuffle_frame, text="NW Continent").grid(row=0, column=4, sticky=tk.W)

ow_sw1_menu = tk.OptionMenu(ow_shuffle_frame, ow_sw1, *ow_choices).grid(row=1, column=0)
ow_sw2_menu = tk.OptionMenu(ow_shuffle_frame, ow_sw2, *ow_choices).grid(row=2, column=0)
ow_sw3_menu = tk.OptionMenu(ow_shuffle_frame, ow_sw3, *ow_choices).grid(row=3, column=0)
ow_sw4_menu = tk.OptionMenu(ow_shuffle_frame, ow_sw4, *ow_choices).grid(row=4, column=0)
ow_sw5_menu = tk.OptionMenu(ow_shuffle_frame, ow_sw5, *ow_choices).grid(row=5, column=0)

ow_se1_menu = tk.OptionMenu(ow_shuffle_frame, ow_se1, *ow_choices).grid(row=1, column=1)
ow_se2_menu = tk.OptionMenu(ow_shuffle_frame, ow_se2, *ow_choices).grid(row=2, column=1)
ow_se3_menu = tk.OptionMenu(ow_shuffle_frame, ow_se3, *ow_choices).grid(row=3, column=1)
ow_se4_menu = tk.OptionMenu(ow_shuffle_frame, ow_se4, *ow_choices).grid(row=4, column=1)
ow_se5_menu = tk.OptionMenu(ow_shuffle_frame, ow_se5, *ow_choices).grid(row=5, column=1)

ow_ne1_menu = tk.OptionMenu(ow_shuffle_frame, ow_ne1, *ow_choices).grid(row=1, column=2)
ow_ne2_menu = tk.OptionMenu(ow_shuffle_frame, ow_ne2, *ow_choices).grid(row=2, column=2)
ow_ne3_menu = tk.OptionMenu(ow_shuffle_frame, ow_ne3, *ow_choices).grid(row=3, column=2)

ow_n1_menu = tk.OptionMenu(ow_shuffle_frame, ow_n1, *ow_choices).grid(row=1, column=3)
ow_n2_menu = tk.OptionMenu(ow_shuffle_frame, ow_n2, *ow_choices).grid(row=2, column=3)
ow_n3_menu = tk.OptionMenu(ow_shuffle_frame, ow_n3, *ow_choices).grid(row=3, column=3)
ow_n4_menu = tk.OptionMenu(ow_shuffle_frame, ow_n4, *ow_choices).grid(row=4, column=3)

ow_nw1_menu = tk.OptionMenu(ow_shuffle_frame, ow_nw1, *ow_choices).grid(row=1, column=4)
ow_nw2_menu = tk.OptionMenu(ow_shuffle_frame, ow_nw2, *ow_choices).grid(row=2, column=4)

def ow_toggle(var, index, mode):
    if ow_shuffle.get() == "Vanilla":
        ow_shuffle_frame.pack_forget()
    else:
        ow_shuffle_frame.pack()

ow_shuffle.trace_add(['write'], ow_toggle)

tk.Label(ow_frame1, text="Overworld").grid(row=0, column=0, sticky=tk.W)
ow_shuffle_menu = tk.OptionMenu(ow_frame1, ow_shuffle, *ow_shuffle_choices).grid(row=0, column=1)

#   Setting 6: Jeweler Rewards
gem_frame = tk.Frame(tab2frame)
gem_frame.pack(pady=15)

tk.Label(gem_frame, text="Jeweler Rewards").grid(row=0, column=0, sticky=tk.W)
gem1 = tk.Entry(gem_frame, width="4")
gem1.grid(row=0, column=1)
gem1.insert(0,"3")
gem2 = tk.Entry(gem_frame, width="4")
gem2.grid(row=0, column=2)
gem2.insert(0,"5")
gem3 = tk.Entry(gem_frame, width="4")
gem3.grid(row=0, column=3)
gem3.insert(0,"8")
gem4 = tk.Entry(gem_frame, width="4")
gem4.grid(row=0, column=4)
gem4.insert(0,"12")
gem5 = tk.Entry(gem_frame, width="4")
gem5.grid(row=0, column=5)
gem5.insert(0,"20")
gem6 = tk.Entry(gem_frame, width="4")
gem6.grid(row=0, column=6)
gem6.insert(0,"30")
gem7 = tk.Entry(gem_frame, width="4")
gem7.grid(row=0, column=7)
gem7.insert(0,"50")

# Tabs 3&4: Items and Abilities
item_vars = []
MAX_ROWS = 15
MAX_COLS = 4

tk.Label(tab3frame, text=ability_names[0]).grid(row=0, column=1, sticky=tk.W)
tk.Label(tab3frame, text=ability_names[1]).grid(row=0, column=3, sticky=tk.W)
tk.Label(tab3frame, text=ability_names[2]).grid(row=0, column=5, sticky=tk.W)
tk.Label(tab3frame, text=ability_names[3]).grid(row=1, column=1, sticky=tk.W)
tk.Label(tab3frame, text=ability_names[4]).grid(row=1, column=3, sticky=tk.W)
tk.Label(tab3frame, text=ability_names[5]).grid(row=1, column=5, sticky=tk.W)
ability1_menu = tk.OptionMenu(tab3frame, ability1, *ability_choices).grid(row=0, column=2)
ability2_menu = tk.OptionMenu(tab3frame, ability2, *ability_choices).grid(row=0, column=4)
ability3_menu = tk.OptionMenu(tab3frame, ability3, *ability_choices).grid(row=0, column=6)
ability4_menu = tk.OptionMenu(tab3frame, ability4, *ability_choices).grid(row=1, column=2)
ability5_menu = tk.OptionMenu(tab3frame, ability5, *ability_choices).grid(row=1, column=4)
ability6_menu = tk.OptionMenu(tab3frame, ability6, *ability_choices).grid(row=1, column=6)

for i in range(len(loc_names)):
    item_var = tk.StringVar(root)
    item_vars.append(item_var)
    if i < (MAX_ROWS-2)*MAX_COLS:
        tk.Label(tab3frame, text=loc_names[i]).grid(row=i%(MAX_ROWS-2)+2, column=int(i/(MAX_ROWS-2))*2, sticky=tk.W)
        item_menu = tk.OptionMenu(tab3frame, item_var, *item_choices).grid(row=i%(MAX_ROWS-2)+2, column=int(i/(MAX_ROWS-2))*2+1)
    else:
        tk.Label(tab4frame, text=loc_names[i]).grid(row=(i-(MAX_ROWS-2)*MAX_COLS)%MAX_ROWS, column=int((i-(MAX_ROWS-2)*MAX_COLS)/MAX_ROWS)*2, sticky=tk.W)
        item_menu = tk.OptionMenu(tab4frame, item_var, *item_choices).grid(row=(i-(MAX_ROWS-2)*MAX_COLS)%MAX_ROWS, column=int((i-(MAX_ROWS-2)*MAX_COLS)/MAX_ROWS)*2+1)

# Generate ROM buttom at bottom
tk.Button(root, text='Generate ROM', command=generate_ROM).pack(pady=20, padx=20)

root.mainloop()
