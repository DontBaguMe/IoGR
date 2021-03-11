## The Illusion of Gaia Randomizer (v4.3) - <a href="https://www.iogr.app/">Play Now!</a>
This randomizer is compatible with the US version of the Illusion of Gaia ROM.

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#faq">Jump to the FAQ</a>

<a href="https://discord.gg/KfZ4VeD">Join the Community on Discord</a>

<a href="https://www.youtube.com/watch?v=JobLH53Q1sM">Watch a Video Tutorial (UPDATED!)</a>

The <a href="https://emotracker.net/download/">IoGR EmoTracker</a> is now live!

### Contents
<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#quick-start">Quick Start (tl;dr)</a>

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#randomizer-settings">Randomizer Settings</a>

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#beating-the-game">How to Beat the Game</a>

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#features">Features:</a>
- <a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#overworld-movement">Overworld Movement</a>
- <a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#room-rewards-and-stat-upgrades">Room Rewards and Stat Upgrades</a>
- <a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#in-game-hints">In-Game Hints</a>
- <a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#other-features">Other Features</a>

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#faq">Frequently Asked Questions</a>

### Creating a Randomized ROM
Uploading a US Illusion of Gaia ROM, inputting the desired settings, and hitting "Generate ROM" will allow you to download a randomized ROM (as well as a spoiler log).  The original file will remain intact.


### Quick Start
Here's a quick primer on what you need to know about most randomizer seeds.

#### Differences from the Original Game
- Illusion of Gaia has been transformed into an open-world game for the randomizer. To accomplish this, **some items have different functionalities**:
  - Lola's Letter: Acquiring AND READING this letter allows you to talk to Seth, who can take you between these three locations: South Cape (seaside cave), Diamond Coast (talk to Turbo), and Watermia (talk to the guy standing at the entrance)
  - Teapot: Use this in the Moon Tribe Camp to heal the spirits. They will take you to the Sky Garden and, from there, can take you back to the Moon Tribe Camp, the Nazca Plain, or the Seaside Palace.
  - Memory Melody: Play this melody for Neil in his cottage and he can take you around in his plane. He can take you to/from his cottage, his mansion in Euro, or Dao.  He can also drop you off at Babel Tower.
  - Will: Like the original game, you can use this to travel between Watermia (the guy tending kruks) and Euro (the guy standing near the town entrance)
  - Large Roast: Give this to a hungry kid in Natives Village and he'll guide you to Dao.
  - Necklace: Give this to Lilly in Itory Village and she'll take a ride in your pocket. You need her to progress through Edward's Tunnel and to acquire the coffin item in the Seaside Palace.
- **Item and Ability locations have been shuffled.** Check every location and Dark Space for potential items/moves.

