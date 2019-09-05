import os
from datetime import datetime
import binascii
import random

from .models.enums.difficulty import Difficulty
from .models.enums.enemizer import Enemizer
from .models.enums.goal import Goal
from .models.enums.logic import Logic
from .models.enums.start_location import StartLocation
from .models.randomizer_data import RandomizerData
from .constants import Constants as constants


class World:
    settings: RandomizerData = None
    placement_log = []
    spoilers = []
    dark_space_sets = [[46, 47], [58, 60]]
    required_items = [20, 36]
    good_items = [10, 13, 24, 25, 49, 50, 51]
    trolly_locations = [32, 45, 64, 65, 102, 108, 121, 128, 136, 147]
    free_locations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 24]
    start_loc = 10

    # Assigns item to location
    def fill_item(self, item, location=-1) -> bool:
        if location == -1:
            return False
        elif constants.ITEM_LOCATIONS[location][2]:
            return False

        constants.ITEM_POOL[item][0] -= 1
        constants.ITEM_LOCATIONS[location][2] = True
        constants.ITEM_LOCATIONS[location][3] = item

        self.placement_log.append([item, location])

        return True

    # Removes an assigned item and returns it to item pool
    def unfill_item(self, location=-1):
        if location == -1:
            return 0
        elif not constants.ITEM_LOCATIONS[location][2]:
            return 0

        item = constants.ITEM_LOCATIONS[location][3]
        constants.ITEM_LOCATIONS[location][2] = False
        constants.ITEM_POOL[item][0] += 1

        for x in self.placement_log:
            if x[1] == location:
                self.placement_log.remove(x)

        return item

    # Find and clear non-progression item to make room for progression item
    def make_room(self, item_locations, inv=False, count=1):
        unfilled = []
        while count > 0:
            i = 0
            done = False
            while not done:
                loc = item_locations[i]
                region = constants.ITEM_LOCATIONS[loc][0]
                type = constants.ITEM_LOCATIONS[loc][1]

                if type == 1 and constants.ITEM_LOCATIONS[loc][2]:
                    item = constants.ITEM_LOCATIONS[loc][3]
                    if inv and not constants.GRAPH[region][0] and constants.ITEM_POOL[item][4]:
                        done = True
                    elif not inv and constants.GRAPH[region][0] and constants.ITEM_POOL[item][5] != 1:
                        done = True

                if done:
                    self.unfill_item(loc)
                    unfilled.append(loc)

                i += 1
                if i >= len(item_locations):
                    return []
            count -= 1

        return unfilled

    # Converts item pool into list of unique items, returns list
    def list_item_pool(self, type=0, items=[], progress_type=0):
        item_list = []
        for x in constants.ITEM_POOL:
            if not items or x in items:
                if type == 0 or type == constants.ITEM_POOL[x][1]:
                    if progress_type == 0 or progress_type == constants.ITEM_POOL[x][5]:
                        i = 0
                        while i < constants.ITEM_POOL[x][0]:
                            item_list.append(x)
                            i += 1
        return item_list

    # Returns a list of unfilled item locations
    def list_item_locations(self):
        locations = []
        for x in constants.ITEM_LOCATIONS:
            locations.append(x)
        return locations

    # Returns list of graph edges
    def list_logic(self):
        edges = []
        for x in self.world_logic:
            edges.append(x)
        return edges

    # Checks if one list is contained inside another list
    def is_sublist(self, list, sublist):
        if sublist == []:
            return True
        elif sublist == list:
            return True
        elif len(sublist) > len(list):
            return False

        l = list[:]

        for x in sublist:
            if x in l:
                l.remove(x)
            else:
                return False

        return True

    # Returns lists of accessible item, ability, and statue locations
    def open_locations(self):
        # Accessible open location for items, abilities, and Mystic Statues
        locations = [[], [], []]
        for x in constants.ITEM_LOCATIONS:
            region = constants.ITEM_LOCATIONS[x][0]
            type = constants.ITEM_LOCATIONS[x][1]
            if constants.GRAPH[region][0] and not constants.ITEM_LOCATIONS[x][2]:
                locations[type - 1].append(x)
        return locations

    # Zeroes out accessible flags for all world regions
    def unsolve(self):
        for x in constants.GRAPH:
            constants.GRAPH[x][0] = False

    # Finds all accessible locations and returns all accessible items
    def traverse(self, start_items=[]):
        # print "Traverse:"
        self.unsolve()
        to_visit = [-1]
        items = start_items[:]
        while to_visit:
            origin = to_visit.pop(0)
            # print "Visiting ",origin

            if not constants.GRAPH[origin][0]:
                constants.GRAPH[origin][0] = True
                for x in constants.GRAPH[origin][1]:
                    if x not in to_visit:
                        to_visit.append(x)
                found_item = False
                for location in constants.ITEM_LOCATIONS:
                    if constants.ITEM_LOCATIONS[location][0] == origin and constants.ITEM_LOCATIONS[location][2]:
                        items.append(constants.ITEM_LOCATIONS[location][3])
                        found_item = True
                        # print "Found item in location: ", constants.ITEM_LOCATIONS[location][3], location
                if found_item:
                    # print "We found an item"
                    for y in constants.GRAPH:
                        if constants.GRAPH[y][0] and y != origin:
                            to_visit.append(y)

            for edge in self.world_logic:
                if self.world_logic[edge][0] == origin:
                    dest = self.world_logic[edge][1]
                    if not constants.GRAPH[dest][0] and dest not in to_visit:
                        req_items = []
                        for req in self.world_logic[edge][2]:
                            i = 0
                            while i < req[1]:
                                req_items.append(req[0])
                                i += 1
                        if self.is_sublist(items, req_items):
                            to_visit.append(dest)

        return items

    # Returns full list of accessible locations
    def accessible_locations(self, item_locations):
        accessible = []
        for x in item_locations:
            region = constants.ITEM_LOCATIONS[x][0]
            if constants.GRAPH[region][0]:
                accessible.append(x)
        return accessible

    # Returns full list of unaccessible locations
    def unaccessible_locations(self, item_locations):
        unaccessible = []
        for x in item_locations:
            region = constants.ITEM_LOCATIONS[x][0]
            if not constants.GRAPH[region][0]:
                unaccessible.append(x)
        return unaccessible

    # Fill a list of items randomly in a list of locations
    def random_fill(self, items=[], item_locations=[], accessible=True):
        if not items:
            return True
        elif not item_locations:
            return False

        to_place = items[:]
        to_fill = item_locations[:]

        while to_place:
            item = to_place.pop(0)
            item_type = constants.ITEM_POOL[item][1]

            placed = False
            i = 0
            for dest in to_fill:
                if not placed:
                    region = constants.ITEM_LOCATIONS[dest][0]
                    location_type = constants.ITEM_LOCATIONS[dest][1]
                    filled = constants.ITEM_LOCATIONS[dest][2]
                    restrictions = constants.ITEM_LOCATIONS[dest][4]
                    if not filled and item_type == location_type and item not in restrictions:
                        if not accessible or region != constants.INACCESSIBLE:
                            if self.fill_item(item, dest):
                                to_fill.remove(dest)
                                placed = True

        return True

    # Place list of items into random accessible locations
    def forward_fill(self, items=[], item_locations=[]):
        if not items:
            return True
        elif not item_locations:
            return False

        to_place = items[:]
        to_fill = item_locations[:]

        item = to_place.pop(0)
        item_type = constants.ITEM_POOL[item][1]

        for dest in to_fill:
            region = constants.ITEM_LOCATIONS[dest][0]
            location_type = constants.ITEM_LOCATIONS[dest][1]
            filled = constants.ITEM_LOCATIONS[dest][2]
            restrictions = constants.ITEM_LOCATIONS[dest][4]
            if constants.GRAPH[region][0] and not filled and constants.ITEM_POOL[item][0] > 0:
                if item_type == location_type and item not in restrictions:
                    # print "Placing item: ", item, dest
                    if self.fill_item(item, dest):
                        to_fill_new = to_fill[:]
                        to_fill_new.remove(dest)
                        if self.forward_fill(to_place, to_fill_new):
                            # print "Filled ",dest," with ",item
                            # self.placement_log.append([item,dest])
                            return True
                        else:
                            item = self.unfill_item(dest)

        return False

    # Convert a prerequisite to a list of items needed to fulfill it
    def items_needed(self, prereq=[], items=[]):
        if not prereq:
            return []
        elif not items:
            return prereq

        prereq_new = prereq[:]
        items_new = items[:]

        for x in prereq:
            if x in items_new:
                prereq_new.remove(x)
                items_new.remove(x)

        return prereq_new

    # Returns list of item combinations that grant progression
    def progression_list(self, start_items=[]):
        open_locations = self.open_locations()
        open_items = len(open_locations[0])
        open_abilities = len(open_locations[1])

        item_pool = self.list_item_pool(1)
        ability_pool = self.list_item_pool(2)
        all_items = item_pool + ability_pool

        prereq_list = []

        for x in self.world_logic:
            origin = self.world_logic[x][0]
            dest = self.world_logic[x][1]
            if constants.GRAPH[origin][0] and not constants.GRAPH[dest][0]:
                prereq = []
                for req in self.world_logic[x][2]:
                    item = req[0]
                    i = 0
                    while i < req[1]:
                        prereq.append(item)
                        i += 1
                prereq = self.items_needed(prereq, start_items)

                item_prereqs = 0
                ability_prereqs = 0
                for y in prereq:
                    if constants.ITEM_POOL[y][1] == 1:
                        item_prereqs += 1
                    elif constants.ITEM_POOL[y][1] == 2:
                        ability_prereqs += 1

                if prereq and self.is_sublist(all_items, prereq) and prereq not in prereq_list:
                    if item_prereqs <= open_items and ability_prereqs <= open_abilities:
                        constants.GRAPH[dest][0] = True
                        start_items_temp = start_items[:] + prereq
                        # for req in prereq:
                        #    if constants.ITEM_POOL[req][4]:
                        #        start_items_temp.append(req)
                        inv_temp = self.get_inventory(start_items_temp)
                        # neg_inv_temp = negative_inventory[:]

                        # for item in inv_temp:
                        #    if item in neg_inv_temp:
                        #        inv_temp.remove(item)
                        #        neg_inv_temp.remove(item)
                        if len(inv_temp) <= constants.MAX_INVENTORY:
                            prereq_list.append(prereq)
                        else:
                            prereq_list.append(-1)
                        constants.GRAPH[dest][0] = False

        if not prereq_list:
            return -1
        else:
            while -1 in prereq_list:
                prereq_list.remove(-1)
            if not prereq_list:
                return -2
            else:
                return prereq_list

    # Converts a progression list into a normalized Monte Carlo distribution
    def monte_carlo(self, progression=[], start_items=[]):
        if not progression:
            return []

        open_locations = self.open_locations()
        open_items = len(open_locations[0])
        open_abilities = len(open_locations[1])

        items = self.list_item_pool(1)
        abilities = self.list_item_pool(2)
        all_items = items + abilities
        sum_items = len(items)
        sum_abilities = len(abilities)

        probability = []

        monte_carlo = []
        sum_prob = 0
        sum_edges = 0

        probabilities = []

        while progression:
            current_prereq = progression.pop(0)
            prereqs = current_prereq[:]
            probability = 1.0
            i = 0
            j = 0
            while prereqs:
                item = prereqs.pop(0)
                if item in all_items:
                    if constants.ITEM_POOL[item][1] == 1:
                        probability *= float(constants.ITEM_POOL[item][0]) / float((sum_items - i))
                        i += 1
                    elif constants.ITEM_POOL[item][1] == 2:
                        probability *= float(constants.ITEM_POOL[item][0]) / float((sum_abilities - j))
                        j += 1
                    if item in self.required_items:
                        probability *= constants.PROGRESS_ADJ[self.settings.difficulty.value]
            probabilities.append([probability, current_prereq])
            sum_prob += probability
            sum_edges += 1

        prob_adj = 100.0 / sum_prob
        rolling_sum = 0
        for x in probabilities:
            x[0] = x[0] * prob_adj + rolling_sum
            rolling_sum = x[0]

        # print probabilities
        return probabilities

    # Returns a list of map lists, by boss
    def get_maps(self):
        maps = [[], [], [], [], [], [], []]
        for map in constants.MAPS:
            boss = constants.MAPS[map][1]
            maps[boss].append(map)

        maps.pop(0)
        return maps

    # Randomize map-clearing rewards
    def map_rewards(self):
        maps = self.get_maps()
        # print maps

        for area in maps:
            random.shuffle(area)

        boss_rewards = 4 - self.settings.difficulty.value

        rewards = []  # Total rewards by mode (HP/STR/DEF)
        if self.settings.difficulty.value == 0:  # Easy: 10/7/7
            rewards += [1] * 10
            rewards += [2] * 7
            rewards += [3] * 7
        elif self.settings.difficulty.value == 1:  # Normal: 10/4/4
            rewards += [1] * 10
            rewards += [2] * 4
            rewards += [3] * 4
        elif self.settings.difficulty.value == 2:  # Hard: 8/2/2
            rewards += [1] * 8
            rewards += [2] * 2
            rewards += [3] * 2
        elif self.settings.difficulty.value == 3:  # Extreme: 6/0/0
            rewards += [1] * 6

        random.shuffle(rewards)

        # Add in rewards, where applicable, by difficulty
        for area in maps:
            i = 0
            while i < boss_rewards:
                map = area[i]
                reward = rewards.pop(0)
                if not self.settings.ohko or reward > 1:  # No HP rewards for OHKO
                    constants.MAPS[map][2] = reward
                i += 1

    # Place Mystic Statues in World
    def fill_statues(self, locations=[148, 149, 150, 151, 152, 153]):
        return self.random_fill([54, 55, 56, 57, 58, 59], locations)

    def lock_dark_spaces(self, item_locations=[]):
        for set in self.dark_space_sets:
            ds = -1
            for location in item_locations:
                if location in set:
                    ds = location
            if ds == -1:
                return False
            else:
                constants.ITEM_LOCATIONS[ds][2] = True
        return True

    # Initialize World parameters
    def initialize(self):
        # Manage required items
        if 1 in self.statues:
            self.required_items += [3, 4, 7, 8]
        if 2 in self.statues:
            self.required_items += [14]
        if 3 in self.statues:
            self.required_items += [18, 19]
        if 4 in self.statues:
            self.required_items += [50, 51]
        if 5 in self.statues:
            self.required_items += [38, 30, 31, 32, 33, 34, 35]
        if 6 in self.statues:
            self.required_items += [39]

        if self.kara == 1:
            self.required_items += [2, 9, 23]
        elif self.kara == 2:
            self.required_items += [11, 12, 15]
        elif self.kara == 3:
            self.required_items += [49]
        elif self.kara == 4:
            self.required_items += [26, 50]
        elif self.kara == 5:
            self.required_items += [28, 50, 53]

        # Update inventory space logic
        if 3 in self.statues:
            constants.ITEM_POOL[19][4] = True
        if 5 in self.statues:
            constants.ITEM_POOL[30][4] = True
            constants.ITEM_POOL[31][4] = True
            constants.ITEM_POOL[32][4] = True
            constants.ITEM_POOL[33][4] = True
            constants.ITEM_POOL[34][4] = True
            constants.ITEM_POOL[35][4] = True
            constants.ITEM_POOL[38][4] = True

        # Random start location
        if self.settings.start_location.value != StartLocation.SOUTH_CAPE.value:
            self.start_loc = self.random_start()
            constants.GRAPH[-1][1] = [constants.ITEM_LOCATIONS[self.start_loc][0]]

        # Chaos mode
        if self.settings.logic.value == Logic.CHAOS.value:
            # Add "Inaccessible" node to graph
            constants.GRAPH[constants.INACCESSIBLE] = [False, [], "Inaccessible", []]

            # Towns can have Freedan abilities
            for x in [10, 14, 22, 39, 57, 66, 77, 88, 103, 114, 129, 145, 146]:
                for y in [51, 52, 53]:
                    constants.ITEM_LOCATIONS[x][4].remove(y)

            # Several locked Dark Spaces can have abilities
            ds_unlock = [74, 94, 124, 142]

            if 1 not in self.statues:  # First DS in Inca
                ds_unlock.append(29)
            if 4 in self.statues:
                self.dark_space_sets.append([93, 94])
            if self.kara != 1:  # DS in Underground Tunnel
                ds_unlock.append(19)
            if self.kara != 5:  # DS in Ankor Wat garden
                ds_unlock.append(122)

            for x in ds_unlock:
                constants.ITEM_LOCATIONS[x][2] = False

        # Change graph logic depending on Kara's location
        if self.kara == 1:
            self.world_logic[150][2][0][1] = 1
            constants.GRAPH[10][3].append(20)
        elif self.kara == 2:
            self.world_logic[151][2][0][1] = 1
            constants.GRAPH[26][3].append(20)
            # Change "Sam" to "Samlet"
            constants.LOCATION_TEXT[45] = b"\x63\x80\x8c\x8b\x84\xa4"
        elif self.kara == 3:
            self.world_logic[152][2][0][1] = 1
            constants.GRAPH[43][3].append(20)
        elif self.kara == 4:
            self.world_logic[153][2][0][1] = 1
            constants.GRAPH[53][3].append(20)
        elif self.kara == 5:
            self.world_logic[154][2][0][1] = 1
            constants.GRAPH[60][3].append(20)

        # Change logic based on which statues are required
        for x in self.statues:
            self.world_logic[155][2][x][1] = 1

    #        print self.start_loc
    #        for x in constants.GRAPH:
    #            print x, constants.GRAPH[x]
    #        for y in self.world_logic:
    #            print y, self.world_logic[y]

    # Update item placement logic after abilities are placed
    def check_logic(self):
        abilities = [48, 49, 50, 51, 52, 53]
        inaccessible = []

        # Check for abilities in critical Dark Spaces
        if constants.ITEM_LOCATIONS[19][3] in abilities:  # Underground Tunnel
            inaccessible += [17, 18]
        if constants.ITEM_LOCATIONS[29][3] in abilities:  # Inca Ruins
            inaccessible += [26, 27, 30, 31, 32]
            constants.GRAPH[18][1].remove(19)
        if (constants.ITEM_LOCATIONS[46][3] in abilities and  # Diamond Mine
                constants.ITEM_LOCATIONS[47][3] in abilities and
                constants.ITEM_LOCATIONS[48][3] in abilities):
            del self.world_logic[73]
        if (constants.ITEM_LOCATIONS[58][3] in abilities and  # Sky Garden
                constants.ITEM_LOCATIONS[59][3] in abilities and
                constants.ITEM_LOCATIONS[60][3] in abilities):
            del self.world_logic[77]
        if constants.ITEM_LOCATIONS[94][3] in abilities:  # Great Wall
            constants.GRAPH[200] = [False, [], "Great Wall - Behind Slider or Spin", []]
            self.world_logic[200] = [45, 200, [[49, 1]]]
            self.world_logic[201] = [45, 200, [[50, 1]]]
            constants.ITEM_LOCATIONS[93][0] = 200
            if constants.ITEM_LOCATIONS[93][3] in abilities:
                inaccessible += [95]
        if constants.ITEM_LOCATIONS[122][3] in abilities:  # Ankor Wat
            inaccessible += [117, 118, 119, 120, 121]
        #        if constants.ITEM_LOCATIONS[142][3] in abilities:        # Pyramid
        #            inaccessible += [133,134,136,139,140]

        # Change graph node for inaccessible locations
        for x in inaccessible:
            constants.ITEM_LOCATIONS[x][0] = constants.INACCESSIBLE

    # Simulate inventory
    def get_inventory(self, start_items=[]):
        inventory = []
        for item in start_items:
            if constants.ITEM_POOL[item][4]:
                inventory.append(item)

        negative_inventory = []
        for node in constants.GRAPH:
            if constants.GRAPH[node][0]:
                negative_inventory += constants.GRAPH[node][3]

        i = 0
        while i < len(inventory):
            item = inventory[i]
            if inventory[i] in negative_inventory:
                inventory.remove(item)
                negative_inventory.remove(item)
            else:
                i += 1

        return inventory

    # Takes a random seed and builds out a randomized world
    def randomize(self, seed_adj=0):
        self.initialize()

        solved = False

        random.seed(self.settings.seed + seed_adj)

        # Assign map rewards
        self.map_rewards()

        # Initialize and shuffle location list
        item_locations = self.list_item_locations()
        random.shuffle(item_locations)

        # Fill the Mustic Statues
        self.fill_statues()
        if not self.lock_dark_spaces(item_locations):
            print("ERROR: Couldn't lock dark spaces")
            return False

        # Randomly place non-progression items and abilities
        non_prog_items = self.list_item_pool(0, [], 2)
        non_prog_items += self.list_item_pool(0, [], 3)

        # For Easy mode
        if self.settings.logic.value == Logic.CHAOS.value or self.settings.difficulty.value > 2:
            non_prog_items += self.list_item_pool(2)
        elif self.settings.difficulty.value == 0:
            non_prog_items += [52]
        elif self.settings.difficulty.value == 1:
            non_prog_items += [49, 50, 52, 53]

        random.shuffle(non_prog_items)
        self.random_fill(non_prog_items, item_locations)

        # Check if ability placement affects logic
        self.check_logic()

        # List and shuffle remaining key items
        item_list = self.list_item_pool()
        random.shuffle(item_list)

        inventory = []

        # Forward fill progression items with Monte Carlo simulation method
        # Continue to place progression items until all locations are accessible
        done = False
        goal = False
        cycle = 0

        # while self.unaccessible_locations(item_locations):
        while not done:
            cycle += 1
            if cycle > constants.MAX_CYCLES:
                print("ERROR: Max cycles exceeded")
                return False

            start_items = self.traverse()
            # print "We found these: ",start_items

            inv_size = len(self.get_inventory(start_items))
            if inv_size > constants.MAX_INVENTORY:
                goal = False
                print("ERROR: Inventory capacity exceeded")
            else:
                goal = ((self.settings.goal.value == Goal.DARK_GAIA.value and constants.GRAPH[70][0]) or
                        (self.settings.goal.value == Goal.RED_JEWEL_HUNT.value and constants.GRAPH[68][0]))

            # Get list of new progression options
            progression_list = self.progression_list(start_items)

            done = goal and (self.settings.logic.value != Logic.COMPLETABLE.value or progression_list == -1)
            # print done, progression_list

            if not done and progression_list == -1:  # No empty locations available
                removed = self.make_room(item_locations)
                if not removed:
                    print("ERROR: Could not remove non-progression item")
                    return False
                progression_list = []
            elif not done and progression_list == -2:  # All new locations have too many inventory items
                removed = self.make_room(item_locations, True)
                if not removed:
                    print("ERROR: Could not remove inventory item")
                    return False
                progression_list = []

            # print "To progress: ",progression_list

            #            if not done and not progression_list:
            #                #print "Gotta make room..."
            #                removed = self.make_room(item_locations,inv_full)
            #                if not removed:
            #                    print "ERROR: Could not remove non-progression item"
            #                    return False
            #                #print "Cleared this location: ", removed

            if not done and progression_list:
                # Determine next progression items to add to accessible locations
                progression_mc = self.monte_carlo(progression_list)
                progress = False
                while not progress:
                    key = random.uniform(0, 100)
                    # print key
                    items = []
                    for x in progression_mc:
                        if key <= x[0] and not items:
                            items = x[1]

                    if not items:
                        print("What happened?")
                        # done = True
                    elif self.forward_fill(items, item_locations):
                        progress = True
                        # print "We made progress!",items
                        # print constants.GRAPH

            # print goal, done

        # print "Unaccessible: ",self.unaccessible_locations(item_locations)
        #        for node in constants.GRAPH:
        #            if not constants.GRAPH[node][0]:
        #                print "Can't reach ",constants.GRAPH[node][2]

        junk_items = self.list_item_pool()
        self.random_fill(junk_items, item_locations, False)

        placement_log = self.placement_log[:]
        random.shuffle(placement_log)
        self.in_game_spoilers(placement_log)

        # print cycle

        return True

    # Prepares dataset to give in-game spoilers
    def in_game_spoilers(self, placement_log=[]):
        for x in placement_log:
            item = x[0]
            location = x[1]

            if location not in self.free_locations:
                if item in self.required_items or item in self.good_items or location in self.trolly_locations:
                    spoiler_str = b"\xd3" + constants.LOCATION_TEXT[location] + b"\xac\x87\x80\xa3\xcb"
                    spoiler_str += constants.ITEM_TEXT_SHORT[item] + b"\xc0"
                    # No in-game spoilers in Extreme mode
                    if self.settings.difficulty.value == Difficulty.EXTREME.value:
                        spoiler_str = b"\xd3\x8d\x88\x82\x84\xac\xa4\xa2\xa9\xac\x83\x8e\x83\x8e\x8d\x86\x8e\x4f\xc0"
                    self.spoilers.append(spoiler_str)
                    # print item, location

    # Prints item and ability locations
    def generate_spoiler(self, folder="", version="", filename="IoGR_spoiler"):
        if not os.path.exists(folder):
            os.makedirs(folder)
            return

        if self.kara == 1:
            kara_txt = "Edward's Castle"
        elif self.kara == 2:
            kara_txt = "Diamond Mine"
        elif self.kara == 3:
            kara_txt = "Angel Dungeon"
        elif self.kara == 4:
            kara_txt = "Mt. Kress"
        elif self.kara == 5:
            kara_txt = "Ankor Wat"

        f = open(folder + filename + ".txt", "w+")

        f.write("Illusion of Gaia Randomizer - " + version + "\r\n")
        f.write("Seed generated " + str(datetime.today()) + "\r\n")

        f.write("\r\n")
        f.write("Seed                                  >  " + str(self.settings.seed) + "\r\n")
        f.write("Goal                                  >  " + str(self.settings.goal.name) + "\r\n")
        f.write("Logic                                 >  " + str(self.settings.logic.name) + "\r\n")
        f.write("Difficulty                            >  " + str(self.settings.difficulty.name) + "\r\n")
        f.write("\r\n")

        f.write("Statues Required                      >  " + str(self.statues) + "\r\n")
        f.write("Kara Location                         >  " + kara_txt + "\r\n")
        f.write("Jeweler Reward Amounts                >  " + str(self.gem) + "\r\n")
        f.write("Inca Tile (column, row)               >  " + str(self.incatile) + "\r\n")
        f.write("Hieroglyph Order                      >  " + str(self.hieroglyphs) + "\r\n")
        f.write("\r\n")

        for x in constants.ITEM_LOCATIONS:
            item = constants.ITEM_LOCATIONS[x][3]
            location_name = constants.ITEM_LOCATIONS[x][9]
            item_name = constants.ITEM_POOL[item][3]
            f.write(location_name + "  >  " + item_name + "\r\n")

    def print_enemy_locations(self, filepath, offset=0):
        f = open(filepath, "r+b")
        rom = f.read()
        for enemy in constants.ENEMIES:
            print(constants.ENEMIES[enemy][3])
            done = False
            addr = int("c8200", 16) + offset
            while not done:
                addr = rom.find(constants.ENEMIES[enemy][1], addr + 1)
                if addr < 0 or addr > int("ce5e4", 16) + offset:
                    done = True
                else:
                    f.seek(addr)
                    # f.write(b"\x55\x87\x8a\x05")
                    print(" ", addr, hex(addr), binascii.hexlify(f.read(4)))
        f.close

    # Prints item and ability locations
    def print_spoiler(self):
        if self.kara == 1:
            kara_txt = "Edward's Castle"
        elif self.kara == 2:
            kara_txt = "Diamond Mine"
        elif self.kara == 3:
            kara_txt = "Angel Dungeon"
        elif self.kara == 4:
            kara_txt = "Mt. Kress"
        elif self.kara == 5:
            kara_txt = "Ankor Wat"

        print("")
        print("Seed                                   >  ", self.settings.seed)
        print("Statues Required                       >  ", self.statues)
        print("Kara Location                          >  ", kara_txt)
        print("Jeweler Reward Amounts                 >  ", self.gem)
        print("Inca Tile (column, row)                >  ", self.incatile)
        print("Hieroglyph Order                       >  ", self.hieroglyphs)
        print("")

        for x in constants.ITEM_LOCATIONS:
            item = constants.ITEM_LOCATIONS[x][3]
            location_name = constants.ITEM_LOCATIONS[x][9]
            item_name = constants.ITEM_POOL[item][3]
            print(location_name, "  >  ", item_name)

    # Modifies game ROM to reflect the current state of the World
    def write_to_rom(self, f, rom_offset=0):
        # Room-clearing rewards
        for map in constants.MAPS:
            reward = constants.MAPS[map][2]
            if reward > 0:
                f.seek(int("1aade", 16) + map + rom_offset)
                if reward == 1:
                    f.write(b"\x01")
                elif reward == 2:
                    f.write(b"\x02")
                elif reward == 3:
                    f.write(b"\x03")

        # Items and abilities
        for x in constants.ITEM_LOCATIONS:
            type = constants.ITEM_LOCATIONS[x][1]

            # Write items to ROM
            if type == 1:
                item = constants.ITEM_LOCATIONS[x][3]
                # print "Writing item ", item
                item_addr = constants.ITEM_LOCATIONS[x][5]
                item_code = constants.ITEM_POOL[item][2]
                text1_addr = constants.ITEM_LOCATIONS[x][6]
                text2_addr = constants.ITEM_LOCATIONS[x][7]
                text3_addr = constants.ITEM_LOCATIONS[x][8]
                text_long = constants.ITEM_TEXT_LONG[item]
                text_short = constants.ITEM_TEXT_SHORT[item]

                # Write item code to memory
                if item_code:
                    f.seek(int(item_addr, 16) + rom_offset)
                    f.write(item_code)

                # Write item text, if appropriate
                if text1_addr:
                    f.seek(int(text1_addr, 16) + rom_offset)
                    f.write(text_long)
                    # f.write(b"\xd3")
                    # f.write(text_short)
                    f.write(b"\xc0")

                # Write "inventory full" item text, if appropriate
                if text2_addr:
                    f.seek(int(text2_addr, 16) + rom_offset)
                    # f.write(b"\xd3")
                    # f.write(text_short)
                    f.write(text_long)
                    f.write(b"\xcb\x45\x65\x4b\x4b\x4f\xc0")  # Just says "FULL!"

                # Write jeweler inventory text, if apprpriate
                if text3_addr:
                    f.seek(int(text3_addr, 16) + rom_offset)
                    f.write(text_short)

            # Write abilities to ROM
            elif type == 2:  # Check if filled
                ability = constants.ITEM_LOCATIONS[x][3]
                ability_addr = constants.ITEM_LOCATIONS[x][5]
                map = constants.ITEM_LOCATIONS[x][8]

                # Change Dark Space type in event table
                if ability in [48, 49, 50, 51, 52, 53]:
                    f.seek(int(ability_addr, 16) + rom_offset)
                    f.write(b"\x05")

                # Update ability text table
                if ability == 48:  # Psycho Dash
                    # f.seek(int("8eb5a",16)+2*i+rom_offset)
                    f.seek(int("8eb5a", 16) + rom_offset)
                    f.write(map)
                if ability == 49:  # Psycho Slide
                    f.seek(int("8eb5c", 16) + rom_offset)
                    f.write(map)
                if ability == 50:  # Spin Dash
                    f.seek(int("8eb5e", 16) + rom_offset)
                    f.write(map)
                if ability == 51:  # Dark Friar
                    f.seek(int("8eb60", 16) + rom_offset)
                    f.write(map)
                if ability == 52:  # Aura Barrier
                    f.seek(int("8eb62", 16) + rom_offset)
                    f.write(map)
                if ability == 53:  # Earthquaker
                    f.seek(int("8eb64", 16) + rom_offset)
                    f.write(map)

        # Special code for 2-item event in Dao
        item1 = constants.ITEM_LOCATIONS[125][3]
        item2 = constants.ITEM_LOCATIONS[126][3]
        f.seek(int("8fde0", 16) + rom_offset)
        f.write(b"\xd3" + constants.ITEM_TEXT_SHORT[item1] + b"\xcb")
        f.write(constants.ITEM_TEXT_SHORT[item2] + b"\xcf\xce")

        # Write in-game spoilers
        i = 0
        for addr in constants.SPOILER_ADDRESSES:
            f.seek(int(constants.SPOILER_ADDRESSES[addr], 16) + rom_offset)
            if i < len(self.spoilers):
                f.write(self.spoilers[i])
                i += 1

        # Enemizer
        if self.settings.enemizer.value != Enemizer.NONE.value:
            # "Fix" Ankor Wat Gorgons so they don't fall from the ceiling
            f.seek(int("bb825", 16) + rom_offset)
            f.write(b"\x00\x00\x00\x02\x27\x0F\x02\xC1\x4C\xA0\xB8\x6B")

            # Run enemizer
            self.enemize(f, rom_offset)
            # self.parse_maps(f,rom_offset)

        # Random start location
        if self.settings.start_location != StartLocation.SOUTH_CAPE.value:
            # print self.start_loc
            map_str = constants.ITEM_LOCATIONS[self.start_loc][8] + constants.ITEM_LOCATIONS[self.start_loc][7]

            # Change game start location
            f.seek(int("be517", 16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp location
            f.seek(int("8dbea", 16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp text
            map_name = constants.LOCATION_TEXT[self.start_loc]
            f.seek(int("8de1f", 16) + rom_offset)
            f.write(map_name + b"\x0D\xCB\xAC\x4D\x8E\xCB\xAC\x69\x84\xA3\xCA")

            # Check for additional switches that need to be set
            switch_str = ""
            if self.start_loc == 30:  # Inca ramp can hardlock you
                switch_str = b"\x02\xcd\x0c\x01"
            elif self.start_loc == 47:  # Diamond Mine behind fences
                switch_str = b"\x02\xcd\x34\x01\x02\xcd\x35\x01\x02\xcd\x36\x01"

            if switch_str:
                f.seek(int("bfdf3", 16) + rom_offset)
                f.write(switch_str + b"\x02\xe0")

        # print "ROM successfully created"

    # Shuffle enemies in ROM
    def parse_maps(self, f, rom_offset=0):
        f.seek(int("d8000", 16) + rom_offset)

        header_lengths = {
            b"\x02": 1,
            b"\x03": 7,
            b"\x04": 6,
            b"\x05": 7,
            b"\x06": 4,
            b"\x0e": 3,
            b"\x10": 6,
            b"\x11": 5,
            b"\x13": 2,
            b"\x14": 1,
            b"\x15": 1,
            b"\x17": 5
        }

        done = False
        addr = 0
        map_dataset = {}
        anchor_dataset = {}

        while not done:
            map_id = f.read(2)
            print(binascii.hexlify(map_id))
            map_headers = []
            anchor_headers = []
            map_done = False
            anchor = False
            while not map_done:
                map_header = f.read(1)
                if map_header == b"\x14":
                    anchor = True
                    anchor_id = f.read(1)
                    map_header += anchor_id
                    map_headers.append(map_header)
                    print(binascii.hexlify(map_header))
                elif map_header == b"\x00":
                    map_done = True
                    print(binascii.hexlify(map_header))
                    print("")
                else:
                    header_len = header_lengths[map_header]
                    map_header += f.read(header_len)
                    map_headers.append(map_header)
                    print(binascii.hexlify(map_header))
                    if anchor:
                        anchor_headers.append(map_header)

            anchor_dataset[map_id] = map_headers
            if anchor_headers:
                anchor_dataset[anchor_id] = anchor_headers

            if f.tell() >= int("daffe", 16) + rom_offset:
                done = True

        #        print map_headers
        print(anchor_headers)

    # Pick random start location
    def random_start(self):
        locations = []
        for loc in constants.ITEM_LOCATIONS:
            if (self.settings.start_location.value == StartLocation.FORCED_UNSAFE and constants.ITEM_LOCATIONS[loc][6] == "Unsafe") or (
                    self.settings.start_location.value != StartLocation.FORCED_UNSAFE and constants.ITEM_LOCATIONS[loc][6] == "Safe") or (
                    constants.ITEM_LOCATIONS[loc][6] == self.settings.start_location.value):
                locations.append(loc)

        if not locations:
            print("ERROR: Something is fishy with start locations")
            return -1
        else:
            # print locations
            # return 93   # TESTING!
            return locations[random.randint(0, len(locations) - 1)]

    # Shuffle enemies in ROM
    def enemize(self, f, rom_offset=0):
        f.seek(0)
        rom = f.read()

        # test_enemy = 13                         # TESTING!
        # test_set = constants.ENEMIES[test_enemy][0]

        complex_enemies = [4, 15, 53, 62, 88]  # Enemies with many sprites, or are no fun
        max_complex = 5

        # Get list of enemysets
        enemysets = []
        for set in constants.ENEMY_SETS:
            enemysets.append(set)

        f.seek(0)
        rom = f.read()

        # Shuffle enemy stats in Insane
        if self.settings.enemizer.value == Enemizer.INSANE.value:
            insane_enemies = []
            insane_templates = []
            for enemy in constants.ENEMIES:
                if constants.ENEMIES[enemy][5] and enemy != 102:  # Special exception for Zombies
                    insane_enemies.append(enemy)
                    insane_templates.append(constants.ENEMIES[enemy][2])

            random.shuffle(insane_templates)
            insane_dictionary = {}
            i = 0

            for enemy in insane_enemies:
                insane_dictionary[enemy] = insane_templates[i]
                i += 1

        # Randomize enemy spritesets
        for map_index in constants.MAPS:
            complex_ct = 0
            oldset = constants.MAPS[map_index][0]
            # Determine new enemyset for map
            if self.settings.enemizer.value == Enemizer.LIMITED.value:
                sets = [oldset]
            elif not constants.MAPS[map_index][7]:
                sets = enemysets[:]
            else:
                sets = constants.MAPS[map_index][7][:]

            random.shuffle(sets)
            newset = sets[0]
            # if 10 in sets:      # TESTING!
            #    newset = 10
            # newset = test_set  # TESTING!

            # Gather enemies from old and new sets
            old_enemies = []
            new_enemies = []
            for enemy in constants.ENEMIES:
                if constants.ENEMIES[enemy][0] == oldset:
                    old_enemies.append(enemy)
                if constants.ENEMIES[enemy][0] == newset and constants.ENEMIES[enemy][5]:
                    new_enemies.append(enemy)

            # Update map header to reflect new enemyset
            if constants.MAPS[map_index][3]:
                addr = rom.find(constants.MAPS[map_index][3], int("d8000", 16) + rom_offset)
                if addr < 0 or addr > int("daffe", 16) + rom_offset:
                    print("ERROR: Couldn't find header for map ", map_index)
                else:
                    f.seek(addr + constants.MAPS[map_index][4])
                    f.write(constants.ENEMY_SETS[newset][0])

            # Randomize each enemy in map
            addr_start = constants.MAPS[map_index][5]
            addr_end = constants.MAPS[map_index][6]
            for enemy in old_enemies:
                # print constants.ENEMIES[enemy][3]
                done = False
                addr = int(addr_start, 16) + rom_offset
                while not done:
                    addr = rom.find(constants.ENEMIES[enemy][1] + constants.ENEMIES[enemy][2], addr + 1)
                    if addr < 0 or addr > int(addr_end, 16) + rom_offset:
                        done = True
                    else:
                        # Pick an enemy from new set
                        enemytype = constants.ENEMIES[enemy][3]
                        walkable = constants.ENEMIES[enemy][4]

                        new_enemies_tmp = new_enemies[:]

                        # Get X/Y for special placement exceptions
                        f.seek(addr - 3)
                        xcoord = binascii.hexlify(f.read(1))
                        ycoord = binascii.hexlify(f.read(1))

                        # 4-Ways cannot be on a #$XF x-coord
                        if newset == 1 and 13 in new_enemies_tmp:
                            if xcoord[1] == "f":
                                new_enemies_tmp.remove(13)
                        # Zip Flies can't be too close to map origin
                        elif newset == 10 and 103 in new_enemies_tmp:
                            if int(xcoord, 16) <= 4 or int(ycoord, 16) <= 4:
                                new_enemies_tmp.remove(103)

                        random.shuffle(new_enemies_tmp)

                        i = 0
                        found_enemy = False

                        # if 13 in new_enemies_tmp:   # TESTING!
                        #    new_enemy = 13
                        #    found_enemy = True

                        while not found_enemy:
                            new_enemy = new_enemies_tmp[i]
                            new_enemytype = constants.ENEMIES[new_enemy][3]
                            new_walkable = constants.ENEMIES[new_enemy][4]
                            if walkable or new_enemytype == 3 or walkable == new_walkable or i == len(new_enemies_tmp) - 1:
                                found_enemy = True
                                # Limit number of complex enemies per map
                                if new_enemy in complex_enemies:
                                    complex_ct += 1
                                    if complex_ct >= max_complex:
                                        for enemy_tmp in new_enemies:
                                            if enemy_tmp in complex_enemies:
                                                new_enemies.remove(enemy_tmp)
                                                i -= 1
                            i += 1
                        f.seek(addr - 1)
                        # f.write(b"\x00" + constants.ENEMIES[test_enemy][1] + constants.ENEMIES[test_enemy][2])  # TESTING!
                        f.write(b"\x00" + constants.ENEMIES[new_enemy][1])
                        if self.settings.enemizer.value == Enemizer.BALANCED.value and enemy == 102:
                            f.write(b"\x47")
                        elif map_index != 27 and self.settings.enemizer.value != Enemizer.BALANCED.value:  # Moon Tribe cave enemies retain same template
                            if self.settings.enemizer.value == Enemizer.INSANE.value and new_enemy != 102:  # Again, zombie exception
                                f.write(insane_dictionary[new_enemy])
                            else:
                                f.write(constants.ENEMIES[new_enemy][2])

        # Disable all non-enemy sprites
        if self.settings.enemizer.value == Enemizer.LIMITED.value:
            for sprite in constants.NOENEMY_SPRITES:
                f.seek(int(constants.NOENEMY_SPRITES[sprite][1], 16) + rom_offset + 3)
                f.write(b"\x02\xe0")

    # Build world
    def __init__(self, settings: RandomizerData, statues=None, kara=3, gem=None, incatile=None, hieroglyphs=None):
        if incatile is None:
            incatile = [9, 5]
        if hieroglyphs is None:
            hieroglyphs = [1, 2, 3, 4, 5, 6]
        if gem is None:
            gem = [3, 5, 8, 12, 20, 30, 50]
        if statues is None:
            statues = [1, 2, 3, 4, 5, 6]

        self.settings = settings
        self.statues = statues
        self.kara = kara
        self.gem = gem
        self.incatile = incatile
        self.hieroglyphs = hieroglyphs

        # Format: { ID: [StartRegion, DestRegion, [[item1, qty1],[item2,qty2]...]]}
        self.world_logic = {
            # Jeweler Rewards
            0: [74, 1, [[1, gem[0]]]],  # Jeweler Reward 1
            1: [74, 1, [[1, gem[0] - 2], [46, 1]]],

            2: [74, 1, [[1, gem[0] - 3], [47, 1]]],
            3: [74, 1, [[1, gem[0] - 5], [46, 1], [47, 1]]],
            4: [1, 2, [[1, gem[1]]]],  # Jeweler Reward 2
            5: [1, 2, [[1, gem[1] - 2], [46, 1]]],
            6: [1, 2, [[1, gem[1] - 3], [47, 1]]],
            7: [1, 2, [[1, gem[1] - 5], [46, 1], [47, 1]]],
            8: [2, 3, [[1, gem[2]]]],  # Jeweler Reward 3
            9: [2, 3, [[1, gem[2] - 2], [46, 1]]],
            10: [2, 3, [[1, gem[2] - 3], [47, 1]]],
            11: [2, 3, [[1, gem[2] - 5], [46, 1], [47, 1]]],
            12: [3, 4, [[1, gem[3]]]],  # Jeweler Reward 4
            13: [3, 4, [[1, gem[3] - 2], [46, 1]]],
            14: [3, 4, [[1, gem[3] - 3], [47, 1]]],
            15: [3, 4, [[1, gem[3] - 5], [46, 1], [47, 1]]],
            16: [4, 5, [[1, gem[4]]]],  # Jeweler Reward 5
            17: [4, 5, [[1, gem[4] - 2], [46, 1]]],
            18: [4, 5, [[1, gem[4] - 3], [47, 1]]],
            19: [4, 5, [[1, gem[4] - 5], [46, 1], [47, 1]]],
            20: [5, 6, [[1, gem[5]]]],  # Jeweler Reward 6
            21: [5, 6, [[1, gem[5] - 2], [46, 1]]],
            22: [5, 6, [[1, gem[5] - 3], [47, 1]]],
            23: [5, 6, [[1, gem[5] - 5], [46, 1], [47, 1]]],
            24: [6, 68, [[1, gem[6]]]],  # Jeweler Reward 7 (Mansion)
            25: [6, 68, [[1, gem[6] - 2], [46, 1]]],
            26: [6, 68, [[1, gem[6] - 3], [47, 1]]],
            27: [6, 68, [[1, gem[6] - 5], [46, 1], [47, 1]]],

            # Inter-Continental Travel
            30: [0, 20, [[37, 1]]],  # Cape to Coast w/ Lola's Letter
            31: [0, 44, [[37, 1]]],  # Cape to Watermia w/ Lola's Letter
            32: [20, 0, [[37, 1]]],  # Coast to Cape w/ Lola's Letter
            33: [20, 44, [[37, 1]]],  # Coast to Watermia w/ Lola's Letter
            34: [44, 0, [[37, 1]]],  # Watermia to Cape w/ Lola's Letter
            35: [44, 20, [[37, 1]]],  # Watermia to Coast w/ Lola's Letter
            36: [27, 48, [[13, 1]]],  # Neil's to Euro w/ Memory Melody
            37: [27, 61, [[13, 1]]],  # Neil's to Dao w/ Memory Melody
            38: [27, 66, [[13, 1]]],  # Neil's to Babel w/ Memory Melody
            39: [14, 28, [[25, 1]]],  # Moon Tribe to Nazca w/ Teapot
            40: [14, 33, [[25, 1]]],  # Moon Tribe to Seaside Palace w/ Teapot
            41: [44, 48, [[24, 1]]],  # Watermia to Euro w/ Will
            42: [48, 44, [[24, 1]]],  # Euro to Watermia w/ Will
            43: [54, 61, [[10, 1]]],  # Natives' to Dao w/ Large Roast

            # SW Continent
            50: [0, 12, [[9, 1]]],  # Cape to Itory w/ Lola's Melody
            51: [8, 9, [[2, 1]]],  # Prison to Tunnel w/ Prison Key
            52: [75, 10, [[2, 1]]],  # Tunnel Progression w/ Lilly
            53: [12, 13, [[48, 1]]],  # Itory Cave w/ Psycho Dash
            54: [12, 13, [[49, 1]]],  # Itory Cave w/ Psycho Slide
            55: [12, 13, [[50, 1]]],  # Itory Cave w/ Spin Dash
            56: [12, 75, [[23, 1]]],  # Get Lilly w/ Necklace
            57: [14, 29, [[25, 1]]],  # Moon Tribe to Sky Garden w/ Teapot
            58: [15, 16, [[7, 1], [48, 1]]],  # Inca Ruins w/ Tile and Psycho Dash
            59: [15, 16, [[7, 1], [49, 1]]],  # Inca Ruins w/ Tile and Psycho Slide
            60: [15, 16, [[7, 1], [50, 1]]],  # Inca Ruins w/ Tile and Spin Dash
            61: [16, 17, [[8, 1]]],  # Inca Ruins w/ Wind Melody
            62: [17, 18, [[3, 1], [4, 1]]],  # Inca Ruins w/ Inca Statues
            63: [14, 73, [[48, 1]]],  # Moon Tribe Cave w/ Psycho Dash
            64: [14, 73, [[49, 1]]],  # Moon Tribe Cave w/ Psycho Slider
            65: [14, 73, [[50, 1]]],  # Moon Tribe Cave w/ Spin Dash

            # SE Continent
            70: [22, 23, [[48, 1]]],  # Diamond Mine Progression w/ Psycho Dash
            71: [22, 23, [[49, 1]]],  # Diamond Mine Progression w/ Psycho Slide
            72: [22, 23, [[50, 1]]],  # Diamond Mine Progression w/ Spin Dash
            73: [22, 24, [[51, 1]]],  # Diamond Mine Progression w/ Dark Friar
            74: [22, 24, [[50, 1]]],  # Diamond Mine Progression w/ Spin Dash
            75: [22, 25, [[15, 1]]],  # Diamond Mine Progression w/ Elevator Key
            76: [25, 26, [[11, 1], [12, 1]]],  # Diamond Mine Progression w/ Mine Keys
            77: [29, 30, [[51, 1]]],  # Sky Garden Progression w/ Dark Friar
            78: [29, 72, [[52, 1]]],  # Sky Garden Progression w/ Aura Barrier
            79: [29, 32, [[14, 4]]],  # Sky Garden Progression w/ Crystal Balls
            80: [29, 31, [[48, 1]]],  # Sky Garden Progression w/ Psycho Dash
            81: [29, 31, [[49, 1]]],  # Sky Garden Progression w/ Psycho Slide
            82: [29, 31, [[50, 1]]],  # Sky Garden Progression w/ Spin Dash

            # NE Continent
            90: [33, 34, [[17, 1]]],  # Seaside Progression w/ Purity Stone
            91: [33, 35, [[9, 1], [16, 1], [23, 1], [37, 1]]],
            # Seaside Progression w/ Lilly
            92: [33, 36, [[16, 1]]],  # Seaside to Mu w/ Mu Key
            93: [36, 33, [[16, 1]]],  # Mu to Seaside w/ Mu Key
            94: [37, 38, [[18, 1]]],  # Mu Progression w/ Statue of Hope 1
            95: [38, 71, [[51, 1]]],  # Mu Progression w/ Dark Friar
            96: [38, 71, [[49, 1]]],  # Mu Progression w/ Psycho Slide
            97: [38, 39, [[49, 1]]],  # Mu Progression w/ Psycho Slide
            98: [71, 40, [[18, 2]]],  # Mu Progression w/ Statue of Hope 2
            99: [40, 41, [[19, 2]]],  # Mu Progression w/ Rama Statues
            100: [42, 43, [[49, 1]]],  # Angel Village to Dungeon w/ Slide
            101: [80, 46, [[51, 1]]],  # Great Wall Progression w/ Dark Friar
            102: [46, 47, [[50, 1]]],  # Great Wall Progression w/ Spin Dash
            103: [80, 45, [[50, 1]]],  # Escape Great Wall w/ Spin Dash

            # N Continent
            110: [48, 49, [[40, 1]]],  # Ann item w/ Apple
            111: [48, 50, [[50, 1]]],  # Euro to Mt. Temple w/ Spin Dash
            112: [50, 51, [[26, 1]]],  # Mt. Temple Progression w/ Drops 1
            113: [51, 52, [[26, 2]]],  # Mt. Temple Progression w/ Drops 2
            114: [52, 53, [[26, 3]]],  # Mt. Temple Progression w/ Drops 3
            115: [50, 48, [[50, 1]]],  # Mt. Temple to Euro w/ Spin
            116: [54, 55, [[29, 1]]],  # Natives' Village Progression w/ Flower
            # Ankor Wat Progression w/ Slide and Spin
            117: [56, 57, [[49, 1], [50, 1]]],
            118: [57, 58, [[51, 1]]],  # Ankor Wat Progression w/ Dark Friar
            119: [57, 58, [[36, 1]]],  # Ankor Wat Progression w/ Aura
            120: [57, 59, [[53, 1]]],  # Ankor Wat Progression w/ Earthquaker
            # Ankor Wat Progression w/ Black Glasses
            121: [59, 60, [[28, 1], [49, 1]]],

            # NW Continent
            130: [61, 62, [[49, 1]]],  # Pyramid foyer w/ Slide
            131: [61, 62, [[50, 1]]],  # Pyramid foyer w/ Spin
            132: [62, 63, [[36, 1]]],  # Pyramid Progression w/ Aura
            133: [77, 78, [[51, 1]]],  # Pyramid Progression w/ Dark Friar
            134: [77, 79, [[53, 1]]],  # Pyramid Progression w/ Earthquaker
            135: [62, 65, [[30, 1], [31, 1], [32, 1], [33, 1], [34, 1], [35, 1], [38, 1]]],
            # Pyramid Boss w/ Hieroglyphs and Journal
            136: [77, 64, [[50, 1]]],  # Pyramid Progression w/ Spin Dash

            # Babel/Jeweler Mansion
            # Babel Progression w/ Aura and Crystal Ring
            140: [66, 67, [[36, 1], [39, 1]]],
            # 141: [68,67,[[49,1]]],         # Jeweler Mansion to Babel Top w/Slide      # Solid Arm will not be required

            # Endgame
            150: [10, 69, [[20, 2]]],  # Rescue Kara from Edward's w/ Magic Dust
            151: [26, 69, [[20, 2]]],  # Rescue Kara from Mine w/ Magic Dust
            152: [43, 69, [[20, 2]]],  # Rescue Kara from Angel w/ Magic Dust
            # Rescue Kara from Mt. Temple w/ Magic Dust
            153: [53, 69, [[20, 2]]],
            154: [60, 69, [[20, 2]]],  # Rescue Kara from Ankor Wat w/ Magic Dust
            155: [69, 70, [[36, 1], [54, 0], [55, 0], [56, 0], [57, 0], [58, 0], [59, 0]]]
            # Beat Game w/Mystic Statues and Aura
        }
