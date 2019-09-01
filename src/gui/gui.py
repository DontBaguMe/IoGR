import tkinter
import tkinter.filedialog
import tkinter.messagebox
import os
import random
import sys

# pylint: disable=import-error
import randomizer.classes, randomizer.iogr_rom
from randomizer.errors import FileNotFoundError, OffsetError

VERSION = randomizer.iogr_rom.VERSION

def find_ROM():
    ROM.delete(0, tkinter.END)    
    ROM.insert(10, tkinter.filedialog.askopenfilename())


def generate_seed():
    seed.delete(0, tkinter.END)
    seed.insert(10,random.randint(0,99999999))


def generate_ROM():
    rompath = ROM.get()
    rompath = rompath.lower()
    seed_str = seed.get()

    if not seed_str.isdigit():
        tkinter.messagebox.showinfo("ERROR", "Please enter or generate a valid seed")
        return

    statues_str = statues.get()
    goal_str = goal.get()
    logic_str = logic.get()
    diff_str = difficulty.get()
    start_str = start.get()
    variant_str = variant.get()
    enemizer_str = enemizer.get()

    try:
        seed_int = int(seed_str)
        fb = firebird.get()

        filename = randomizer.iogr_rom.generate_filename(seed_int, diff_str, goal_str, logic_str, statues_str, start_str, variant_str, enemizer_str, fb)
        randomizer.iogr_rom.generate_rom(filename, rompath, seed_int, diff_str, goal_str, logic_str, statues_str, start_str, variant_str, enemizer_str, fb)

        tkinter.messagebox.showinfo("Success!", filename + " has been successfully created!")
    except OffsetError:
        tkinter.messagebox.showinfo("ERROR", "This randomizer is only compatible with the (US) version of Illusion of Gaia")
    except FileNotFoundError:
        tkinter.messagebox.showinfo("ERROR", "ROM file does not exist")
    except Exception as e:
        tkinter.messagebox.showinfo("ERROR", e)

def diff_help():
    lines = []
    lines.append("Difficulty affects enemy strength as well as stat upgrades available to the player (HP/STR/DEF):")
    lines.append("")
    lines.append("EASY:")
    lines.append(" - Enemies have 50% STR/DEF and 67% HP compared to Normal")
    lines.append(" - Herbs restore HP to full")
    lines.append(" - Player upgrades available: 10/7/7 (4 upgrades per boss)")
    lines.append("")
    lines.append("NORMAL:")
    lines.append(" - Enemy stats roughly mirror a vanilla playthrough")
    lines.append(" - Herbs restore 8 HP")
    lines.append(" - Player upgrades available: 10/4/4 (3 upgrades per boss)")
    lines.append("")
    lines.append("HARD:")
    lines.append(" - Enemies have roughly 2x STR/DEF compared to Normal")
    lines.append(" - Herbs restore 4 HP")
    lines.append(" - Player upgrades available: 8/2/2 (2 upgrades per boss)")
    lines.append("")
    lines.append("EXTREME:")
    lines.append(" - Enemies have roughly 2x STR/DEF compared to Normal")
    lines.append(" - Herbs restore 2 HP, item hints are removed")
    lines.append(" - Player upgrades available: 6/0/0 (1 upgrade per boss)")
    tkinter.messagebox.showinfo("Difficulties", "\n".join(lines))

def goal_help():
    lines = []
    lines.append("Goal determines the required conditions to beat the game:")
    lines.append("")
    lines.append("DARK GAIA:")
    lines.append(" - Collect the required Mystic Statues (if any)")
    lines.append(" - Rescue Kara from her portrait using the Magic Dust")
    lines.append(" - Acquire and use the Aura to gain Shadow's form")
    lines.append(" - Talk to Gaia in any Dark Space to face and defeat Dark Gaia")
    lines.append("")
    lines.append("RED JEWEL HUNT:")
    lines.append("Collect the appropriate number of Red Jewels, by difficulty, and turn them into the Jeweler:")
    lines.append(" - Easy: 35 Red Jewels")
    lines.append(" - Normal: 40 Red Jewels")
    lines.append(" - Hard/Extreme: 50 Red Jewels")
    tkinter.messagebox.showinfo("Goal", "\n".join(lines))

def logic_help():
    lines = []
    lines.append("Logic determines how items and abilities are placed:")
    lines.append("")
    lines.append("COMPLETABLE:")
    lines.append(" - All locations are accessible")
    lines.append(" - Freedan abilities will only show up in dungeons")
    lines.append("")
    lines.append("BEATABLE:")
    lines.append(" - Some non-essential items may be inaccessible")
    lines.append(" - Freedan abilities will only show up in dungeons")
    lines.append("")
    lines.append("CHAOS:")
    lines.append(" - Some non-essential items may be inaccessible")
    lines.append(" - Freedan abilities may show up in towns")
    tkinter.messagebox.showinfo("Logic Modes", "\n".join(lines))

def firebird_help():
    lines = []
    lines.append("Checking this box grants early access to the Firebird attack, when:")
    lines.append(" - The Crystal Ring is equipped,")
    lines.append(" - Kara is saved from her painting, and")
    lines.append(" - Player is in Shadow's form.")
    tkinter.messagebox.showinfo("Firebird", "\n".join(lines))

def variant_help():
    lines = []
    lines.append("The following variants are currently available:")
    lines.append("")
    lines.append("OHKO:")
    lines.append(" - Player starts with 1 HP")
    lines.append(" - All HP upgrades are removed or negated")
    tkinter.messagebox.showinfo("Variants", "\n".join(lines))

