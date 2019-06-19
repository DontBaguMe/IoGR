from Tkinter import *
from tkMessageBox import *
from tkFileDialog import askopenfilename
import os
import random
import classes
import iogr_rom
import quintet_text

VERSION = "1.1-beta3"

def find_ROM():
    ROM.delete(0,END)
    ROM.insert(10,askopenfilename())

def generate_seed():
    seed.delete(0,END)
    seed.insert(10,random.randint(0,99999999))

def generate_ROM():
    rompath = ROM.get()
    rompath = rompath.lower()
    seed_str = seed.get()
#    if not (rompath.endswith(".sfc") or rompath.endswith(".smc")):
#        showinfo("ERROR", "Please enter a valid ROM file")
#        return
    if not seed_str.isdigit():
        showinfo("ERROR", "Please enter or generate a valid seed")
        return

    try:
        f = open(rompath,"rb")
    except:
        showinfo("ERROR", "ROM file does not exist")
        return
    rom_data = f.read()
    header = "\x49\x4C\x4C\x55\x53\x49\x4F\x4E\x20\x4F\x46\x20\x47\x41\x49\x41\x20\x55\x53\x41"
    h_addr = rom_data.find(header)
    if h_addr < 0:
        showinfo("ERROR", "This randomizer is only compatible with the (US) version of Illusion of Gaia")
        return
    else:
        rom_offset = h_addr - int("ffc0",16)
#        if rom_offset != 0:
#            showinfo("ERROR", "Sorry, this version of the ROM includes an offset that makes it incompatible with the randomizer. Please use another ROM.")
#            return

    statues_str = statues.get()
    goal_str = goal.get()
    logic_str = logic.get()
    diff_str = difficulty.get()

    if goal_str == "Dark Gaia":
        goal_cd = "DG" + statues_str[0]
    elif goal.get() == "Red Jewel Hunt":
        goal_cd = "RJ"

    filename = "IoGR_v" + VERSION + "_" + diff_str + "_" + goal_cd + "_" + logic_str[0] + "_" + seed_str
    #filename = "Illusion of Gaia Randomized.sfc"

    if iogr_rom.generate_rom(VERSION, rom_offset, int(seed_str), rompath, filename, diff_str, goal_str, logic_str, statues_str):
        showinfo("Success!", filename + " has been successfully created!")
    else:
        showinfo("ERROR", "Operation failed")

root = Tk()
root.title("Illusion of Gaia Randomizer (v." + VERSION + ")")
if os.name == 'nt':
    root.wm_iconbitmap('iogr.ico')
else:
    root.tk.call('wm', 'iconphoto', root._w, PhotoImage(file=os.path.join(".",'iogr.png')))

# Add a grid
mainframe = Frame(root)
mainframe.grid(column=2,row=5, sticky=(N,W,E,S) )
mainframe.columnconfigure(0, weight = 1)
mainframe.rowconfigure(0, weight = 1)
mainframe.pack(pady = 20, padx = 20)

Label(mainframe,text="ROM File").grid(row=0,column=0,sticky=W)
Label(mainframe,text="Seed").grid(row=1,column=0,sticky=W)
Label(mainframe,text="Difficulty").grid(row=2,column=0,sticky=W)
Label(mainframe,text="Goal").grid(row=3,column=0,sticky=W)
Label(mainframe,text="Logic").grid(row=4,column=0,sticky=W)
Label(mainframe,text="Statues").grid(row=5,column=0,sticky=W)

difficulty = StringVar(root)
diff_choices = ["Easy", "Normal", "Hard", "Extreme"]
difficulty.set("Normal")

goal = StringVar(root)
goal_choices = ["Dark Gaia", "Red Jewel Hunt"]
goal.set("Dark Gaia")

logic = StringVar(root)
logic_choices = ["Completable", "Beatable", "Chaos"]
logic.set("Completable")

statues = StringVar(root)
statue_choices = ["0","1","2","3","4","5","6","Random"]
statues.set("Random")

ROM = Entry(mainframe,width="40")
ROM.grid(row=0,column=1)

seed = Entry(mainframe)
seed.grid(row=1,column=1)
seed.insert(10,random.randint(0,999999))

diff_menu = OptionMenu(mainframe,difficulty,*diff_choices).grid(row=2,column=1)
goal_menu = OptionMenu(mainframe,goal,*goal_choices).grid(row=3,column=1)
logic_menu = OptionMenu(mainframe,logic,*logic_choices).grid(row=4,column=1)
statues_menu = OptionMenu(mainframe,statues,*statue_choices).grid(row=5,column=1)

Button(mainframe,text='Browse...', command=find_ROM).grid(row=0,column=2)
Button(mainframe,text='Generate Seed', command=generate_seed).grid(row=1,column=2)
Button(mainframe,text='Generate ROM', command=generate_ROM).grid(row=5,column=2)

#top_frame = Frame(window)
#top_frame.pack()
#bottom_frame = Frame(window)
#bottom_frame.pack(side=BOTTOM)

#button_seed = Button(top_frame,text="Generate Seed")
#button_generate = Button(bottom_frame,text="Generate ROM")

#button_seed.pack()
#button_generate.pack()

#theLabel = Label(root,text="IoGR v.0.6.0")
#theLabel.pack()

root.mainloop()