#### Win Conditions
- For most seeds, you must **rescue Kara** from a painting using the Magic Dust. She can show up at the end of one of the five minor dungeons (Edward's Prison, Diamond Mine, Angel Village, Mt. Temple, or Ankor Wat).
- For most seeds, you must **collect Mystic Statues** by beating bosses. You can find out the statues you'll need to get from the teacher in South Cape.
- Once you free Kara, collect the needed Mystic Statues, and acquire and use the Aura, you can face Dark Gaia.  **Talk to Gaia in any Dark Space** when you've completed these conditions and she can take you to fight her.

#### Tips and Tricks
- Acquiring late-game abilities early can open up progression in unique ways. Think outside the box if you're stuck.
- There are a couple **in-game tools** to help newcomers:
  - Talk to the guy standing in front of the school in South Cape for a guidebook. This outlines much of the information discussed above, so it's handy as a quick reference if you get stuck.
  - Enter the house to the east of Will's House in South Cape to access a world map.  When you walk over a map location, it will break down the number of items you still need to collect from that area.

### Randomizer Settings
Below are explanations of the various settings of the randomizer.

#### Seed
This is a non-negative integer value that initializes the randomization algorithm.  Generating randomizers with the same seed and randomizer settings will produce identical games.

#### Difficulty
There are four difficulty settings: Easy, Normal, Hard, and Extreme. The difficulty chosen affects the following game mechanics:
- Item and Ability Placement: Easy and Normal modes both include a slight bias toward making required items and abilities available to the player earlier on.
- In-Game Spoilers: Hints have been removed in Extreme mode.
- Boss Logic: Solid Arm can be required for Extreme seeds.
- Boss Shuffle: In Extreme, dungeons keep their vanilla music so you don't know which boss is at the end.  Solid Arm is included in Boss Shuffle in Extreme, but not other modes
- Red Jewel Hunt: The number of Red Jewels required to beat the game, by difficulty, is 35/40/45/50
- Open World: The items that replace the five travel items are more favorable in easier difficulties.

#### Level
You choose your level from the start menu when you create a new game file.  Level does not affect game logic or item placement, so if desired players could race the same seed at varying levels.  There are four level settings: Beginner, Intermediate, Advanced, and Expert. The level chosen affects the following game mechanics:
- Enemies: Enemies scale in strength with each level.
- Room Rewards: The number of room-clearing rewards available to the player is affected by difficulty (see below).
- Herbs:  By level, the number of HP restored by herbs are full/8/6/4
- Snake Game: The number of snakes required will increase at harder difficulties.

#### Goal
This allows you to choose a game mode. There are currently four goals available (see below for more details):
- Dark Gaia: Rescue Kara, find and use the Aura, collect required Mystic Statues (if any), and defeat Dark Gaia on the Comet to beat the game.
- Red Jewel Hunt: Beat the game by collecting a number of Red Jewels and turning them into the Jeweler (see below).
- Apocalypse Gaia: Same as Dark Gaia, except you'll face the true final boss hidden in the game code!  Shoutouts to Raeven0 for uncovering and reprogramming this masterpiece. (Very hard) NOTE: This fight has five phases -- the first two are identical to the vanilla Dark Gaia fight, and phases 3-5 are new.  Once you hit Phase 3, you set a checkpoint where if you die: 1) you return to the beginning of Phase 3 with full health, and 2) you regain any herbs you had at the beginning of that phase.
- Random Gaia: Same as Dark Gaia, except there's a 50/50 chance you'll face Apocalypse Gaia instead.  In Random Gaia seeds, you'll know whom you're facing in the text box that appears after you merge forms with Kara: 1) if it's Dark Gaia, you'll get a random quote as normal; 2) if it's Apocalypse Gaia, the quote will read "Apocalypse Now!"

#### Statues
You can choose the number of Mystic Statues required to complete Dark Gaia seeds, or make the number random. This parameter is ignored for Red Jewel Hunts.

#### Starting Location
You can choose to have the game start you in random locations throughout the world. Gaia's "warp to start" will return you to wherever you begin the game.
- South Cape: You start the game in the vanilla location.
- Safe: You start the game in a random safe location (e.g. a town)
- Unsafe: You can start the game at any random Dark Space. It can be either a safe location (town) or an unsafe location (dungeon).
- Forced Unsafe: You will start the game in the middle of a random dungeon.

#### Logic
There are three logic modes available to the player.
- Completable: This logic ensures that every item and ability location is reachable, allowing every seed to be completed 100%. This tends to yield slightly longer gameplay experiences.
- Beatable: In Beatable seeds, you are guaranteed to have access to every item and ability you need to complete your goal, though you may not have access to every item location in the game. This tends to yield slightly more streamlined seeds -- however, it could also make helpful items like status upgrades unattainable, making this mode slightly more dangerous.
- Chaos: Ability placement restrictions have been drastically loosened in this mode -- for instance, Freedan abilities can show up in towns, and Dark Spaces that are typically reserved for form changes might contain abilities, preventing the player from completing dungeons and accessing certain item locations.  As in Beatable, Chaos mode still ensures that the player has access to all the items and locations necessary to beat the game.