def enemizer_help():
    lines = []
    lines.append("The following enemy shuffle modes are available:")
    lines.append("")
    lines.append("LIMITED:")
    lines.append(" - Enemies only appear within their own dungeons")
    lines.append("")
    lines.append("BALANCED:")
    lines.append(" - Enemies can show up in any dungeon, but retain the stats of the enemies they replace")
    lines.append("")
    lines.append("FULL:")
    lines.append(" - Enemies can show up in any dungeon with their normal stats")
    lines.append("")
    lines.append("INSANE:")
    lines.append(" - Same as Full, but enemy stats are shuffled")
    tkinter.messagebox.showinfo("Enemizer", "\n".join(lines))

def start_help():
    lines = []
    lines.append("You can change this setting to affect where you start the game.")
    lines.append("Where you start the game is also where Gaia sends you when you warp to start.")
    lines.append("")
    lines.append("SOUTH CAPE:")
    lines.append(" - You start the game in South Cape, as normal")
    lines.append("")
    lines.append("SAFE:")
    lines.append(" - You start the game in a random town, in front of a Dark Space")
    lines.append("")
    lines.append("UNSAFE:")
    lines.append(" - You start the game in front of a random Dark Space, could be in a town or a dungeon")
    lines.append("")
    lines.append("FORCED UNSAFE:")
    lines.append(" - You're guaranteed to start the game in the middle of a dungeon")
    tkinter.messagebox.showinfo("Start Location", "\n".join(lines))

root = tkinter.Tk()
root.title("Illusion of Gaia Randomizer (v." + VERSION + ")")
# if os.name == 'nt':
#     root.wm_iconbitmap('iogr.ico')
# else:
#     root.tk.call('wm', 'iconphoto', root._w, tkinter.PhotoImage(file=os.path.join(".",'iogr.png')))

# Add a grid
mainframe = tkinter.Frame(root)
mainframe.grid(column=2,row=9, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
mainframe.columnconfigure(0, weight = 1)
mainframe.rowconfigure(0, weight = 1)
mainframe.pack(pady = 20, padx = 20)

tkinter.Label(mainframe,text="ROM File").grid(row=0,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Seed").grid(row=1,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Difficulty").grid(row=2,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Goal").grid(row=3,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Logic").grid(row=4,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Early Firebird").grid(row=5,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Start Location").grid(row=6,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Variant").grid(row=7,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Enemizer (beta)").grid(row=8,column=0,sticky=tkinter.W)
tkinter.Label(mainframe,text="Statues").grid(row=9,column=0,sticky=tkinter.W)

difficulty = tkinter.StringVar(root)
diff_choices = ["Easy", "Normal", "Hard", "Extreme"]
difficulty.set("Normal")

goal = tkinter.StringVar(root)
goal_choices = ["Dark Gaia", "Red Jewel Hunt"]
goal.set("Dark Gaia")

logic = tkinter.StringVar(root)
logic_choices = ["Completable", "Beatable", "Chaos"]
logic.set("Completable")

firebird = tkinter.IntVar(root)
firebird.set(0)

start = tkinter.StringVar(root)
start_choices = ["South Cape", "Safe", "Unsafe", "Forced Unsafe"]
start.set("South Cape")

variant = tkinter.StringVar(root)
variant_choices = ["None", "OHKO"]
variant.set("None")

enemizer = tkinter.StringVar(root)
enemizer_choices = ["None", "Limited", "Balanced", "Full", "Insane"]
enemizer.set("None")

statues = tkinter.StringVar(root)
statue_choices = ["0","1","2","3","4","5","6","Random"]
statues.set("Random")

ROM = tkinter.Entry(mainframe,width="40")
ROM.grid(row=0,column=1)

seed = tkinter.Entry(mainframe)
seed.grid(row=1,column=1)
seed.insert(10,random.randint(0,999999))

diff_menu = tkinter.OptionMenu(mainframe,difficulty,*diff_choices).grid(row=2,column=1)
goal_menu = tkinter.OptionMenu(mainframe,goal,*goal_choices).grid(row=3,column=1)
logic_menu = tkinter.OptionMenu(mainframe,logic,*logic_choices).grid(row=4,column=1)
firebird_checkbox = tkinter.Checkbutton(mainframe,variable=firebird,onvalue=1,offvalue=0).grid(row=5,column=1)
start_menu = tkinter.OptionMenu(mainframe,start,*start_choices).grid(row=6,column=1)
variant_menu = tkinter.OptionMenu(mainframe,variant,*variant_choices).grid(row=7,column=1)
enemizer_menu = tkinter.OptionMenu(mainframe,enemizer,*enemizer_choices).grid(row=8,column=1)
statues_menu = tkinter.OptionMenu(mainframe,statues,*statue_choices).grid(row=9,column=1)

tkinter.Button(mainframe,text='Browse...', command=find_ROM).grid(row=0,column=2)
tkinter.Button(mainframe,text='Generate Seed', command=generate_seed).grid(row=1,column=2)
tkinter.Button(mainframe,text='Generate ROM', command=generate_ROM).grid(row=9,column=2)

tkinter.Button(mainframe,text='?', command=diff_help).grid(row=2,column=2)
tkinter.Button(mainframe,text='?', command=goal_help).grid(row=3,column=2)
tkinter.Button(mainframe,text='?', command=logic_help).grid(row=4,column=2)
tkinter.Button(mainframe,text='?', command=firebird_help).grid(row=5,column=2)
tkinter.Button(mainframe,text='?', command=start_help).grid(row=6,column=2)
tkinter.Button(mainframe,text='?', command=variant_help).grid(row=7,column=2)
tkinter.Button(mainframe,text='?', command=enemizer_help).grid(row=8,column=2)

root.mainloop()
