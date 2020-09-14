# The Illusion of Gaia Randomizer CLI
This randomizer is only compatible with the US version of the Illusion of Gaia ROM.

## How To Use

### Prerequisites
- Python 3.8

### Usage
> py /path/to/src/cli/\_\_main\_\_.py -p <path to ROM file>

### Parameters
| Short | Long | Required | Values | Default | Description |
| ----- | ---- | -------- | ------ | ------- | ----------- |
|-p|--path|YES|||Path to the base ROM file|
|-s|--seed|NO|||A seed number, must be a valid integer|
|-d|--difficulty|NO|EASY = 0<br>NORMAL = 1<br>HARD = 2<br>EXTREME = 3|1|Decreases rewards and increases enemy scaling|
|-g|--goal|NO|DARK_GAIA = 0<br>RED_JEWEL_HUNT = 1<br>APO_GAIA = 2<br>RANDOM_GAIA = 3|0|Goal to complete the seed|
|-l|--logic|NO|COMPLETABLE = 0<br>BEATABLE = 1<br>CHAOS = 2|0|Logic Variance|
|-e|--enemizer|NO|NONE = 0<br>LIMITED = 1<br>BALANCED = 2<br>FULL = 3<br>INSANE = 4|0|Randomizes which set of enemies appear throughout the game|
|-z|--z3|NO|0, 1|0|Changes the flow of character progression to be more in line with Zelda 3|
|-r|--race|NO|0, 1|0|Determines whether or not to generate a spoiler|
||--start-pos|NO|SOUTH_CAPE = 0<br>SAFE = 1<br>UNSAFE = 2<br>FORCED_UNSAFE = 3|0|Randomizes where the player starts|
||--statues|NO|0<br>1<br>2<br>3<br>4<br>5<br>6<br>Random|4|Sets how many statues are required to face Dark Gaia -- Only valid in non-Red Jewel Hunt seeds|
||--ohko|NO|0, 1|0|One hit will kill the player -- Cannot be used with Red Jewel Madness|
||--red-jewel-madness|NO|0, 1|0|Start at 40 HP and lose 1 HP for each Red Jewel used -- Cannot be used with OHKO|
||--open-mode|NO|0, 1|0|Entire world is open at the start of the game|
||--firebird|NO|0, 1|0|Allow for early Firebird|
||--allow-glitches|NO|0, 1|0|Allow glitches to be (possibly) required to beat the game|
||--boss-shuffle|NO|0, 1|0|Randomizes where bosses are placed|
||--overworld-shuffle|NO|0, 1|0|Not Yet Implemented|
||--dungeon-shuffle|NO|0, 1|0|Not Yet Implemented|