#### Variants
- Open World: All overworld movement is unlocked from the start -- i.e. Lola's Letter, the Teapot, the Memory Melody, the Will, and the Large Roast are all activated at start.  Additionally, these five items have been removed from the item pool and have been replaced with STR upgrades, DEF upgrades, herbs, and/or nothing (dependent on difficulty setting).
- Allow Glitches: You may be required to perform simple glitches to access progression items or abilities.
- OHKO (One Hit Knockout): You start the game with 1 HP and will never gain an HP upgrade, so each hit kills you automatically.
- Red Jewel Madness: You start the game with 40 HP (max) and lose 1 HP for every Red Jewel you turn into the Jeweler. If you reach 0 total HP, you will be caught in an infinite death loop. Note: Gaining an HP upgrade when you're at or near 40 HP may result in lost upgrades, as any HP value above 40 is ignored.
- Early Firebird: In this mode, you gain access to the Firebird attack when 1) you rescure Kara, 2) you equip the Crystal Ring, and 3) you're in Shadow's form.
- Zelda 3 Mode: Choosing this variant makes some significant alterations to the game, inspired by the combat system of <i>The Legend of Zelda: A Link to the Past (ALTTP)</i>.  Below are the changes made in this mode. (Where appropriate, values given by level are provided in the format Beginner/Intermediate/Advanced/Expert.)
  - You begin the game with 6 HP instead of 8 (to mirror Link's starting health).
  - 12 Red Jewels have been removed from the game and replaced with 4 HP upgrades and 8 HP Pieces.  HP upgrades add +2 HP (+1 in Expert), and HP Pieces add +1 HP (+0.5 in Advanced and Expert).
  - Room rewards (HP only) grant +1 each.  The number of HP room upgrades available, by level, are 12/12/6/6
  - STR and DEF upgrades have been removed from the room/boss rewards and have been put into the item pool.
  - The max STR upgrades you can receive by level are 3/2/1/0.
  - The max DEF upgrades you can receive by level are 2/2/1/0.
  - Jump slashes deal double damage instead of +1 damage.
  - Each STR and DEF upgrade doubles the applicable stat instead of adding +1.
  - Herbs and HP upgrades provide the following refills, by level: 40/40/14/8.
  - Max HP available to the player, by level is 40/40/28/23.
  - Non-boss enemy stats are not shuffled between level choices. All non-bosses have 0 DEF.  Enemy damage ranges from 1 to 16.  (These values correspond to the enemies in A Link to the Past.)

#### Enemizer (beta)
The enemizer is (and likely will forever be) in beta, so play at your own risk. Graphical glitches abound, and some seeds may be incompletable due to enemy placement. Please report any game-breaking situations in the Discord.
References to enemy stats refer to STR, DEF and HP.
Note: Non-enemy sprites in dungeons have been largely removed in every enemizer setting except for Limited.
- Limited: Enemies will be shuffled, but will only appear in their vanilla dungeons.
- Balanced: Enemies can appear in any dungeon, but they will retain the stats of the enemies they replace, making each dungeon's difficulty relatively balanced to vanilla levels.
- Full: Enemies can appear in any dungeon and retain their vanilla stats.
- Insane: Enemeies can appear in any dungeon. Furthermore, enemy stats have been shuffled, so early enemies can have the stats of later enemies, and vice versa.
- Boss Shuffle (in development!): In this mode, the bosses are shuffled throughout the dungeons. Each boss guards the same Mystic Statue as they do in the vanilla game, so completing a dungeon may grant you a different Statue than normal. For Easy and Normal difficulties, each dungeon will inherit the music of the dungeon its boss typically resides in -- for example, if you hear the Inca Ruins music in Sky Garden, that means that Castoth is where Viper normally is, and defeating him will grant you the first Mystic Statue. Solid Arm will only be included in the shuffle for Extreme difficulty.

#### Entrance Randomizer (new feature!)
This feature will be fully implemented in a future version.  However, there is one feature you can choose:

- Overword Shuffle: This mode shuffles the 19 overworld locations among the five continents, so the locations you have access to in each continent will be different in each seed.

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>

### Beating the Game
There are currently two modes (goals) for completing the game:

#### Dark Gaia / Apocalypse Gaia / Random Gaia
In these modes, you must find the Magic Dust and use it to free Kara from her portrait.  You must then unite with her to defeat the final boss (either Dark Gaia or Apocalypse Gaia), a process which requires you to have Shadow's form unlocked (by obtaining and using the Aura) as well as a certain number of the game's six Mystic Statues.

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
For this mode, the sole objective is to collect the required number of Red Jewels as quickly as possible and turn them into the Jeweler.  The number of Red Jewels required is 35 for Easy, 40 for Normal, 45 for Hard, and 50 for Extreme.  Turning these into the Jeweler and speaking with him allows you to beat the game.

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>

### Features

#### In-Game Tutorial
You can speak to the NPC standing in front of the school in South Cape for an in-game tutorial.  This guide will be tailored to the seed settings.

#### Item Shuffle
The items in the game will be shuffled across the game.  If the randomizer is created with "Completable" logic, every item location will be accessible; if it is "Beatable" or "Chaos", certain items not required to fulfill the game's objectives may be inaccessible.

#### Ability Shuffle
The special attacks are shuffled throughout the Dark Spaces in the game.  In "Completable" and "Beatable" logic, Dark Spaces in peaceful locations can only contain Will abilities, whereas Dark Spaces in battle areas can contain either Will or Freedan abilities.  In "Chaos" logic, town Dark Spaces can contain Freedan abilities.

Also, in "Completable" mode, some Dark Spaces are reserved for form changes and will never contain abilities -- such as the Dark Space in the Underground Tunnel, for example. If one of these Dark Spaces contains an ability in "Beatable" or "Chaos", the logic will assume you don't have access to the rest of the dungeon.

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
- The man playing the flute at the entrance to Dao can hire a guide to take you to the Natives' Village.

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
- The differences between the puzzle rooms in Ishtar's Studio in Angel Village are also random and could differ from the vanilla game. In Easy and Normal, the first room will always be vanilla; in Hard and Extreme difficulties, there could be changes in the first room from vanilla. However, there will always only be one change between the two rooms.
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

#### Inventory Management Tips
With only sixteen slots available for items, inventory management is a significant meta aspect of this randomizer.  Below are some tips to help you manage your inventory space.  Logic will never grant you access to more key items than you can carry and/or get rid of.

- The following items can be used immediately upon acquisition, upon which they disappear: Red Jewels (including "2 Red Jewels" and "3 Red Jewels"), herbs, status upgrades ("HP Jewels", "DEF Jewels" "STR Jewels", "Light Jewels" and "Dark Jewels"), Lola's Letter, Black Glasses, and Crystal Ring

- The following items can be removed from inventory at any time: herbs, Lance's Letter, Rama Statues (if Mystic Statue 3 is not required), Father's Journal and Hieroglyphs (if Mystic Statue 5 is not required)

- If you have access to the Pyramid, you can drop off any Hieroglyphs in the slots even if you don't have Father's Journal.  You can gain back placed hieroglyphs either by swapping them with a different hieroglyph from you inventory, or by filling in the slots completely in the wrong order.

#### Misc. Notes and Strategies
- Sky Garden: The Dark Space in the SW room does not in fact require Dark Friar to access. You can stand below the switch as Freedan and reach it easily with his sword. Also, you can use Aura Barrier to complete the NW room instead of Dark Friar.

- Great Wall: In Completable logic, the Dark Space where Spin Dash is normally found, as it's the only Dark Space in that area that can be accessed without any abilities, will actually never have an ability and will always be open for changing forms.  The Dark Space in the previous room might have an ability, and you can reach it without Spin Dash by turning into Freedan or Shadow, walking back, and using the longer reach of one of these characters to hit the switch that allows entrance into that map.

- Ankor Wat: The Gorgon that blocks the way (for which you are intended to use the Earthquaker) can be easily defeated if you have Dark Friar, 2nd upgrade, by standing on the platform and spamming him with fireballs before he blocks the passage.

- Ankor Wat: To get to the Dark Space with vanilla Earthquaker, you are intended to have Dark Friar to defeat the Frenzy that moves along the wall across the gap.  However, if you have Shadow unlocked, his attack has enough reach to defeat this enemy, so this may be the intended way to access that Dark Space in a randomized seed.

- Pyramid: Room 3 (the "killer 6" room) can be done with Fredan if you have Dark Friar.  Some might find this form to be helpful to survive in this area, especially if you have upgraded Dark Friar and/or Aura Barrier.  Similarly, Room 5 can be completed with Freedan if you have the Earthquaker ability by using that ability from the various platforms in this area.  (Tiles will fall from the ceiling, allowing you to progress.)

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>

### EmoTracker
The offical <a href="https://emotracker.net/download/">IoGR EmoTracker</a> is available for download. Furthermore, you can access a beta version of the autotracker by joining the <a href="https://discord.gg/KfZ4VeD">Discord</a> and referring to the #tracker channel.

### Future Releases
- Entrance randomizer
- More text edits

### Known Bugs and Quirks
If you have an issue with the randomizer, please join our
<a href="https://discord.gg/KfZ4VeD">Discord</a> and report your issue in the #bugs channel.

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>

### FAQ
#### Can special abilities be found in any Dark Space?
If you're playing Completable or Beatable logic (without glitches allowed), certain Dark Spaces will always be reserved for form changes and will never have abilities in them. (Though enabling glitches or choosing Chaos logic breaks this restriction.) You can skip checking these:
- Underground Tunnel: The DS behind Lily's room will never have an ability
- Inca Ruins: The DS north of the singing statue will never have an ability
- Diamond Mine: If one of the Dark Spaces (not counting the one behind the false wall) has an ability, the other one is guaranteed not to have one
- Sky Garden: between the Dark Spaces in the SE and NW rooms, one of them is guaranteed not to have an ability
- Mu: the Dark Space to the west of the row of spikes will never have an ability
- Great Wall: The DS you fall down to access (vanilla Spin Dash) will never have an ability
- Ankor Wat: The DS in the garden will never have an ability
- Pyramid: Neither DS will ever have an ability

#### If you have Psycho Slider and Spin Dash, do you need to keep looking for Psycho Dash?
No.  Anything you would need Psycho Dash for can be done with either Slider or Spin.

#### Where the heck is Dark Friar?
It could be virtually anywhere, I'm afraid.  However, you may not need it:
- The ramp at the end of Diamond Mine can be scaled with Spin Dash
- The Dark Space in SW Sky Garden can be accessed with Freedan's sword alone
- The two chests in NW Sky Garden can be accessed with Aura Barrier
- In Ankor Wat, you can use Shadow's basic attack to access the Dark Space where Earthquaker normally is

#### Are Aura Barrier and Earthquaker useful at all?
Sort of.  If you happen to have Aura Barrier but not Dark Friar, you can access the two chests in NW Sky Garden.  If you have Earthquaker and don't have Dark Friar with both upgrades, you can use it to progess past the spinning Gorgon in Ankor Wat.  Beyond that, they're largely useless.

#### Does the second Dark Friar upgrade do anything?
Yes. If you have one upgrade, the fireball explodes upon impact only.  With two upgrades, you can control when it explodes by hitting the attack button again.

#### I'm clearing rooms of enemies. Why am I not getting stat upgrades?
Not every room has a stat upgrade, only those with a pulsing "Force" icon on the map screen.

#### Why did you take away stat upgrades?
Scaling down the range of enemy strength was necessary to make end-game enemies somewhat approachable with early-game stats; so reducing the number of upgrades available to the player accordingly was necessary to balance the game. Basically, there are less upgrades available, but each one is more significant than it was in the vanilla game.  For instance, each HP upgrade gives you +3 HP.

#### Where did the stat upgrade items come from?  Were they taken from room rewards?
No. In the vanilla game, there are a number of stat upgrades that are given through NPCs and other locations - namely, 1 DEF upgrade, 2 STR upgrades, and 3 HP upgrades.

#### My inventory keeps getting full, what do I do?
Inventory management is a big part of the game. You may be required to drop or use herbs to make space for key items, but the game will never give you access to more key items than you can carry or use. Keep in mind that you may be able to dump certain key items that only access bosses you don't need to fight (see below).

#### Can I dump items that only grant access to bosses I don't need to fight?
Generally yes.  The Rama Statues can be discarded from inventory if Statue 3 is not required, and the Hieroglyph Tiles/journal can be discarded if Statue 5 is not required. The restrictions on which items can be discarded changes from seed to seed.  Basically, if you're given the option to discard a key item, it means you don't need it to complete the game.

#### I had to dump my tutorial journal to make room in my inventory. Can I get it back?
Yes. The NPC in front of the school in South Cape will keep you stocked with an infinite supply of tutorial journals, should you desire.

#### I've done everything I need to complete the game. Why can't I face Dark Gaia?
For Dark Gaia seeds, you need to both acquire AND use the Aura, on top of freeing Kara and gathering the needed Mystic Statues.

#### I forgot to open the chests in Ishtar's puzzle, and now I can't get back into those rooms.
If you talk to Ishtar, the puzzle will reset and you can start again from the beginning.

#### The jeweler keeps telling me poker's not my game.
He's trying to give you an item, but your inventory's full. Make room and you can progress through that conversation.

#### Who the heck is Samlet?
Due to graphical limitations, when Kara's portrait is in the Diamond Mine, we had to turn Sam into Samlet.

#### Who the heck is Buffy?
That's what we named the NPC in the Seaside Palace who gives you an item after you purify the fountain.

#### What does "nice try dodongo" mean?
http://www.hrwiki.org/wiki/Nice_Try

#### How many custom death quotes are there?
Over 50 at this point. Collect them all for a commemorative patch.

#### What do the Black Glasses and Crystal Ring do anyway?
The Crystal Ring is one of the items you need to pass the force field at the base of Babel Tower.  In early Firebird seeds, it also is one of the triggers that grants access to the Firebird attack.  The Black Glasses make it so you can see in the white room in Ankor Wat. It also allows you to know which stat upgrades are available in each room.

#### Why is the game so mean to me?
#blamebagu

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>

### Support the Dev
No one does a project like this for the money -- I love this game, wanted a randomizer to exist for it, and had a blast making one.  I neither need nor expect any compensation for my work -- I hope you enjoy it, no strings attached.  However, if you feel compelled to support me for this project (or if you'd like to see more game-modding from me), I humbly invite you to consider subscribing to
<a href="https://www.twitch.tv/dontbagume">my channel on Twitch.</a>

<a href="https://github.com/DontBaguMe/IoGR/blob/master/README.md#contents">Return to Top</a>
