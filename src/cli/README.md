## The Illusion of Gaia Randomizer (v1.5.1) - <a href="https://github.com/DontBaguMe/IoGR/releases/tag/v1.5.1">Download</a>
This randomizer is compatible with the US version of the Illusion of Gaia ROM.

<a href="https://discord.gg/KfZ4VeD">Join the Community on Discord</a>

<a href="https://www.youtube.com/watch?v=Y55btoDfuDw&list=PLe2Rz7BOWk02gsG4MnXT5D_76omVT8Q7k">Watch a Video Tutorial</a>

The <a href="https://emotracker.net/download/">IoGR EmoTracker</a> is now live!

#### The .exe package
The executable has been verified to work on Windows, Linux and Wine.

NOTE: It is common for the randomizer program to be flagged as a virus in Windows Defender.  This is a known issue for many programs that have been compiled in Pyinstaller, and a ticket has been submitted for this program in particular.  In the meantime, you can <a href="https://support.microsoft.com/en-us/help/4028485/windows-10-add-an-exclusion-to-windows-security">create an exclusion</a> for the folder to which you extract the IoGR program files.

#### the .py package
For non-Windows user with Python 2.7 installed, use the "py" package and run the "iogr.py" script to execute the randomizer interface.

### Creating a Randomized ROM
For the randomizer to function, you must ensure that "iogr.exe" or "iogr.py" is run from the same directory that also contains the "bin" directory (as well as "iogr.ico" or "iogr.png" for the .exe).  It is recommended that a copy of the US version of the Illusion of Gaia ROM also exist within this directory, to make browsing within the user interface more convenient.  The name of the ROM file does not need to adhere to a standard format.

Running "iogr.exe" or "iogr.py", inputting the desired settings, and hitting "Generate ROM" will create a randomized ROM (as well as a spoiler log) in the same directory as your original ROM file.  The original file will remain intact.

### Randomizer Settings
Below are explanations of the various settings of the randomizer.
#### Difficulty
There are four difficulty settings: Easy, Normal, Hard, and Extreme. The difficulty chosen affects the following game mechanics:
- Enemies: Enemies scale in strength with each difficulty mode.
- Room Rewards: The number of room-clearing rewards available to the player is affected by difficulty (see below).
- Item and Ability Placement: Easy and Normal modes both include a slight bias toward making required items and abilities available to the player earlier on.
- In-Game Spoilers: Hints have been removed in Extreme mode.

#### Goal
This allows you to choose a game mode, whether Dark Gaia or Red Jewel Hunt (see below).

#### Logic
There are three logic modes available to the player.
- Completable: This logic ensures that every item and ability location is reachable, allowing every seed to be completed 100%. This tends to yield slightly longer gameplay experiences.
- Beatable: In Beatable seeds, you are guaranteed to have access to every item and ability you need to complete your goal, though you may not have access to every item location in the game. This tends to yield slightly more streamlined seeds -- however, it could also make helpful items like status upgrades unattainable, making this mode slightly more dangerous.
- Chaos: Ability placement restrictions have been drastically loosened in this mode -- for instance, Freedan abilities can show up in towns, and Dark Spaces that are typically reserved for form changes might contain abilities, preventing the player from completing dungeons and accessing certain item locations.  As in Beatable, Chaos mode still ensures that the player has access to all the items and locations necessary to beat the game.

#### Statues
You can choose the number of Mystic Statues required to complete Dark Gaia seeds, or make the number random. This parameter is ignored for Red Jewel Hunts.

### Beating the Game
There are currently two modes (goals) for completing the game:
#### Dark Gaia
In this mode, you must find the Magic Dust and use it to free Kara from her portrait.  You must then unite with her to defeat Dark Gaia, a process which requires you to have Shadow's form unlocked (by obtaining and using the Aura) as well as a certain number of the game's six Mystic Statues.

Kara's portrait can be found in one of the five minor dungeons, specified below.  The location of Kara's portrait will be contained in Lance's Letter.
- Edward's Underground Tunnel
- The Diamond Mine
- The Angel Village
- Mt. Kress
- Ankor Wat.

Each seed may require a certain number of the six Mystic Statues. Talking to the schoolteacher in South Cape at the start of the game will indicate which statues are required. The statues are acquired by completing the following bosses/locations:

- Statue 1: Castoth (Inca Ruins)
- Statue 2: Viper (Sky Garden)
- Statue 3: Vampires (Mu)
- Statue 4: Sang Fanger (Great Wall)
- Statue 5: Mummy Queen (Pyramid)
- Statue 6: Boss Rush (Babel Tower) OR Solid Arm (Jeweler's Mansion)

Once you rescue Kara, unlock Shadow's form, and earn the applicable Statues (if any), you may talk to Gaia at any Dark Space, who will grant you the option to face Dark Gaia and win the game.

#### Red Jewel Hunt
For this mode, the sole objective is to collect the required number of Red Jewels as quickly as possible and turn them into the Jeweler.  The number of Red Jewels required is 35 for Easy, 40 for Normal, and 50 for Hard/Extreme.  Turning these into the Jeweler and speaking with him allows you to beat the game.

### Features
#### Item Shuffle
The items in the game will be shuffled across the game.  If the randomizer is created with "Completable" logic, every item location will be accessible; if it is "Beatable", certain items not required to fulfill the game's objectives may be inaccessible.
#### Ability Shuffle
The special attacks are shuffled throughout the Dark Spaces in the game.  Dark Spaces in peaceful locations can only contain Will abilities, whereas Dark Spaces in battle areas can contain either Will or Freedan abilities.  In "Completable" mode, some Dark Spaces are reserved for form changes and will never contain abilities -- such as the Dark Space in the Underground Tunnel, for example.
#### Overworld Movement
The world is broken up into continents. The locations in a continent are all accessible to one another through the world map screen. The following locations are accessible to one another via the overworld:
- South-West Continent (South Cape, Edward's Castle, Itory Village, Moon Tribe Camp, Inca Ruins)
- South-East Continent (Diamond Coast, Freejia, Diamond Mine, Neil's Cottage, Nazca Plain)
- North-East Continent (Angel Village, Watermia, Great Wall)
- North Continent (Euro, Mt. Kress, Natives' Village, Ankor Wat)
- North-West Continent (Dao, Pyramid)

Movement between continents (and to locations not specified above) becomes possible as items are acquired, or as quest events are completed:
- Defeating Castoth in Inca Ruins grants you access to the Gold Ship, which takes you to the Diamond Coast.
- Defeating Viper in Sky Garden takes you to the Seaside Palace.
- Acquiring the Teapot allows you to use it on the plateau in the Moon Tribe camp. This grants you access to the Sky Garden. (After using the Teapot, you can use the Sky Garden to travel to the Moon Tribe Camp, the Nacza Plain, or the Seaside Palace.)
- Acquiring Lola's Letter allows you to learn Morse Code. After reading the letter, talk to Erik in the Seaside Cave in South Cape. Together you can communicate with Seth (who is in Riverson form), who can transport you to the Diamond Coast or Watermia. Turbo the dog (Diamond Coast) and the man standing at the entrance in Watermia can also communicate with Seth for you.
- Upon acquiring the Memory Melody, you can visit Neil in his cottage, who has forgotten how to pilot his airplane. Playing this melody for him restores his memory. From then on, he is happy to take you to Euro, Dao, or Babel Tower. He can be found either in his home, in his mansion in Euro, or in his room in Dao.
- Acquiring the Will allows you to use Kruks to travel between Watermia and Euro. When the Will is in your inventory, speak to the man tending his Kruks in Watermia just east of the town entrance, or to the man standing by the east entrance to the city of Euro. 
- Upon acquiring the Large Roast, go to the Natives' Village and talk to the young boy. If you give him the roast, he will gratefully guide you across the treacherous expanse from the village to Dao. The man in Dao who grants you two items can also hire a guide to take you back to Natives' for free.
- In the Nazca Plain, if you go to the location of the tile buried in the sand, you can warp to the Sky Garden. However, the Moon Tribe will only appear there if you have healed them with the Teapot. You can exit to the overworld from the Sky Garden by going up into the area where you normally enter from Nazca.
- Mu and the Seaside Palace are accessible directly from Angel Village. What is originally the guest room in the vanilla game takes you to the Passage to Mu inside the Seaside Palace. Mu is freely accessible this way, but the Mu Palace Key is required to enter the Seaside Palace via this route.
#### Room Rewards and Stat Upgrades
The number of HP, STR and DEF upgrades available in the game has been reduced to reflect the extreme balancing of enemy statistics throughout the game -- so though the number of upgrades has decreased, each upgrade is much more significant than in the vanilla game.  HP upgrades grant you +3 HP each.

The rewards are shuffled at random throughout the entire game, map by map.  The total rewards available by difficulty (HP/STR/DEF) are:
- Easy: 10/7/7
- Normal: 10/4/4
- Hard: 8/2/2 (max HP 35)
- Extreme: 6/0/0 (max HP 29)

Upgrades can be accessed by clearing rooms that have a "Force" in them on the start menu.  (If you have the Black Glasses or the Crystal Ring equipped, the start menu will forecast which stat upgrade you'll receive for clearing a room.)

Alternatively, defeating a boss will grant you any unobtained upgrades in the following dungeons, by boss:
- Castoth: Underground Tunnel and Inca Ruins
- Viper: Diamond Mine and Sky Garden
- Vampires: Mu and Angel Dungeon
- Sand Fanger: Great Wall and Mt. Kress
- Mummy Queen: Pyramid
- Babel Tower: Ankor Wat

Each boss (and, by extension, the dungeons under each boss) is guaranteed to grant a total number of upgrades based on difficulty: 4 for Easy, 3 for Normal, 2 for Hard, and 1 for Extreme.
#### In-Game Tutorial
You can speak to the NPC standing in front of the school in South Cape for an in-game tutorial.  This guide will be tailored to the seed settings.

Additionally, for Easy Mode, enter right-most house in South Cape for an interactive overworld map that allows you to explore how many items and Dark Spaces are available in each location, as well as the number of items you've gathered for each location.
#### In-Game Hints

You may speak to a number of NPCs throughout the game to receive hints as to the location of certain key items in the game, as well as the contents of certain hard-to-reach locations.  The following NPCs will give you a hint (hints have been removed in Extreme difficulty):
- Kara's Guard in Edward's Castle
- The Elder at Itory Village
- The Queen on the Gold Ship
- The man at Diamond Coast
- The empty coffin at the Seaside Palace
- Ishtar's Apprentice in Angel Village
- Kara's Journal in Watermia
- Erasquez the Explorer in Euro
- The spirit at the end of Ankor Wat
- The girl with Jackal's note in Dao
- The first spirit in Babel Tower
#### Other Features
- The location of the glowing Gold Tile in Inca Ruins has been randomized, making the Wind Melody a requirement to progress to the end of that dungeon.
- The differences between the puzzle rooms in Ishtar's Studio in Angel Village are also random and could differ from the vanilla game.
- The order of the hieroglyphs in the Pyramid has been shuffled, making the Father's Journal a required item to face the Mummy Queen. (You can give the Father's Journal to the guide in the hieroglyph room of the Pyramid for safe keeping.)
- Herbs restore HP at rates that depend on the difficulty setting, either full restore (Easy), 8 HP (Normal), 4 HP (Hard), or 2 HP (Extreme).  An HP Jewel will restore your HP to full when used in Easy mode only.
- Upon acquiring the Aura, equip it and use it to unlock Shadow's form. From then on, you can fight as Shadow in any dungeon.
- Shadow's form must be unlocked to enter Babel Tower, as well as face Dark Gaia.
- If you bring the Necklace back to Lilly in Itory Village, she will accompany you.  This will allow you to progress to the end of Edward's Underground Tunnel, as well as access the item locked in the coffin in the Seaside Palace.
- A number of new items have been added to the game to simulate ability upgrades. These jewels appear as circles of flame in your inventory and, when used, upgrade the appropriate ability -- either your HP, STR, DEF, Psycho Dash, or Dark Friar abilities. Items representing multiple Red Jewels are handled similarly and must be used -- talking to the Jeweler will not remove these items from your inventory.
- Any barrier that can be removed with the Psycho Dash can also be destroyed with either the Psycho Slider or the Spin Dash.
- The Dark Spaces in both Edward's Prison and Babel Tower have been relocated to prevent softlocks.
- The spirits in Babel Tower can warp you back to the bottom of the tower, allowing you to escape if you cannot defeat one of the bosses.
- You can talk to the NPC in front of the school in South Cape for an in-game tutorial.

#### Misc. Notes and Strategies
- Sky Garden: The Dark Space in the SW room does not in fact require Dark Friar to access. You can stand below the switch as Freedan and reach it easily with his sword. Also, you can use Aura Barrier to complete the NW room instead of Dark Friar.

- Great Wall: The Dark Space where Spin Dash is normally found, as it's the only Dark Space in that area that can be accessed without any abilities, will actually never have an ability and will always be open for changing forms.  The Dark Space in the previous room might have an ability, and you can reach it without Spin Dash by turning into Freedan or Shadow, walking back, and using the longer reach of one of these characters to hit the switch that allows entrance into that map.

- Ankor Wat: The Gorgon that blocks the way (for which you are intended to use the Earthquaker) can be easily defeated if you have Dark Friar, 2nd upgrade, by standing on the platform and spamming him with fireballs before he blocks the passage.

- Ankor Wat: To get to the Dark Space with vanilla Earthquaker, you are intended to have Dark Friar to defeat the Frenzy that moves along the wall across the gap.  However, if you have Shadow unlocked, his attack has enough reach to defeat this enemy, so this may be the intended way to access that Dark Space in a randomized seed.

- Pyramid: Room 3 (the "killer 6" room) can be done with Fredan if you have Dark Friar.  Some might find this form to be helpful to survive in this area, especially if you have upgraded Dark Friar and/or Aura Barrier.  Similarly, Room 5 can be completed with Freedan if you have the Earthquaker ability by using that ability from the various platforms in this area.  (Tiles will fall from the ceiling, allowing you to progress.)

### Item Tracker
There is a simple item tracker included with this release.  Official trackers for the game are in development.

### Future Releases
- Enemizer
- Entrance randomizer
- Boss shuffle
- More text edits

### Known Bugs and Quirks
If you have an issue with the randomizer, please join our 
<a href="https://discord.gg/KfZ4VeD">Discord</a> and report your issue in the #bugs channel.

### Support the Dev
No one does a project like this for the money -- I love this game, wanted a randomizer to exist for it, and had a blast making one.  I neither need nor expect any compensation for my work -- I hope you enjoy it, no strings attached.  However, if you feel compelled to support me for this project (or if you'd like to see more game-modding from me), I humbly invite you to consider becoming a 
<a href="https://www.patreon.com/dontbagume">patron.</a>
