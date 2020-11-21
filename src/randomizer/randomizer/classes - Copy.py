import copy
import time
from datetime import datetime
import binascii
import graphviz
import random

from .models.enums.start_location import StartLocation
from .models.enums.goal import Goal
from .models.enums.entrance_shuffle import EntranceShuffle
from .models.enums.enemizer import Enemizer
from .models.enums.logic import Logic
from .models.randomizer_data import RandomizerData

MAX_INVENTORY = 15
PROGRESS_ADJ = [1.5, 1.25, 1, 0.75]  # Required items are more likely to be placed in easier modes
MAX_CYCLES = 100
INACCESSIBLE = 9999


class World:
    # Assigns item to location
    def fill_item(self, item, location=-1):
        if location == -1:
            return False
        elif self.item_locations[location][2]:
            return False

        self.item_pool[item][0] -= 1
        self.item_locations[location][2] = True
        self.item_locations[location][3] = item

        self.placement_log.append([item, location])

        return True

    # Removes an assigned item and returns it to item pool
    def unfill_item(self, location=-1):
        if location == -1:
            return 0
        elif not self.item_locations[location][2]:
            return 0

        item = self.item_locations[location][3]
        self.item_locations[location][2] = False
        self.item_pool[item][0] += 1

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
                region = self.item_locations[loc][0]
                type = self.item_locations[loc][1]

                if type == 1 and self.item_locations[loc][2]:
                    item = self.item_locations[loc][3]
                    if inv and not self.graph[region][0] and self.item_pool[item][4]:
                        done = True
                    elif not inv and self.graph[region][0] and self.item_pool[item][5] != 1:
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
        for x in self.item_pool:
            if not items or x in items:
                if type == 0 or type == self.item_pool[x][1]:
                    if progress_type == 0 or progress_type == self.item_pool[x][5]:
                        i = 0
                        while i < self.item_pool[x][0]:
                            item_list.append(x)
                            i += 1
        return item_list

    # Returns a list of unfilled item locations
    def list_item_locations(self):
        locations = []
        for x in self.item_locations:
            locations.append(x)
        return locations

    # Returns list of graph edges
    def list_logic(self):
        edges = []
        for x in self.logic:
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
        for x in self.item_locations:
            region = self.item_locations[x][0]
            type = self.item_locations[x][1]
            if self.graph[region][0] and not self.item_locations[x][2]:
                locations[type - 1].append(x)
        return locations

    # Zeroes out accessible flags for all world regions
    def unsolve(self):
        for x in self.graph:
            self.graph[x][0] = False

    # Finds all accessible locations and returns all accessible items
    def traverse(self, start_items=[]):
        # print "Traverse:"
        self.unsolve()
        to_visit = [0]
        items = start_items[:]
        while to_visit:
            origin = to_visit.pop(0)
            # print "Visiting ",origin

            if not self.graph[origin][0]:
                self.graph[origin][0] = True
                for x in self.graph[origin][1]:
                    if x not in to_visit:
                        to_visit.append(x)
                found_item = False
                for location in self.item_locations:
                    if self.item_locations[location][0] == origin and self.item_locations[location][2]:
                        items.append(self.item_locations[location][3])
                        found_item = True
                        # print "Found item in location: ", self.item_locations[location][3], location
                if found_item:
                    # print "We found an item"
                    for y in self.graph:
                        if self.graph[y][0] and y != origin:
                            to_visit.append(y)

            for edge in self.logic:
                if self.logic[edge][0] == origin:
                    dest = self.logic[edge][1]
                    if not self.graph[dest][0] and dest not in to_visit:
                        req_items = []
                        for req in self.logic[edge][2]:
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
            region = self.item_locations[x][0]
            if self.graph[region][0]:
                accessible.append(x)
        return accessible

    # Returns full list of inaccessible locations
    def inaccessible_locations(self, item_locations):
        inaccessible = []
        for x in item_locations:
            region = self.item_locations[x][0]
            if not self.graph[region][0]:
                inaccessible.append(x)
        return inaccessible

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
            item_type = self.item_pool[item][1]

            placed = False
            i = 0
            for dest in to_fill:
                if not placed:
                    region = self.item_locations[dest][0]
                    location_type = self.item_locations[dest][1]
                    filled = self.item_locations[dest][2]
                    restrictions = self.item_locations[dest][4]
                    if not filled and item_type == location_type and item not in restrictions:
                        if not accessible or region != INACCESSIBLE:
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
        item_type = self.item_pool[item][1]

        for dest in to_fill:
            region = self.item_locations[dest][0]
            location_type = self.item_locations[dest][1]
            filled = self.item_locations[dest][2]
            restrictions = self.item_locations[dest][4]
            if self.graph[region][0] and not filled and self.item_pool[item][0] > 0:
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

        for x in self.logic:
            origin = self.logic[x][0]
            dest = self.logic[x][1]
            if self.graph[origin][0] and not self.graph[dest][0]:
                prereq = []
                for req in self.logic[x][2]:
                    item = req[0]
                    i = 0
                    while i < req[1]:
                        prereq.append(item)
                        i += 1
                prereq = self.items_needed(prereq, start_items)

                item_prereqs = 0
                ability_prereqs = 0
                for y in prereq:
                    if self.item_pool[y][1] == 1:
                        item_prereqs += 1
                    elif self.item_pool[y][1] == 2:
                        ability_prereqs += 1

                if prereq and self.is_sublist(all_items, prereq) and prereq not in prereq_list:
                    if item_prereqs <= open_items and ability_prereqs <= open_abilities:
                        self.graph[dest][0] = True
                        start_items_temp = start_items[:] + prereq
                        # for req in prereq:
                        #    if self.item_pool[req][4]:
                        #        start_items_temp.append(req)
                        inv_temp = self.get_inventory(start_items_temp)
                        # neg_inv_temp = negative_inventory[:]

                        # for item in inv_temp:
                        #    if item in neg_inv_temp:
                        #        inv_temp.remove(item)
                        #        neg_inv_temp.remove(item)
                        if len(inv_temp) <= MAX_INVENTORY:
                            prereq_list.append(prereq)
                        else:
                            prereq_list.append(-1)
                        self.graph[dest][0] = False

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
                    if self.item_pool[item][1] == 1:
                        probability *= float(self.item_pool[item][0]) / float((sum_items - i))
                        i += 1
                    elif self.item_pool[item][1] == 2:
                        probability *= float(self.item_pool[item][0]) / float((sum_abilities - j))
                        j += 1
                    if item in self.required_items:
                        probability *= PROGRESS_ADJ[self.difficulty]
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
        for map in self.maps:
            boss = self.maps[map][1]
            maps[boss].append(map)

        maps.pop(0)
        return maps

    # Randomize map-clearing rewards
    def map_rewards(self):
        maps = self.get_maps()
        # print maps

        for area in maps:
            random.shuffle(area)

        boss_rewards = 4

        # Total rewards by type, by level (HP/STR/DEF)
        if "Z3 Mode" in self.variant:
            rewards_tier1 = [1] * 6    # Expert: 6 HP
            rewards_tier2 = [1] * 6    # Advanced: 12 HP
            rewards_tier3 = [1] * 6    # Intermediate: 18 HP
            rewards_tier4 = []         # Beginner: 18 HP
        else:  # Remove all HP upgrades
            rewards_tier1 = [1,1,1,1,1,1]    # Expert: 6/0/0
            rewards_tier2 = [1,1,2,2,3,3]    # Advanced: 8/2/2
            rewards_tier3 = [1,1,2,2,3,3]    # Intermediate: 10/4/4
            rewards_tier4 = [2,2,2,3,3,3]    # Beginner: 10/7/7

        # Remove HP upgrades in OHKO
        if "OHKO" in self.variant:
            for n, i in enumerate(rewards_tier1):
                if i == 1:
                    rewards_tier1[n] = 0
            for n, i in enumerate(rewards_tier2):
                if i == 1:
                    rewards_tier2[n] = 0
            for n, i in enumerate(rewards_tier3):
                if i == 1:
                    rewards_tier3[n] = 0
            for n, i in enumerate(rewards_tier4):
                if i == 1:
                    rewards_tier4[n] = 0

        random.shuffle(rewards_tier1)
        random.shuffle(rewards_tier2)
        random.shuffle(rewards_tier3)
        random.shuffle(rewards_tier4)

        # Allocate rewards to maps
        for area in maps:
            random.shuffle(area)
            self.maps[area[0]][2] = [rewards_tier1.pop(0),1]
            self.maps[area[1]][2] = [rewards_tier2.pop(0),2]
            self.maps[area[2]][2] = [rewards_tier3.pop(0),3]
            if rewards_tier4:
                self.maps[area[3]][2] = [rewards_tier4.pop(0),4]
            else:
                self.maps[area[3]][2] = [0,4]

    # Place Mystic Statues in World
    def fill_statues(self, locations=[148, 149, 150, 151, 152, 153]):
        return self.random_fill([100, 101, 102, 103, 104, 105], locations)

    def lock_dark_spaces(self, item_locations=[]):
        for set in self.dark_space_sets:
            ds = -1
            for location in item_locations:
                if location in set:
                    ds = location
            if ds == -1:
                return False
            else:
                self.item_locations[ds][2] = True
        return True


    # Determine an exit's direction (e.g. outside to inside)
    def is_exit_coupled(self,exit):
        if exit not in self.exits:
            return False
        if self.exits[exit][0]:
            sister_exit = self.exits[exit][0]
            if self.exits[sister_exit][0] == exit:
                return True
            else:
                print("WARNING: Exits linked incorrectly",exit,sister_exit)
                return True
        return False


    # Determine an exit's direction (e.g. outside to inside)
    def exit_direction(self,exit):
        if exit not in self.exits:
            return False
        origin = self.exits[exit][3]
        dest = self.exits[exit][4]
        if self.graph[origin][2] == 2:
            o_type = 2
        else:
            o_type = 1
        if self.graph[dest][2] == 2:
            d_type = 2
        else:
            d_type = 1
        return (o_type,d_type)


    # Get lists of unmatched origin/destination exits
    def get_remaining_exits(self):
        exits_remaining = [[],[]]
        for exit in self.exits:
            if self.exits[exit][1] == -1:
                exits_remaining[0].append(exit)
            if self.exits[exit][2] == -1:
                exits_remaining[1].append(exit)
        return exits_remaining

    # Link one exit to another
    def link_exits(self, origin_exit, dest_exit, check_connections=True):
        if origin_exit not in self.exits or dest_exit not in self.exits:
            return False
        self.exits[origin_exit][1] = dest_exit
        self.exits[dest_exit][2] = origin_exit
#        print(self.exits[origin_exit][10], "-", self.exits[dest_exit][10])
        origin = self.exits[origin_exit][3]
        dest = self.exits[dest_exit][4]
        if dest not in self.graph[origin][1]:
            self.graph[origin][1].append(dest)
        if not check_connections:
            return True
        if self.entrance_shuffle == "Coupled" and self.is_exit_coupled(origin_exit) and self.is_exit_coupled(dest_exit):
            self.exits[self.exits[dest_exit][0]][1] = self.exits[origin_exit][0]
            self.exits[self.exits[origin_exit][0]][2] = self.exits[dest_exit][0]
            coupled_origin = self.exits[origin_exit][0]
            coupled_dest = self.exits[dest_exit][0]
            self.exits[coupled_dest][1] = coupled_origin
            self.exits[coupled_origin][2] = coupled_dest
#            print(" ",self.exits[coupled_dest][10], "-", self.exits[coupled_origin][10])
            if origin not in self.graph[dest][1] and self.exits[coupled_dest][5]:
                self.graph[dest][1].append(origin)
        return True


    # Entrance randomizer
    def shuffle_exits(self):
        # Make a clean copy of world graph for later replacement
        graph_copy = copy.deepcopy(self.graph)

        # Assume all items and abilities
        for x in self.logic:
            if x < 400 or x > 404 or (x - self.kara + 1) == 400:
                origin = self.logic[x][0]
                dest = self.logic[x][1]
                if origin in self.graph:
                    if dest and dest not in self.graph[origin][1]:
                        self.graph[origin][1].append(dest)

        # Map passages and internal dungeon exits to graph and list all available exits
        for x in self.exits:
            if self.is_exit_coupled(x) and not self.exits[x][3]:    # Map missing O/D data for coupled exits
                xprime = self.exits[x][0]
                self.exits[x][3] = self.exits[xprime][4]
                self.exits[x][4] = self.exits[xprime][3]
            if self.exits[x][1] or (not self.exits[x][5] and not self.exits[x][6]) or self.exits[x][7] or (self.exits[x][8] and not self.exits[x][9]):
                origin = self.exits[x][3]
                dest = self.exits[x][4]
                if origin and dest:
                    if dest not in self.graph[origin][1]:
                        self.graph[origin][1].append(dest)
            elif self.exits[x][3] and self.exits[x][4]:
                self.exits[x][1] = -1    # Mark exit for shuffling
                self.exits[x][2] = -1
                #print(self.exits[x][10])

        # Map exits that open up the graph
        check_direction = True
        solved = False
        progress = False
        cycle = 1
        quarantine = []
        while not solved:# and cycle<10:
            #print(cycle)
            origin_exits = []
            dest_exits = []
            items = self.traverse()

            # Identify exits that will open up unexplored areas
            for exit in self.exits:
                origin = self.exits[exit][3]
                dest = self.exits[exit][4]
                if self.exits[exit][1] == -1 and self.graph[origin][0] and exit not in origin_exits:
                    origin_exits.append(exit)
                if self.exits[exit][2] == -1 and not self.graph[dest][0] and exit not in dest_exits:
                    dest_exits.append(exit)

            random.shuffle(origin_exits)

            if not dest_exits:
                solved = True
            elif not origin_exits:
                print("ERROR: We ran out of exits!")
                return False
            else:
                random.shuffle(dest_exits)
                origin_exit = 0
                while origin_exits:
                    origin_exit = origin_exits.pop(0)
                    if origin_exit in quarantine:
                        origin_exit = 0
                if not origin_exit:
#                    print("Emptying quarantine:")
#                    for x in quarantine:
#                        print(" ",self.exits[x][10])
                    quarantine.clear()
                    if progress:
                        progress = False
                    elif check_direction:
                        check_direction = False
                    else:
                        print("ERROR: We ran out of exits!")
                        return False
                else:
                    origin = self.exits[origin_exit][3]
                    dest_old = self.exits[origin_exit][4]
                    coupled = self.is_exit_coupled(origin_exit)
                    direction = self.exit_direction(origin_exit)

                    dest_exit = 0
                    for x in dest_exits:
                        if not dest_exit:
                            if (coupled and self.exits[x][0] and self.exits[self.exits[x][0]][1] == -1) or (
                                    not coupled and not self.exits[x][0]):
                                origin_new = self.exits[x][3]
                                dest_new = self.exits[x][4]
                                direction_new = (self.graph[origin_new][2],self.graph[dest_new][2])
                                #print(direction,direction_new)
                                if not check_direction or not coupled:
                                    dest_exit = x
                                elif direction == direction_new and x != origin_exit:
                                    dest_exit = x

                    if dest_exit:
                        progress = True
                        self.link_exits(origin_exit,dest_exit)
                    else:
                        quarantine.append(origin_exit)

            cycle += 1

#        print("Round 1 finished")

        quarantine.clear()
        # Link remaining exits
        check_direction = True
        done = False
        while not done:
            exits_remaining = self.get_remaining_exits()
            origin_exits = exits_remaining[0]
            dest_exits = exits_remaining[1]

            if not origin_exits or not dest_exits:
                done = True
            else:
                random.shuffle(origin_exits)
                random.shuffle(dest_exits)

                exit = 0
                while not exit and origin_exits:
                    exit = origin_exits.pop(0)
                    if exit in quarantine:
                        exit = 0
                if not exit:
#                    print("Emptying quarantine:")
#                    for x in quarantine:
#                        print(" ",self.exits[x][10])
                    quarantine.clear()
                    check_direction = False
                else:
                    coupled = self.is_exit_coupled(exit)
                    direction = self.exit_direction(exit)
                    found_new_exit = False
                    for new_exit in dest_exits:
                        if not found_new_exit and (not check_direction or direction == self.exit_direction(new_exit) or not coupled):
                            if (coupled and self.is_exit_coupled(new_exit) and self.exits[self.exits[new_exit][0]][1] == -1) or (
                                    not coupled and not self.is_exit_coupled(new_exit)):
                                found_new_exit = True
                                self.link_exits(exit, new_exit)
                    if not found_new_exit:
                        quarantine.append(exit)

#        print("Round 2 finished")

        # Clean up whatever's left
        exits_remaining = self.get_remaining_exits()
        origin_exits = exits_remaining[0]
        dest_exits = exits_remaining[1]
        random.shuffle(origin_exits)
        random.shuffle(dest_exits)

        while origin_exits:
            exit1 = origin_exits.pop(0)
            if self.exits[exit1][1] == -1:
                exit2 = 0
                while dest_remaining and not exit2:
                    exit2 = dest_remaining.pop(0)
                    if self.exits[exit2][2] != -1:
                        exit2 = 0
                if not exit2:
                    print("WARNING: Odd number of shuffled addresses", exit1)
                    self.exits[exit1][1] = 0
                else:
                    self.link_exits(exit1, exit2)

#        print("Round 3 finished")

        for exit in self.exits:
            if self.exits[exit][1] == -1:
                print("How'd we miss this one??", exit)
                self.exits[exit][1] = 0

        # Re-initialize world graph
        self.graph = copy.deepcopy(graph_copy)
#        print("We done")
        graph_copy = None
        return True


    # Translates exits to world graph
    def update_graph(self):
        for exit in self.exits:
            # Check if exit has been shuffled
            if self.exits[exit][1]:
                new_exit = self.exits[exit][1]
            else:
                new_exit = exit
            # Get exit origin
            origin = self.exits[exit][3]
            if not origin and self.is_exit_coupled(exit):
                sister_exit = self.exits[exit][0]
                origin = self.exits[sister_exit][4]
                self.exits[exit][3] = origin

            # Get (new) exit destination
            dest = self.exits[new_exit][4]
            if not dest and self.is_exit_coupled(new_exit):
                sister_exit = self.exits[new_exit][0]
                dest = self.exits[sister_exit][3]
                self.exits[new_exit][4] = dest

            # Translate link into world graph
            if origin and dest and (dest not in self.graph[origin][1]):
                self.graph[origin][1].append(dest)

#        for x in self.graph:
#            print(x,self.graph[x])

    # Initialize World parameters
    def initialize(self):
        # Manage required items
        if 1 in self.dungeons_req:
            self.required_items += [3, 4, 7, 8]
        if 2 in self.dungeons_req:
            self.required_items += [14]
        if 3 in self.dungeons_req:
            self.required_items += [18, 19]
        if 4 in self.dungeons_req:
            self.required_items += [63, 64]
        if 5 in self.dungeons_req:
            self.required_items += [38, 30, 31, 32, 33, 34, 35]
        if 6 in self.dungeons_req:
            self.required_items += [39]

        if self.kara == 1:
            self.required_items += [2, 9, 23]
        elif self.kara == 2:
            self.required_items += [11, 12, 15]
        elif self.kara == 3:
            self.required_items += [62]
        elif self.kara == 4:
            self.required_items += [26, 63]
        elif self.kara == 5:
            self.required_items += [28, 62, 63, 66]

        # Update inventory space logic
        if 3 in self.dungeons_req:
            self.item_pool[19][4] = True
        if 5 in self.dungeons_req:
            self.item_pool[30][4] = True
            self.item_pool[31][4] = True
            self.item_pool[32][4] = True
            self.item_pool[33][4] = True
            self.item_pool[34][4] = True
            self.item_pool[35][4] = True
            self.item_pool[38][4] = True

        # Solid Arm can only be required in Extreme
        if self.difficulty < 3:
            self.exits[21][4] = self.exits[21][3]

        # Random start location
        if self.start_mode != "South Cape":
            self.start_loc = self.random_start()
            self.graph[0][1].remove(22)
            self.graph[0][1].append(self.item_locations[self.start_loc][0])
            print("Start:",self.item_locations[self.start_loc][9])

        # Overworld shuffle
        if "Overworld Shuffle" in self.variant:
            self.shuffle_overworld()

            # Remove old overworld from the graph
#            for i in self.graph:
#                for j in range(100, 105):
#                    if j in self.graph[i][1]:
#                        self.graph[i][1].remove(j)

            self.graph[10][1].clear()
            self.graph[11][1].clear()
            self.graph[12][1].clear()
            self.graph[13][1].clear()
            self.graph[14][1].clear()

            # Add new overworld to the graph
            for entry in self.overworld_menus:
                new_entry = self.overworld_menus[entry][0]
                self.graph[self.overworld_menus[entry][2]][1].append(self.overworld_menus[new_entry][3])
                self.graph[self.overworld_menus[new_entry][3]][1].remove(self.overworld_menus[new_entry][2])
                self.graph[self.overworld_menus[new_entry][3]][1].append(self.overworld_menus[entry][2])

            #print(self.graph)

#                new_target_region = self.overworld_menus[self.overworld_menus[entry][0]][3]
#                old_map_region = self.overworld_menus[self.overworld_menus[entry][0]][2]
#                map_region = self.overworld_menus[entry][2]
#                for _, logic_data in self.logic.items():
#                    if old_map_region == logic_data[0] and new_target_region == logic_data[1]:
#                        logic_data[0] = map_region
#                    if old_map_region == logic_data[1] and new_target_region == logic_data[0]:
#                        logic_data[1] = map_region
#                self.graph[map_region][1].append(new_target_region)
#                self.graph[new_target_region][1].append(map_region)

        # Allow glitches
        if "Allow Glitches" in self.variant:
            self.graph[0][1].append(601)
            self.graph[61][1].append(62)          # Moon Tribe: No ability required
            self.graph[181][1].append(182)        # Sky Garden: Ramp glitch, cage glitch
            self.graph[181][1].append(184)
            self.graph[182][1].append(183)
            self.graph[182][1].append(185)
            self.graph[222][1].append(221)        # Mu: Golem skip
            self.item_locations[94][2] = False    # Great Wall: Slider glitch
            self.graph[294][1].append(295)
            self.logic[268][2][1][1] = 0          # Ankor Wat: Earthquaker not required
            self.logic[273][2][0][1] = 0          # Ankor Wat: Glasses not required
            self.logic[274][2][0][1] = 0
            self.item_locations[124][2] = False   # Ankor Wat: Dropdown DS has abilities
            self.graph[410][1].append(411)        # Pyramid: No ability required
            self.item_locations[142][2] = False   # Pyramid: Bottom DS can have abilities

        # Early Firebird
        if self.firebird:
            self.graph[0][1].append(602)

        # Zelda 3 Mode
        if "Z3 Mode" in self.variant:
            # Update item pool
            self.item_pool[1][0] = 29  # Red Jewels
            self.item_pool[50][0] = 5  # HP upgrades
            self.item_pool[51][0] = 2  # DEF upgrades
            self.item_pool[52][0] = 3  # STR upgrades
            self.item_pool[55][0] = 12  # HP Pieces

        # Open Mode
        if "Open Mode" in self.variant:
            # Update graph logic
            self.logic[30][2][0][1] = 0     # Lola's Letter
            self.logic[31][2][0][1] = 0
            self.logic[32][2][0][1] = 0
            self.logic[33][2][0][1] = 0     # Memory Melody
            self.logic[36][2][0][1] = 0     # Teapot
            self.logic[38][2][0][1] = 0     # Will
            self.logic[39][2][0][1] = 0
            self.logic[40][2][0][1] = 0     # Roast

            # Remove travel items from pool
            self.item_pool[10][0] = 0  # Large Roast
            self.item_pool[13][0] = 0  # Memory Melody
            self.item_pool[24][0] = 0  # Will
            self.item_pool[25][0] = 0  # Teapot
            self.item_pool[37][0] = 0  # Lola's Letter
            self.item_pool[6][0] += 4  # Herbs
            self.item_pool[0][0] += 1  # Nothing

        # Boss Shuffle
        if "Boss Shuffle" in self.variant:
            boss_entrance_idx = [1,4,7,10,13,16,19]
            boss_exit_idx = [3,6,9,12,15,18,21]
            dungeon = 0
            # print("Boss order: ",self.boss_order)
            while dungeon < 7:
                boss = self.boss_order[dungeon]
                self.exits[boss_entrance_idx[dungeon]][1] = boss_entrance_idx[boss-1]
                self.exits[boss_exit_idx[boss-1]][1] = boss_exit_idx[dungeon]
                dungeon += 1

        # Chaos mode
        if self.logic_mode == "Chaos":
            # Add "Inaccessible" node to graph
            self.graph[INACCESSIBLE] = [False, [], 0, [0,0,b"\x00"], 0, "Inaccessible", []]

            # Towns can have Freedan abilities
            for x in self.item_locations:
                if self.item_locations[x][4] == [64, 65, 66]:
                    self.item_locations[x][4].clear()

            # Several locked Dark Spaces can have abilities
            ds_unlock = [74, 94, 124, 142]

            if 1 not in self.dungeons_req:  # First DS in Inca
                ds_unlock.append(29)
            if 4 in self.dungeons_req:
                self.dark_space_sets.append([93, 94])
            if self.kara != 1:  # DS in Underground Tunnel
                ds_unlock.append(19)
            if self.kara != 5:  # DS in Ankor Wat garden
                ds_unlock.append(122)

            for x in ds_unlock:
                self.item_locations[x][2] = False

        # Red Jewel Hunts change the graph
        if self.goal == "Red Jewel Hunt":
            self.logic[24][1] = 492
            self.logic[25][1] = 492
            self.logic[26][1] = 492
            self.logic[27][1] = 492

        # Change graph logic depending on Kara's location
        if self.kara == 1:
            self.logic[400][2][0][1] = 1
            self.graph[49][6].append(20)
        elif self.kara == 2:
            self.logic[401][2][0][1] = 1
            self.graph[150][6].append(20)
            # Change "Sam" to "Samlet"
            self.location_text[45] = b"\x63\x80\x8c\x8b\x84\xa4"
        elif self.kara == 3:
            self.logic[402][2][0][1] = 1
            self.graph[270][6].append(20)
        elif self.kara == 4:
            self.logic[403][2][0][1] = 1
            self.graph[345][6].append(20)
        elif self.kara == 5:
            self.logic[404][2][0][1] = 1
            self.graph[391][6].append(20)

        # Change logic based on which dungeons are required
        for x in self.statues:
            self.logic[406][2][x][1] = 1
        # Shuffle exits
        if self.entrance_shuffle != "None":
            # Always start from a Dark Space
            self.graph[0][1] = [self.item_locations[self.start_loc][0]]
            if not self.shuffle_exits():
                print("ERROR: Entrance rando failed")
                return False

        # Update graph with exit data
        self.update_graph()

        return True

    # Update item placement logic after abilities are placed
    def check_logic(self):
        abilities = [61, 62, 63, 64, 65, 66]
        inaccessible_ls = []

        # Check for abilities in critical Dark Spaces
        if self.item_locations[19][3] in abilities:  # Underground Tunnel
            inaccessible_ls += [17, 18]
        if self.item_locations[29][3] in abilities:  # Inca Ruins
            inaccessible_ls += [26, 27, 30, 31, 32]
            #self.graph[18][1].remove(19)
        if (self.item_locations[46][3] in abilities and  # Diamond Mine
                self.item_locations[47][3] in abilities and
                self.item_locations[48][3] in abilities):
            del self.logic[118]
        if (self.item_locations[58][3] in abilities and  # Sky Garden
                self.item_locations[59][3] in abilities and
                self.item_locations[60][3] in abilities):
            del self.logic[131]
            del self.logic[132]
            del self.logic[144]
            del self.logic[147]
            del self.logic[148]
        if self.item_locations[94][3] in abilities:  # Great Wall
            self.graph[700] = [False, [], 0, [3,15,b"\x00"], 0, "Great Wall - Behind Spin", []]
            self.logic[700] = [296, 700, [[63, 1]]]
            self.item_locations[93][0] = 700
            if self.item_locations[93][3] in abilities:
                inaccessible_ls += [95]
        if self.item_locations[122][3] in abilities:  # Ankor Wat
            inaccessible_ls += [117, 118, 119, 120, 121]
        #        if self.item_locations[142][3] in abilities:        # Pyramid
        #            inaccessible_ls += [133,134,136,139,140]

        # Change graph node for inaccessible_ls locations
        for x in inaccessible_ls:
            self.item_locations[x][0] = INACCESSIBLE

    # Simulate inventory
    def get_inventory(self, start_items=[]):
        inventory = []
        for item in start_items:
            if self.item_pool[item][4]:
                inventory.append(item)

        negative_inventory = []
        for node in self.graph:
            if self.graph[node][0]:
                negative_inventory += self.graph[node][6]

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
        if not self.initialize():
            print("ERROR: Could not initialize world")
            return False
#        for x in self.graph:
#            if self.graph[x][0]:
#                print(self.graph[x][5])
        solved = False

        random.seed(self.seed + seed_adj)

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
        if self.logic_mode == "Chaos" or self.difficulty > 2:
            non_prog_items += self.list_item_pool(2)
        elif self.difficulty == 0:
            non_prog_items += [65]
        elif self.difficulty == 1:
            non_prog_items += [62, 63, 65, 66]

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

        # while self.inaccessible_locations(item_locations):
        while not done:
            #print(cycle)
            cycle += 1
            if cycle > MAX_CYCLES:
                print("ERROR: Max cycles exceeded")
                print(self.graph)
                print(self.overworld_menus)
                return False

            start_items = self.traverse()
#            print("Cycle",cycle)
#            for x in self.graph:
#                if self.graph[x][0]:
#                    print(self.graph[x][5])
            #print("We found these: ",start_items)

            inv_size = len(self.get_inventory(start_items))
            if inv_size > MAX_INVENTORY:
                goal = False
                print("ERROR: Inventory capacity exceeded")
            else:
                goal = self.graph[192][0]

            # Get list of new progression options
            progression_list = self.progression_list(start_items)
            #print(progression_list)

            done = goal and (self.logic_mode != "Completable" or progression_list == -1)
            #print(done, progression_list)

            if not done:
                if progression_list == -1:  # No empty locations available
                    removed = self.make_room(item_locations)
                    if not removed:
                        print("ERROR: Could not remove non-progression item")
                        return False
                    #progression_list = []
                elif progression_list == -2:  # All new locations have too many inventory items
                    removed = self.make_room(item_locations, True)
                    if not removed:
                        print("ERROR: Could not remove inventory item")
                        return False
                    #progression_list = []
                else:
                    progress = False
                    key_tries = 0
                    while not progress and progression_list and key_tries < 5:
                        # Determine next progression items to add to accessible locations
                        progression_mc = self.monte_carlo(progression_list)
                        key = random.uniform(0, 100)
                        key_tries += 1
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
                            # print self.graph

                    if not progress:
                        removed = self.make_room(item_locations)
                        if not removed:
                            print("ERROR: Could not remove non-progression item")
                            return False


            # print goal, done

        print("Inaccessible: ",self.inaccessible_locations(item_locations))
        for node in self.graph:
            if not self.graph[node][0]:
                print("Can't reach ",self.graph[node][5])

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

            if location not in self.free_locations and location in self.location_text:
                if item in self.required_items or item in self.good_items or location in self.trolly_locations:
                    spoiler_str = b"\xd3" + self.location_text[location] + b"\xac\x87\x80\xa3\xcb"
                    spoiler_str += self.item_text_short[item] + b"\xc0"
                    # No in-game spoilers in Expert mode
                    if self.difficulty >= 3:
                        spoiler_str = b"\xd3\x8d\x88\x82\x84\xac\xa4\xa2\xa9\xac\x83\x8e\x83\x8e\x8d\x86\x8e\x4f\xc0"
                    self.spoilers.append(spoiler_str)
                    # print item, location

    # Prints item and ability locations
    def generate_spoiler(self, version=""):
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

        if self.difficulty == 0:
            difficulty_txt = "Easy"
        elif self.difficulty == 1:
            difficulty_txt = "Normal"
        elif self.difficulty == 2:
            difficulty_txt = "Hard"
        elif self.difficulty == 3:
            difficulty_txt = "Extreme"

        spoiler = dict()
        spoiler["version"] = version
        spoiler["seed"] = str(self.seed)
        spoiler["date"] = str(datetime.utcfromtimestamp(time.time()))
        spoiler["goal"] = str(self.goal)
        spoiler["entrance_shuffle"] = str(self.entrance_shuffle)
        spoiler["start_location"] = self.item_locations[self.start_loc][9].strip()
        spoiler["logic"] = str(self.logic_mode)
        spoiler["difficulty"] = str(difficulty_txt)
        spoiler["statues_required"] = self.statues
        spoiler["boss_order"] = self.boss_order
        spoiler["kara_location"] = kara_txt
        spoiler["jeweler_amounts"] = self.gem
        spoiler["inca_tiles"] = self.incatile
        spoiler["hieroglyph_order"] = self.hieroglyphs

        items = []
        for x in self.item_locations:
            item = self.item_locations[x][3]
            location_name = self.item_locations[x][9].strip()
            item_name = self.item_pool[item][3]
            items.append({"location": location_name, "name": item_name})
        spoiler["items"] = items

        if "Overworld Shuffle" in self.variant:
            overworld_links = []
            for continent_id, continent_data in self.overworld_menus.items():
                continent_name = self.graph[continent_data[2]][2]
                region_name = self.graph[self.overworld_menus[continent_data[0]][3]][2]
                overworld_links.append({"continent": continent_name, "region": region_name})
            spoiler["overworld_entrances"] = overworld_links

        self.spoiler = spoiler
        self.complete_graph_visualization()

    def complete_graph_visualization(self):
        graph = self.graph_viz

        areas = dict()
        area_names = ["Overworld",
                      "South Cape",
                      "Edward's Castle",
                      "Itory Village",
                      "Moon Tribe",
                      "Inca Ruins",
                      "Diamond Coast",
                      "Freejia",
                      "Diamond Mine",
                      "Neil's Cottage",
                      "Nazca Plain",
                      "Seaside Palace",
                      "Mu",
                      "Angel Village",
                      "Watermia",
                      "Great Wall",
                      "Euro",
                      "Mt. Kress",
                      "Native's Village",
                      "Ankor Wat",
                      "Dao",
                      "Pyramid",
                      "Babel",
                      "Jeweler's Mansion"]
        graph.attr('node', shape='box')
        for area_id in range(len(area_names)):
            areas[area_id] = list()

        for area_id in range(1,len(area_names)):
            node_name = f"area_{area_id}"
            node_content = area_names[area_id]
            #areas[0].append((node_name, node_content))

        for region_id, region_data in self.graph.items():
            area = region_data[3][1]
            node_name = f"region_{region_id}"
            node_content = region_data[5]
            areas[area].append((node_name, node_content))

        for area_id, area_nodes in areas.items():
            for node_id, node_content in area_nodes:
                graph.node(node_id, node_content)
            #with graph.subgraph(name=f"cluster_{area_id}") as c:
            #    c.attr(label=area_names[area_id],
            #           color="black")
            #    for node_id, node_content in area_nodes:
            #        if area_id != 0:
            #            c.node(node_id, node_content)
            #        else:
            #            graph.node(node_id,node_content)

        for region_id, region_data in self.graph.items():
            start_area = region_data[3][1]
            node_name = f"region_{region_id}"
            area_name = f"area_{start_area}"
            for accessible_region_id in region_data[1]:
                end_area = self.graph[accessible_region_id][3][1]
                end_area_name = f"area_{end_area}"
                accessible_node_name = f"region_{accessible_region_id}"
                graph.edge(node_name, accessible_node_name)
                #if start_area != 0 and end_area != 0:
                #    if start_area != end_area:
                #        graph.edge(area_name, end_area_name)
                #    else:
                #        graph.edge(node_name, accessible_node_name)
                #elif start_area != 0:
                #    graph.edge(area_name, accessible_node_name)
                #elif end_area != 0:
                #    graph.edge(node_name, end_area_name)
                #else:
                #    graph.edge(node_name, accessible_node_name)

        for _, logic_data in self.logic.items():
            needed_items = logic_data[2]
            enough_items = True
            for item_id, quantity in needed_items:
                existing_quantity = 0
                if item_id not in self.item_pool:
                    print("Missing info about item:", item_id)
                else:
                    existing_quantity = self.item_pool[item_id][0]
                for _, location_data in self.item_locations.items():
                    if location_data[2] and item_id == location_data[3]:
                        existing_quantity += 1
                if existing_quantity < quantity:
                    enough_items = False
                    break
            if not enough_items:
                continue
            start_name = f"region_{logic_data[0]}"
            dest_name = f"region_{logic_data[1]}"
            start_area = self.graph[logic_data[0]][3][1]
            end_area = self.graph[logic_data[1]][3][1]
            area_name = f"area_{start_area}"
            end_area_name = f"area_{end_area}"
            graph.edge(start_name, dest_name)
            #if start_area != 0 and end_area != 0:
            #    if start_area != end_area:
            #        graph.edge(area_name, end_area_name)
            #    else:
            #        graph.edge(start_name, dest_name)
            #elif start_area != 0:
            #    graph.edge(area_name, dest_name)
            #elif end_area != 0:
            #    graph.edge(start_name, end_area_name)
            #else:
            #    graph.edge(start_name, dest_name)

        per_region_item_node = dict()
        item_location_color_map = {
            1: "yellow",
            2: "blue",
            3: "green",
            4: "white"
        }
        graph.attr('node', shape='plaintext')
        for itemloc_id, itemloc_data in self.item_locations.items():
            # Add Item_location_nodes
            location_region = itemloc_data[0]
            region_node_name = f"region_{location_region}"
            region_item_node_name = f"region_itemnode_{location_region}"
            if (itemloc_data[1] != 2 or itemloc_data[3] != 0) and itemloc_data[1] != 4:
                if region_item_node_name not in per_region_item_node:
                    per_region_item_node[region_item_node_name] = []
                    graph.edge(region_node_name, f"{region_item_node_name}")
                per_region_item_node[region_item_node_name].append((itemloc_id))

        for region_item_node_name, locations_id in per_region_item_node.items():
            node_content = "<<table border='0' cellborder='1' cellspacing='0'>"
            for itemloc_id in locations_id:
                itemloc_data = self.item_locations[itemloc_id]
                item_name = self.item_pool[itemloc_data[3]][3]
                location_name = itemloc_data[9]
                if ":" in location_name:
                    location_name = ":".join(location_name.split(':')[1:])
                location_type = itemloc_data[1]
                node_content += f"""<tr>
<td ALIGN='left' bgcolor='{item_location_color_map[location_type]}'>{location_name.strip()}</td>
<td align='center'>{item_name}</td>
</tr>"""
            node_content += "</table>>"
            graph.node(region_item_node_name, node_content)

    def print_enemy_locations(self, filepath, offset=0):
        f = open(filepath, "r+b")
        rom = f.read()
        for enemy in self.enemies:
            print(self.enemies[enemy][3])
            done = False
            addr = int("c8200", 16) + offset
            while not done:
                addr = rom.find(self.enemies[enemy][1], addr + 1)
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
        print("Seed                                   >  ", self.seed)
        print("Statues Required                       >  ", self.statues)
        print("Kara Location                          >  ", kara_txt)
        print("Jeweler Reward Amounts                 >  ", self.gem)
        print("Inca Tile (column, row)                >  ", self.incatile)
        print("Hieroglyph Order                       >  ", self.hieroglyphs)
        print("")

        for x in self.item_locations:
            item = self.item_locations[x][3]
            location_name = self.item_locations[x][9]
            item_name = self.item_pool[item][3]
            print(location_name, "  >  ", item_name)

    # Modifies game ROM to reflect the current state of the World
    def write_to_rom(self, f, rom_offset=0):
        # Room-clearing rewards
        idx_tier2 = 0
        idx_tier3 = 0
        idx_tier4 = 0
        for map in self.maps:
            reward_tier = self.maps[map][2][1]
            if reward_tier > 0:
                reward = self.maps[map][2][0]
                f.seek(int("1aade", 16) + map + rom_offset)
                f.write(binascii.unhexlify(format(reward,"02x")))

                # Populate player level logic
                if reward_tier == 2:
                    f.seek(int("f4a7", 16) + 4*idx_tier2 + rom_offset)
                    f.write(binascii.unhexlify(format(map,"02x"))+b"\x03")
                    idx_tier2 += 1
                elif reward_tier == 3:
                    f.seek(int("f4bf", 16) + 4*idx_tier3 + rom_offset)
                    f.write(binascii.unhexlify(format(map,"02x"))+b"\x03")
                    idx_tier3 += 1
                elif reward_tier == 4:
                    f.seek(int("f4d7", 16) + 4*idx_tier4 + rom_offset)
                    f.write(binascii.unhexlify(format(map,"02x"))+b"\x03")
                    idx_tier4 += 1
        #print("maps done")

        # Items and abilities
        for x in self.item_locations:
            type = self.item_locations[x][1]

            # Write items to ROM
            if type == 1:
                item = self.item_locations[x][3]
                # print "Writing item ", item
                item_addr = self.item_locations[x][5]
                item_code = self.item_pool[item][2]
                text1_addr = self.item_locations[x][6]
                text2_addr = self.item_locations[x][7]
                text3_addr = self.item_locations[x][8]
                if item in self.item_text_long:
                    text_long = self.item_text_long[item]
                else:
                    text_long = ""
                if item in self.item_text_short:
                    text_short = self.item_text_short[item]
                else:
                    text_short = ""

                # Write item code to memory
                if item_code and item_addr:
                    f.seek(int(item_addr, 16) + rom_offset)
                    f.write(item_code)

                # Write item text, if appropriate
                if text1_addr and text_long:
                    f.seek(int(text1_addr, 16) + rom_offset)
                    f.write(text_long)
                    # f.write(b"\xd3")
                    # f.write(text_short)
                    f.write(b"\xc0")

                # Write "inventory full" item text, if appropriate
                if text2_addr and text_long:
                    f.seek(int(text2_addr, 16) + rom_offset)
                    # f.write(b"\xd3")
                    # f.write(text_short)
                    f.write(text_long)
                    f.write(b"\xcb\x45\x65\x4b\x4b\x4f\xc0")  # Just says "FULL!"

                # Write jeweler inventory text, if apprpriate
                if text3_addr and text_short:
                    f.seek(int(text3_addr, 16) + rom_offset)
                    f.write(text_short)

            # Write abilities to ROM
            elif type == 2:  # Check if filled
                ability = self.item_locations[x][3]
                ability_addr = self.item_locations[x][5]
                map = self.item_locations[x][8]

                # Change Dark Space type in event table
                if ability in [61, 62, 63, 64, 65, 66]:
                    f.seek(int(ability_addr, 16) + rom_offset)
                    f.write(b"\x05")

                # Update ability text table
                if ability == 61:  # Psycho Dash
                    # f.seek(int("8eb5a",16)+2*i+rom_offset)
                    f.seek(int("8eb5a", 16) + rom_offset)
                    f.write(map)
                if ability == 62:  # Psycho Slide
                    f.seek(int("8eb5c", 16) + rom_offset)
                    f.write(map)
                if ability == 63:  # Spin Dash
                    f.seek(int("8eb5e", 16) + rom_offset)
                    f.write(map)
                if ability == 64:  # Dark Friar
                    f.seek(int("8eb60", 16) + rom_offset)
                    f.write(map)
                if ability == 65:  # Aura Barrier
                    f.seek(int("8eb62", 16) + rom_offset)
                    f.write(map)
                if ability == 66:  # Earthquaker
                    f.seek(int("8eb64", 16) + rom_offset)
                    f.write(map)
        #print("items/abilities done")

        # Special code for 2-item event in Dao
        item1 = self.item_locations[125][3]
        item2 = self.item_locations[126][3]
        f.seek(int("8fde0", 16) + rom_offset)
        f.write(b"\xd3" + self.item_text_short[item1] + b"\xcb")
        f.write(self.item_text_short[item2] + b"\xcf\xce")

        # Write in-game spoilers
        i = 0
        for addr in self.spoiler_addresses:
            f.seek(int(self.spoiler_addresses[addr], 16) + rom_offset)
            if i < len(self.spoilers):
                f.write(self.spoilers[i])
                i += 1
        #print("spoilers done")

        # Enemizer
        if self.enemizer != "None":
            # "Fix" Ankor Wat Gorgons so they don't fall from the ceiling
            f.seek(int("bb825", 16) + rom_offset)
            f.write(b"\x00\x00\x00\x02\x27\x0F\x02\xC1\x4C\xA0\xB8\x6B")

            # Run enemizer
            self.enemize(f, rom_offset)
            # self.parse_maps(f,rom_offset)

        # Random start location
        if self.start_mode != "South Cape" or self.entrance_shuffle != "None":
            # print self.start_loc
            map_str = self.item_locations[self.start_loc][8] + self.item_locations[self.start_loc][7]

            # Change game start location
            f.seek(int("be517", 16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp location
            f.seek(int("8dbea", 16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp text
            map_name = self.location_text[self.start_loc]
            f.seek(int("8de1f", 16) + rom_offset)
            f.write(map_name + b"\x0D\xCB\xAC\x4D\x8E\xCB\xAC\x69\x84\xA3\xCA")
        #print("random start done")

        # Overworld shuffle
        if "Overworld Shuffle" in self.variant:
            ow_patch_data = []
            for entry in self.overworld_menus:
                # Prepare ROM edits
                new_entry = self.overworld_menus[entry][0]
                f.seek(int(self.overworld_menus[new_entry][4], 16) + rom_offset)
                ow_patch_data.append([self.overworld_menus[entry][4], f.read(8)])
                f.seek(int(self.overworld_menus[new_entry][6], 16) + rom_offset)
                ow_patch_data.append([self.overworld_menus[entry][6], f.read(11)])
                ow_patch_data.append([self.overworld_menus[new_entry][5], self.overworld_menus[entry][1]])

            for x in ow_patch_data:
                f.seek(int(x[0], 16) + rom_offset)
                f.write(x[1])
        #print("overworld shuffle done")

        # Entrance shuffle
        er_patch_data = []
        for exit in self.exits:
            #self.exits[exit][0] = exit   #TESTING ONLY
            # Prepare ROM edits
            new_exit = self.exits[exit][1]
            if new_exit and self.exits[exit][5]: # and exit != new_exit:
                try:
                    if self.exits[new_exit][6]:
                        new_data = self.exits[new_exit][6]
                    else:
                        f.seek(int(self.exits[new_exit][5], 16) + rom_offset)
                        new_data = f.read(8)
                    er_patch_data.append([self.exits[exit][5], new_data])
                except:
                    print("ERROR: exit data invalid",exit,new_exit)

        for x in er_patch_data:
            try:
                f.seek(int(x[0], 16) + rom_offset)
                f.write(x[1])
            except:
                print("ERROR: Not a valid address", x)
        #print("entrance shuffle done")

        # Check for additional switches that need to be set
        switch_str = []
        if self.start_loc == 30:  # Inca ramp can hardlock you
            switch_str.append(b"\x02\xcd\x0c\x01")
        elif self.start_loc == 47:  # Diamond Mine behind fences
            switch_str.append(b"\x02\xcd\x34\x01\x02\xcd\x35\x01\x02\xcd\x36\x01")

        if "Open Mode" in self.variant:
            switch_str.append(b"\x02\xcc\x11\x02\xcc\x14\x02\xcc\x1f\x02\xcc\x2a\x02\xcc\x41")

        if self.enemizer != "None" and self.enemizer != "Limited":
            switch_str.append(b"\x02\xcc\xa0\x02\xcc\xa1")

        f.seek(int("1ffb0", 16) + rom_offset)
        for x in switch_str:
            f.write(x)
        f.write(b"\x6b")
        #print("switches done")

        # Swapped exits
#        for exit in self.exits:
#            if self.exits[exit][1] > 0:
#                to_exit = self.exits[exit][1]
#                map_str = self.exits[to_exit][9]
#                if self.exits[exit][8] != "":
#                    f.seek(int(self.exits[exit][8], 16) + rom_offset)
#                    f.write(map_str)
#                else:
#                    map_id = map_str[0:1]
#                    xcoord = int.to_bytes(int.from_bytes(map_str[1:3], byteorder="little") // 16, 2, byteorder='little')
#                    ycoord = int.to_bytes(int.from_bytes(map_str[3:5], byteorder="little") // 16, 2, byteorder='little')
#                    facedir = map_str[5:6]
#                    camera = map_str[6:8]
#                    # print(map_id,xcoord,ycoord,facedir,camera)
#
#                    f.seek(int(self.exits_detailed[exit][0], 16) + rom_offset)
#                    f.write(map_id)
#                    f.seek(int(self.exits_detailed[exit][1], 16) + rom_offset)
#                    f.write(xcoord)
#                    f.seek(int(self.exits_detailed[exit][2], 16) + rom_offset)
#                    f.write(ycoord)
#                    if self.exits_detailed[exit][3] != "":
#                        f.seek(int(self.exits_detailed[exit][3], 16) + rom_offset)
#                        f.write(facedir)
#                    f.seek(int(self.exits_detailed[exit][4], 16) + rom_offset)
#                    f.write(camera)

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
        for loc in self.item_locations:
            if (self.start_mode == "Forced Unsafe" and self.item_locations[loc][6] == "Unsafe") or (
                    self.start_mode != "Forced Unsafe" and self.item_locations[loc][6] == "Safe") or (
                    self.item_locations[loc][6] == self.start_mode):
                locations.append(loc)

        if not locations:
            print("ERROR: Something is fishy with start locations")
            return -1
        else:
            # print locations
            # return 93   # TESTING!
            return locations[random.randint(0, len(locations) - 1)]


    # Shuffle travel destinations
    def shuffle_overworld(self):
        new_continents = [[],[],[],[],[]]

        # Ensure each continent has at least one travel location
        destination_list = [1,6,12,14,16,18]
        random.shuffle(destination_list)
        for continent in new_continents:
        	continent.append(destination_list.pop(0))

        # Randomly assign the rest of the locations
        destination_list += [2,3,4,5,7,8,9,10,11,13,15,17,19]
        random.shuffle(destination_list)
        new_continents[0] += destination_list[:4]
        new_continents[1] += destination_list[4:8]
        new_continents[2] += destination_list[8:10]
        new_continents[3] += destination_list[10:13]
        new_continents[4] += destination_list[-1:]
        for continent in new_continents:
        	random.shuffle(continent)

        self.overworld_menus[1][0] = new_continents[0][0]
        self.overworld_menus[2][0] = new_continents[0][1]
        self.overworld_menus[3][0] = new_continents[0][2]
        self.overworld_menus[4][0] = new_continents[0][3]
        self.overworld_menus[5][0] = new_continents[0][4]
        self.overworld_menus[6][0] = new_continents[1][0]
        self.overworld_menus[7][0] = new_continents[1][1]
        self.overworld_menus[8][0] = new_continents[1][2]
        self.overworld_menus[9][0] = new_continents[1][3]
        self.overworld_menus[10][0] = new_continents[1][4]
        self.overworld_menus[11][0] = new_continents[2][0]
        self.overworld_menus[12][0] = new_continents[2][1]
        self.overworld_menus[13][0] = new_continents[2][2]
        self.overworld_menus[14][0] = new_continents[3][0]
        self.overworld_menus[15][0] = new_continents[3][1]
        self.overworld_menus[16][0] = new_continents[3][2]
        self.overworld_menus[17][0] = new_continents[3][3]
        self.overworld_menus[18][0] = new_continents[4][0]
        self.overworld_menus[19][0] = new_continents[4][1]

        #print(self.overworld_menus)

        return


    # Shuffle enemies in ROM
    def enemize(self, f, rom_offset=0):
        f.seek(0)
        rom = f.read()

        # test_enemy = 13                         # TESTING!
        # test_set = self.enemies[test_enemy][0]

        complex_enemies = [4, 15, 53, 62, 88]  # Enemies with many sprites, or are no fun
        max_complex = 5

        # Get list of enemysets
        enemysets = []
        for set in self.enemysets:
            enemysets.append(set)

        f.seek(0)
        rom = f.read()

        # Shuffle enemy stats in Insane
        if self.enemizer == "Insane":
            insane_enemies = []
            insane_templates = []
            for enemy in self.enemies:
                if self.enemies[enemy][5] and enemy != 102:  # Special exception for Zombies
                    insane_enemies.append(enemy)
                    insane_templates.append(self.enemies[enemy][2])

            random.shuffle(insane_templates)
            insane_dictionary = {}
            i = 0

            for enemy in insane_enemies:
                insane_dictionary[enemy] = insane_templates[i]
                i += 1

        # Randomize enemy spritesets
        for map in self.maps:
            complex_ct = 0
            oldset = self.maps[map][0]
            # Determine new enemyset for map
            if self.enemizer == "Limited":
                sets = [oldset]
            elif not self.maps[map][7]:
                sets = enemysets[:]
            else:
                sets = self.maps[map][7][:]

            random.shuffle(sets)
            newset = sets[0]
            # if 10 in sets:      # TESTING!
            #    newset = 10
            # newset = test_set  # TESTING!

            # Gather enemies from old and new sets
            old_enemies = []
            new_enemies = []
            for enemy in self.enemies:
                if self.enemies[enemy][0] == oldset:
                    old_enemies.append(enemy)
                if self.enemies[enemy][0] == newset and self.enemies[enemy][5]:
                    new_enemies.append(enemy)

            # Update map header to reflect new enemyset
            if self.maps[map][3]:
                self.map_patches.append([self.maps[map][3],self.enemysets[newset][0],self.maps[map][4]])

            # Randomize each enemy in map
            addr_start = self.maps[map][5]
            addr_end = self.maps[map][6]
            for enemy in old_enemies:
                # print self.enemies[enemy][3]
                done = False
                addr = int(addr_start, 16) + rom_offset
                while not done:
                    addr = rom.find(self.enemies[enemy][1] + self.enemies[enemy][2], addr + 1)
                    if addr < 0 or addr > int(addr_end, 16) + rom_offset:
                        done = True
                    else:
                        # Pick an enemy from new set
                        enemytype = self.enemies[enemy][3]
                        walkable = self.enemies[enemy][4]

                        new_enemies_tmp = new_enemies[:]

                        # Get X/Y for special placement exceptions
                        f.seek(addr - 3)
                        xcoord = binascii.hexlify(f.read(1))
                        ycoord = binascii.hexlify(f.read(1))

                        # 4-Ways cannot be on a #$XF x-coord
                        if newset == 1 and 13 in new_enemies_tmp:
                            if xcoord[1] == 102:
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
                            new_enemytype = self.enemies[new_enemy][3]
                            new_walkable = self.enemies[new_enemy][4]
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
                        # f.write(b"\x00" + self.enemies[test_enemy][1] + self.enemies[test_enemy][2])  # TESTING!
                        f.write(b"\x00" + self.enemies[new_enemy][1])
                        if self.enemizer == "Balanced" and enemy == 102:
                            f.write(b"\x47")
                        elif map != 27 and self.enemizer != "Balanced":  # Moon Tribe cave enemies retain same template
                            if self.enemizer == "Insane" and new_enemy != 102:  # Again, zombie exception
                                f.write(insane_dictionary[new_enemy])
                            else:
                                f.write(self.enemies[new_enemy][2])

        # Disable all non-enemy sprites
        if self.enemizer != "Limited":
            for sprite in self.nonenemy_sprites:
                f.seek(int(self.nonenemy_sprites[sprite][1], 16) + rom_offset + 3)
                f.write(b"\x02\xe0")

    # Build world
    def __init__(self, settings: RandomizerData, statues=[1,2,3,4,5,6], kara=3, gem=[3,5,8,12,20,30,50], incatile=[9,5], hieroglyphs=[1,2,3,4,5,6], boss_order=[1,2,3,4,5,6,7]):

        self.seed = settings.seed
        self.statues = statues
        self.boss_order = boss_order
        self.dungeons_req = []
        for x in self.statues:
            self.dungeons_req.append(self.boss_order[x-1])

        gaia_coinflip = random.randint(0, 1)
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            self.goal = "Red Jewel Hunt"
        elif settings.goal.value == Goal.APO_GAIA.value or (settings.goal.value == Goal.RANDOM_GAIA.value and gaia_coinflip):
            self.goal = "Apocalypse Gaia"
        else:
            self.goal = "Dark Gaia"


        if settings.logic.value == Logic.COMPLETABLE.value:
            self.logic_mode = "Completable"
        elif settings.logic.value == Logic.BEATABLE.value:
            self.logic_mode = "Beatable"
        else:
            self.logic_mode = "Chaos"

        if settings.entrance_shuffle.value == EntranceShuffle.NONE.value:
            self.entrance_shuffle = "None"
        elif settings.entrance_shuffle.value == EntranceShuffle.COUPLED.value:
            self.entrance_shuffle = "Coupled"
        elif settings.entrance_shuffle.value == EntranceShuffle.UNCOUPLED.value:
            self.entrance_shuffle = "Uncoupled"

        if settings.start_location.value == StartLocation.SOUTH_CAPE.value:
            self.start_mode = "South Cape"
        elif settings.start_location.value == StartLocation.SAFE.value:
            self.start_mode = "Safe"
        elif settings.start_location.value == StartLocation.UNSAFE.value:
            self.start_mode = "Unsafe"
        else:
            self.start_mode = "Forced Unsafe"

        if settings.enemizer.value == Enemizer.NONE.value:
            self.enemizer = "None"
        elif settings.enemizer.value == Enemizer.BALANCED.value:
            self.enemizer = "Balanced"
        elif settings.enemizer.value == Enemizer.LIMITED.value:
            self.enemizer = "Limited"
        elif settings.enemizer.value == Enemizer.FULL.value:
            self.enemizer = "Full"
        else:
            self.enemizer = "Insane"

        if settings.ohko:
            self.variant = ["OHKO"]
        elif settings.red_jewel_madness:
            self.variant = ["RJM"]
        else:
            self.variant = []

        if settings.allow_glitches:
            self.variant.append("Allow Glitches")

        if settings.boss_shuffle:
            self.variant.append("Boss Shuffle")

        if settings.overworld_shuffle:
            self.variant.append("Overworld Shuffle")

        if settings.open_mode:
            self.variant.append("Open Mode")

        if settings.z3:
            self.variant.append("Z3 Mode")

        self.firebird = settings.firebird
        self.start_loc = 10
#        self.level = settings.level.value
        self.difficulty = settings.difficulty.value
        self.kara = kara
        self.gem = gem
        self.incatile = incatile
        self.hieroglyphs = hieroglyphs
        self.placement_log = []
        self.spoilers = []
        self.dark_space_sets = [[46, 47], [58, 60]]
        self.required_items = [20, 36]
        self.good_items = [10, 13, 24, 25, 63, 64, 65]
        self.trolly_locations = [32, 45, 64, 65, 102, 108, 121, 128, 136, 147]
        self.free_locations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 24]
        self.map_patches = []

        # Initialize item pool, considers special attacks as "items"
        # Format = { ID:  [Quantity, Type code (1=item, 2=ability, 3=statue,4=other),
        #                  ROM Code, Name, TakesInventorySpace,
        #                  ProgressionType (1=unlocks new locations,2=quest item,3=no progression)] }
        self.item_pool = {
            # Items
            0: [2, 1, b"\x00", "Nothing", False, 3],
            1: [45, 1, b"\x01", "Red Jewel", False, 1],
            2: [1, 1, b"\x02", "Prison Key", True, 1],
            3: [1, 1, b"\x03", "Inca Statue A", True, 1],
            4: [1, 1, b"\x04", "Inca Statue B", True, 1],
            5: [0, 1, b"\x05", "Inca Melody", True, 3],
            6: [12, 1, b"\x06", "Herb", False, 3],
            7: [1, 1, b"\x07", "Diamond Block", True, 1],
            8: [1, 1, b"\x08", "Wind Melody", True, 1],
            9: [1, 1, b"\x09", "Lola's Melody", True, 1],
            10: [1, 1, b"\x0a", "Large Roast", True, 1],
            11: [1, 1, b"\x0b", "Mine Key A", True, 1],
            12: [1, 1, b"\x0c", "Mine Key B", True, 1],
            13: [1, 1, b"\x0d", "Memory Melody", True, 1],
            14: [4, 1, b"\x0e", "Crystal Ball", True, 2],
            15: [1, 1, b"\x0f", "Elevator Key", True, 1],
            16: [1, 1, b"\x10", "Mu Palace Key", True, 1],
            17: [1, 1, b"\x11", "Purification Stone", True, 1],
            18: [2, 1, b"\x12", "Statue of Hope", True, 1],
            19: [2, 1, b"\x13", "Rama Statue", False, 2],
            20: [1, 1, b"\x14", "Magic Dust", True, 2],
            21: [0, 1, b"\x15", "Blue Journal", False, 3],
            22: [1, 1, b"\x16", "Lance's Letter", False, 3],
            23: [1, 1, b"\x17", "Necklace Stones", True, 1],
            24: [1, 1, b"\x18", "Will", True, 1],
            25: [1, 1, b"\x19", "Teapot", True, 1],
            26: [3, 1, b"\x1a", "Mushroom Drops", True, 1],
            27: [0, 1, b"\x1b", "Bag of Gold", False, 3],
            28: [1, 1, b"\x1c", "Black Glasses", False, 1],
            29: [1, 1, b"\x1d", "Gorgon Flower", True, 1],
            30: [1, 1, b"\x1e", "Hieroglyph", False, 2],
            31: [1, 1, b"\x1f", "Hieroglyph", False, 2],
            32: [1, 1, b"\x20", "Hieroglyph", False, 2],
            33: [1, 1, b"\x21", "Hieroglyph", False, 2],
            34: [1, 1, b"\x22", "Hieroglyph", False, 2],
            35: [1, 1, b"\x23", "Hieroglyph", False, 2],
            36: [1, 1, b"\x24", "Aura", True, 1],
            37: [1, 1, b"\x25", "Lola's Letter", False, 1],
            38: [1, 1, b"\x26", "Father's Journal", False, 2],
            39: [1, 1, b"\x27", "Crystal Ring", False, 1],
            40: [1, 1, b"\x28", "Apple", True, 1],
            41: [1, 1, b"\x2e", "2 Red Jewels", False, 3],
            42: [1, 1, b"\x2f", "3 Red Jewels", False, 3],

            # Status Upgrades
            50: [3, 1, b"\x87", "HP Upgrade", False, 3],
            51: [1, 1, b"\x89", "DEF Upgrade", False, 3],
            52: [2, 1, b"\x88", "STR Upgrade", False, 3],
            53: [1, 1, b"\x8a", "Psycho Dash Upgrade", False, 3],
            54: [2, 1, b"\x8b", "Dark Friar Upgrade", False, 3],
            55: [0, 1, b"\x8c", "Heart Piece", False, 3],

            # Abilities
            60: [0, 2, "", "Nothing", False, 3],
            61: [1, 2, "", "Psycho Dash", False, 1],
            62: [1, 2, "", "Psycho Slider", False, 1],
            63: [1, 2, "", "Spin Dash", False, 1],
            64: [1, 2, "", "Dark Friar", False, 1],
            65: [1, 2, "", "Aura Barrier", False, 1],
            66: [1, 2, "", "Earthquaker", False, 1],
            67: [0, 2, "", "Firebird", False, 1],

            # Mystic Statues
            100: [1, 3, "", "Mystic Statue 1", False, 2],
            101: [1, 3, "", "Mystic Statue 2", False, 2],
            102: [1, 3, "", "Mystic Statue 3", False, 2],
            103: [1, 3, "", "Mystic Statue 4", False, 2],
            104: [1, 3, "", "Mystic Statue 5", False, 2],
            105: [1, 3, "", "Mystic Statue 6", False, 2],

            # Event Switches
            500: [0, 4, "", "Kara Released", False, 1],
            501: [0, 4, "", "Itory: Got Lilly", False, 1],
            502: [0, 4, "", "Moon Tribe: Healed Spirits", False, 1],
            503: [0, 4, "", "Inca: Beat Castoth", False, 1],
            504: [0, 4, "", "Freejia: Found Laborer", False, 1],
            505: [0, 4, "", "Neil's: Memory Restored", False, 1],
            506: [0, 4, "", "Sky Garden: Map 82 NW Switch", False, 1],
            507: [0, 4, "", "Sky Garden: Map 82 NE Switch", False, 1],
            508: [0, 4, "", "Sky Garden: Map 82 NW Switch", False, 1],
            509: [0, 4, "", "Sky Garden: Map 84 Switch", False, 1],
            510: [0, 4, "", "Seaside: Fountain Purified", False, 1],
            511: [0, 4, "", "Mu: Water Lowered 1", False, 1],
            512: [0, 4, "", "Mu: Water Lowered 2", False, 1],
            513: [0, 4, "", "Angel: Puzzle Complete", False, 1],
            514: [0, 4, "", "Mt Kress: Drops Used 1", False, 1],
            515: [0, 4, "", "Mt Kress: Drops Used 2", False, 1],
            516: [0, 4, "", "Mt Kress: Drops Used 3", False, 1],
            517: [0, 4, "", "Pyramid: Hieroglyphs Placed", False, 1],
            518: [0, 4, "", "Babel: Castoth Defeated", False, 1],
            519: [0, 4, "", "Babel: Viper Defeated", False, 1],
            520: [0, 4, "", "Babel: Vampires Defeated", False, 1],
            521: [0, 4, "", "Babel: Sand Fanger Defeated", False, 1],
            522: [0, 4, "", "Babel: Mummy Queen Defeated", False, 1],
            523: [0, 4, "", "Mansion: Solid Arm Defeated", False, 1],

            # Misc
            600: [0, 4, "", "Freedan Access", False, 1],
            601: [0, 4, "", "Glitches", False, 1],
            602: [0, 4, "", "Early Firebird", False, 1]
        }

        # Define Item/Ability/Statue locations
        # Format: { ID: [Region, Type (1=item,2=ability,3=statue,4=other), Filled Flag,
        #                Filled Item, Restricted Items, Item Addr, Text Addr, Text2 Addr,
        #                Special (map# or inventory addr), Name, Swapped Flag]}
        #         (For random start, [6]=Type, [7]=XY_spawn_data)
        self.item_locations = {
            # Jeweler
            0:   [2, 1, False, 0, [], "8d019", "8d19d", "", "8d260", "Jeweler Reward 1                    "],
            1:   [3, 1, False, 0, [], "8d028", "8d1ba", "", "8d274", "Jeweler Reward 2                    "],
            2:   [4, 1, False, 0, [], "8d037", "8d1d7", "", "8d288", "Jeweler Reward 3                    "],
            3:   [5, 1, False, 0, [], "8d04a", "8d1f4", "", "8d29c", "Jeweler Reward 4                    "],
            4:   [6, 1, False, 0, [], "8d059", "8d211", "", "8d2b0", "Jeweler Reward 5                    "],
            5:   [7, 1, False, 0, [], "8d069", "8d2ea", "", "8d2c4", "Jeweler Reward 6                    "],

            # South Cape
            6:   [21, 1, False, 0, [],  "F51D",  "F52D", "F543", "", "South Cape: Bell Tower              "],
            7:   [20, 1, False, 0, [], "4846e", "48479",     "", "", "South Cape: Fisherman               "],  # text2 was 0c6a1
            8:   [26, 1, False, 0, [],  "F59D",  "F5AD", "F5C3", "", "South Cape: Lance's House           "],
            9:   [23, 1, False, 0, [], "499e4", "49be5",     "", "", "South Cape: Lola                    "],

            10:  [21, 2, False, 0, [64, 65, 66], "c830a", "Safe", b"\xE0\x00\x70\x00\x83\x00\x43", b"\x01", "South Cape: Dark Space              "],

            # Edward's
            11:  [30, 1, False, 0, [], "4c214", "4c299", "", "", "Edward's Castle: Hidden Guard       "],
            12:  [30, 1, False, 0, [], "4d0ef", "4d141", "", "", "Edward's Castle: Basement           "],
            13:  [32, 1, False, 0, [], "4d32f", "4d4b1", "", "", "Edward's Prison: Hamlet             "],  # text 4d5f4?

            14:  [32, 2, False, 0, [64, 65, 66], "c8637", "", "", b"\x0b", "Edward's Prison: Dark Space         "],

            # Underground Tunnel
            15:  [42, 1, False, 0, [], "1AFA9",    "",     "", "", "Underground Tunnel: Spike's Chest   "],
            16:  [44, 1, False, 0, [], "1AFAE",    "",     "", "", "Underground Tunnel: Small Room Chest"],
            17:  [48, 1, False, 0, [], "1AFB3",    "",     "", "", "Underground Tunnel: Ribber's Chest  "],
            18:  [49, 1, False, 0, [], "F61D", "F62D", "F643", "", "Underground Tunnel: Barrels         "],

            19:  [47, 2, True, 0, [], "c8aa2", "Unsafe", b"\xA0\x00\xD0\x04\x83\x00\x74", b"\x12", "Underground Tunnel: Dark Space      "],  # Always open

            # Itory
            20:  [51, 1, False, 0, [],  "F69D",  "F6AD",  "F6C3", "", "Itory Village: Logs                 "],
            21:  [58, 1, False, 0, [], "4f375", "4f38d", "4f3a8", "", "Itory Village: Cave                 "],

            22:  [51, 2, False, 0, [64, 65, 66], "c8b34", "Safe", b"\x30\x04\x90\x00\x83\x00\x35", b"\x15", "Itory Village: Dark Space           "],

            # Moon Tribe
            23:  [62, 1, False, 0, [], "4fae1", "4faf9", "4fb16", "", "Moon Tribe: Cave                    "],

            # Inca
            24:  [71, 1, False, 0, [], "1AFB8",      "",      "", "", "Inca Ruins: Diamond-Block Chest     "],
            25:  [92, 1, False, 0, [], "1AFC2",      "",      "", "", "Inca Ruins: Broken Statues Chest    "],
            26:  [83, 1, False, 0, [], "1AFBD",      "",      "", "", "Inca Ruins: Stone Lord Chest        "],
            27:  [93, 1, False, 0, [], "1AFC6",      "",      "", "", "Inca Ruins: Slugger Chest           "],
            28:  [76, 1, False, 0, [], "9c5bd", "9c614", "9c637", "", "Inca Ruins: Singing Statue          "],

            29:  [96, 2,  True, 0, [], "c9302", "Unsafe", b"\x10\x01\x90\x00\x83\x00\x32", b"\x28", "Inca Ruins: Dark Space 1            "],  # Always open
            30:  [93, 2, False, 0, [], "c923b", "Unsafe", b"\xC0\x01\x50\x01\x83\x00\x32", b"\x26", "Inca Ruins: Dark Space 2            "],
            31:  [77, 2, False, 0, [], "c8db8",       "",                              "", b"\x1e", "Inca Ruins: Final Dark Space        "],

            # Gold Ship
            32:  [100, 1, False, 0, [], "5965e", "5966e", "", "", "Gold Ship: Seth                     "],

            # Diamond Coast
            33:  [102, 1, False, 0, [], "F71D", "F72D", "F743", "", "Diamond Coast: Jar                  "],

            # Freejia
            34:  [121, 1, False, 0, [],  "F79D",  "F7AD",  "F7C3", "", "Freejia: Hotel                      "],
            35:  [110, 1, False, 0, [], "5b6d8", "5b6e8",      "", "", "Freejia: Creepy Guy                 "],
            36:  [110, 1, False, 0, [], "5cf9e", "5cfae", "5cfc4", "", "Freejia: Trash Can 1                "],
            37:  [110, 1, False, 0, [], "5cf3d", "5cf49",      "", "", "Freejia: Trash Can 2                "],  # text2 was 5cf5b
            38:  [115, 1, False, 0, [], "5b8b7", "5b962", "5b9ee", "", "Freejia: Snitch                     "],  # text1 was @5b94d

            39:  [125, 2, False, 0, [64, 65, 66], "c96ce", "Safe", b"\x40\x00\xa0\x00\x83\x00\x11", b"\x34", "Freejia: Dark Space                 "],

            # Diamond Mine
            40:  [134, 1, False, 0, [], "1AFD0",      "",      "", "", "Diamond Mine: Chest                 "],
            41:  [137, 1, False, 0, [], "5d7e4", "5d819", "5d830", "", "Diamond Mine: Trapped Laborer       "],
            42:  [143, 1, False, 0, [], "aa777", "aa85c",      "", "", "Diamond Mine: Laborer w/Elevator Key"],  # text1 was aa811
            43:  [148, 1, False, 0, [], "5d4d2", "5d4eb", "5d506", "", "Diamond Mine: Morgue                "],
            44:  [149, 1, False, 0, [], "aa757", "aa7ef",      "", "", "Diamond Mine: Laborer w/Mine Key    "],  # text1 was aa7b4
            45:  [150, 1, False, 0, [], "5d2b0", "5d2da",      "", "", "Diamond Mine: Sam                   "],

            46:  [136, 2, False, 0, [], "c9a87", "Unsafe", b"\xb0\x01\x70\x01\x83\x00\x32", b"\x40", "Diamond Mine: Appearing Dark Space  "],  # Always open
            47:  [131, 2, False, 0, [], "c98b0", "Unsafe", b"\xd0\x00\xc0\x00\x83\x00\x61", b"\x3d", "Diamond Mine: Dark Space at Wall    "],
            48:  [142, 2, False, 0, [], "c9b49",       "",                              "", b"\x42", "Diamond Mine: Dark Space behind Wall"],

            49:  [173, 1, False, 0, [], "1AFDD", "", "", "", "Sky Garden: (NE) Platform Chest     "],
            50:  [174, 1, False, 0, [], "1AFD9", "", "", "", "Sky Garden: (NE) Blue Cyber Chest   "],
            51:  [175, 1, False, 0, [], "1AFD5", "", "", "", "Sky Garden: (NE) Statue Chest       "],
            52:  [181, 1, False, 0, [], "1AFE2", "", "", "", "Sky Garden: (SE) Dark Side Chest    "],
            53:  [186, 1, False, 0, [], "1AFE7", "", "", "", "Sky Garden: (SW) Ramp Chest         "],
            54:  [187, 1, False, 0, [], "1AFEC", "", "", "", "Sky Garden: (SW) Dark Side Chest    "],
            55:  [193, 1, False, 0, [], "1AFF1", "", "", "", "Sky Garden: (NW) Top Chest          "],
            56:  [193, 1, False, 0, [], "1AFF5", "", "", "", "Sky Garden: (NW) Bottom Chest       "],

            57:  [170, 2, False, 0, [64, 65, 66], "c9d63",   "Safe", b"\x90\x00\x70\x00\x83\x00\x22", b"\x4c", "Sky Garden: Dark Space (Foyer)      "],
            58:  [169, 2, False, 0,           [], "ca505", "Unsafe", b"\x70\x00\xa0\x00\x83\x00\x11", b"\x56", "Sky Garden: Dark Space (SE)         "],  # in the room
            59:  [184, 2, False, 0,           [], "ca173",       "",                              "", b"\x51", "Sky Garden: Dark Space (SW)         "],
            60:  [195, 2, False, 0,           [], "ca422", "Unsafe", b"\x20\x00\x70\x00\x83\x00\x44", b"\x54", "Sky Garden: Dark Space (NW)         "],

            # Seaside Palace
            61:  [202, 1, False, 0, [], "1AFFF",      "",      "", "", "Seaside Palace: Side Room Chest     "],
            62:  [200, 1, False, 0, [], "1AFFA",      "",      "", "", "Seaside Palace: First Area Chest    "],
            63:  [205, 1, False, 0, [], "1B004",      "",      "", "", "Seaside Palace: Second Area Chest   "],
            64:  [206, 1, False, 0, [], "68af7", "68ea9", "68f02", "", "Seaside Palace: Buffy               "],
            65:  [208, 1, False, 0, [], "6922d", "6939e", "693b7", "", "Seaside Palace: Coffin              "],  # text1 was 69377

            66:  [200, 2, False, 0, [64, 65, 66], "ca574", "Safe", b"\xf0\x02\x90\x00\x83\x00\x64", b"\x5a", "Seaside Palace: Dark Space          "],

            # Mu
            67:  [215, 1, False, 0, [], "1B012",      "", "", "", "Mu: Empty Chest 1                   "],
            68:  [218, 1, False, 0, [], "1B01B",      "", "", "", "Mu: Empty Chest 2                   "],
            69:  [223, 1, False, 0, [], "698be", "698d2", "", "", "Mu: Hope Statue 1                   "],
            70:  [234, 1, False, 0, [], "69966", "69975", "", "", "Mu: Hope Statue 2                   "],
            71:  [213, 1, False, 0, [], "1B00D",      "", "", "", "Mu: Chest s/o Hope Room 2           "],
            72:  [212, 1, False, 0, [], "1B009",      "", "", "", "Mu: Rama Chest N                    "],
            73:  [217, 1, False, 0, [], "1B016",      "", "", "", "Mu: Rama Chest E                    "],

            74:  [216, 2,  True, 0, [], "ca92d", "", "", b"\x60", "Mu: Open Dark Space                 "],  # Always open
            75:  [226, 2, False, 0, [], "caa99", "", "", b"\x62", "Mu: Slider Dark Space               "],

            # Angel Village
            76:  [254, 1, False, 0, [], "F81D", "F82D", "F843", "", "Angel Village: Dance Hall           "],
            77:  [255, 2, False, 0, [64, 65, 66], "caf67", "Safe", b"\x90\x01\xb0\x00\x83\x01\x12", b"\x6c", "Angel Village: Dark Space           "],

            # Angel Dungeon
            78:  [265, 1, False, 0, [], "1B020",    "",     "", "", "Angel Dungeon: Slider Chest         "],
            79:  [271, 1, False, 0, [], "F89D", "F8AD", "F8C3", "", "Angel Dungeon: Ishtar's Room        "],
            80:  [274, 1, False, 0, [], "1B02A",    "",     "", "", "Angel Dungeon: Puzzle Chest 1       "],
            81:  [274, 1, False, 0, [], "1B02E",    "",     "", "", "Angel Dungeon: Puzzle Chest 2       "],
            82:  [273, 1, False, 0, [], "1B025",    "",     "", "", "Angel Dungeon: Ishtar's Chest       "],

            # Watermia
            83:  [280, 1, False, 0, [],  "F91D",  "F92D",  "F943", "", "Watermia: West Jar                  "],
            85:  [286, 1, False, 0, [], "7ad21", "7aede",      "", "", "Watermia: Lance                     "],  # text2 was 7afa7
            86:  [283, 1, False, 0, [],  "F99D",  "F9AD",  "F9C3", "", "Watermia: Gambling House            "],
            87:  [280, 1, False, 0, [], "79248", "79288", "792a1", "", "Watermia: Russian Glass             "],

            88:  [282, 2, False, 0, [64, 65, 66], "cb644", "Safe", b"\x40\x00\xa0\x00\x83\x00\x11", b"\x7c", "Watermia: Dark Space                "],

            # Great Wall
            89:  [290, 1, False, 0, [], "7b5c5", "7b5d1", "", "", "Great Wall: Necklace 1              "],
            90:  [292, 1, False, 0, [], "7b625", "7b631", "", "", "Great Wall: Necklace 2              "],
            91:  [292, 1, False, 0, [], "1B033",      "", "", "", "Great Wall: Chest 1                 "],
            92:  [294, 1, False, 0, [], "1B038",      "", "", "", "Great Wall: Chest 2                 "],

            93:  [295, 2, False, 0, [], "cbb11", "Unsafe", b"\x60\x00\xc0\x02\x83\x20\x38", b"\x85", "Great Wall: Archer Dark Space       "],
            94:  [297, 2,  True, 0, [], "cbb80", "Unsafe", b"\x50\x01\x80\x04\x83\x00\x63", b"\x86", "Great Wall: Platform Dark Space     "],  # Always open
            95:  [300, 2, False, 0, [], "cbc60",       "",                              "", b"\x88", "Great Wall: Appearing Dark Space    "],

            # Euro
            96:  [310, 1, False, 0, [],  "FA1D",  "FA2D",  "FA43", "", "Euro: Alley                         "],
            97:  [310, 1, False, 0, [], "7c0b3", "7c0f3",      "", "", "Euro: Apple Vendor                  "],
            98:  [320, 1, False, 0, [], "7e51f", "7e534", "7e54a", "", "Euro: Hidden House                  "],
            99:  [323, 1, False, 0, [], "7cd12", "7cd39", "7cd9b", "", "Euro: Store Item 1                  "],
            100: [323, 1, False, 0, [], "7cdf9", "7ce28", "7ce3e", "", "Euro: Store Item 2                  "],  # text2 was 7cedd
            101: [321, 1, False, 0, [],  "FA9D",  "FAAD",  "FAC3", "", "Euro: Shrine                        "],
            102: [315, 1, False, 0, [], "7df58", "7e10a",      "", "", "Euro: Ann                           "],

            103: [325, 2, False, 0, [64, 65, 66], "cc0b0", "Safe", b"\xb0\x00\xb0\x00\x83\x00\x11", b"\x99", "Euro: Dark Space                    "],

            # Mt Temple
            104: [336, 1, False, 0, [], "1B03D", "", "", "", "Mt. Temple: Red Jewel Chest         "],
            105: [338, 1, False, 0, [], "1B042", "", "", "", "Mt. Temple: Drops Chest 1           "],
            106: [342, 1, False, 0, [], "1B047", "", "", "", "Mt. Temple: Drops Chest 2           "],
            107: [343, 1, False, 0, [], "1B04C", "", "", "", "Mt. Temple: Drops Chest 3           "],
            108: [345, 1, False, 0, [], "1B051", "", "", "", "Mt. Temple: Final Chest             "],

            109: [332, 2, False, 0, [], "cc24f", "Unsafe", b"\xf0\x01\x10\x03\x83\x00\x44", b"\xa1", "Mt. Temple: Dark Space 1            "],
            110: [337, 2, False, 0, [], "cc419", "Unsafe", b"\xc0\x07\xc0\x00\x83\x00\x28", b"\xa3", "Mt. Temple: Dark Space 2            "],
            111: [343, 2, False, 0, [], "cc7b8",       "",                              "", b"\xa7", "Mt. Temple: Dark Space 3            "],

            # Natives'
            112: [353, 1, False, 0, [],  "FB1D",  "FB2D", "FB43", "", "Natives' Village: Statue Room       "],
            113: [354, 1, False, 0, [], "893af", "8942a",     "", "", "Natives' Village: Statue            "],

            114: [350, 2, False, 0, [64, 65, 66], "cca37", "Safe", b"\xc0\x01\x50\x00\x83\x00\x22", b"\xac", "Natives' Village: Dark Space        "],

            # Ankor Wat
            115: [361, 1, False, 0, [], "1B056",      "",      "", "", "Ankor Wat: Ramp Chest               "],
            116: [370, 1, False, 0, [], "1B05B",      "",      "", "", "Ankor Wat: Flyover Chest            "],
            117: [378, 1, False, 0, [], "1B060",      "",      "", "", "Ankor Wat: U-Turn Chest             "],
            118: [382, 1, False, 0, [], "1B065",      "",      "", "", "Ankor Wat: Drop Down Chest          "],
            119: [389, 1, False, 0, [], "1B06A",      "",      "", "", "Ankor Wat: Forgotten Chest          "],
            120: [380, 1, False, 0, [], "89fa3", "89fbb",      "", "", "Ankor Wat: Glasses Location         "],  # slow text @89fdc
            121: [391, 1, False, 0, [], "89adc", "89af1", "89b07", "", "Ankor Wat: Spirit                   "],  # item was 89b0d, text was 89e2e

            122: [372, 2,  True, 0, [], "cce92", "Unsafe", b"\x20\x04\x30\x03\x83\x00\x46", b"\xb6", "Ankor Wat: Garden Dark Space        "],  # Always open
            123: [377, 2, False, 0, [], "cd0a2",       "",                              "", b"\xb8", "Ankor Wat: Earthquaker Dark Space   "],
            124: [383, 2,  True, 0, [], "cd1a7", "Unsafe", b"\xb0\x02\xc0\x01\x83\x00\x33", b"\xbb", "Ankor Wat: Drop Down Dark Space     "],  # Always open

            # Dao
            125: [400, 1, False, 0, [], "8b1b0",      "",      "", "", "Dao: Entrance Item 1                "],
            126: [400, 1, False, 0, [], "8b1b5",      "",      "", "", "Dao: Entrance Item 2                "],
            127: [400, 1, False, 0, [],  "FB9D",  "FBAD",  "FBC3", "", "Dao: East Grass                     "],
            128: [403, 1, False, 0, [], "8b016", "8b073", "8b090", "", "Dao: Snake Game                     "],

            129: [400, 2, False, 0, [64, 65, 66], "cd3d0", "Safe", b"\x20\x00\x80\x00\x83\x00\x23", b"\xc3", "Dao: Dark Space                     "],

            # Pyramid
            130: [411, 1, False, 0, [], "8dcb7", "8e66c", "8e800", "", "Pyramid: Dark Space Top             "],  # text2 was 8e800
            131: [412, 1, False, 0, [],  "FC1D",  "FC2D",  "FC43", "", "Pyramid: Hidden Platform            "],
            132: [442, 1, False, 0, [], "8c7b2", "8c7c9",      "", "", "Pyramid: Hieroglyph 1               "],
            133: [422, 1, False, 0, [], "1B06F",      "",      "", "", "Pyramid: Room 2 Chest               "],
            134: [443, 1, False, 0, [], "8c879", "8c88c",      "", "", "Pyramid: Hieroglyph 2               "],
            135: [432, 1, False, 0, [], "1B079",      "",      "", "", "Pyramid: Room 3 Chest               "],
            136: [444, 1, False, 0, [], "8c921", "8c934",      "", "", "Pyramid: Hieroglyph 3               "],
            137: [439, 1, False, 0, [], "1B07E",      "",      "", "", "Pyramid: Room 4 Chest               "],
            138: [445, 1, False, 0, [], "8c9c9", "8c9dc",      "", "", "Pyramid: Hieroglyph 4               "],
            139: [428, 1, False, 0, [], "1B074",      "",      "", "", "Pyramid: Room 5 Chest               "],
            140: [446, 1, False, 0, [], "8ca71", "8ca84",      "", "", "Pyramid: Hieroglyph 5               "],
            141: [447, 1, False, 0, [], "8cb19", "8cb2c",      "", "", "Pyramid: Hieroglyph 6               "],

            142: [413, 2, True, 0, [], "cd570", "Unsafe", b"\xc0\x01\x90\x03\x83\x00\x44", b"\xcc", "Pyramid: Dark Space Bottom          "],  # Always open

            # Babel
            143: [461, 1, False, 0, [],  "FC9D",  "FCAD",  "FCC3", "", "Babel: Pillow                       "],
            144: [461, 1, False, 0, [], "99a4f", "99ae4", "99afe", "", "Babel: Force Field                  "],  # item was  99a61

            145: [461, 2, False, 0, [64, 65, 66], "ce09b", "Forced Unsafe", b"\x90\x07\xb0\x01\x83\x10\x28", b"\xdf", "Babel: Dark Space Bottom            "],
            146: [472, 2, False, 0, [64, 65, 66], "ce159",          "Safe", b"\xb0\x02\xb0\x01\x83\x10\x23", b"\xe3", "Babel: Dark Space Top               "],

            # Jeweler's Mansion
            147: [480, 1, False, 0, [], "1B083", "", "", "", "Jeweler's Mansion: Chest            "],

            # Mystic Statues
            148: [101, 3, False, 0, [101, 102, 103, 104, 105], "", "", "", "", "Castoth Prize                       "],
            149: [198, 3, False, 0, [100, 102, 103, 104, 105], "", "", "", "", "Viper Prize                         "],
            150: [244, 3, False, 0, [100, 101, 103, 104, 105], "", "", "", "", "Vampires Prize                      "],
            151: [302, 3, False, 0, [100, 101, 102, 104, 105], "", "", "", "", "Sand Fanger Prize                   "],
            152: [448, 3, False, 0, [100, 101, 102, 103, 105], "", "", "", "", "Mummy Queen Prize                   "],
            153: [479, 3, False, 0, [100, 101, 102, 103, 104], "", "", "", "", "Babel Prize                         "],

            # Event Switches
            500: [500, 4, True, 500, [], "", "", "", "", "Kara                                "],
            501: [501, 4, True, 501, [], "", "", "", "", "Lilly                               "],
            502: [502, 4, True, 502, [], "", "", "", "", "Moon Tribe: Spirits Healed          "],
            503: [503, 4, True, 503, [], "", "", "", "", "Inca: Castoth defeated              "],
            504: [504, 4, True, 504, [], "", "", "", "", "Freejia: Found Laborer              "],
            505: [505, 4, True, 505, [], "", "", "", "", "Neil's Memory Restored              "],
            506: [506, 4, True, 506, [], "", "", "", "", "Sky Garden: Map 82 NW Switch        "],
            507: [507, 4, True, 507, [], "", "", "", "", "Sky Garden: Map 82 NE Switch        "],
            508: [508, 4, True, 508, [], "", "", "", "", "Sky Garden: Map 82 SE Switch        "],
            509: [509, 4, True, 509, [], "", "", "", "", "Sky Garden: Map 84 Switch           "],
            510: [510, 4, True, 510, [], "", "", "", "", "Seaside: Fountain Purified          "],
            511: [511, 4, True, 511, [], "", "", "", "", "Mu: Water Lowered 1                 "],
            512: [512, 4, True, 512, [], "", "", "", "", "Mu: Water Lowered 2                 "],
            513: [513, 4, True, 513, [], "", "", "", "", "Angel: Puzzle Complete              "],
            514: [514, 4, True, 514, [], "", "", "", "", "Mt Kress: Drops used 1              "],
            515: [515, 4, True, 515, [], "", "", "", "", "Mt Kress: Drops used 2              "],
            516: [516, 4, True, 516, [], "", "", "", "", "Mt Kress: Drops used 3              "],
            517: [517, 4, True, 517, [], "", "", "", "", "Pyramid: Hieroglyphs placed         "],
            518: [518, 4, True, 518, [], "", "", "", "", "Babel: Castoth defeated             "],
            519: [519, 4, True, 519, [], "", "", "", "", "Babel: Viper defeated               "],
            520: [520, 4, True, 520, [], "", "", "", "", "Babel: Vampires defeated            "],
            521: [521, 4, True, 521, [], "", "", "", "", "Babel: Sand Fanger defeated         "],
            522: [522, 4, True, 522, [], "", "", "", "", "Babel: Mummy Queen defeated         "],
            523: [523, 4, True, 523, [], "", "", "", "", "Mansion: Solid Arm defeated         "],

            # Misc
            600: [600, 4, True, 600, [], "", "", "", "", "Freedan Access                          "],
            601: [601, 4, True, 601, [], "", "", "", "", "Glitches                                "],
            602: [602, 4, True, 602, [], "", "", "", "", "Early Firebird                          "]
        }

        # World graph
        # Format: { Region ID: Traversed_flag, [AccessibleRegions], type(0=other/misc,1=exterior,2=interior), [continentID,areaID,MapID],
        #                 Layer, RegionName, [ItemsToRemove] }
        self.graph = {
            # Game Start
            0: [False, [22,600], 0, [0,0,b"\x00"], 0, "Game Start", []],  # 600 shoudln't be here, fix later

            # Jeweler
            1: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Access", []],
            2: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 1", []],
            3: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 2", []],
            4: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 3", []],
            5: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 4", []],
            6: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 5", []],
            7: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 6", []],
            8: [False, [], 0, [0,0,b"\x00"], 0, "Jeweler Reward 7", []],

            # Overworld Menus
            10: [False, [20,30,50,60,63],      0, [1,0,b"\x00"], 0, "Overworld: SW Continent", []],
            11: [False, [102,110,133,160,162], 0, [2,0,b"\x00"], 0, "Overworld: SE Continent", []],
            12: [False, [250,280,290],         0, [3,0,b"\x00"], 0, "Overworld: NE Continent", []],
            13: [False, [310,330,350,360],     0, [4,0,b"\x00"], 0, "Overworld: N Continent", []],
            14: [False, [400,410],             0, [5,0,b"\x00"], 0, "Overworld: NW Continent", []],

            # Passage Menus
            15: [False, [], 0, [0,0,b"\x00"], 0, "Passage: Seth", []],
            16: [False, [], 0, [0,0,b"\x00"], 0, "Passage: Moon Tribe", []],
            17: [False, [], 0, [0,0,b"\x00"], 0, "Passage: Neil", []],

            # South Cape
            20: [False, [1,10],  1, [1,1,b"\x00"], 0, "South Cape: Main Area", []],
            21: [False, [20],    1, [1,1,b"\x00"], 0, "South Cape: School Roof", []],
            22: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: School", []],
            23: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: Will's House", []],
            24: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: East House", []],
            25: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: Seth's House", []],
            26: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: Lance's House", []],
            27: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: Erik's House", []],
            28: [False, [],      2, [1,1,b"\x00"], 0, "South Cape: Seaside Cave", []],

            # Edward's / Prison
            30: [False, [10], 2, [1,2,b"\x00"], 0, "Edward's Castle: Main Area", []],
            31: [False, [30], 2, [1,2,b"\x00"], 0, "Edward's Castle: Behind Guard", []],
            32: [False, [],   2, [1,2,b"\x00"], 0, "Edward's Prison: Will's Cell", [2]],
            33: [False, [],   2, [1,2,b"\x00"], 0, "Edward's Prison: Prison Main", [2]],

            # Underground Tunnel
            40: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 12", []],
            41: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 13", []],
            42: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 14", []],
            43: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 15", []],
            44: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 16", []],
            45: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 17 (entrance)", []],
            46: [False, [45], 2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 17 (exit open)", []],
            47: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 18 (before bridge)", []],
            48: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Map 18 (after bridge)", []],
            49: [False, [],   2, [1,2,b"\x00"], 0, "Underground Tunnel: Exit", []],

            # Itory
            50: [False, [10],  1, [1,3,b"\x00"], 0, "Itory: Entrance", [9]],
            51: [False, [50],  1, [1,3,b"\x00"], 0, "Itory: Main Area", []],
            52: [False, [],    1, [1,3,b"\x00"], 0, "Itory: Lilly's Back Porch", []],
            53: [False, [],    2, [1,3,b"\x00"], 0, "Itory: West House", []],
            54: [False, [],    2, [1,3,b"\x00"], 0, "Itory: North House", []],
            55: [False, [],    2, [1,3,b"\x00"], 0, "Itory: Lilly's House", [23]],
            56: [False, [],    2, [1,3,b"\x00"], 0, "Itory: Cave", []],
            57: [False, [],    2, [1,3,b"\x00"], 0, "Itory: Cave (behind false wall)", []],
            58: [False, [],    2, [1,3,b"\x00"], 0, "Itory: Cave (secret room)", []],
            59: [False, [501], 0, [1,3,b"\x00"], 0, "Itory: Got Lilly", []],

            # Moon Tribe / Inca Entrance
            60: [False, [10],     1, [1,4,b"\x00"], 0, "Moon Tribe: Main Area", [25]],
            61: [False, [],       2, [1,4,b"\x00"], 0, "Moon Tribe: Cave", []],
            62: [False, [],       2, [1,4,b"\x00"], 0, "Moon Tribe: Cave (Pedestal)", []],
            63: [False, [10],     1, [1,5,b"\x00"], 0, "Inca: Entrance", []],
            64: [False, [60,502], 0, [1,4,b"\x00"], 0, "Moon Tribe: Spirits Awake", []],

            # Inca Ruins
            70: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 29 (NE)", []],
            71: [False, [],   1, [1,5,b"\x00"], 0, "Inca: Map 29 (NW)", []],
            72: [False, [73], 1, [1,5,b"\x00"], 0, "Inca: Map 29 (N)", []],
            73: [False, [],   1, [1,5,b"\x00"], 0, "Inca: Map 29 (center)", []],
            74: [False, [72], 1, [1,5,b"\x00"], 0, "Inca: Map 29 (SW)", []],
            75: [False, [72], 1, [1,5,b"\x00"], 0, "Inca: Map 29 (SE)", []],
            76: [False, [],   1, [1,5,b"\x00"], 0, "Inca: Map 29 (statue head)", []],
            77: [False, [],   1, [1,5,b"\x00"], 0, "Inca: Map 30 (first area)", [3, 4]],
            78: [False, [77], 1, [1,5,b"\x00"], 0, "Inca: Map 30 (second area)", []],
            79: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 31", []],
            80: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 32 (entrance)", []],
            81: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 32 (behind statue)", []],
            82: [False, [83], 2, [1,5,b"\x00"], 0, "Inca: Map 33 (entrance)", []],
            83: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 33 (over ramp)", []],      # Need to prevent softlocks here
            84: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 34", []],
            85: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 35 (entrance)", []],
            86: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 35 (over ramp)", []],      # Check for potential softlock?
            87: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 36 (main)", [8]],
            88: [False, [87], 2, [1,5,b"\x00"], 0, "Inca: Map 36 (exit opened)", []],
            89: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 37 (main area)", [7]],
            90: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 37 (tile bridge)", []],     # Check for potential softlock?
            91: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 38 (south section)", []],
            92: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 38 (behind statues)", []],
            93: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 38 (north section)", []],
            94: [False, [],   2, [1,5,b"\x00"], 0, "Inca: Map 39", []],
            95: [False, [96], 2, [1,5,b"\x00"], 0, "Inca: Map 40 (entrance)", []],
            96: [False, [95], 2, [1,5,b"\x00"], 0, "Inca: Map 40 (past tiles)", []],
            97: [False, [98,503], 2, [1,5,b"\x00"], 0, "Inca: Boss Room", []],       # might need to add an exit for this
            98: [False, [97],     2, [1,5,b"\x00"], 0, "Inca: Behind Boss Room", []],

            # Gold Ship / Diamond Coast
            100: [False, [],   1, [1,5,b"\x00"], 0, "Gold Ship: Deck", []],
            101: [False, [],   2, [1,5,b"\x00"], 0, "Gold Ship: Interior", []],
            102: [False, [11], 1, [2,6,b"\x00"], 0, "Diamond Coast: Main Area", []],
            103: [False, [],   2, [2,6,b"\x00"], 0, "Diamond Coast: House", []],
            104: [False, [],   0, [1,5,b"\x00"], 0, "Gold Ship: Crow's Nest Passage", []],

            # Freejia
            110: [False, [11],       1, [2,7,b"\x00"], 0, "Freejia: Main Area", []],
            111: [False, [1, 110],   1, [2,7,b"\x00"], 0, "Freejia: 2-story House Roof", []],
            112: [False, [],         1, [2,7,b"\x00"], 0, "Freejia: Laborer House Roof", []],
            113: [False, [110, 114], 1, [2,7,b"\x00"], 0, "Freejia: Labor Trade Roof", []],
            114: [False, [110, 112], 1, [2,7,b"\x00"], 0, "Freejia: Back Alley", []],
            115: [False, [],         0, [2,7,b"\x00"], 0, "Freejia: Slaver", []],
            116: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: West House", []],
            117: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: 2-story House", []],
            118: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Lovers' House", []],
            119: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Hotel (common area)", []],
            120: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Hotel (west room)", []],
            121: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Hotel (east room)", []],
            122: [False, [504],      2, [2,7,b"\x00"], 0, "Freejia: Laborer House", []],
            123: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Messy House", []],
            124: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Erik House", []],
            125: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Dark Space House", []],
            126: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Labor Trade House", []],
            127: [False, [],         2, [2,7,b"\x00"], 0, "Freejia: Labor Market", []],

            # Diamond Mine
            130: [False, [131], 2, [2,8,b"\x00"], 0, "Diamond Mine: Map 61 (entrance)", []],
            131: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 61 (behind barriers)", []],
            132: [False, [131], 2, [2,8,b"\x00"], 0, "Diamond Mine: Map 61 (false wall)", []],
            133: [False, [11],  2, [2,8,b"\x00"], 0, "Diamond Mine: Map 62", []],
            134: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 63 (main)", []],
            135: [False, [134], 2, [2,8,b"\x00"], 0, "Diamond Mine: Map 63 (elevator)", []],
            136: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 64 (main)", []],
            137: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 64 (trapped laborer)", []],
            138: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 65 (main)", []],
            139: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 65 (behind ramp)", []],
            140: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 66 (elevator 1)", []],
            141: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 66 (elevator 2)", []],
            142: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 66 (Dark Space)", []],
            143: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 66 (laborer)", []],
            144: [False, [145], 2, [2,8,b"\x00"], 0, "Diamond Mine: Map 67 (entrance)", []],
            145: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 67 (exit)", []],         # potential softlock?
            146: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 68 (main)", []],
            147: [False, [146], 2, [2,8,b"\x00"], 0, "Diamond Mine: Map 68 (door open)", []],
            148: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 69", []],
            149: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 70", []],
            150: [False, [],    2, [2,8,b"\x00"], 0, "Diamond Mine: Map 71", []],

            # Neil's Cottage / Nazca
            160: [False, [11],         2, [2,9,b"\x00"],  0, "Neil's Cottage", [13]],
            161: [False, [17,160,505], 2, [2,9,b"\x00"],  0, "Neil's Cottage: Neil", []],
            162: [False, [11],         1, [2,10,b"\x00"], 0, "Nazca Plain", []],

            # Sky Garden
            168: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (north)", []],
            169: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 86 (DS Room)", []],
            170: [False, [],         1, [2,10,b"\x00"], 0, "Sky Garden: Foyer", [14, 14, 14, 14]],
            171: [False, [],         1, [2,10,b"\x00"], 0, "Sky Garden: Boss Entrance", []],
            172: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 77 (main)", []],
            173: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 77 (SW)", []],
            174: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 77 (SE)", []],
            175: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 78", []],
            176: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 79 (main)", []],
            177: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 79 (center)", []],
            178: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 79 (behind barrier)", []],
            179: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 80 (north)", []],
            180: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 80 (south)", []],
            181: [False, [168],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (main)", []],
            182: [False, [181],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (west)", []],
            183: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (Dark Space cage)", []],
            184: [False, [183],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (SE platform)", []],
            185: [False, [183],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 81 (SW platform)", []],
            186: [False, [506],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 82 (north)", []],        # deal with switches
            187: [False, [508],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 82 (south)", []],
            188: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 82 (NE)", []],
            189: [False, [507],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 82 (switch cage)", []],
            190: [False, [191],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 83 (NE)", []],
            191: [False, [190, 192], 2, [2,10,b"\x00"], 0, "Sky Garden: Map 83 (NW)", []],
            192: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 83 (center)", []],
            193: [False, [194],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 83 (south)", []],
            194: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 83 (SE)", []],
            195: [False, [196],      2, [2,10,b"\x00"], 0, "Sky Garden: Map 84 (main)", []],
            196: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 84 (NE)", []],
            197: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Map 84 (behind statue)", []],
            198: [False, [],         2, [2,10,b"\x00"], 0, "Sky Garden: Boss Room", []],
            199: [False, [197,509],  2, [2,10,b"\x00"], 0, "Sky Garden: Map 84 (statue)", []],

            # Seaside Palace
            200: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 1", [16]],
            201: [False, [200], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 1 (door unlocked)", []],
            202: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 1 NE Room", []],
            203: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 1 NW Room", []],
            204: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 1 SE Room", []],
            205: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 2", []],
            206: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Buffy", []],
            207: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Area 2 SW Room", []],
            208: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Coffin", []],
            209: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Fountain", [17]],
            210: [False,    [], 2, [3,11,b"\x00"], 0, "Seaside Palace: Mu Passage", [16]],
            211: [False, [210], 2, [3,11,b"\x00"], 0, "Seaside Palace: Mu Passage (door unlocked)", []],

            # Mu
            212: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 95 (top)", []],
            213: [False, [212],      2, [3,12,b"\x00"], 1, "Mu: Map 95 (middle E)", []],
            214: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 95 (middle W)", []],
            215: [False, [213],      2, [3,12,b"\x00"], 2, "Mu: Map 95 (bottom E)", []],
            216: [False, [214],      2, [3,12,b"\x00"], 2, "Mu: Map 95 (bottom W)", []],
            217: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 96 (top)", []],
            218: [False, [217],      2, [3,12,b"\x00"], 1, "Mu: Map 96 (middle)", []],
            219: [False, [],         2, [3,12,b"\x00"], 2, "Mu: Map 96 (bottom)", []],
            220: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 97 (top main)", []],
            221: [False, [222, 223], 2, [3,12,b"\x00"], 0, "Mu: Map 97 (top island)", []],
            222: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 97 (middle NE)", []],
            223: [False, [221],      2, [3,12,b"\x00"], 1, "Mu: Map 97 (middle SW)", []],
            224: [False, [],         2, [3,12,b"\x00"], 2, "Mu: Map 97 (bottom)", []],
            225: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 98 (top S)", []],
            226: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 98 (top N)", []],
            227: [False, [226],      2, [3,12,b"\x00"], 1, "Mu: Map 98 (middle E)", []],
            228: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 98 (middle W)", []],
            229: [False, [227],      2, [3,12,b"\x00"], 2, "Mu: Map 98 (bottom E)", []],
            230: [False, [228],      2, [3,12,b"\x00"], 2, "Mu: Map 98 (bottom W)", []],
            231: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 99 (Room of Hope 1)", [18]],
            232: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 99 (Room of Hope 2)", [18]],
            233: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 100 (middle E)", []],
            234: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 100 (middle W)", []],
            235: [False, [],         2, [3,12,b"\x00"], 2, "Mu: Map 100 (bottom)", []],
            236: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 101 (top)", []],
            237: [False, [],         2, [3,12,b"\x00"], 1, "Mu: Map 101 (middle W)", []],
            238: [False, [236],      2, [3,12,b"\x00"], 1, "Mu: Map 101 (middle E)", []],
            239: [False, [],         2, [3,12,b"\x00"], 2, "Mu: Map 101 (bottom)", []],
            240: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 102 (pedestals)", [19, 19]],
            241: [False, [240,243],  2, [3,12,b"\x00"], 0, "Mu: Map 102 (statues placed)", []],  # might need an exit for this
            242: [False, [],         2, [3,12,b"\x00"], 0, "Mu: Map 102 (statue get)", []],
            243: [False, [244,249],  2, [3,12,b"\x00"], 0, "Mu: Boss Room (entryway)", []],    # Might need to add an exit for this?
            244: [False, [242,243],  2, [3,12,b"\x00"], 0, "Mu: Boss Room (main)", []],
            245: [False, [212],      2, [3,12,b"\x00"], 0, "Mu: Map 95 (top, Slider exit)", []],
            246: [False, [226],      2, [3,12,b"\x00"], 0, "Mu: Map 98 (top, Slider exit)", []],
            247: [False, [511],      2, [3,12,b"\x00"], 0, "Mu: Water lowered 1", []],
            248: [False, [512],      2, [3,12,b"\x00"], 0, "Mu: Water lowered 2", []],
            249: [False, [240],      2, [3,12,b"\x00"], 0, "Mu: Map 102 (statues placed)", []],

            # Angel Village
            250: [False, [12], 1, [3,13,b"\x00"], 0, "Angel Village: Outside", []],
            251: [False, [1],  2, [3,13,b"\x00"], 0, "Angel Village: Underground", []],
            252: [False, [],   2, [3,13,b"\x00"], 0, "Angel Village: Room 1", []],
            253: [False, [],   2, [3,13,b"\x00"], 0, "Angel Village: Room 2", []],
            254: [False, [],   2, [3,13,b"\x00"], 0, "Angel Village: Dance Hall", []],
            255: [False, [],   2, [3,13,b"\x00"], 0, "Angel Village: DS Room", []],
            #256: [False, [],   2, [3,13,b"\x00"], 0, "Angel Village: Room 3", []],

            # Angel Dungeon
            260: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 109", []],
            261: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 110", []],
            262: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 111", []],
            263: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 112 (main)", []],
            264: [False, [263], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 112 (slider)", []],
            265: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 112 (alcove)", []],
            266: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 113", []],
            267: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 114 (main)", []],
            268: [False, [267], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 114 (slider exit)", []],
            269: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 115 (main)", []],
            270: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 116 (portrait room)", []],
            271: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 116 (side room)", []],
            272: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 116 (Ishtar's room)", []],
            273: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 116 (Ishtar's chest)", []],
            274: [False, [513], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Puzzle Room", []],
            275: [False, [265], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 112 (alcove slider)", []],
            276: [False, [277], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 115 (slider exit)", []],
            277: [False,    [], 2, [3,13,b"\x00"], 0, "Angel Dungeon: Map 115 (foyer)", []],

            # Watermia
            280: [False,     [12], 1, [3,14,b"\x00"], 0, "Watermia: Main Area", [24]],
            #281: [False, [15,280], 0, [3,14,b"\x00"], 0, "Watermia: Bridge Man", []],
            282: [False,       [], 2, [3,14,b"\x00"], 0, "Watermia: DS House", []],
            283: [False,      [1], 2, [3,14,b"\x00"], 0, "Watermia: Gambling House", []],
            284: [False,       [], 2, [3,14,b"\x00"], 0, "Watermia: West House", []],
            285: [False,       [], 2, [3,14,b"\x00"], 0, "Watermia: East House", []],
            286: [False,       [], 2, [3,14,b"\x00"], 0, "Watermia: Lance's House", []],
            287: [False,       [], 2, [3,14,b"\x00"], 0, "Watermia: NW House", []],
            288: [False,    [280], 0, [3,14,b"\x00"], 0, "Watermia: Stablemaster", []],

            # Great Wall
            290: [False, [12],  2, [3,15,b"\x00"], 0, "Great Wall: Map 130", []],
            291: [False, [292], 2, [3,15,b"\x00"], 0, "Great Wall: Map 131 (NW)", []],
            292: [False, [293], 2, [3,15,b"\x00"], 0, "Great Wall: Map 131 (S)", []],
            293: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 131 (NE)", []],
            294: [False, [296], 2, [3,15,b"\x00"], 0, "Great Wall: Map 133 (W)", []],
            295: [False, [296], 2, [3,15,b"\x00"], 0, "Great Wall: Map 133 (center)", []],
            296: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 133 (E)", []],
            297: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 134", []],
            298: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 135 (W)", []],
            299: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 135 (E)", []],
            300: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 136 (W)", []],
            301: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Map 136 (E)", []],
            302: [False, [303], 2, [3,15,b"\x00"], 0, "Great Wall: Boss Room (entrance)", []],
            303: [False, [],    2, [3,15,b"\x00"], 0, "Great Wall: Boss Room (exit)", []],

            # Euro
            310: [False, [13],  1, [4,16,b"\x00"], 0, "Euro: Main Area", [24]],
            311: [False, [310], 0, [4,16,b"\x00"], 0, "Euro: Stablemaster", []],
            312: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Rolek Company", []],
            313: [False, [],    2, [4,16,b"\x00"], 0, "Euro: West House", []],
            314: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Rolek Mansion", [40]],
            315: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Ann", []],
            316: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Guest Room", []],
            317: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Central House", []],
            318: [False, [1],   2, [4,16,b"\x00"], 0, "Euro: Jeweler House", []],
            319: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Twins House", []],
            320: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Hidden House", []],
            321: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Shrine", []],
            322: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Explorer's House", []],
            323: [False, [324], 2, [4,16,b"\x00"], 0, "Euro: Store Entrance", []],
            324: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Store Exit", []],
            325: [False, [],    2, [4,16,b"\x00"], 0, "Euro: Dark Space House", []],

            # Mt. Kress
            330: [False, [13],        2, [4,17,b"\x00"], 0, "Mt. Kress: Map 160", []],
            331: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 161 (E)", []],
            332: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 161 (W)", []],
            333: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 162 (main)", [26]],
            334: [False, [333],       2, [4,17,b"\x00"], 0, "Mt. Kress: Map 162 (S)", []],
            335: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 162 (NW)", []],
            336: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 162 (SE)", []],
            337: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 163", []],
            338: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 164", []],
            339: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 165 (S)", [26]],
            340: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 165 (NE)", [26]],
            341: [False, [338],       2, [4,17,b"\x00"], 0, "Mt. Kress: Map 165 (NW)", []],
            342: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 166", []],
            343: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 167", []],
            344: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 168", []],
            345: [False, [],          2, [4,17,b"\x00"], 0, "Mt. Kress: Map 169", []],

            # Natives' Village
            350: [False, [13],  1, [4,18,b"\x00"], 0, "Natives' Village: Main Area", [10]],
            351: [False, [350], 0, [4,18,b"\x00"], 0, "Natives' Village: Child Guide", []],
            352: [False, [],    2, [4,18,b"\x00"], 0, "Natives' Village: West House", []],
            353: [False, [],    2, [4,18,b"\x00"], 0, "Natives' Village: House w/Statues", [29]],
            354: [False, [],    0, [4,18,b"\x00"], 0, "Natives' Village: Statues Awake", []],

            # Ankor Wat
            360: [False, [13],  2, [4,19,b"\x00"], 0, "Ankor Wat: Map 176", []],
            361: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 177 (E)", []],
            362: [False, [361], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 177 (W)", []],
            363: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 178 (S)", []],
            364: [False, [363], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 178 (center)", []],
            365: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 178 (N)", []],
            366: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 179 (E)", []],
            367: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 179 (W)", []],
            368: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 180", []],
            369: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 181 (N)", []],
            370: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 181 (center)", []],
            371: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 181 (S)", []],
            372: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 182", []],
            373: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 183 (S)", []],
            374: [False, [373], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 183 (NW)", []],
            375: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 183 (NE)", []],
            376: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 184 (S)", []],
            377: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 184 (N)", []],
            378: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 185", []],
            379: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 186 (main)", []],
            380: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 186 (NE)", []],
            381: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 187 (main)", []],
            382: [False, [381], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 187 (chest)", []],
            383: [False, [381], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 187 (Dark Space)", []],
            384: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 188 (N)", []],
            385: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 188 (S)", []],
            386: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 189 (floor S)", []],
            387: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 189 (floor N)", []],
            388: [False, [386], 2, [4,19,b"\x00"], 0, "Ankor Wat: Map 189 (platform)", []],
            389: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 190 (E)", []],
            390: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 190 (W)", []],
            391: [False, [],    2, [4,19,b"\x00"], 0, "Ankor Wat: Map 191", []],

            # Dao
            400: [False, [1,14], 1, [5,20,b"\x00"], 0, "Dao: Main Area", []],
            401: [False, [],     2, [5,20,b"\x00"], 0, "Dao: NW House", []],
            402: [False, [],     2, [5,20,b"\x00"], 0, "Dao: Neil's House", []],
            403: [False, [],     2, [5,20,b"\x00"], 0, "Dao: Snake Game", []],
            404: [False, [],     2, [5,20,b"\x00"], 0, "Dao: SW House", []],
            405: [False, [],     2, [5,20,b"\x00"], 0, "Dao: S House", []],
            406: [False, [],     2, [5,20,b"\x00"], 0, "Dao: SE House", []],

            # Pyramid
            410: [False, [14],  2, [5,21,b"\x00"], 0, "Pyramid: Entrance (main)", []],
            411: [False, [410], 2, [5,21,b"\x00"], 0, "Pyramid: Entrance (behind orbs)", []],
            412: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Entrance (hidden platform)", []],
            413: [False, [411], 2, [5,21,b"\x00"], 0, "Pyramid: Entrance (bottom)", []],
            414: [False, [411], 2, [5,21,b"\x00"], 0, "Pyramid: Entrance (boss entrance)", []],
            415: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph room", [30, 31, 32, 33, 34, 35, 38]],
            416: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 206 (E)", []],
            417: [False, [416], 2, [5,21,b"\x00"], 0, "Pyramid: Map 206 (W)", []],
            418: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 207 (NE)", []],
            419: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 207 (SW)", []],
            420: [False, [421], 2, [5,21,b"\x00"], 0, "Pyramid: Map 208 (N)", []],
            421: [False, [420], 2, [5,21,b"\x00"], 0, "Pyramid: Map 208 (S)", []],
            422: [False, [423], 2, [5,21,b"\x00"], 0, "Pyramid: Map 209 (W)", []],
            423: [False, [422], 2, [5,21,b"\x00"], 0, "Pyramid: Map 209 (E)", []],
            424: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 210", []],
            425: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 211", []],
            426: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 212 (N)", []],
            427: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 212 (center)", []],
            428: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 212 (SE)", []],
            429: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 212 (SW)", []],
            430: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 213", []],
            431: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 214 (NW)", []],
            432: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 214 (NE)", []],
            433: [False, [434], 2, [5,21,b"\x00"], 0, "Pyramid: Map 214 (SE)", []],
            434: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 214 (SW)", []],
            435: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 215 (main)", []],
            436: [False, [437], 2, [5,21,b"\x00"], 0, "Pyramid: Map 216 (N)", []],
            437: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 216 (S)", []],
            438: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 217 (W)", []],
            439: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 217 (E)", []],
            440: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 219 (W)", []],
            441: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 219 (E)", []],
            442: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 1", []],
            443: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 2", []],
            444: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 3", []],
            445: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 4", []],
            446: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 5", []],
            447: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Hieroglyph 6", []],
            448: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Boss Room", []],
            449: [False, [517], 0, [5,21,b"\x00"], 0, "Pyramid: Hieroglyphs Placed", []],
            450: [False, [],    2, [5,21,b"\x00"], 0, "Pyramid: Map 215 (past Killer 6)", []],

            # Babel
            460: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Foyer", []],
            461: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Map 223 (bottom)", []],
            462: [False, [461],    2, [6,22,b"\x00"], 0, "Babel: Map 223 (top)", []],
            463: [False, [518,519],2, [6,22,b"\x00"], 0, "Babel: Map 224 (bottom)", []],
            464: [False, [520,521],2, [6,22,b"\x00"], 0, "Babel: Map 224 (top)", []],
            465: [False, [466],    2, [6,22,b"\x00"], 0, "Babel: Map 225 (SW)", []],
            466: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Map 225 (NW)", []],
            467: [False, [468],    2, [6,22,b"\x00"], 0, "Babel: Map 225 (SE)", []],
            468: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Map 225 (NE)", []],
            469: [False, [470],    2, [6,22,b"\x00"], 0, "Babel: Map 226 (bottom)", []],
            470: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Map 226 (top)", []],
            471: [False, [522],    2, [6,22,b"\x00"], 0, "Babel: Map 227 (bottom)", []],
            472: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Map 227 (top)", []],
            473: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Olman's Room", []],
            474: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Castoth", []],
            475: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Viper", []],
            476: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Vampires", []],
            477: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Sand Fanger", []],
            478: [False, [],       2, [6,22,b"\x00"], 0, "Babel: Mummy Queen", []],
            479: [False, [],       0, [6,22,b"\x00"], 0, "Babel: Statue Get", []],

            # Jeweler's Mansion
            480: [False, [],    2, [6,23,b"\x00"], 0, "Jeweler's Mansion: Main", []],
            481: [False, [],    2, [6,23,b"\x00"], 0, "Jeweler's Mansion: Behind Psycho Slider", []],
            482: [False, [523], 2, [6,23,b"\x00"], 0, "Jeweler's Mansion: Solid Arm", []],

            # Game End
            490: [False, [500], 0, [0,0,b"\x00"], 0, "Kara Released", []],
            491: [False,    [], 0, [0,0,b"\x00"], 0, "Firebird", []],
            492: [False,    [], 0, [0,0,b"\x00"], 0, "Dark Gaia/End Game", []],

            # Event Switches
            500: [False, [], 0, [0,0,b"\x00"], 0, "Kara                                ", []],
            501: [False, [], 0, [0,0,b"\x00"], 0, "Lilly                               ", []],
            502: [False, [], 0, [0,0,b"\x00"], 0, "Moon Tribe: Spirits Healed          ", []],
            503: [False, [], 0, [0,0,b"\x00"], 0, "Inca: Castoth defeated              ", []],
            504: [False, [], 0, [0,0,b"\x00"], 0, "Freejia: Found Laborer              ", []],
            505: [False, [], 0, [0,0,b"\x00"], 0, "Neil's Memory Restored              ", []],
            506: [False, [], 0, [0,0,b"\x00"], 0, "Sky Garden: Map 82 NW Switch        ", []],
            507: [False, [], 0, [0,0,b"\x00"], 0, "Sky Garden: Map 82 NE Switch        ", []],
            508: [False, [], 0, [0,0,b"\x00"], 0, "Sky Garden: Map 82 SE Switch        ", []],
            509: [False, [], 0, [0,0,b"\x00"], 0, "Sky Garden: Map 84 Switch           ", []],
            510: [False, [], 0, [0,0,b"\x00"], 0, "Seaside: Fountain Purified          ", []],
            511: [False, [], 0, [0,0,b"\x00"], 0, "Mu: Water Lowered 1                 ", []],
            512: [False, [], 0, [0,0,b"\x00"], 0, "Mu: Water Lowered 2                 ", []],
            513: [False, [], 0, [0,0,b"\x00"], 0, "Angel: Puzzle Complete              ", []],
            514: [False, [333,335], 0, [0,0,b"\x00"], 0, "Mt Kress: Drops used 1              ", []],
            515: [False, [339,340], 0, [0,0,b"\x00"], 0, "Mt Kress: Drops used 2              ", []],
            516: [False, [340,341], 0, [0,0,b"\x00"], 0, "Mt Kress: Drops used 3              ", []],
            517: [False, [], 0, [0,0,b"\x00"], 0, "Pyramid: Hieroglyphs placed         ", []],
            518: [False, [], 0, [0,0,b"\x00"], 0, "Babel: Castoth defeated             ", []],
            519: [False, [], 0, [0,0,b"\x00"], 0, "Babel: Viper defeated               ", []],
            520: [False, [], 0, [0,0,b"\x00"], 0, "Babel: Vampires defeated            ", []],
            521: [False, [], 0, [0,0,b"\x00"], 0, "Babel: Sand Fanger defeated         ", []],
            522: [False, [], 0, [0,0,b"\x00"], 0, "Babel: Mummy Queen defeated         ", []],
            523: [False, [], 0, [0,0,b"\x00"], 0, "Mansion: Solid Arm defeated         ", []],

            # Misc
            600: [False, [], 0, [0,0,b"\x00"], 0, "Freedan Access                      ", []],
            601: [False, [], 0, [0,0,b"\x00"], 0, "Glitches                            ", []],
            602: [False, [], 0, [0,0,b"\x00"], 0, "Early Firebird                      ", []]

        }

        # Define logical paths in dynamic graph
        # Format: { ID: [StartRegion, DestRegion, [[item1, qty1],[item2,qty2]...]]}
        self.logic = {
            # Jeweler Rewards
            0: [1, 2, [[1, gem[0]]]],  # Jeweler Reward 1
            1: [1, 2, [[1, gem[0] - 2], [41, 1]]],
            2: [1, 2, [[1, gem[0] - 3], [42, 1]]],
            3: [1, 2, [[1, gem[0] - 5], [41, 1], [42, 1]]],
            4: [2, 3, [[1, gem[1]]]],  # Jeweler Reward 2
            5: [2, 3, [[1, gem[1] - 2], [41, 1]]],
            6: [2, 3, [[1, gem[1] - 3], [42, 1]]],
            7: [2, 3, [[1, gem[1] - 5], [41, 1], [42, 1]]],
            8: [3, 4, [[1, gem[2]]]],  # Jeweler Reward 3
            9: [3, 4, [[1, gem[2] - 2], [41, 1]]],
            10: [3, 4, [[1, gem[2] - 3], [42, 1]]],
            11: [3, 4, [[1, gem[2] - 5], [41, 1], [42, 1]]],
            12: [4, 5, [[1, gem[3]]]],  # Jeweler Reward 4
            13: [4, 5, [[1, gem[3] - 2], [41, 1]]],
            14: [4, 5, [[1, gem[3] - 3], [42, 1]]],
            15: [4, 5, [[1, gem[3] - 5], [41, 1], [42, 1]]],
            16: [5, 6, [[1, gem[4]]]],  # Jeweler Reward 5
            17: [5, 6, [[1, gem[4] - 2], [41, 1]]],
            18: [5, 6, [[1, gem[4] - 3], [42, 1]]],
            19: [5, 6, [[1, gem[4] - 5], [41, 1], [42, 1]]],
            20: [6, 7, [[1, gem[5]]]],  # Jeweler Reward 6
            21: [6, 7, [[1, gem[5] - 2], [41, 1]]],
            22: [6, 7, [[1, gem[5] - 3], [42, 1]]],
            23: [6, 7, [[1, gem[5] - 5], [41, 1], [42, 1]]],
            24: [7, 8, [[1, gem[6]]]],  # Jeweler Reward 7 (Mansion)
            25: [7, 8, [[1, gem[6] - 2], [41, 1]]],
            26: [7, 8, [[1, gem[6] - 3], [42, 1]]],
            27: [7, 8, [[1, gem[6] - 5], [41, 1], [42, 1]]],

            # Inter-Continental Travel
            30: [28,   15, [[37, 1]]],   # South Cape: Erik w/ Lola's Letter
            31: [102,  15, [[37, 1]]],   # Coast: Turbo w/ Lola's Letter
            32: [280,  15, [[37, 1]]],   # Watermia: Bridgeman w/ Lola's Letter
            33: [160, 161, [[13, 1]]],   # Neil's: Neil w/ Memory Melody
            34: [314,  17, [[505, 1]]],  # Euro: Neil w/ Memory restored
            35: [402,  17, [[505, 1]]],  # Dao: Neil w/ Memory restored
            36: [ 60,  64, [[25, 1]]],   # Moon Tribe healed w/ Teapot
            37: [170,  16, [[502, 1]]],  # Sky Garden: Spirits w/ spirits healed
            38: [280, 288, [[24, 1]]],   # Watermia: Stablemaster w/ Will
            39: [310, 311, [[24, 1]]],   # Euro: Stablemaster w/ Will
            40: [350, 351, [[10, 1]]],   # Natives': Child Guide w/ Large Roast

            # Edward's / Tunnel
            60: [32, 33, [[2, 1]]],    # Escape cell w/Prison Key
            61: [33, 32, [[2, 1]]],    # Enter cell w/Prison Key
            62: [45, 46, [[501, 1]]],  # Progression w/ Lilly
            63: [47, 48, [[600, 1]]],  # Activate Bridge w/ Freedan

            # Itory
            70: [50, 51, [[9, 1]]],    # Town appears w/ Lola's Melody
            71: [55, 59, [[23, 1]]],   # Get Lilly w/ Necklace
            72: [56, 57, [[61, 1]]],   # Cave w/ Psycho Dash
            73: [56, 57, [[62, 1]]],   # Cave w/ Psycho Slide
            74: [56, 57, [[63, 1]]],   # Cave w/ Spin Dash

            # Moon Tribe
            80: [61, 62, [[61, 1]]],   # Cave challenge w/ Psycho Dash
            81: [61, 62, [[62, 1]]],   # Cave challenge w/ Psycho Slide
            82: [61, 62, [[63, 1]]],   # Cave challenge w/ Spin Dash

            # Inca / Gold Ship / Freejia
            90:  [77, 78, [[3, 1], [4, 1]]],  # Map 30 progression w/ Inca Statues
            91:  [80, 81, [[61, 1]]],         # Map 32 progression w/ Psycho Dash
            92:  [80, 81, [[62, 1]]],         # Map 32 progression w/ Psycho Slider
            93:  [80, 81, [[63, 1]]],         # Map 32 progression w/ Spin Dash
            94:  [85, 86, [[600, 1]]],        # Map 35 progression w/ Freedan
            95:  [87, 88, [[8, 1]]],          # Map 36 progression w/ Wind Melody
            96:  [89, 90, [[7, 1]]],          # Map 37 progression w/ Diamond Block
            97:  [91, 92, [[61, 1]]],         # Map 38 progression w/ Psycho Dash
            98:  [91, 92, [[62, 1]]],         # Map 38 progression w/ Psycho Slider
            99:  [91, 92, [[63, 1]]],         # Map 38 progression w/ Spin Dash
            100: [100, 104, [[100, 1]]],      # Gold Ship progression w/ Statue 1
            101: [110, 115, [[504, 1]]],      # Freejia: Slaver item w/ Laborer Found

            # Diamond Mine
            110: [131, 132, [[61, 1]]],            # Map 61 false wall w/ Psycho Dash
            111: [131, 132, [[62, 1]]],            # Map 61 false wall w/ Psycho Slider
            112: [131, 132, [[63, 1]]],            # Map 61 false wall w/ Spin Dash
            113: [134, 135, [[15, 1]]],            # Map 63 progression w/ Elevator Key
            114: [136, 137, [[61, 1]]],            # Map 64 trapped laborer w/ Psycho Dash
            115: [136, 137, [[62, 1]]],            # Map 64 trapped laborer w/ Psycho Slider
            116: [136, 137, [[63, 1]]],            # Map 64 trapped laborer w/ Spin Dash
            117: [138, 139, [[63, 1]]],            # Map 65 progression w/ Spin Dash
            118: [138, 139, [[64, 1], [600, 1]]],  # Map 65 progression w/ Dark Friar
            119: [146, 147, [[11, 1], [12, 1]]],   # Map 68 progression w/ mine keys

            # Sky Garden
            130: [170, 171, [[14, 4]]],            # Boss access w/ Crystal Balls
            131: [177, 178, [[64, 1], [600, 1]]],  # Map 79 progression w/ Dark Friar
            132: [177, 178, [[67, 1], [600, 1]]],  # Map 79 progression w/ Firebird
            133: [168, 182, [[506, 1]]],           # Map 81 progression w/ switch 1
            134: [182, 183, [[507, 1]]],           # Map 81 progression w/ switch 2
            135: [182, 184, [[61, 1]]],            # Map 81 progression w/ Psycho Dash
            136: [182, 184, [[62, 1]]],            # Map 81 progression w/ Psycho Dash
            137: [182, 184, [[63, 1]]],            # Map 81 progression w/ Psycho Dash
            138: [184, 185, [[508, 1], [61, 1]]],  # Map 81 progression w/ switch 3 & Psycho Dash
            139: [184, 185, [[508, 1], [62, 1]]],  # Map 81 progression w/ switch 3 & Psycho Slider
            140: [184, 185, [[508, 1], [63, 1]]],  # Map 81 progression w/ switch 3 & Spin Dash
            141: [181, 182, [[63, 1]]],            # Map 81 progression w/ Spin Dash
            142: [181, 184, [[63, 1]]],            # Map 81 progression w/ Spin Dash
            143: [182, 185, [[63, 1]]],            # Map 81 progression w/ Spin Dash
            144: [188, 189, [[600, 1]]],           # Map 82 progression w/ Freedan
            145: [188, 189, [[601, 1]]],           # Map 82 progression w/ Glitches
            146: [192, 190, [[63, 1]]],            # Map 83 progression w/ Spin Dash
            147: [195, 199, [[64, 1], [600, 1]]],  # Map 84 progression w/ Dark Friar
            148: [195, 199, [[67, 1], [600, 1]]],  # Map 84 progression w/ Firebird
            149: [195, 199, [[65, 1], [600, 1]]],  # Map 84 progression w/ Aura Barrier
            150: [197, 199, [[64, 1], [600, 1]]],  # Map 84 progression w/ Dark Friar
            151: [197, 199, [[67, 1], [600, 1]]],  # Map 84 progression w/ Firebird
            152: [170,  16, [[502, 1]]],           # Moon Tribe passage w/ spirits healed

            # Seaside Palace
            160: [205, 208, [[501, 1]]],   # Coffin access w/ Lilly
            161: [209, 510, [[17, 1]]],    # Purify fountain w/stone
            162: [205, 206, [[510, 1]]],   # Buffy access w/ purified fountain
            163: [200, 201, [[16, 1]]],    # Seaside to Mu w/ Mu key
            164: [210, 211, [[16, 1]]],    # Mu to Seaside w/ Mu key

            # Mu
            170: [212, 245, [[62, 1]]],                       # Map 95 progression w/ Psycho Slider
            171: [212, 213, [[511, 1]]],                      # Map 95 progression w/ water lowered 1
            172: [213, 215, [[512, 1]]],                      # Map 95 progression w/ water lowered 2
            173: [214, 216, [[512, 1]]],                      # Map 95 progression w/ water lowered 2
            174: [217, 218, [[511, 1]]],                      # Map 96 progression w/ water lowered 1
            175: [222, 221, [[511, 1], [64, 1], [600, 1]]],   # Map 97 progression w/ water lowered 1 & Friar
            176: [222, 221, [[511, 1], [67, 1], [600, 1]]],   # Map 97 progression w/ water lowered 1 & Firebird
            177: [222, 221, [[511, 1], [601, 1]]],            # Map 97 progression w/ water lowered 1 & glitches
            178: [226, 227, [[511, 1]]],                      # Map 98 progression w/ water lowered 1
            179: [227, 229, [[512, 1]]],                      # Map 98 progression w/ water lowered 2
            180: [228, 230, [[512, 1]]],                      # Map 98 progression w/ water lowered 2
            181: [229, 230, [[62, 1]]],                       # Map 98 progression w/ Psycho Slider
            182: [230, 229, [[62, 1]]],                       # Map 98 progression w/ Psycho Slider
            183: [226, 246, [[62, 1]]],                       # Map 98 progression w/ Psycho Slider
            184: [237, 238, [[62, 1]]],                       # Map 101 progression w/ Psycho Slider
            185: [240, 241, [[19, 2]]],                       # Map 102 progression w/ Rama Statues
            186: [231, 247, [[18, 1]]],                       # Water lowered 1 w/ Hope Statue
            187: [232, 248, [[18, 2]]],                       # Water lowered 2 w/ Hope Statues

            # Angel Dungeon
            210: [263, 264, [[62, 1]]],    # Map 112 progression w/ Psycho Slider
            211: [265, 275, [[62, 1]]],    # Map 112 backwards progression w/ Psycho Slider
            212: [267, 268, [[62, 1]]],    # Map 114 progression w/ Psycho Slider
            213: [269, 276, [[62, 1]]],    # Map 114 backwards progression w/ Psycho Slider
            214: [272, 273, [[513, 1]]],   # Ishtar's chest w/ puzzle complete

            # Great Wall
            220: [294, 295, [[601, 1]]],           # Map 133 progression w/ glitches
            221: [296, 295, [[63, 1]]],            # Map 133 progression w/ Spin Dash
            222: [296, 295, [[600, 1]]],           # Map 133 progression w/ Freedan
            223: [298, 299, [[64, 1], [600, 1]]],  # Map 135 progression w/ Friar
            224: [298, 299, [[67, 1], [600, 1]]],  # Map 135 progression w/ Firebird
            225: [299, 298, [[64, 1], [54, 2]]],   # Map 135 progression w/ Friar III
            227: [300, 301, [[63, 1]]],            # Map 136 progression w/ Spin Dash

            # Euro
            230: [314, 315, [[40, 1]]],    # Ann item w/ Apple

            # Mt. Temple
            240: [331, 332, [[63, 1]]],   # Map 161 progression w/ Spin Dash
            241: [332, 331, [[63, 1]]],   # Map 161 backwards progression w/ Spin Dash
            242: [333, 514, [[26, 1]]],   # Map 162 progression w/ Mushroom drops 1
            243: [335, 514, [[26, 1]]],   # Map 162 progression w/ Mushroom drops 1  -- IS THIS TRUE?
            244: [339, 515, [[26, 2]]],   # Map 162 progression w/ Mushroom drops 2
            245: [340, 515, [[26, 2]]],   # Map 162 progression w/ Mushroom drops 2  -- IS THIS TRUE?
            246: [340, 516, [[26, 3]]],   # Map 162 progression w/ Mushroom drops 3
            247: [341, 516, [[26, 3]]],   # Map 162 progression w/ Mushroom drops 3  -- IS THIS TRUE?

            # Natives'
            250: [353, 354, [[29, 1]]],    # Statues awake w/ Gorgon Flower

            # Ankor Wat
            260: [361, 362, [[64, 1], [600, 1]]],            # Map 177 progression w/ Friar
            261: [363, 364, [[63, 1]]],                      # Map 178 progression w/ Spin Dash
            262: [364, 365, [[62, 1]]],                      # Map 178 progression w/ Psycho Slider
            263: [365, 364, [[62, 1]]],                      # Map 178 progression w/ Psycho Slider
            264: [367, 366, [[63, 1]]],                      # Map 179 progression w/ Spin Dash
            265: [369, 370, [[62, 1]]],                      # Map 181 progression w/ Psycho Slider
            266: [370, 371, [[63, 1]]],                      # Map 181 progression w/ Spin Dash
            267: [373, 374, [[66, 1], [600, 1]]],            # Map 183 progression w/ Earthquaker
            268: [373, 374, [[64, 1], [54, 2], [600, 1]]],   # Map 183 progression w/ upgraded Friar
            269: [373, 374, [[64, 1], [601, 1], [600, 1]]],  # Map 183 progression w/ Friar and glitches
            270: [373, 374, [[67, 1], [600, 1]]],            # Map 183 progression w/ Firebird       -- IS THIS TRUE?
            271: [376, 377, [[64, 1], [600, 1]]],            # Map 184 progression w/ Friar
            272: [376, 377, [[36, 1], [600, 1]]],            # Map 184 progression w/ Shadow
            273: [384, 385, [[28, 1], [62, 1]]],             # Map 188 progression w/ Black Glasses & Slider
            274: [385, 384, [[28, 1], [62, 1]]],             # Map 188 progression w/ Black Glasses & Slider
            275: [384, 385, [[601, 1], [62, 1]]],            # Map 188 progression w/ glitches & Slider
            276: [385, 384, [[601, 1], [62, 1]]],            # Map 188 progression w/ glitches & Slider
            277: [386, 387, [[62, 1]]],                      # Map 188 progression w/ Psycho Slider
            278: [387, 386, [[62, 1]]],                      # Map 188 progression w/ Psycho Slider

            # Pyramid
            290: [410, 411, [[62, 1]]],             # Map 204 progression w/ Slider
            291: [410, 411, [[63, 1]]],             # Map 204 progression w/ Spin
            292: [410, 411, [[601, 1]]],            # Map 204 progression w/ glitches
            293: [411, 412, [[36, 1]]],             # Map 204 progression w/ Aura
            294: [411, 413, [[36, 1]]],             # Map 204 progression w/ Aura
            295: [415, 449, [[30, 1], [31, 1], [32, 1], [33, 1], [34, 1], [35, 1], [38, 1]]],
                                                    # Boss door open w/ Hieroglyphs
            296: [416, 417, [[63, 1]]],             # Map 206 progression w/ Spin Dash
            297: [417, 416, [[63, 1]]],             # Map 206 progression w/ Spin Dash
            298: [418, 419, [[63, 1]]],             # Map 206 progression w/ Spin Dash
            299: [419, 418, [[63, 1]]],             # Map 206 progression w/ Spin Dash
            300: [426, 427, [[36, 1], [600, 1]]],   # Map 212 progression w/ Aura
            301: [426, 427, [[66, 1], [600, 1]]],   # Map 212 progression w/ Earthquaker
            302: [427, 428, [[36, 1], [600, 1]]],   # Map 212 progression w/ Aura
            303: [427, 429, [[36, 1], [600, 1]]],   # Map 212 progression w/ Aura
            304: [427, 429, [[66, 1], [600, 1]]],   # Map 212 progression w/ Earthquaker
            305: [431, 432, [[63, 1]]],             # Map 214 progression w/ Spin Dash
            306: [431, 434, [[36, 1], [600, 1]]],   # Map 214 progression w/ Aura
            307: [431, 433, [[64, 1], [600, 1]]],   # Map 214 progression w/ Friar
            308: [438, 439, [[63, 1]]],             # Map 217 progression w/ Spin Dash
            309: [439, 438, [[63, 1]]],             # Map 217 progression w/ Spin Dash
            310: [440, 441, [[63, 1]]],             # Map 219 progression w/ Spin Dash
            311: [441, 440, [[63, 1]]],             # Map 219 progression w/ Spin Dash
            312: [435, 450, [[6, 6], [50, 2], [51, 1], [52, 1]]],
                                                    # Killer 6 w/ herbs and upgrades
            313: [435, 450, [[64, 1], [54, 1], [600, 1]]],
                                                    # Killer 6 w/ Friar II
            314: [411, 414, [[517, 1]]],            # Pyramid to boss w/hieroglyphs placed

            # Babel / Mansion
            320: [461, 462, [[36, 1], [39, 1]]],    # Map 219 progression w/ Aura and Ring
            321: [473, 479, [[522, 1]]],            # Olman statue w/ Mummy Queen 2
            322: [473, 479, [[523, 1]]],            # Olman statue w/ Solid Arm
            323: [480, 481, [[62, 1]]],             # Mansion progression w/ Slider

            # Endgame / Misc
            400: [49, 490, [[20, 2]]],                       # Rescue Kara from Edward's w/ Magic Dust
            401: [150, 490, [[20, 2]]],                      # Rescue Kara from Mine w/ Magic Dust
            402: [270, 490, [[20, 2]]],                      # Rescue Kara from Angel w/ Magic Dust
            403: [345, 490, [[20, 2]]],                      # Rescue Kara from Mt. Temple w/ Magic Dust
            404: [391, 490, [[20, 2]]],                      # Rescue Kara from Ankor Wat w/ Magic Dust
            405: [490, 491, [[36, 1], [39, 1]]],             # Early Firebird w/ Kara, Aura and Ring
            406: [490, 492, [[36, 1], [100, 0], [101, 0], [102, 0], [103, 0], [104, 0], [105, 0]]]
                                                             # Beat Game w/Mystic Statues and Aura
        }


        # Define addresses for in-game spoiler text
        self.spoiler_addresses = {
            0: "4caf5",  # Edward's Castle guard, top floor (4c947)
            1: "4e9ff",  # Itory elder (4e929)
            2: "58ac0",  # Gold Ship queen (589ff)
            3: "5ad6b",  # Man at Diamond Coast (5ab5c)
            # 4: "5bfde",   # Freejia laborer (5bfaa)
            5: "69167",  # Seaside Palace empty coffin (68feb)
            6: "6dc97",  # Ishtar's apprentice (6dc50)
            7: "79c81",  # Watermia, Kara's journal (79bf5)
            8: "7d892",  # Euro: Erasquez (7d79e)
            9: "89b2a",  # Ankor Wat, spirit (89abf)
            10: "8ad0c", # Dao: girl with note (8acc5)
            11: "99b8f"  # Babel: spirit (99b2e)
        }

        # Define location text for in-game format
        self.location_text = {
            0: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            1: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            2: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            3: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            4: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            5: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"

            6: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",  # "South Cape"
            7: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",  # "South Cape"
            8: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",  # "South Cape"
            9: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",  # "South Cape"
            10: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",  # "South Cape"

            11: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",  # "Edward's Castle"
            12: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",  # "Edward's Castle"

            13: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",  # "Edward's Prison"
            14: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",  # "Edward's Prison"

            15: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",  # "Edward's Tunnel"
            16: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",  # "Edward's Tunnel"
            17: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",  # "Edward's Tunnel"
            18: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",  # "Edward's Tunnel"
            19: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",  # "Edward's Tunnel"

            20: b"\x48\xa4\x8e\xa2\xa9",  # "Itory"
            21: b"\x48\xa4\x8e\xa2\xa9",  # "Itory"
            22: b"\x48\xa4\x8e\xa2\xa9",  # "Itory"

            23: b"\x4c\x8e\x8e\x8d\xac\x64\xa2\x88\x81\x84",  # "Moon Tribe"

            24: b"\x48\x8d\x82\x80",  # "Inca"
            25: b"\x48\x8d\x82\x80",  # "Inca"
            26: b"\x48\x8d\x82\x80",  # "Inca"
            27: b"\x48\x8d\x82\x80",  # "Inca"
            28: b"\x63\x88\x8d\x86\x88\x8d\x86\xac\xa3\xa4\x80\xa4\xa5\x84",  # "Singing Statue"
            29: b"\x48\x8d\x82\x80",  # "Inca"
            30: b"\x48\x8d\x82\x80",  # "Inca"
            31: b"\x48\x8d\x82\x80",  # "Inca"

            32: b"\x46\x8e\x8b\x83\xac\x63\x87\x88\xa0",  # "Gold Ship"

            33: b"\xd6\x0e\x42\x8e\x80\xa3\xa4",  # "Diamond Coast"

            34: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"
            35: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"
            36: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"
            37: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"
            38: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"
            39: b"\x45\xa2\x84\x84\x89\x88\x80",  # "Freejia"

            40: b"\xd6\x0e\x4c\x88\x8d\x84",  # "Diamond Mine"
            41: b"\x4b\x80\x81\x8e\xa2\x84\xa2",  # "Laborer"
            42: b"\x4b\x80\x81\x8e\xa2\x84\xa2",  # "Laborer"
            43: b"\xd6\x0e\x4c\x88\x8d\x84",  # "Diamond Mine"
            44: b"\x4b\x80\x81\x8e\xa2\x84\xa2",  # "Laborer"
            45: b"\x63\x80\x8c",  # "Sam"
            46: b"\xd6\x0e\x4c\x88\x8d\x84",  # "Diamond Mine"
            47: b"\xd6\x0e\x4c\x88\x8d\x84",  # "Diamond Mine"
            48: b"\xd6\x0e\x4c\x88\x8d\x84",  # "Diamond Mine"

            49: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            50: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            51: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            52: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            53: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            54: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            55: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            56: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            57: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            58: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            59: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"
            60: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",  # "Sky Garden"

            61: b"\xd7\x32\xd7\x93",  # "Seaside Palace"
            62: b"\xd7\x32\xd7\x93",  # "Seaside Palace"
            63: b"\xd7\x32\xd7\x93",  # "Seaside Palace"
            64: b"\x41\xa5\x85\x85\xa9",  # "Buffy"
            65: b"\x42\x8e\x85\x85\x88\x8d",  # "Coffin"
            66: b"\xd7\x32\xd7\x93",  # "Seaside Palace"

            67: b"\x4c\xa5",  # "Mu"
            68: b"\x4c\xa5",  # "Mu"
            69: b"\x4c\xa5",  # "Mu"
            70: b"\x4c\xa5",  # "Mu"
            71: b"\x4c\xa5",  # "Mu"
            72: b"\x4c\xa5",  # "Mu"
            73: b"\x4c\xa5",  # "Mu"
            74: b"\x4c\xa5",  # "Mu"
            75: b"\x4c\xa5",  # "Mu"

            76: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            77: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            78: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            79: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            80: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            81: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"
            82: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",  # "Angel Village"

            83: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",  # "Watermia"
            84: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",  # "Watermia"
            85: b"\x4b\x80\x8d\x82\x84",  # "Lance"
            86: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",  # "Watermia"
            87: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",  # "Watermia"
            88: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",  # "Watermia"

            89: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            90: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            91: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            92: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            93: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            94: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"
            95: b"\xd6\x16\x67\x80\x8b\x8b",  # "Great Wall"

            96: b"\x44\xa5\xa2\x8e",  # "Euro"
            97: b"\x44\xa5\xa2\x8e",  # "Euro"
            98: b"\x44\xa5\xa2\x8e",  # "Euro"
            99: b"\x44\xa5\xa2\x8e",  # "Euro"
            100: b"\x44\xa5\xa2\x8e",  # "Euro"
            101: b"\x44\xa5\xa2\x8e",  # "Euro"
            102: b"\x40\x8d\x8d",  # "Ann"
            103: b"\x44\xa5\xa2\x8e",  # "Euro"

            104: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            105: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            106: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            107: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            108: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3\xac\x6e\x84\x8d\x83\x6f",  # "Mt. Kress (end)"
            109: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            110: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"
            111: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",  # "Mt. Kress"

            112: b"\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",  # "Native Village"
            113: b"\x63\xa4\x80\xa4\xa5\x84",  # "Statue"
            114: b"\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",  # "Native Village"

            115: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            116: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            117: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            118: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            119: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            120: b"\x63\x87\xa2\xa5\x81\x81\x84\xa2",  # "Shrubber"
            121: b"\x63\xa0\x88\xa2\x88\xa4",  # "Spirit"
            122: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            123: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"
            124: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",  # "Ankor Wat"

            125: b"\x43\x80\x8e",  # "Dao"
            126: b"\x43\x80\x8e",  # "Dao"
            127: b"\x43\x80\x8e",  # "Dao"
            128: b"\x63\x8d\x80\x8a\x84\xac\x86\x80\x8c\x84",  # "Snake Game"
            129: b"\x43\x80\x8e",  # "Dao"

            130: b"\x46\x80\x88\x80",  # "Gaia"
            131: b"\xd6\x3f",  # "Pyramid"
            132: b"\xd6\x3f",  # "Pyramid"
            133: b"\xd6\x3f",  # "Pyramid"
            134: b"\xd6\x3f",  # "Pyramid"
            135: b"\xd6\x3f",  # "Pyramid"
            136: b"\x4a\x88\x8b\x8b\x84\xa2\xac\x26",  # "Killer 6"
            137: b"\xd6\x3f",  # "Pyramid"
            138: b"\xd6\x3f",  # "Pyramid"
            139: b"\xd6\x3f",  # "Pyramid"
            140: b"\xd6\x3f",  # "Pyramid"
            141: b"\xd6\x3f",  # "Pyramid"
            142: b"\xd6\x3f",  # "Pyramid"

            143: b"\x41\x80\x81\x84\x8b",  # "Babel"
            144: b"\x41\x80\x81\x84\x8b",  # "Babel"
            145: b"\x41\x80\x81\x84\x8b",  # "Babel"
            146: b"\x41\x80\x81\x84\x8b",  # "Babel"

            147: b"\x49\x84\xa7\x84\x8b\x84\xa2\x0e\xa3\xac\x4c\x80\x8d\xa3\x88\x8e\x8d",  # "Jeweler's Mansion"

            148: "",  # "Castoth"
            149: "",  # "Viper"
            150: "",  # "Vampires"
            151: "",  # "Sand Fanger"
            152: "",  # "Mummy Queen"
            153: ""  # "Olman"

        }

        # Define long item text for in-game format
        self.item_text_long = {
            0: b"\xd3\xd6\x1d\x8d\x8e\xa4\x87\x88\x8d\x86\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            1: b"\xd3\xd6\x1d\x80\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
            2: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\x4f\xac\xac\xac",
            3: b"\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40\x4f\xac\xac\xac\xac",
            4: b"\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41\x4f\xac\xac\xac\xac",
            5: "",
            6: b"\xd3\xd6\x1d\x80\x8d\xac\x87\x84\xa2\x81\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            7: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a\x4f",
            8: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac",
            9: b"\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac\xac\xac",
            10: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\x4f\xac\xac",
            11: b"\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\x4f\xac\xac\xac\xac\xac\xac\xac",
            12: b"\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\x4f\xac\xac\xac\xac\xac\xac\xac",
            13: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9\x4f",
            14: b"\xd3\xd6\x1d\x80\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\x4f\xac\xac\xac",
            15: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\x4f\xac",
            16: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9\x4f",
            17: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\x4f\xac",
            18: b"\xd3\xd6\x1d\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x8e\x85\xac\x47\x8e\xa0\x84\x4f\xac",
            19: b"\xd3\xd6\x1d\x80\xac\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\x4f\xac\xac\xac\xac",
            20: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\x4f\xac\xac\xac",
            21: "",
            22: b"\xd3\xd6\x1d\x4b\x80\x8d\x82\x84\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac",
            23: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4d\x84\x82\x8a\x8b\x80\x82\x84\x4f\xac\xac\xac\xac\xac",
            24: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8b\x8b\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            25: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x64\x84\x80\xa0\x8e\xa4\x4f\xac\xac\xac\xac\xac\xac\xac",
            26: b"\xd3\xd6\x1d\x4c\xa5\xa3\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\x4f\xac\xac\xac",
            27: "",
            28: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3\x4f",
            29: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2\x4f",
            30: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            31: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            32: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            33: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            34: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            35: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            36: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x40\xa5\xa2\x80\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            37: b"\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac\xac",
            38: b"\xd3\xd6\x1d\x45\x80\xa4\x87\x84\xa2\x0e\xa3\xac\x49\x8e\xa5\xa2\x8d\x80\x8b\x4f\xac",
            39: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\x4f\xac",
            40: b"\xd3\xd6\x1d\x80\x8d\xac\x40\xa0\xa0\x8b\x84\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            41: b"\xd3\xd6\x1d\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",
            42: b"\xd3\xd6\x1d\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",

            50: b"\xd3\xd6\x1d\x80\x8d\xac\x47\x60\xac\xa5\xa0\x86\xa2\x80\x83\x84\x4f\xac\xac\xac\xac",
            51: b"\xd3\xd6\x1d\x80\xac\x43\x44\x45\xac\xa5\xa0\x86\xa2\x80\x83\x84\x4f\xac\xac\xac\xac",
            52: b"\xd3\xd6\x1d\x80\xac\x63\x64\x62\xac\xa5\xa0\x86\xa2\x80\x83\x84\x4f\xac\xac\xac\xac",
            53: b"\xd3\xd6\x3c\x43\x80\xa3\x87\xac\x88\xa3\xac\x88\x8c\xa0\xa2\x8e\xa6\x84\x83\x4f\xac",
            54: b"\xd3\xd6\x0c\x45\xa2\x88\x80\xa2\xac\x88\xa3\xac\x88\x8c\xa0\xa2\x8e\xa6\x84\x83\x4f",
            55: b"\xd3\xd6\x1d\x80\xac\x47\x84\x80\xa2\xa4\xac\x60\x88\x84\x82\x84\x4f\xac\xac\xac\xac"

        }

        # Define short item text for in-game format
        # Currently only used in Jeweler's inventory
        self.item_text_short = {
            0: b"\x4d\x8e\xa4\x87\x88\x8d\x86\xac\xac\xac\xac\xac\xac",
            1: b"\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
            2: b"\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\xac\xac\xac",
            3: b"\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40",
            4: b"\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41",
            5: "",
            6: b"\x47\x84\xa2\x81\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            7: b"\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a",
            8: b"\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\xac\xac",
            9: b"\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9",
            10: b"\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\xac\xac",
            11: b"\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\xac\xac\xac",
            12: b"\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\xac\xac\xac",
            13: b"\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9",
            14: b"\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\xac",
            15: b"\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\xac",
            16: b"\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9",
            17: b"\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\xac",
            18: b"\x47\x8e\xa0\x84\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
            19: b"\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
            20: b"\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\xac\xac\xac",
            21: "",
            22: b"\x4b\x80\x8d\x82\x84\xac\x4b\x84\xa4\xa4\x84\xa2\xac",
            23: b"\x4d\x84\x82\x8a\x8b\x80\x82\x84\xac\xac\xac\xac\xac",
            24: b"\x67\x88\x8b\x8b\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            25: b"\x64\x84\x80\xa0\x8e\xa4\xac\xac\xac\xac\xac\xac\xac",
            26: b"\x63\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\xac",
            27: "",
            28: b"\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3",
            29: b"\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2",
            30: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            31: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            32: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            33: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            34: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            35: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            36: b"\x40\xa5\xa2\x80\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            37: b"\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2",
            38: b"\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac",
            39: b"\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\xac",
            40: b"\x40\xa0\xa0\x8b\x84\xac\xac\xac\xac\xac\xac\xac\xac",
            41: b"\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",
            42: b"\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",

            50: b"\x47\x60\xac\x65\xa0\x86\xa2\x80\x83\x84\xac\xac\xac",
            51: b"\x43\x44\x45\xac\x65\xa0\x86\xa2\x80\x83\x84\xac\xac",
            52: b"\x63\x64\x62\xac\x65\xa0\x86\xa2\x80\x83\x84\xac\xac",
            53: b"\x43\x80\xa3\x87\xac\x65\xa0\x86\xa2\x80\x83\x84\xac",
            54: b"\x45\xa2\x88\x80\xa2\xac\x65\xa0\x86\xa2\x80\x83\x84",
            55: b"\x47\x84\x80\xa2\xa4\xac\x60\x88\x84\x82\x84\xac\xac",

            61: b"\xd6\x3c\x43\x80\xa3\x87",
            62: b"\xd6\x3c\x63\x8b\x88\x83\x84\xa2",
            63: b"\xd7\x31\x43\x80\xa3\x87",
            64: b"\xd6\x0c\x45\xa2\x88\x80\xa2",
            65: b"\xd6\x03\x41\x80\xa2\xa2\x88\x84\xa2",
            66: b"\x44\x80\xa2\xa4\x87\xa1\xa5\x80\x8a\x84\xa2"
        }

        # Database of enemy groups and spritesets
        # FORMAT: { ID: [ROM_Loction, HeaderCode, HeaderData, Name]}
        self.enemysets = {
            0: [b"\x03\x00\x10\x10\xEC\x59\xCD\x01\x04\x00\x60\xA0\x8C\x75\xDE\x10\xD0\x21\x00\x47\xED\x9F", "Underground Tunnel"],
            1: [b"\x03\x00\x10\x10\xBC\x33\xC2\x01\x04\x00\x60\xA0\x0C\x77\xDE\x10\x2A\x0F\x00\xE6\x08\xD5", "Inca Ruins (Mud Monster and Larva)"],
            2: [b"\x03\x00\x10\x10\x23\x4D\xC2\x01\x04\x00\x60\xA0\xCC\x77\xDE\x10\x36\x23\x00\x24\x45\xCC", "Inca Ruins (Statues)"],
            3: [b"\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xCC\x7A\xDE\x10\x30\x29\x00\xBE\x2F\xCB", "Diamond Mine"],
            4: [b"\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x4C\x7C\xDE\x10\x54\x1D\x00\xEF\xEE\x9E", "Sky Garden (top)"],
            5: [b"\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x0C\x7D\xDE\x10\x54\x1D\x00\xEF\xEE\x9E", "Sky Garden (bottom)"],
            6: [b"\x03\x00\x10\x10\x2D\x2E\xCC\x01\x04\x00\x60\xA0\x00\x00\xDF\x10\x16\x1C\x00\x41\x36\xD1", "Mu"],
            7: [b"\x03\x00\x10\x10\xD1\x14\xCF\x01\x04\x00\x60\xA0\x40\x02\xDF\x10\x7F\x0F\x00\x2C\x2B\xD5", "Angel Dungeon"],
            8: [b"\x03\x00\x10\x10\x6D\x13\xD0\x01\x04\x00\x60\xA0\x40\x05\xDF\x10\xFF\x16\x00\xF7\xF3\x99", "Great Wall"],
            9: [b"\x03\x00\x10\x10\x00\x00\xD0\x01\x04\x00\x60\xA0\x40\x08\xDF\x10\x70\x0E\x00\x5C\x4D\xD8", "Mt. Kress"],
            10: [b"\x03\x00\x10\x10\xEA\x15\xCE\x01\x04\x00\x70\x90\x53\x55\xDE\x10\xD5\x14\x00\x08\x73\xCC", "Ankor Wat (outside)"],
            11: [b"\x03\x00\x10\x10\x81\x6A\xC1\x01\x04\x00\x70\x90\x13\x57\xDE\x10\x57\x10\x00\x5F\x39\xD4", "Ankor Wat (inside)"],
            12: [b"\x03\x00\x10\x10\x0d\x18\xcb\x01\x04\x00\x60\x90\x80\x0a\xdf\x10\xfb\x13\x00\x0e\x67\xd1", "Pyramid"],
            13: [b"\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xC0\x0C\xDF\x10\x30\x29\x00\xBE\x2F\xCB", "Jeweler's Mansion"]
        }

        # Enemy map database
        # FORMAT: { ID: [EnemySet, RewardBoss(0 for no reward), Reward[type, tier], SearchHeader,
        #           SpritesetOffset,EventAddrLow,EventAddrHigh,RestrictedEnemysets]}
        # ROM address for room reward table is mapID + $1aade
        self.maps = {
            # For now, no one can have enemyset 10 (Ankor Wat outside)
            # Underground Tunnel
            12: [0, 1, [0,0], b"\x0C\x00\x02\x05\x03", 4, "c867a", "c86ac", []],
            13: [0, 1, [0,0], b"\x0D\x00\x02\x03\x03", 4, "c86ac", "c875c", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
            14: [0, 1, [0,0], b"\x0E\x00\x02\x03\x03", 4, "c875c", "c8847", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],  # Weird 4way issues
            15: [0, 1, [0,0], b"\x0F\x00\x02\x03\x03", 4, "c8847", "c8935", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            18: [0, 1, [0,0], b"\x12\x00\x02\x03\x03", 4, "c8986", "c8aa9", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],  # Spike balls

            # Inca Ruins
            27: [1, 0, [0,0], b"\x1B\x00\x02\x05\x03", 4, "c8c33", "c8c87", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],  # Moon Tribe cave
            29: [1, 1, [0,0], b"\x1D\x00\x02\x0F\x03", 4, "c8cc4", "c8d85", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            32: [1, 1, [0,0], b"\x20\x00\x02\x08\x03", 4, "c8e16", "c8e75", []],  # Broken statue
            33: [2, 1, [0,0], b"\x21\x00\x02\x08\x03", 4, "c8e75", "c8f57", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],  # Floor switch
            34: [2, 1, [0,0], b"\x22\x00\x02\x08\x03", 4, "c8f57", "c9029", []],  # Floor switch
            35: [2, 1, [0,0], b"\x23\x00\x02\x0A\x03", 4, "c9029", "c90d5", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
            37: [1, 1, [0,0], b"\x25\x00\x02\x08\x03", 4, "c90f3", "c91a0", [1]],  # Diamond block
            38: [1, 1, [0,0], b"\x26\x00\x02\x08\x03", 4, "c91a0", "c9242", []],  # Broken statues
            39: [1, 1, [0,0], b"\x27\x00\x02\x0A\x03", 4, "c9242", "c92f2", []],
            40: [1, 1, [0,0], b"\x28\x00\x02\x08\x03", 4, "c92f2", "c935f", [1]],  # Falling blocks

            # Diamond Mine
            61: [3, 2, [0,0], b"\x3D\x00\x02\x08\x03", 4, "c9836", "c98b7", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            62: [3, 2, [0,0], b"\x3E\x00\x02\x08\x03", 4, "c98b7", "c991a", []],
            63: [3, 2, [0,0], b"\x3F\x00\x02\x05\x03", 4, "c991a", "c9a41", []],
            64: [3, 2, [0,0], b"\x40\x00\x02\x08\x03", 4, "c9a41", "c9a95", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],  # Trapped laborer (??)
            65: [3, 2, [0,0], b"\x41\x00\x02\x00\x03", 4, "c9a95", "c9b39", [0, 2, 3, 4, 5, 11]],  # Stationary Grundit
            69: [3, 2, [0,0], b"\x45\x00\x02\x08\x03", 4, "c9ba1", "c9bf4", []],
            70: [3, 2, [0,0], b"\x46\x00\x02\x08\x03", 4, "c9bf4", "c9c5c", [3, 13]],

            # Sky Garden
            77: [4, 2, [0,0], b"\x4D\x00\x02\x12\x03", 4, "c9db3", "c9e92", []],
            78: [5, 2, [0,0], b"\x4E\x00\x02\x10\x03", 4, "c9e92", "c9f53", []],
            79: [4, 2, [0,0], b"\x4F\x00\x02\x12\x03", 4, "c9f53", "ca01a", [4, 5]],
            80: [5, 2, [0,0], b"\x50\x00\x02\x10\x03", 4, "ca01a", "ca0cb", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            81: [4, 2, [0,0], b"\x51\x00\x02\x12\x03", 4, "ca0cb", "ca192", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            82: [5, 2, [0,0], b"\x52\x00\x02\x10\x03", 4, "ca192", "ca247", [4, 5]],
            83: [4, 2, [0,0], b"\x53\x00\x02\x12\x03", 4, "ca247", "ca335", [4, 5]],
            84: [5, 2, [0,0], b"\x54\x00\x02\x12\x03", 4, "ca335", "ca43b", [4, 5]],

            # Mu
            #            92: [6,0,0,b"\x5C\x00\x02\x15\x03",4,[]],  # Seaside Palace
            95: [6, 3, [0,0], b"\x5F\x00\x02\x14\x03", 4, "ca71b", "ca7ed", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
            96: [6, 3, [0,0], b"\x60\x00\x02\x14\x03", 4, "ca7ed", "ca934", [6]],
            97: [6, 3, [0,0], b"\x61\x00\x02\x14\x03", 4, "ca934", "caa7b", [6]],
            98: [6, 3, [0,0], b"\x62\x00\x02\x14\x03", 4, "caa7b", "cab28", []],
            100: [6, 3, [0,0], b"\x64\x00\x02\x14\x03", 4, "cab4b", "cabd4", []],
            101: [6, 3, [0,0], b"\x65\x00\x02\x14\x03", 4, "cabd4", "cacc3", [6]],

            # Angel Dungeon
            109: [7, 3, [0,0], b"\x6D\x00\x02\x16\x03", 4, "caf6e", "cb04b", [7, 8, 9, 10]],  # Add 10's back in once flies are fixed
            110: [7, 3, [0,0], b"\x6E\x00\x02\x18\x03", 4, "cb04b", "cb13e", [7, 8, 9, 10]],
            111: [7, 3, [0,0], b"\x6F\x00\x02\x1B\x03", 4, "cb13e", "cb1ae", [7, 8, 9, 10]],
            112: [7, 3, [0,0], b"\x70\x00\x02\x16\x03", 4, "cb1ae", "cb258", [7, 8, 9, 10]],
            113: [7, 3, [0,0], b"\x71\x00\x02\x18\x03", 4, "cb258", "cb29e", [7, 8, 9, 10]],
            114: [7, 3, [0,0], b"\x72\x00\x02\x18\x03", 4, "cb29e", "cb355", [7, 8, 9, 10]],

            # Great Wall
            130: [8, 4, [0,0], b"\x82\x00\x02\x1D\x03", 4, "cb6c1", "cb845", [8, 9, 10]],  # Add 10's back in once flies are fixed
            131: [8, 4, [0,0], b"\x83\x00\x02\x1D\x03", 4, "cb845", "cb966", [7, 8, 9, 10]],
            133: [8, 4, [0,0], b"\x85\x00\x02\x1D\x03", 4, "cb97d", "cbb18", [8, 9, 10]],
            134: [8, 4, [0,0], b"\x86\x00\x02\x1D\x03", 4, "cbb18", "cbb87", [7, 8, 9, 10]],
            135: [8, 4, [0,0], b"\x87\x00\x02\x1D\x03", 4, "cbb87", "cbc3b", [8]],
            136: [8, 4, [0,0], b"\x88\x00\x02\x1D\x03", 4, "cbc3b", "cbd0a", [7, 8, 9]],

            # Mt Temple
            160: [9, 4, [0,0], b"\xA0\x00\x02\x20\x03", 4, "cc18c", "cc21c", []],
            161: [9, 4, [0,0], b"\xA1\x00\x02\x20\x03", 4, "cc21c", "cc335", [7, 8, 9, 10]],
            162: [9, 4, [0,0], b"\xA2\x00\x02\x20\x03", 4, "cc335", "cc3df", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13]],  # Drops
            163: [9, 4, [0,0], b"\xA3\x00\x02\x20\x03", 4, "cc3df", "cc4f7", []],
            164: [9, 4, [0,0], b"\xA4\x00\x02\x20\x03", 4, "cc4f7", "cc5f8", [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13]],
            165: [9, 4, [0,0], b"\xA5\x00\x02\x20\x03", 4, "cc5f8", "cc703", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13]],  # Drops
            166: [9, 4, [0,0], b"\xA6\x00\x02\x20\x03", 4, "cc703", "cc7a1", []],
            167: [9, 4, [0,0], b"\xA7\x00\x02\x20\x03", 4, "cc7a1", "cc9a3", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
            168: [9, 4, [0,0], b"\xA8\x00\x02\x20\x03", 4, "cc9a3", "cca02", [7, 8, 9, 10]],

            # Ankor Wat
            176: [10, 6, [0,0], b"\xB0\x00\x02\x2C\x03", 4, "ccb1b", "ccbd8", []],
            177: [11, 6, [0,0], b"\xB1\x00\x02\x08\x03", 4, "ccbd8", "ccca5", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
            178: [11, 6, [0,0], b"\xB2\x00\x02\x08\x03", 4, "ccca5", "ccd26", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13]],
            179: [11, 6, [0,0], b"\xB3\x00\x02\x08\x03", 4, "ccd26", "ccd83", []],
            180: [11, 6, [0,0], b"\xB4\x00\x02\x08\x03", 4, "ccd83", "ccdd7", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13]],
            181: [11, 6, [0,0], b"\xB5\x00\x02\x08\x03", 4, "ccdd7", "cce7b", []],
            182: [10, 6, [0,0], b"\xB6\x00\x02\x2C\x03", 4, "cce7b", "cd005", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
            183: [11, 6, [0,0], b"\xB7\x00\x02\x08\x03", 4, "cd005", "cd092", []],  # Earthquaker Golem
            184: [11, 6, [0,0], b"\xB8\x00\x02\x08\x03", 4, "cd092", "cd0df", [0, 1, 3, 4, 5, 7, 8, 9, 11, 13]],
            185: [11, 6, [0,0], b"\xB9\x00\x02\x08\x03", 4, "cd0df", "cd137", []],
            186: [10, 6, [0,0], b"\xBA\x00\x02\x2C\x03", 4, "cd137", "cd197", []],
            187: [11, 6, [0,0], b"\xBB\x00\x02\x08\x03", 4, "cd197", "cd1f4", []],
            188: [11, 6, [0,0], b"\xBC\x00\x02\x24\x03", 4, "cd1f4", "cd29a", []],
            189: [11, 6, [0,0], b"\xBD\x00\x02\x08\x03", 4, "cd29a", "cd339", []],
            190: [11, 6, [0,0], b"\xBE\x00\x02\x08\x03", 4, "cd339", "cd392", []],

            # Pyramid
            204: [12, 5, [0,0], b"\xCC\x00\x02\x08\x03", 4, "cd539", "cd58c", []],
            206: [12, 5, [0,0], b"\xCE\x00\x02\x08\x03", 4, "cd5c6", "cd650", []],
            207: [12, 5, [0,0], b"\xCF\x00\x02\x08\x03", 4, "cd650", "cd6f3", []],
            208: [12, 5, [0,0], b"\xD0\x00\x02\x08\x03", 4, "cd6f3", "cd752", []],
            209: [12, 5, [0,0], b"\xD1\x00\x02\x08\x03", 4, "cd752", "cd81b", []],
            210: [12, 5, [0,0], b"\xD2\x00\x02\x08\x03", 4, "cd81b", "cd8f1", []],
            211: [12, 5, [0,0], b"\xD3\x00\x02\x08\x03", 4, "cd8f1", "cd9a1", []],
            212: [12, 5, [0,0], b"\xD4\x00\x02\x08\x03", 4, "cd9a1", "cda80", []],
            213: [12, 5, [0,0], b"\xD5\x00\x02\x08\x03", 4, "cda80", "cdb4b", []],
            214: [12, 5, [0,0], b"\xD6\x00\x02\x26\x03", 4, "cdb4b", "cdc1e", []],
            215: [12, 5, [0,0], b"\xD7\x00\x02\x28\x03", 4, "cdc1e", "cdcfd", [0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13]],
            216: [12, 5, [0,0], b"\xD8\x00\x02\x08\x03", 4, "cdcfd", "cde4f", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
            217: [12, 5, [0,0], b"\xD9\x00\x02\x26\x03", 4, "cde4f", "cdf3c", []],
            219: [12, 5, [0,0], b"\xDB\x00\x02\x26\x03", 4, "cdf76", "ce010", [0, 4, 5, 8, 9, 11, 12]],  #Spike elevators

            # Jeweler's Mansion
            233: [13, 0, [0,0], b"\xE9\x00\x02\x22\x03", 4, "ce224", "ce3a6", [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13]]

        }

        # Database of enemy types
        # FORMAT: { ID: [Enemyset, Event addr, VanillaTemplate,
        #           Type(1=stationary,2=walking,3=flying),OnWalkableTile,CanBeRandom,Name]}
        self.enemies = {
            # Underground Tunnel
            0: [0, b"\x55\x87\x8a", b"\x05", 2, True, True, "Bat"],  # a8755
            1: [0, b"\x6c\x82\x8a", b"\x01", 2, True, True, "Ribber"],
            2: [0, b"\x00\x80\x8a", b"\x02", 1, False, True, "Canal Worm"],
            3: [0, b"\xf7\x85\x8a", b"\x03", 2, True, False, "King Bat"],
            4: [0, b"\x76\x84\x8a", b"\x10", 2, True, True, "Skull Chaser"],
            5: [0, b"\xff\x86\x8a", b"\x04", 2, True, False, "Bat Minion 1"],
            6: [0, b"\x9a\x86\x8a", b"\x04", 2, True, False, "Bat Minion 2"],
            7: [0, b"\x69\x86\x8a", b"\x04", 2, True, False, "Bat Minion 3"],
            8: [0, b"\xcb\x86\x8a", b"\x04", 2, True, False, "Bat Minion 4"],

            # Inca Ruins
            10: [1, b"\xb7\x8d\x8a", b"\x0b", 2, True, True, "Slugger"],
            11: [1, b"\xb6\x8e\x8a", b"\x0b", 2, True, False, "Scuttlebug"],
            12: [1, b"\x1b\x8b\x8a", b"\x0a", 2, True, True, "Mudpit"],
            13: [1, b"\x70\x8c\x8a", b"\x0c", 1, True, True, "Four Way"],
            14: [2, b"\xee\x97\x8a", b"\x0f", 2, True, True, "Splop"],
            15: [2, b"\xbc\x98\x8a", b"\x0e", 3, False, True, "Whirligig"],
            16: [2, b"\xc2\x95\x8a", b"\x0d", 2, True, False, "Stone Lord R"],  # shoots fire
            17: [2, b"\xb3\x95\x8a", b"\x0d", 2, True, True, "Stone Lord D"],  # shoots fire
            18: [2, b"\xb8\x95\x8a", b"\x0d", 2, True, False, "Stone Lord U"],  # shoots fire
            19: [2, b"\xbd\x95\x8a", b"\x0d", 2, True, False, "Stone Lord L"],  # shoots fire
            20: [2, b"\x70\x90\x8a", b"\x0d", 2, True, False, "Stone Guard R"],  # throws spears
            21: [2, b"\x6b\x90\x8a", b"\x0d", 2, True, False, "Stone Guard L"],  # throws spears
            22: [2, b"\x61\x90\x8a", b"\x0d", 2, True, True, "Stone Guard D"],  # throws spears
            23: [2, b"\xc3\x99\x8a", b"\x0e", 1, False, False, "Whirligig (stationary)"],

            # Diamond Mine
            30: [3, b"\xca\xaa\x8a", b"\x18", 2, True, True, "Flayzer 1"],
            31: [3, b"\x54\xaa\x8a", b"\x18", 2, True, False, "Flayzer 2"],
            32: [3, b"\x8a\xaa\x8a", b"\x18", 2, True, False, "Flayzer 3"],
            33: [3, b"\x03\xb1\x8a", b"\x19", 2, True, True, "Eye Stalker"],
            34: [3, b"\xb3\xb0\x8a", b"\x19", 2, True, False, "Eye Stalker (stone)"],
            35: [3, b"\xf5\xaf\x8a", b"\x1a", 1, True, True, "Grundit"],
            #            36: [3,b"\xf5\xa4\x8a",b"\x1a","Grundit (stationary)"],  # Can't randomize this guy

            # Sky Garden
            40: [4, b"\xb0\xb4\x8a", b"\x1d", 2, True, True, "Blue Cyber"],
            41: [4, b"\x20\xc5\x8a", b"\x1b", 2, True, True, "Dynapede 1"],
            42: [4, b"\x33\xc5\x8a", b"\x1b", 2, True, False, "Dynapede 2"],
            43: [5, b"\xb0\xb8\x8a", b"\x1e", 2, True, True, "Red Cyber"],
            44: [5, b"\x16\xc8\x8a", b"\x1c", 2, True, True, "Nitropede"],

            # Mu
            50: [6, b"\xcc\xe6\x8a", b"\x2b", 2, True, True, "Slipper"],
            51: [6, b"\x5c\xe4\x8a", b"\x2a", 2, True, True, "Skuddle"],
            52: [6, b"\x9e\xdd\x8a", b"\x28", 2, True, True, "Cyclops"],
            53: [6, b"\x6e\xe2\x8a", b"\x29", 3, True, True, "Flasher"],
            54: [6, b"\x07\xde\x8a", b"\x28", 2, True, False, "Cyclops (asleep)"],
            55: [6, b"\xf4\xe6\x8a", b"\x2b", 2, True, True, "Slipper (falling)"],

            # Angel Dungeon
            60: [7, b"\x9f\xee\x8a", b"\x2d", 3, False, True, "Dive Bat"],
            61: [7, b"\x51\xea\x8a", b"\x2c", 2, True, True, "Steelbones"],
            62: [7, b"\x33\xef\x8a", b"\x2e", 1, True, True, "Draco"],  # False for now...
            63: [7, b"\xc7\xf0\x8a", b"\x2e", 1, True, True, "Ramskull"],

            # Great Wall
            70: [8, b"\x55\x91\x8b", b"\x33", 2, True, True, "Archer 1"],
            71: [8, b"\xfe\x8e\x8b", b"\x33", 2, True, False, "Archer Statue"],
            72: [8, b"\xbe\x8d\x8b", b"\x34", 2, True, True, "Eyesore"],
            73: [8, b"\x70\x8c\x8b", b"\x35", 3, False, True, "Fire Bug 1"],
            74: [8, b"\x70\x8c\x8b", b"\x33", 3, False, False, "Fire Bug 2"],
            75: [8, b"\x23\x94\x8b", b"\x32", 2, True, True, "Asp"],
            76: [8, b"\x65\x91\x8b", b"\x33", 2, True, False, "Archer 2"],
            77: [8, b"\x77\x91\x8b", b"\x33", 2, True, False, "Archer 3"],
            78: [8, b"\x72\x8f\x8b", b"\x46", 2, True, False, "Archer Statue (switch) 1"],
            79: [8, b"\x4f\x8f\x8b", b"\x33", 2, True, False, "Archer Statue (switch) 2"],

            # Mt. Kress
            80: [9, b"\xac\x9b\x8b", b"\x3e", 3, True, True, "Skulker (N/S)"],
            81: [9, b"\x4e\x9c\x8b", b"\x3e", 3, True, True, "Skulker (E/W)"],
            82: [9, b"\x44\x9c\x8b", b"\x3e", 3, True, False, "Skulker (E/W)"],
            83: [9, b"\xa2\x9b\x8b", b"\x3e", 3, True, False, "Skulker (E/W)"],
            84: [9, b"\x8b\x9e\x8b", b"\x3d", 3, False, True, "Yorrick (E/W)"],
            85: [9, b"\x53\x9f\x8b", b"\x3d", 3, False, False, "Yorrick (E/W)"],
            86: [9, b"\x0f\x9d\x8b", b"\x3d", 3, False, True, "Yorrick (N/S)"],
            87: [9, b"\xcd\x9d\x8b", b"\x3d", 3, False, False, "Yorrick (N/S)"],
            88: [9, b"\x3b\x98\x8b", b"\x3f", 3, False, True, "Fire Sprite"],
            89: [9, b"\xcf\xa0\x8b", b"\x3c", 2, True, True, "Acid Splasher"],
            90: [9, b"\xa1\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary E)"],
            91: [9, b"\x75\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary W)"],
            92: [9, b"\x49\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary S)"],
            93: [9, b"\x1d\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary N)"],

            # Ankor Wat
            100: [10, b"\xd7\xb1\x8b", b"\x49", 2, True, True, "Shrubber"],
            101: [10, b"\xb4\xb1\x8b", b"\x49", 2, True, False, "Shrubber 2"],
            102: [10, b"\x75\xb2\x8b", b"\x46", 2, True, True, "Zombie"],
            103: [10, b"\x4f\xaf\x8b", b"\x4a", 3, True, True, "Zip Fly"],  # False for now...
            104: [11, b"\x8d\xbd\x8b", b"\x42", 3, True, True, "Goldcap"],
            105: [11, b"\x25\xb8\x8b", b"\x45", 2, True, True, "Gorgon"],
            106: [11, b"\x17\xb8\x8b", b"\x45", 2, True, False, "Gorgon (jump down)"],
            107: [11, b"\xbb\xbf\x8b", b"\x43", 2, True, False, "Frenzie"],
            108: [11, b"\xd0\xbf\x8b", b"\x43", 2, True, True, "Frenzie 2"],
            109: [11, b"\x66\xbb\x8b", b"\x44", 1, False, True, "Wall Walker"],
            110: [11, b"\x66\xbb\x8b", b"\x3a", 1, False, False, "Wall Walker 2"],
            111: [11, b"\x5c\xbb\x8b", b"\x44", 1, False, False, "Wall Walker 3"],
            112: [11, b"\x5c\xbb\x8b", b"\x3a", 1, False, False, "Wall Walker 4"],
            113: [11, b"\xaf\x99\x88", b"\x45", 2, True, False, "Gorgon (block)"],

            # Pyramid
            120: [12, b"\x5f\xc6\x8b", b"\x4f", 1, True, True, "Mystic Ball (stationary)"],
            121: [12, b"\xfc\xc5\x8b", b"\x4f", 2, True, True, "Mystic Ball"],
            122: [12, b"\xa3\xc5\x8b", b"\x4f", 2, True, True, "Mystic Ball"],
            123: [12, b"\x9d\xc3\x8b", b"\x4e", 2, True, True, "Tuts"],
            124: [12, b"\x98\xc7\x8b", b"\x51", 1, True, True, "Blaster"],
            125: [12, b"\x84\xc1\x8b", b"\x4c", 2, True, False, "Haunt (stationary)"],
            126: [12, b"\xa7\xc1\x8b", b"\x4c", 2, True, True, "Haunt"],

            # Babel Tower
            #            130: [14,b"\xd7\x99\x8a",b"\x5a","Castoth (boss)"],
            #            131: [14,b"\xd5\xd0\x8a",b"\x5b","Viper (boss)"],
            #            132: [14,b"\x50\xf1\x8a",b"\x5c","Vampire (boss)"],
            #            133: [14,b"\x9c\xf1\x8a",b"\x5c","Vampire (boss)"],
            #            134: [14,b"\x00\x80\x8b",b"\x5d","Sand Fanger (boss)"],
            #            135: [14,b"\x1a\xa6\x8b",b"\x5e","Mummy Queen (boss)"],

            # Jeweler's Mansion
            140: [13, b"\xca\xaa\x8a", b"\x61", 2, True, True, "Flayzer"],
            141: [13, b"\xf5\xaf\x8a", b"\x63", 1, True, True, "Grundit"],
            142: [13, b"\xd8\xb0\x8a", b"\x62", 2, True, False, "Eye Stalker 1"],
            143: [13, b"\x03\xb1\x8a", b"\x62", 2, True, True, "Eye Stalker 2"]

            # Bosses
            #            24: [15,b"\x03\x9b\x8a",b"\x14","Castoth (boss)"],
            #            45: [15,b"\x6f\xd1\x8a",b"\x27","Viper (boss)"],
            #            55: [15,b"\xf7\xf1\x8a",b"\x2f","Vampire (boss)"],
            #            56: [15,b"\xc8\xf3\x8a",b"\x30","Vampire (boss)"],
            #            79: [15,b"\x5c\x81\x8b",b"\x36","Sand Fanger (boss)"],
            #            128: [15,b"\xb6\xa6\x8b",b"\x50","Mummy Queen (boss)"],
            #            143: [15,b"\x09\xf7\x88",b"\x5f","Solid Arm (boss)"],
            #            140: [15,b"\xaa\xee\x8c",b"\x54","Dark Gaia"]

        }

        # Database of non-enemy sprites to disable in enemizer
        # FORMAT: { ID: [Enemyset, Event addr, Name]}
        self.nonenemy_sprites = {
            # Underground Tunnel
            0: [0, "a8835", "Movable statue"],
            1: [0, "a87ce", "Falling spear 1"],
            2: [0, "a87c3", "Falling spear 2"],
            3: [0, "a8aae", "Spike ball 1"],
            4: [0, "a8a0f", "Spike ball 2"],
            5: [0, "a8a7d", "Spike ball 3"],
            6: [0, "a8a46", "Spike ball 4"],
            7: [0, "a89de", "Spike ball 5"],

            # Inca Ruins
            10: [1, "9c26f", "Skeleton 1"],
            11: [1, "9c798", "Skeleton 2"],
            #            12: [1,"9c89d","Skeleton 3"],   # Spriteset already restricted for this room
            13: [1, "9c8f7", "Skeleton 4"],
            14: [1, "a8896", "Broken statue (chest)"],
            15: [1, "a88de", "Broken statue (blockade)"],

            # Diamond Mine
            20: [3, "5d6a8", "Elevator sign"],
            21: [3, "aa4f5", "Elevator platform 1"],
            22: [3, "aa50c", "Elevator platform 2"],
            23: [3, "aa4e2", "Elevator platform 3"],

            # Sky Garden
            30: [4, "5f8c0", "Broken statue"],
            31: [4, "ac0fe", "Sword statue 1"],

         #            32: [4,"ac150","Sword statue 2"],
            33: [4, "ac3b3", "Sword statue 3"],
            #            34: [4,"ac409","Sword statue 4"],
            35: [4, "accd4", "Fire snake (top)"],
            36: [5, "accf1", "Fire snake (bottom)"],

            # Mu
            40: [6, "69ce9", "Floor spikes 1"],
            41: [6, "69d1f", "Floor spikes 2"],
            42: [6, "ae943", "Fire snake"],
            #            43: [6,"69d4d","Donut"],

            # Angel
            50: [7, "6d56f", "Flame 1"],
            51: [7, "6d57e", "Flame 2"],
            52: [7, "6d58f", "Flame 3"],

            # Great Wall
            60: [8, "b8c30", "Wall spike 1"],
            61: [8, "b8bf8", "Wall spike 2"],
            62: [8, "7bd17", "Wall spike 3"],
            63: [8, "7bd46", "Wall spike 4"],
            64: [8, "7bd75", "Wall spike 5"],
            65: [8, "7bce8", "Wall spike 5"],

            # Mt Kress (nothing)

            # Ankor Wat
            80: [11, "89f2c", "Floating crystal"],
            81: [11, "89ffc", "Skeleton 1"],
            82: [11, "8a25e", "Skeleton 2"]

            # Pyramid
            #            90: [12,"8b6a2","Warp point"],
            #            91: [12,"8cd6c","Warp point"],

            # Jeweler's Mansion (nothing)

        }

        # Database of overworld menus
        # FORMAT: { ID: [ShuffleID (0=no shuffle), Menu_ID, FromRegion, ToRegion, ROM_EntranceData, ROM_TextLoc, MenuText, Name]}
        self.overworld_menus = {
            # SW Continent "\x01"
            1:  [0, b"\x01", 10, 20, "3b95b", "0cafd", "3b590", "SW Destination 1 (South Cape)"],
            2:  [0, b"\x01", 10, 30, "3b96b", "0cb26", "3b5a9", "SW Destination 2 (Edward's)"],
            3:  [0, b"\x01", 10, 50, "3b97b", "0cb5b", "3b5b5", "SW Destination 3 (Itory)"],
            4:  [0, b"\x01", 10, 60, "3b98b", "4f45a", "3b5c2", "SW Destination 4 (Moon Tribe)"],
            5:  [0, b"\x01", 10, 63, "3b99b", "0cb74", "3b59c", "SW Destination 5 (Inca)"],

            # SE Continent "\x07"
            6:  [0, b"\x07", 11, 102, "3b9ab", "5aab7", "3b5ef", "SE Destination 1 (Diamond Coast)"],
            7:  [0, b"\x07", 11, 110, "3b9bb", "0cba3", "3b5e3", "SE Destination 2 (Freejia)"],
            8:  [0, b"\x07", 11, 133, "3b9cb", "0cbbc", "3b608", "SE Destination 3 (Diamond Mine)"],
            9:  [0, b"\x07", 11, 160, "3b9db", "5e31e", "3b615", "SE Destination 4 (Neil's)"],
            10: [0, b"\x07", 11, 162, "3b9eb", "5e812", "3b5fc", "SE Destination 5 (Nazca)"],

            # NE Continent "\x0a"
            11: [0, b"\x0a", 12, 250, "3ba1b", "0cbeb", "3b642", "NE Destination 1 (Angel Village)"],
            12: [0, b"\x0a", 12, 280, "3ba2b", "0cc30", "3b636", "NE Destination 2 (Watermia)"],
            13: [0, b"\x0a", 12, 290, "3ba3b", "0cc49", "3b64f", "NE Destination 3 (Great Wall)"],

            # N Continent "\x0f"
            14: [0, b"\x0f", 13, 310, "3ba4b", "0cc8e", "3b660", "N Destination 1 (Euro)"],
            15: [0, b"\x0f", 13, 330, "3ba5b", "0cca7", "3b66c", "N Destination 2 (Mt. Temple)"],
            16: [0, b"\x0f", 13, 350, "3ba6b", "0ccec", "3b679", "N Destination 3 (Native's Village)"],
            17: [0, b"\x0f", 13, 360, "3ba7b", "0cd05", "3b685", "N Destination 4 (Ankor Wat)"],

            # NW Continent Overworld "\x16"
            18: [0, b"\x16", 14, 400, "3ba8b", "0cd24", "3b696", "NW Destination 1 (Dao)"],
            19: [0, b"\x16", 14, 410, "3ba9b", "0cd55", "3b6a3", "NW Destination 2 (Pyramid)"]
        }


        # Database of map exits
        # FORMAT: { ID: [CoupleID (0 if one-way), ShuffleTo (0 if no shuffle), ShuffleFrom (0 if no shuffle), FromRegion, ToRegion,
        #           ROM_Location, DestString,BossFlag, DungeonFlag, DungeonEntranceFlag, Name]}
        self.exits = {
            # Bosses
            1:  [ 2, 0, 0,  78,  97, "18872", b"\x29\x78\x00\xC0\x00\x00\x00\x11", True, True, False, "Castoth entrance (in)"],
            2:  [ 1, 0, 0,   0,   0, "189e4", b"\x1E\x68\x00\x00\x01\x03\x00\x24", True, True, False, "Castoth entrance (out)"],
            3:  [ 0, 0, 0, 104, 102, "584cc", b"\x30\x48\x00\x10\x01\x83\x00\x21", True, True, False, "Diamond Coast passage (Gold Ship)"],

            4:  [ 5, 0, 0, 171, 198, "18e20", b"\x55\x70\x00\xE0\x01\x00\x00\x22", True, True, False, "Viper entrance (in)"],
            5:  [ 4, 0, 0,   0,   0, "19006", b"\x4C\xF8\x00\x30\x00\x03\x00\x22", True, True, False, "Viper entrance (out)"],
            6:  [ 0, 0, 0, 198, 200, "acece", b"\x5A\x90\x00\x70\x00\x83\x00\x14", True, True, False, "Seaside Palace passage (Viper)"],

            7:  [ 8, 0, 0, 249, 243, "69c62", b"\x67\x78\x01\xd0\x01\x80\x01\x22", True, True, False, "Vampires entrance (in)"],
            8:  [ 7, 0, 0,   0,   0, "193f8", b"\x65\xb8\x00\x80\x02\x03\x00\x44", True, True, False, "Vampires entrance (out)"],
            9:  [ 0, 0, 0, 242, 212, "193ea", b"\x5f\x80\x00\x50\x00\x83\x00\x44", True, True, False, "Vampires exit"],

            10: [11, 0, 0, 301, 302, "19c2a", b"\x8A\x50\x00\x90\x00\x87\x00\x33", True, True, False, "Sand Fanger entrance (in)"],
            11: [10, 0, 0,   0,   0, "19c78", b"\x88\xE0\x03\x90\x00\x06\x00\x14", True, True, False, "Sand Fanger entrance (out)"],
            12: [ 0, 0, 0, 303, 290, "19c84", b"\x82\x10\x00\x90\x00\x87\x00\x18", True, True, False, "Sand Fanger exit"],

            13: [14, 0, 0, 414, 448, "8cdcf", b"\xDD\xF8\x00\xB0\x01\x00\x00\x22", True, True, False, "Mummy Queen entrance"],
            14: [13, 0, 0,   0,   0, "8cdcf", b"\xDD\xF8\x00\xB0\x01\x00\x00\x22", True, True, False, "Mummy Queen exit (fake)"],
            15: [ 0, 0, 0, 448, 415,      "", b"\xcd\x70\x00\x90\x00\x83\x00\x11", True, True, False, "Mummy Queen exit"],     # This one's dumb

            16: [17, 0, 0, 470, 471, "1a8c2", b"\xE3\xD8\x00\x90\x03\x83\x30\x44", True, True, False, "Babel entrance (in)"],
            17: [16, 0, 0,   0,   0, "1a8d0", b"\xE2\xD0\x00\xE0\x00\x03\x00\x84", True, True, False, "Babel entrance (out)"],
            18: [ 0, 0, 0, 472, 400, "9804a", b"\xC3\x10\x02\x90\x00\x83\x00\x23", True, True, False, "Dao passage (Babel)"],

            19: [20, 0, 0, 481, 482, "1a94e", b"\xEA\x78\x00\xC0\x00\x00\x00\x11", True, True, False, "Solid Arm entrance"],
            20: [19, 0, 0,   0,   0, "1a94e", b"\xEA\x78\x00\xC0\x00\x00\x00\x11", True, True, False, "Solid Arm exit (fake)"],
            21: [ 0, 0, 0, 482, 472, "98115", b"\xE3\x80\x02\xB0\x01\x80\x10\x23", True, True, False, "Babel passage (Solid Arm)"],

            # Passage Menus
            22: [0, 0, 0, 15,  28, "", b"", False, False, False, "Seth: Passage 1 (South Cape)"],
            23: [0, 0, 0, 15, 102, "", b"", False, False, False, "Seth: Passage 2 (Diamond Coast)"],
            24: [0, 0, 0, 15, 280, "", b"", False, False, False, "Seth: Passage 3 (Watermia)"],

            25: [0, 0, 0, 16,  60, "", b"", False, False, False, "Moon Tribe: Passage 1 (Moon Tribe)"],
            26: [0, 0, 0, 16, 200, "", b"", False, False, False, "Moon Tribe: Passage 2 (Seaside Palace)"],

            27: [0, 0, 0, 17, 161, "", b"", False, False, False, "Neil: Passage 1 (Neil's)"],
            28: [0, 0, 0, 17, 314, "", b"", False, False, False, "Neil: Passage 2 (Euro)"],
            29: [0, 0, 0, 17, 402, "", b"", False, False, False, "Neil: Passage 3 (Dao)"],
            30: [0, 0, 0, 17, 460, "", b"", False, False, False, "Neil: Passage 4 (Babel)"],

            # South Cape
            31: [32, 0, 0, 20, 22, "18444", b"", False, False, False, "South Cape: School main (in)"],  # Duplicate exit at 18438?
            32: [31, 0, 0,  0,  0, "1856c", b"", False, False, False, "South Cape: School main (out)"],
            33: [34, 0, 0, 21, 22, "18498", b"", False, False, False, "South Cape: School roof (in)"],
            34: [33, 0, 0,  0,  0, "18560", b"", False, False, False, "South Cape: School roof (out)"],
            35: [36, 0, 0, 20, 23, "18474", b"", False, False, False, "South Cape: Will's House (in)"],
            36: [35, 0, 0,  0,  0, "1852a", b"", False, False, False, "South Cape: Will's House (out)"],
            37: [38, 0, 0, 20, 24, "18480", b"", False, False, False, "South Cape: East House (in)"],
            38: [37, 0, 0,  0,  0, "18552", b"", False, False, False, "South Cape: East House (out)"],
            39: [40, 0, 0, 20, 27, "1845c", b"", False, False, False, "South Cape: Erik's House main (in)"],
            40: [39, 0, 0,  0,  0, "184e8", b"", False, False, False, "South Cape: Erik's House main (out)"],
            41: [42, 0, 0, 20, 27, "184a4", b"", False, False, False, "South Cape: Erik's House roof (in)"],
            42: [41, 0, 0,  0,  0, "184f4", b"", False, False, False, "South Cape: Erik's House roof (out)"],
            43: [44, 0, 0, 20, 26, "18450", b"", False, False, False, "South Cape: Lance's House (in)"],
            44: [43, 0, 0,  0,  0, "184c0", b"", False, False, False, "South Cape: Lance's House (out)"],
            45: [46, 0, 0, 20, 25, "18468", b"", False, False, False, "South Cape: Seth's House (in)"],
            46: [45, 0, 0,  0,  0, "1851c", b"", False, False, False, "South Cape: Seth's House (out)"],
            47: [48, 0, 0, 20, 28, "1848c", b"", False, False, False, "South Cape: Seaside Cave (in)"],
            48: [47, 0, 0,  0,  0, "4be6a", b"", False, False, False, "South Cape: Seaside Cave (out)"],

            # Edward's / Prison
            50: [51, 0, 0, 31, 49, "1857c", b"", False, True, True, "Tunnel back entrance (in)"],
            51: [50, 0, 0,  0,  0, "186f4", b"", False, True, True, "Tunnel back entrance (out)"],
            52: [53, 0, 0, 33, 40, "1860c", b"\x0C\x58\x00\x50\x00\x83\x00\x12", False, True, True, "Tunnel entrance (in)"],  # set checkpoint
            53: [52, 0, 0,  0,  0, "18626", b"", False, True, True, "Tunnel entrance (out)"],
            54: [ 0, 0, 0, 30, 32, "4cfce", b"", False, False, False, "Prison entrance (king)"],
            #55: [54, 0, 0,  0,  2,      "", b"\x0a\xe0\x01\x60\x01\x03\x20\x34", False, False, False, "Prison exit (king), fake"],

            # Tunnel
            60: [61, 0, 0, 40, 41, "18632", b"", False,  True, False, "Tunnel: Map 12 to Map 13"],
            61: [60, 0, 0,  0,  0, "18640", b"", False,  True, False, "Tunnel: Map 13 to Map 12"],
            62: [63, 0, 0, 41, 42, "1864c", b"", False,  True, False, "Tunnel: Map 13 to Map 14"],
            63: [62, 0, 0,  0,  0, "1865a", b"", False,  True, False, "Tunnel: Map 14 to Map 13"],
            64: [65, 0, 0, 42, 43, "18666", b"", False,  True, False, "Tunnel: Map 14 to Map 15"],
            65: [64, 0, 0,  0,  0, "18680", b"", False,  True, False, "Tunnel: Map 15 to Map 14"],
            66: [67, 0, 0, 43, 44, "1868c", b"", False,  True, False, "Tunnel: Map 15 to Map 16"],
            67: [66, 0, 0,  0,  0, "1869a", b"", False,  True, False, "Tunnel: Map 16 to Map 15"],
            68: [69, 0, 0, 43, 45, "18674", b"", False,  True, False, "Tunnel: Map 15 to Map 17"],
            69: [68, 0, 0,  0,  0, "186a8", b"", False,  True, False, "Tunnel: Map 17 to Map 15"],
            70: [71, 0, 0, 46, 47, "186b4", b"", False,  True, False, "Tunnel: Map 17 to Map 18"],
            71: [70, 0, 0,  0,  0, "186c2", b"", False,  True, False, "Tunnel: Map 18 to Map 17"],
            72: [73, 0, 0, 48, 49, "186ce", b"", False,  True, False, "Tunnel: Map 18 to Map 19"],
            73: [72, 0, 0,  0,  0, "186e8", b"", False,  True, False, "Tunnel: Map 19 to Map 18"],

            # Itory
            80: [81, 0, 0, 51, 53, "18704", b"", False, False, False, "Itory: West House (in)"],
            81: [80, 0, 0,  0,  0, "1874e", b"", False, False, False, "Itory: West House (out)"],
            82: [83, 0, 0, 51, 54, "18728", b"", False, False, False, "Itory: North House (in)"],
            83: [82, 0, 0,  0,  0, "18776", b"", False, False, False, "Itory: North House (out)"],
            84: [85, 0, 0, 51, 55, "18710", b"", False, False, False, "Itory: Lilly Front Door (in)"],
            85: [84, 0, 0,  0,  0, "1875c", b"", False, False, False, "Itory: Lilly Front Door (out)"],
            86: [87, 0, 0, 52, 55, "1871c", b"", False, False, False, "Itory: Lilly Back Door (in)"],
            87: [86, 0, 0,  0,  0, "18768", b"", False, False, False, "Itory: Lilly Back Door (out)"],
            88: [89, 0, 0, 51, 56, "18734", b"", False, False, False, "Itory Cave (in)"],
            89: [88, 0, 0,  0,  0, "18784", b"", False, False, False, "Itory Cave (out)"],
            90: [91, 0, 0, 57, 58, "18790", b"", False, False, False, "Itory Cave Hidden Room (in)"],  # always linked?
            91: [90, 0, 0,  0,  0, "1879c", b"", False, False, False, "Itory Cave Hidden Room (out)"],

            # Moon Tribe
            100: [101, 0, 0, 60,  61, "187b6", b"", False, False, False, "Moon Tribe Cave (in)"],
            101: [100, 0, 0,  0,   0, "187c4", b"", False, False, False, "Moon Tribe Cave (out)"],
            102: [  0, 0, 0, 64, 170, "9d1ea", b"", False,  True,  True, "Moon Tribe: Sky Garden passage"],

            # Inca
            110: [111, 0, 0, 64,  70, "187d2", b"", False, True, True, "Inca Ruins entrance (in)"],
            111: [110, 0, 0,  0,   0, "187e0", b"", False, True, True, "Inca Ruins entrance (out)"],
            #114: [  0, 0, 0, 65, 102, "", b"", False, False,  True, "Inca: Diamond Coast passage"],

            # Inca Ruins
            120: [121, 0, 0, 70,  89, "", b"", False,  True, False, "Inca: Map 29 to Map 37 (E)"],
            121: [120, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 37 to Map 29 (E)"],
            122: [123, 0, 0, 89,  94, "", b"", False,  True, False, "Inca: Map 37 to Map 39"],
            123: [122, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 39 to Map 37"],
            124: [125, 0, 0, 94,  71, "", b"", False,  True, False, "Inca: Map 39 to Map 29"],
            125: [124, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 29 to Map 39"],
            126: [127, 0, 0, 90,  72, "", b"", False,  True, False, "Inca: Map 37 to Map 29 (W)"],
            127: [126, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 29 to Map 37 (W)"],
            128: [129, 0, 0, 72,  91, "", b"", False,  True, False, "Inca: Map 29 to Map 38"],
            129: [128, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 38 to Map 29"],
            130: [131, 0, 0, 73,  80, "", b"", False,  True, False, "Inca: Map 29 to Map 32"],
            131: [130, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 32 to Map 29"],
            132: [133, 0, 0, 81,  85, "", b"", False,  True, False, "Inca: Map 32 to Map 35"],
            133: [132, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 35 to Map 32"],
            134: [135, 0, 0, 85,  74, "", b"", False,  True, False, "Inca: Map 35 to Map 29"],
            135: [134, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 35 to Map 29"],
            136: [137, 0, 0, 74,  79, "", b"", False,  True, False, "Inca: Map 29 to Map 31"],
            137: [136, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 31 to Map 29"],
            138: [139, 0, 0, 79,  95, "", b"", False,  True, False, "Inca: Map 31 to Map 40"],
            139: [138, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 40 to Map 31"],
            140: [141, 0, 0, 96,  76, "", b"", False,  True, False, "Inca: Map 40 to Map 29"],
            141: [140, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 29 to Map 40"],
            142: [143, 0, 0, 86,  82, "", b"", False,  True, False, "Inca: Map 35 to Map 33"],
            143: [142, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 33 to Map 35"],
            144: [145, 0, 0, 83,  75, "", b"", False,  True, False, "Inca: Map 33 to Map 29"],
            145: [144, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 29 to Map 33"],
            146: [147, 0, 0, 75,  84, "", b"", False,  True, False, "Inca: Map 29 to Map 34"],
            147: [146, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 34 to Map 29"],
            148: [149, 0, 0, 84,  93, "", b"", False,  True, False, "Inca: Map 34 to Map 38"],
            149: [148, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 38 to Map 34"],
            150: [151, 0, 0, 84,  87, "", b"", False,  True, False, "Inca: Map 34 to Map 36"],
            151: [150, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 36 to Map 34"],
            152: [153, 0, 0, 88,  77, "", b"", False,  True, False, "Inca: Map 36 to Map 30"],
            153: [152, 0, 0,  0,   0, "", b"", False,  True, False, "Inca: Map 30 to Map 36"],
            154: [  0, 0, 0, 98, 100, "", b"", False,  True, False, "Gold Ship entrance"],

            # Gold Ship
            160: [161, 0, 0, 100, 101, "", b"", False, False, False, "Gold Ship Interior (in)"],
            161: [160, 0, 0,   0,   0, "", b"", False, False, False, "Gold Ship Interior (out)"],

            # Diamond Coast
            172: [173, 0, 0, 102, 103, "18aa0", b"", False, False, False, "Coast House (in)"],
            173: [172, 0, 0,   0,   0, "18aae", b"", False, False, False, "Coast House (out)"],

            # Freejia
            182: [183, 0, 0, 110, 116, "18aec", b"", False, False, False, "Freejia: West House (in)"],
            183: [182, 0, 0,   0,   0, "18b9c", b"", False, False, False, "Freejia: West House (out)"],
            184: [185, 0, 0, 110, 117, "18af8", b"", False, False, False, "Freejia: 2-story House (in)"],
            185: [184, 0, 0,   0,   0, "18bc4", b"", False, False, False, "Freejia: 2-story House (out)"],
            186: [187, 0, 0, 111, 117, "18b04", b"", False, False, False, "Freejia: 2-story Roof (in)"],
            187: [186, 0, 0,   0,   0, "18bd0", b"", False, False, False, "Freejia: 2-story Roof (out)"],
            188: [189, 0, 0, 110, 118, "18b10", b"", False, False, False, "Freejia: Lovers' House (in)"],
            189: [188, 0, 0,   0,   0, "18bf8", b"", False, False, False, "Freejia: Lovers' House (out)"],
            190: [191, 0, 0, 110, 119, "18b1c", b"", False, False, False, "Freejia: Hotel (in)"],
            191: [190, 0, 0,   0,   0, "18c20", b"", False, False, False, "Freejia: Hotel (out)"],
            192: [193, 0, 0, 119, 120, "18c2c", b"", False, False, False, "Freejia: Hotel West Room (in)"],
            193: [192, 0, 0,   0,   0, "18c44", b"", False, False, False, "Freejia: Hotel West Room (out)"],
            194: [195, 0, 0, 119, 121, "18c38", b"", False, False, False, "Freejia: Hotel East Room (in)"],
            195: [194, 0, 0,   0,   0, "18c50", b"", False, False, False, "Freejia: Hotel East Room (out)"],
            196: [197, 0, 0, 110, 122, "18b34", b"", False, False, False, "Freejia: Laborer House (in)"],    # might take this out?
            197: [196, 0, 0,   0,   0, "18c78", b"", False, False, False, "Freejia: Laborer House (out)"],
            198: [199, 0, 0, 112, 122, "18b28", b"", False, False, False, "Freejia: Laborer Roof (in)"],
            199: [198, 0, 0,   0,   0, "18c84", b"", False, False, False, "Freejia: Laborer Roof (out)"],
            200: [201, 0, 0, 110, 123, "18b40", b"", False, False, False, "Freejia: Messy House (in)"],
            201: [200, 0, 0,   0,   0, "18c92", b"", False, False, False, "Freejia: Messy House (out)"],
            202: [203, 0, 0, 110, 124, "18abc", b"", False, False, False, "Freejia: Erik House (in)"],
            203: [202, 0, 0,   0,   0, "18b5a", b"", False, False, False, "Freejia: Erik House (out)"],
            204: [205, 0, 0, 110, 125, "18ac8", b"", False, False, False, "Freejia: Dark Space House (in)"],
            205: [204, 0, 0,   0,   0, "18b68", b"", False, False, False, "Freejia: Dark Space House (out)"],
            206: [207, 0, 0, 110, 126, "18ad4", b"", False, False, False, "Freejia: Labor Trade House (in)"],
            207: [206, 0, 0,   0,   0, "18b82", b"", False, False, False, "Freejia: Labor Trade House (out)"],
            208: [209, 0, 0, 113, 126, "18ae0", b"", False, False, False, "Freejia: Labor Trade Roof (in)"],
            209: [208, 0, 0,   0,   0, "18b8e", b"", False, False, False, "Freejia: Labor Trade Roof (out)"],
            210: [211, 0, 0, 114, 127, "18b4c", b"", False, False, False, "Freejia: Labor Market (in)"],
            211: [210, 0, 0,   0,   0, "18ca0", b"", False, False, False, "Freejia: Labor Market (out)"],

            # Diamond Mine
            222: [223, 0, 0, 133, 134, "", b"", False,  True, False, "Diamond Mine: Map 62 to Map 63"],
            223: [222, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 63 to Map 62"],
            224: [225, 0, 0, 135, 140, "", b"", False,  True, False, "Diamond Mine: Map 63 to Map 66"],
            225: [224, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 63"],
            226: [227, 0, 0, 134, 136, "", b"", False,  True, False, "Diamond Mine: Map 63 to Map 64"],
            227: [226, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 64 to Map 63"],
            228: [229, 0, 0, 136, 138, "", b"", False,  True, False, "Diamond Mine: Map 64 to Map 65"],
            229: [228, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 65 to Map 64"],
            230: [231, 0, 0, 139, 143, "", b"", False,  True, False, "Diamond Mine: Map 65 to Map 66"],
            231: [230, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 65"],
            232: [233, 0, 0, 138, 130, "", b"", False,  True, False, "Diamond Mine: Map 65 to Map 61"],
            233: [232, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 61 to Map 65"],
            234: [235, 0, 0, 132, 142, "", b"", False,  True, False, "Diamond Mine: Map 61 to Map 66"],
            235: [234, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 61"],
            236: [237, 0, 0, 140, 144, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 67 (1)"],
            237: [236, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 67 to Map 66 (1)"],
            238: [239, 0, 0, 145, 141, "", b"", False,  True, False, "Diamond Mine: Map 67 to Map 66 (2)"],
            239: [238, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 67 (2)"],
            240: [241, 0, 0, 141, 146, "", b"", False,  True, False, "Diamond Mine: Map 66 to Map 68"],
            241: [240, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 68 to Map 66"],
            242: [243, 0, 0, 146, 148, "", b"", False,  True, False, "Diamond Mine: Map 68 to Map 69"],
            243: [242, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 69 to Map 68"],
            244: [245, 0, 0, 146, 149, "", b"", False,  True, False, "Diamond Mine: Map 68 to Map 70"],
            245: [244, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 70 to Map 68"],
            246: [247, 0, 0, 147, 150, "", b"", False,  True, False, "Diamond Mine: Map 68 to Map 71"],
            247: [246, 0, 0,   0,   0, "", b"", False,  True, False, "Diamond Mine: Map 71 to Map 68"],

            # Nazca
            260: [261, 0, 0, 162, 170, "5e6a2", b"\x4C\x68\x01\x40\x00\x83\x00\x22", False, True, True, "Nazca: Sky Garden entrance"],
            261: [260, 0, 0,   0,   0, "5f429", b"\x4B\xe0\x01\xc0\x02\x03\x00\x44", False, True, True, "Nazca: Sky Garden exit"],

            # Sky Garden
            #270: [  0, 0, 0, 171,  16, "", b"", False,  True,  True, "Moon Tribe: Sky Garden passage"],
            273: [274, 0, 0, 170, 172, "", b"", False,  True, False, "Sky Garden: Map 76 to Map 77"],
            274: [273, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 77 to Map 76"],
            275: [276, 0, 0, 170, 176, "", b"", False,  True, False, "Sky Garden: Map 76 to Map 79"],
            276: [275, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 79 to Map 76"],
            277: [278, 0, 0, 170, 181, "", b"", False,  True, False, "Sky Garden: Map 76 to Map 81"],
            278: [277, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 81 to Map 76"],
            279: [280, 0, 0, 170, 190, "", b"", False,  True, False, "Sky Garden: Map 76 to Map 83"],
            280: [279, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 83 to Map 76"],
            281: [282, 0, 0, 172, 175, "", b"", False,  True, False, "Sky Garden: Map 77 to Map 78 (E)"],   # Room 1
            282: [281, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 78 to Map 77 (W)"],
            283: [284, 0, 0, 175, 173, "", b"", False,  True, False, "Sky Garden: Map 78 to Map 77 (SE)"],
            284: [283, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 77 to Map 78 (SW)"],
            285: [286, 0, 0, 175, 174, "", b"", False,  True, False, "Sky Garden: Map 78 to Map 77 (SW)"],
            286: [285, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 77 to Map 78 (SE)"],
            287: [288, 0, 0, 176, 169, "", b"", False,  True, False, "Sky Garden: Map 79 to Map 86"],       # Room 2
            288: [287, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 86 to Map 79"],
            289: [290, 0, 0, 176, 179, "", b"", False,  True, False, "Sky Garden: Map 79 to Map 80 (NE)"],
            290: [289, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 80 to Map 79 (NW)"],
            291: [292, 0, 0, 179, 177, "", b"", False,  True, False, "Sky Garden: Map 80 to Map 79 (N)"],
            292: [291, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 79 to Map 80 (N)"],
            293: [294, 0, 0, 178, 180, "", b"", False,  True, False, "Sky Garden: Map 79 to Map 80 (S)"],
            294: [293, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 80 to Map 79 (S)"],
            295: [296, 0, 0, 168, 186, "", b"", False,  True, False, "Sky Garden: Map 81 to Map 82 (NE)"],   # Room 3
            296: [295, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 82 to Map 81 (NW)"],
            297: [298, 0, 0, 182, 188, "", b"", False,  True, False, "Sky Garden: Map 81 to Map 82 (NW)"],
            298: [297, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 82 to Map 81 (NE)"],
            299: [300, 0, 0, 184, 187, "", b"", False,  True, False, "Sky Garden: Map 81 to Map 82 (SE)"],
            300: [299, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 82 to Map 81 (SW)"],
            301: [302, 0, 0, 191, 196, "", b"", False,  True, False, "Sky Garden: Map 83 to Map 84 (NW)"],   # Room 4
            302: [301, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 84 to Map 83 (NE)"],
            303: [304, 0, 0, 192, 195, "", b"", False,  True, False, "Sky Garden: Map 83 to Map 84 (C)"],
            304: [303, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 84 to Map 83 (C)"],
            305: [306, 0, 0, 197, 193, "", b"", False,  True, False, "Sky Garden: Map 84 to Map 83 (SE)"],
            306: [305, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 83 to Map 84 (SW)"],
            307: [308, 0, 0, 194, 195, "", b"", False,  True, False, "Sky Garden: Map 83 to Map 84 (E)"],
            308: [307, 0, 0,   0,   0, "", b"", False,  True, False, "Sky Garden: Map 84 to Map 83 (W)"],

            # Seaside Palace
            310: [311, 0, 0, 211, 201, "69759", b"", False, False, False, "Seaside entrance"],
            311: [310, 0, 0,   0,   0, "1906a", b"", False, False, False, "Seaside exit"],
            312: [313, 0, 0, 200, 202, "19046", b"", False, False, False, "Seaside: Area 1 NE Room (in)"],
            313: [312, 0, 0,   0,   0, "19114", b"", False, False, False, "Seaside: Area 1 NE Room (out)"],
            314: [315, 0, 0, 200, 203, "19052", b"", False, False, False, "Seaside: Area 1 NW Room (in)"],
            315: [314, 0, 0,   0,   0, "19120", b"", False, False, False, "Seaside: Area 1 NW Room (out)"],
            316: [317, 0, 0, 200, 204, "1905e", b"", False, False, False, "Seaside: Area 1 SE Room (in)"],
            317: [316, 0, 0,   0,   0, "1912c", b"", False, False, False, "Seaside: Area 1 SE Room (out)"],
            318: [319, 0, 0, 200, 205, "1903a", b"", False, False, False, "Seaside: Area 2 entrance"],
            319: [318, 0, 0,   0,   0, "19146", b"", False, False, False, "Seaside: Area 2 exit"],
            320: [321, 0, 0, 205, 207, "1915e", b"", False, False, False, "Seaside: Area 2 SW Room (in)"],
            321: [320, 0, 0,   0,   0, "19138", b"", False, False, False, "Seaside: Area 2 SW Room (out)"],
            322: [323, 0, 0, 205, 209, "19152", b"", False, False, False, "Seaside: Fountain (in)"],
            323: [322, 0, 0,   0,   0, "191d4", b"", False, False, False, "Seaside: Fountain (out)"],

            # Mu
            330: [331, 0, 0, 210, 212, "191ee", b"", False,  True,  True, "Mu entrance"],
            331: [330, 0, 0,   0,   0, "191fc", b"", False,  True,  True, "Mu exit"],
            332: [333, 0, 0, 212, 217, "", b"", False,  True, False, "Mu: Map 95 to Map 96"],
            333: [332, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 96 to Map 95"],
            334: [335, 0, 0, 217, 220, "", b"", False,  True, False, "Mu: Map 96 to Map 97 (top)"],
            335: [334, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 97 to Map 96 (top)"],
            336: [337, 0, 0, 220, 231, "", b"", False,  True, False, "Mu: Map 97 to Map 99"],
            337: [336, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 99 to Map 97"],
            338: [339, 0, 0, 220, 225, "", b"", False,  True, False, "Mu: Map 97 to Map 98 (top)"],
            339: [338, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 98 to Map 97 (top)"],
            340: [341, 0, 0, 218, 222, "", b"", False,  True, False, "Mu: Map 96 to Map 97 (middle)"],
            341: [340, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 97 to Map 96 (middle)"],
            342: [343, 0, 0, 223, 227, "", b"", False,  True, False, "Mu: Map 97 to Map 98 (middle)"],
            343: [342, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 98 to Map 97 (middle)"],
#            344: [345, 0, 0, 000, 000, "", b"", False,  True, False, "Mu: Map 95 to Map 98 (middle)"],
#            345: [344, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 98 to Map 95 (middle)"],
            346: [347, 0, 0, 227, 233, "", b"", False,  True, False, "Mu: Map 98 to Map 100 (middle E)"],
            347: [346, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 100 to Map 98 (middle E)"],
            348: [349, 0, 0, 233, 237, "", b"", False,  True, False, "Mu: Map 100 to Map 101 (middle N)"],
            349: [348, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 101 to Map 100 (middle N)"],
            350: [351, 0, 0, 237, 234, "", b"", False,  True, False, "Mu: Map 101 to Map 100 (middle S)"],
            351: [350, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 100 to Map 101 (middle S)"],
            352: [353, 0, 0, 234, 228, "", b"", False,  True, False, "Mu: Map 100 to Map 98 (middle W)"],
            353: [352, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 98 to Map 100 (middle W)"],
            354: [355, 0, 0, 213, 232, "", b"", False,  True, False, "Mu: Map 95 to Map 99"],
            355: [354, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 99 to Map 95"],
            356: [357, 0, 0, 245, 246, "", b"", False,  True, False, "Mu: Map 95 to Map 98 (top)"],
            357: [356, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 98 to Map 95 (top)"],
            358: [359, 0, 0, 229, 224, "", b"", False,  True, False, "Mu: Map 98 to Map 97 (bottom)"],
            359: [358, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 97 to Map 98 (bottom)"],
            360: [361, 0, 0, 224, 219, "", b"", False,  True, False, "Mu: Map 97 to Map 96 (bottom)"],
            361: [360, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 96 to Map 97 (bottom)"],
            362: [363, 0, 0, 230, 216, "", b"", False,  True, False, "Mu: Map 98 to Map 95 (bottom)"],
            363: [362, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 95 to Map 98 (bottom)"],
            364: [365, 0, 0, 230, 235, "", b"", False,  True, False, "Mu: Map 98 to Map 100 (bottom)"],
            365: [364, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 100 to Map 98 (bottom)"],
            366: [367, 0, 0, 235, 239, "", b"", False,  True, False, "Mu: Map 100 to Map 101 (bottom)"],
            367: [366, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 101 to Map 100 (bottom)"],
            368: [369, 0, 0, 239, 240, "", b"", False,  True, False, "Mu: Map 101 to Map 102"],
            369: [368, 0, 0,   0,   0, "", b"", False,  True, False, "Mu: Map 102 to Map 101"],

            # Angel Village
            382: [383, 0, 0, 250, 210, "1941e", b"", False, False, False, "Angel: Mu Passage (in)"],
            383: [382, 0, 0,   0,   0, "191e2", b"", False, False, False, "Angel: Mu Passage (out)"], #custom
            384: [385, 0, 0, 250, 251, "1942a", b"", False, False, False, "Angel: Underground entrance (in)"],
            385: [384, 0, 0,   0,   0, "19446", b"", False, False, False, "Angel: Underground entrance (out)"],
            386: [387, 0, 0, 251, 252, "19452", b"", False, False, False, "Angel: Room 1 (in)"],
            387: [386, 0, 0,   0,   0, "194de", b"", False, False, False, "Angel: Room 1 (out)"],
            388: [389, 0, 0, 251, 253, "19476", b"", False, False, False, "Angel: Room 2 (in)"],
            389: [388, 0, 0,   0,   0, "19502", b"", False, False, False, "Angel: Room 2 (out)"],
            390: [391, 0, 0, 251, 254, "1945e", b"", False, False, False, "Angel: Dance Hall (in)"],
            391: [390, 0, 0,   0,   0, "1950e", b"", False, False, False, "Angel: Dance Hall (out)"],
            392: [393, 0, 0, 251, 255, "1946a", b"", False, False, False, "Angel: DS Room (in)"],
            393: [392, 0, 0,   0,   0, "194f6", b"", False, False, False, "Angel: DS Room (out)"],

            # Angel Dungeon
            400: [401, 0, 0, 251, 260, "19482", b"", False,  True,  True, "Angel Dungeon entrance"],
            401: [400, 0, 0,   0,   0, "19534", b"", False,  True,  True, "Angel Dungeon exit"],
            402: [403, 0, 0, 260, 261, "19528", b"", False,  True, False, "Angel Dungeon: Map 109 to Map 110"],
            403: [402, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Map 110 to Map 109"],
            404: [405, 0, 0, 261, 262, "", b"", False,  True, False, "Angel Dungeon: Map 110 to Map 111"],
            405: [404, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Map 111 to Map 110"],
            406: [407, 0, 0, 262, 263, "", b"", False,  True, False, "Angel Dungeon: Map 111 to Map 112"],
            407: [406, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Map 112 to Map 111"],
            408: [409, 0, 0, 264, 265, "", b"", False,  True, False, "Angel Dungeon: Map 112 to Chest"],
            409: [408, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Chest to Map 112"],
            #408: [409, 0, 0, 264, 265, "", b"", False,  True, False, "Angel Dungeon: Map 112 to Chest"],
            #409: [408, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Chest to Map 112"],
            410: [411, 0, 0, 263, 266, "", b"", False,  True, False, "Angel Dungeon: Map 112 to Map 113"],
            411: [410, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Map 113 to Map 112"],
            412: [413, 0, 0, 266, 267, "", b"", False,  True, False, "Angel Dungeon: Map 113 to Map 114"],
            413: [412, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Map 114 to Map 113"],
            414: [415, 0, 0, 268, 276, "", b"", False,  True, False, "Angel Dungeon: Map 114 to Ishtar Foyer"],
            415: [414, 0, 0,   0,   0, "", b"", False,  True, False, "Angel Dungeon: Ishtar Foyer to Map 114"],

            # Ishtar's Studio
            420: [421, 0, 0, 277, 269, "196b6", b"", False, False, False, "Ishtar entrance"],
            421: [420, 0, 0,   0,   0, "196c2", b"", False, False, False, "Ishtar exit"],
            422: [423, 0, 0, 269, 270, "196ce", b"", False, False, False, "Ishtar: Portrait room (in)"],
            423: [422, 0, 0,   0,   0, "196f4", b"", False, False, False, "Ishtar: Portrait room (out)"],
            424: [425, 0, 0, 269, 271, "196da", b"", False, False, False, "Ishtar: Side room (in)"],
            425: [424, 0, 0,   0,   0, "19700", b"", False, False, False, "Ishtar: Side room (out)"],
            426: [427, 0, 0, 269, 272, "196e6", b"", False, False, False, "Ishtar: Ishtar's room (in)"],
            427: [426, 0, 0,   0,   0, "1970c", b"", False, False, False, "Ishtar: Ishtar's room (out)"],
            428: [429, 0, 0, 272, 274, "19718", b"", False, False, False, "Ishtar: Puzzle room (in)"],
            429: [428, 0, 0,   0,   0, "197e6", b"", False, False, False, "Ishtar: Puzzle room (out)"],

            # Watermia
            440: [441, 0, 0, 280, 286, "197f4", b"", False, False, False, "Watermia: Lance House (in)"],
            441: [440, 0, 0,   0,   0, "1983e", b"", False, False, False, "Watermia: Lance House (out)"],
            442: [443, 0, 0, 280, 282, "19818", b"", False, False, False, "Watermia: DS House (in)"],
            443: [442, 0, 0,   0,   0, "19868", b"", False, False, False, "Watermia: DS House (out)"],
            444: [445, 0, 0, 280, 283, "1980c", b"", False, False, False, "Watermia: Gambling House (in)"],
            445: [444, 0, 0,   0,   0, "1985a", b"", False, False, False, "Watermia: Gambling House (out)"],
            446: [447, 0, 0, 280, 284, "19824", b"", False, False, False, "Watermia: West House (in)"],
            447: [446, 0, 0,   0,   0, "19882", b"", False, False, False, "Watermia: West House (out)"],
            448: [449, 0, 0, 280, 285, "19830", b"", False, False, False, "Watermia: East House (in)"],
            449: [448, 0, 0,   0,   0, "19890", b"", False, False, False, "Watermia: East House (out)"],
            450: [451, 0, 0, 280, 287, "19800", b"", False, False, False, "Watermia: NW House (in)"],
            451: [450, 0, 0,   0,   0, "1984c", b"", False, False, False, "Watermia: NW House (out)"],
            452: [453, 0, 0, 288, 311, "", b"", False, False,  True, "Watermia: Euro passage"],
            453: [452, 0, 0,   0,   0, "", b"", False, False,  True, "Euro: Watermia passage"],

            # Great Wall
            462: [463, 0, 0, 290, 291, "", b"", False,  True, False, "Great Wall: Map 130 to Map 131"],
            463: [462, 0, 0,   0,   0, "", b"", False,  True, False, "Great Wall: Map 131 to Map 130"],
            464: [465, 0, 0, 293, 294, "", b"", False,  True, False, "Great Wall: Map 131 to Map 133"],
            465: [464, 0, 0,   0,   0, "", b"", False,  True, False, "Great Wall: Map 133 to Map 131"],
            466: [467, 0, 0, 296, 297, "", b"", False,  True, False, "Great Wall: Map 133 to Map 134"],
            467: [466, 0, 0,   0,   0, "", b"", False,  True, False, "Great Wall: Map 134 to Map 133"],
            468: [469, 0, 0, 297, 298, "", b"", False,  True, False, "Great Wall: Map 134 to Map 135"],
            469: [468, 0, 0,   0,   0, "", b"", False,  True, False, "Great Wall: Map 135 to Map 134"],
            470: [471, 0, 0, 299, 300, "", b"", False,  True, False, "Great Wall: Map 135 to Map 136"],
            471: [470, 0, 0,   0,   0, "", b"", False,  True, False, "Great Wall: Map 136 to Map 135"],

            # Euro
            482: [483, 0, 0, 310, 312, "19cd2", b"", False, False, False, "Euro: Rolek Company (in)"],
            483: [482, 0, 0,   0,   0, "19d74", b"", False, False, False, "Euro: Rolek Company (out)"],
            484: [485, 0, 0, 310, 313, "19d0e", b"", False, False, False, "Euro: West House (in)"],
            485: [484, 0, 0,   0,   0, "19e12", b"", False, False, False, "Euro: West House (out)"],
            486: [487, 0, 0, 310, 314, "19cde", b"", False, False, False, "Euro: Rolek Mansion West (in)"],
            487: [486, 0, 0,   0,   0, "19d9c", b"", False, False, False, "Euro: Rolek Mansion West (out)"],
            488: [489, 0, 0, 310, 314, "19cea", b"", False, False, False, "Euro: Rolek Mansion East (in)"],
            489: [488, 0, 0,   0,   0, "19da8", b"", False, False, False, "Euro: Rolek Mansion East (out)"],
            490: [491, 0, 0, 310, 317, "19d26", b"", False, False, False, "Euro: Central House (in)"],
            491: [490, 0, 0,   0,   0, "19e54", b"", False, False, False, "Euro: Central House (out)"],
            492: [493, 0, 0, 310, 318, "19d32", b"", False, False, False, "Euro: Jeweler House (in)"],
            493: [492, 0, 0,   0,   0, "19e62", b"", False, False, False, "Euro: Jeweler House (out)"],
            494: [495, 0, 0, 310, 319, "19d3e", b"", False, False, False, "Euro: Twins House (in)"],
            495: [494, 0, 0,   0,   0, "19e70", b"", False, False, False, "Euro: Twins House (out)"],
            496: [497, 0, 0, 310, 320, "19cc6", b"", False, False, False, "Euro: Hidden House (in)"],
            497: [496, 0, 0,   0,   0, "19d66", b"", False, False, False, "Euro: Hidden House (out)"],
            498: [499, 0, 0, 310, 321, "19d4a", b"", False, False, False, "Euro: Shrine (in)"],
            499: [498, 0, 0,   0,   0, "19e7e", b"", False, False, False, "Euro: Shrine (out)"],
            500: [501, 0, 0, 310, 322, "19cba", b"", False, False, False, "Euro: Explorer's House (in)"],
            501: [500, 0, 0,   0,   0, "19d58", b"", False, False, False, "Euro: Explorer's House (out)"],
            502: [  0, 0, 0, 310, 323, "19cf6", b"", False, False, False, "Euro: Store Entrance (in)"],
            #503: [502, 0, 0,   0,   0, "", b"", False, False, False, "Euro: Store Entrance (out)"], #this doesn't exist!
            504: [505, 0, 0, 310, 324, "19d02", b"", False, False, False, "Euro: Store Exit (in)"],
            505: [504, 0, 0,   0,   0, "19e04", b"", False, False, False, "Euro: Store Exit (out)"],
            506: [507, 0, 0, 314, 316, "19db4", b"", False, False, False, "Euro: Guest Room (in)"],
            507: [506, 0, 0,   0,   0, "19df6", b"", False, False, False, "Euro: Guest Room (out)"],
            508: [509, 0, 0, 310, 325, "19d1a", b"", False, False, False, "Euro: Dark Space House (in)"],
            509: [508, 0, 0,   0,   0, "19e20", b"", False, False, False, "Euro: Dark Space House (out)"],

            # Mt. Kress
            522: [523, 0, 0, 330, 331, "", b"", False,  True, False, "Mt. Kress: Map 160 to Map 161"],
            523: [522, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 161 to Map 160"],
            524: [525, 0, 0, 332, 333, "", b"", False,  True, False, "Mt. Kress: Map 161 to Map 162 (W)"],
            525: [524, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 161 (W)"],
            526: [527, 0, 0, 332, 334, "", b"", False,  True, False, "Mt. Kress: Map 161 to Map 162 (E)"],
            527: [526, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 161 (E)"],
            528: [529, 0, 0, 333, 337, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 163 (N)"],
            529: [528, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 163 to Map 162 (N)"],
            530: [531, 0, 0, 337, 336, "", b"", False,  True, False, "Mt. Kress: Map 163 to Map 162 (S)"],
            531: [530, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 163 (S)"],
            532: [533, 0, 0, 333, 338, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 164"],
            533: [532, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 164 to Map 162"],
            534: [535, 0, 0, 335, 339, "", b"", False,  True, False, "Mt. Kress: Map 162 to Map 165"],
            535: [534, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 165 to Map 162"],
            536: [537, 0, 0, 339, 342, "", b"", False,  True, False, "Mt. Kress: Map 165 to Map 166"],
            537: [536, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 166 to Map 165"],
            538: [539, 0, 0, 340, 343, "", b"", False,  True, False, "Mt. Kress: Map 165 to Map 167"],
            539: [538, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 167 to Map 165"],
            540: [541, 0, 0, 341, 344, "", b"", False,  True, False, "Mt. Kress: Map 165 to Map 168"],
            541: [540, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 168 to Map 165"],
            542: [543, 0, 0, 344, 345, "", b"", False,  True, False, "Mt. Kress: Map 168 to Map 169"],
            543: [542, 0, 0,   0,   0, "", b"", False,  True, False, "Mt. Kress: Map 169 to Map 168"],

            # Native's Village
            552: [553, 0, 0, 350, 352, "19fe6", b"", False, False, False, "Native's Village: West House (in)"],
            553: [552, 0, 0,   0,   0, "1a00c", b"", False, False, False, "Native's Village: West House (out)"],
            554: [555, 0, 0, 350, 353, "19ff2", b"", False, False, False, "Native's Village: House w/Statues (in)"],
            555: [554, 0, 0,   0,   0, "1a01a", b"", False, False, False, "Native's Village: House w/Statues (out)"],
            556: [557, 0, 0, 351, 400, "", b"", False, False,  True, "Native's Village: Dao Passage"],
            557: [556, 0, 0,   0,   0, "", b"", False, False,  True, "Dao: Natives' Passage"],

            # Ankor Wat
            562: [563, 0, 0, 360, 361, "1a028", b"", False,  True, False, "Ankor Wat: Map 176 to Map 177"],
            563: [562, 0, 0,   0,   0, "1a036", b"", False,  True, False, "Ankor Wat: Map 177 to Map 176"],
            564: [565, 0, 0, 361, 363, "", b"", False,  True, False, "Ankor Wat: Map 177 to Map 178"],
            565: [564, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 178 to Map 177"],
            566: [567, 0, 0, 365, 366, "", b"", False,  True, False, "Ankor Wat: Map 178 to Map 179"],
            567: [566, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 179 to Map 178"],
            568: [569, 0, 0, 368, 367, "", b"", False,  True, False, "Ankor Wat: Map 180 to Map 179"],
            569: [568, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 179 to Map 180"],
            570: [571, 0, 0, 367, 369, "", b"", False,  True, False, "Ankor Wat: Map 179 to Map 181"],
            571: [570, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 181 to Map 179"],
            572: [573, 0, 0, 371, 362, "", b"", False,  True, False, "Ankor Wat: Map 181 to Map 177"],
            573: [572, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 177 to Map 181"],
            574: [575, 0, 0, 362, 372, "", b"", False,  True, False, "Ankor Wat: Map 177 to Map 182"],  # Garden
            575: [574, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 182 to Map 177"],
            576: [577, 0, 0, 372, 373, "", b"", False,  True, False, "Ankor Wat: Map 182 to Map 183"],
            577: [576, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 183 to Map 182"],
            578: [579, 0, 0, 373, 376, "", b"", False,  True, False, "Ankor Wat: Map 183 to Map 184"],
            579: [578, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 184 to Map 183"],
            580: [581, 0, 0, 374, 378, "", b"", False,  True, False, "Ankor Wat: Map 183 to Map 185 (W)"],
            581: [580, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 185 to Map 183 (W)"],
            582: [583, 0, 0, 378, 375, "", b"", False,  True, False, "Ankor Wat: Map 185 to Map 183 (E)"],
            583: [582, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 183 to Map 185 (E)"],
            584: [585, 0, 0, 375, 379, "", b"", False,  True, False, "Ankor Wat: Map 183 to Map 186"],
            585: [584, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 186 to Map 183"],
            586: [587, 0, 0, 379, 381, "", b"", False,  True, False, "Ankor Wat: Map 186 to Map 187 (W)"],
            587: [586, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 187 to Map 186 (W)"],
            588: [589, 0, 0, 381, 380, "", b"", False,  True, False, "Ankor Wat: Map 187 to Map 186 (E)"],
            589: [588, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 186 to Map 187 (E)"],
            590: [591, 0, 0, 381, 384, "", b"", False,  True, False, "Ankor Wat: Map 187 to Map 188"],
            591: [590, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 187"],
            592: [593, 0, 0, 385, 386, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 189"],
            593: [592, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 189 to Map 188"],
            594: [595, 0, 0, 387, 389, "", b"", False,  True, False, "Ankor Wat: Map 189 to Map 190 (E)"],
            595: [594, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 190 to Map 189 (E)"],
            596: [596, 0, 0, 388, 390, "", b"", False,  True, False, "Ankor Wat: Map 189 to Map 190 (W)"],
            597: [597, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 190 to Map 189 (W)"],
            598: [599, 0, 0, 390, 391, "", b"", False,  True, False, "Ankor Wat: Map 190 to Map 191"],
            599: [598, 0, 0,   0,   0, "", b"", False,  True, False, "Ankor Wat: Map 191 to Map 190"],
            600: [  0, 0, 0, 366, 368, "", b"", False,  True, False, "Ankor Wat: Map 179 to Map 180 (drop)"],
            601: [  0, 0, 0, 384, 381, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 187 NW-L (drop)"],
            602: [  0, 0, 0, 384, 381, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 187 NW-R (drop)"],
            603: [  0, 0, 0, 384, 383, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 187 NE (drop)"],
            604: [  0, 0, 0, 385, 382, "", b"", False,  True, False, "Ankor Wat: Map 188 to Map 187 SW (drop)"],
            605: [  0, 0, 0, 389, 388, "", b"", False,  True, False, "Ankor Wat: Map 190 to Map 189 (drop)"],

            # Dao
            612: [613, 0, 0, 400, 401, "1a27c", b"", False, False, False, "Dao: NW House (in)"],
            613: [612, 0, 0,   0,   0, "1a2d2", b"", False, False, False, "Dao: NW House (out)"],
            614: [615, 0, 0, 400, 402, "1a288", b"", False, False, False, "Dao: Neil's House (in)"],
            615: [614, 0, 0,   0,   0, "1a30a", b"", False, False, False, "Dao: Neil's House (out)"],
            616: [617, 0, 0, 400, 403, "1a294", b"", False, False, False, "Dao: Snake Game House (in)"],
            617: [616, 0, 0,   0,   0, "1a2ee", b"", False, False, False, "Dao: Snake Game House (out)"],
            618: [619, 0, 0, 400, 404, "1a2a0", b"", False, False, False, "Dao: SW House (in)"],
            619: [618, 0, 0,   0,   0, "1a2fc", b"", False, False, False, "Dao: SW House (out)"],
            620: [621, 0, 0, 400, 405, "1a2ac", b"", False, False, False, "Dao: S House (in)"],
            621: [620, 0, 0,   0,   0, "1a2e0", b"", False, False, False, "Dao: S House (out)"],
            622: [623, 0, 0, 400, 406, "1a2b8", b"", False, False, False, "Dao: SE House (in)"],
            623: [622, 0, 0,   0,   0, "1a318", b"", False, False, False, "Dao: SE House (out)"],

            # Pyramid
            634: [635, 0, 0, 411, 415, "", b"", False,  True, False, "Pyramid: Map 204 to Map 205"],
            635: [634, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 205 to Map 204"],
            636: [637, 0, 0, 413, 416, "", b"", False,  True, False, "Pyramid: Map 204 to Map 206"],  # Room 1
            637: [636, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 206 to Map 204"],
            638: [639, 0, 0, 417, 418, "", b"", False,  True, False, "Pyramid: Map 206 to Map 207"],
            639: [638, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 207 to Map 206"],
            640: [641, 0, 0, 419, 442, "", b"", False,  True, False, "Pyramid: Map 207 to Map 218"],
            641: [640, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 207"],
            642: [643, 0, 0, 413, 420, "", b"", False,  True, False, "Pyramid: Map 204 to Map 208"],  # Room 2
            643: [642, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 208 to Map 204"],
            644: [645, 0, 0, 421, 422, "", b"", False,  True, False, "Pyramid: Map 208 to Map 209"],
            645: [644, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 209 to Map 208"],
            646: [647, 0, 0, 423, 443, "", b"", False,  True, False, "Pyramid: Map 209 to Map 218"],
            647: [646, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 209"],
            648: [649, 0, 0, 413, 431, "", b"", False,  True, False, "Pyramid: Map 204 to Map 214"],  # Room 3
            649: [648, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 214 to Map 204"],
            650: [651, 0, 0, 434, 435, "", b"", False,  True, False, "Pyramid: Map 214 to Map 215"],
            651: [650, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 214 to Map 215"],
            652: [653, 0, 0, 435, 444, "", b"", False,  True, False, "Pyramid: Map 215 to Map 218"],
            653: [652, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 215"],
            654: [655, 0, 0, 413, 436, "", b"", False,  True, False, "Pyramid: Map 204 to Map 216"],  # Room 4
            655: [654, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 216 to Map 204"],
            656: [657, 0, 0, 437, 438, "", b"", False,  True, False, "Pyramid: Map 216 to Map 217"],
            657: [656, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 217 to Map 216"],
            658: [659, 0, 0, 439, 440, "", b"", False,  True, False, "Pyramid: Map 217 to Map 219"],
            659: [658, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 219 to Map 217"],
            660: [661, 0, 0, 441, 445, "", b"", False,  True, False, "Pyramid: Map 219 to Map 218"],
            661: [660, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 219"],
            662: [663, 0, 0, 413, 426, "", b"", False,  True, False, "Pyramid: Map 204 to Map 212"],  # Room 5
            663: [662, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 212 to Map 204"],
            664: [665, 0, 0, 429, 430, "", b"", False,  True, False, "Pyramid: Map 212 to Map 213"],
            665: [664, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 213 to Map 212"],
            666: [667, 0, 0, 430, 446, "", b"", False,  True, False, "Pyramid: Map 213 to Map 218"],
            667: [666, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 213"],
            668: [669, 0, 0, 413, 424, "", b"", False,  True, False, "Pyramid: Map 204 to Map 210"],  # Room 6
            669: [668, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 210 to Map 204"],
            670: [671, 0, 0, 424, 425, "", b"", False,  True, False, "Pyramid: Map 210 to Map 211"],
            671: [670, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 211 to Map 210"],
            672: [673, 0, 0, 425, 447, "", b"", False,  True, False, "Pyramid: Map 211 to Map 218"],
            673: [672, 0, 0,   0,   0, "", b"", False,  True, False, "Pyramid: Map 218 to Map 211"],

            # Babel
            682: [683, 0, 0, 460, 461, "", b"", False,  True, False, "Babel: Map 222 to Map 223"],
            683: [682, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 223 to Map 222"],
            684: [685, 0, 0, 462, 463, "", b"", False,  True, False, "Babel: Map 223 to Map 224"],
            685: [684, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 224 to Map 223"],
            686: [687, 0, 0, 463, 474, "", b"", False,  True, False, "Babel: Map 224 to Map 242"],  # Castoth
            687: [686, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 242 to Map 224"],
            688: [689, 0, 0, 463, 475, "", b"", False,  True, False, "Babel: Map 224 to Map 243"],  # Viper
            689: [688, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 243 to Map 224"],
            690: [691, 0, 0, 463, 465, "", b"", False,  True, False, "Babel: Map 224 to Map 225 (bottom)"],
            691: [690, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 225 to Map 224 (bottom)"],
            692: [693, 0, 0, 466, 464, "", b"", False,  True, False, "Babel: Map 225 to Map 224 (top)"],
            693: [692, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 224 to Map 225 (top)"],
            694: [695, 0, 0, 464, 476, "", b"", False,  True, False, "Babel: Map 224 to Map 244"],  # Vampires
            695: [694, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 244 to Map 224"],
            696: [697, 0, 0, 464, 477, "", b"", False,  True, False, "Babel: Map 224 to Map 245"],  # Sand Fanger
            697: [696, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 245 to Map 224"],
            698: [699, 0, 0, 464, 469, "", b"", False,  True, False, "Babel: Map 224 to Map 226"],
            699: [698, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 226 to Map 224"],
            700: [701, 0, 0, 470, 471, "", b"", False,  True, False, "Babel: Map 226 to Map 227"],
            701: [700, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 227 to Map 226"],
            702: [703, 0, 0, 471, 478, "", b"", False,  True, False, "Babel: Map 227 to Map 246"],  # Mummy Queen
            703: [702, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 246 to Map 227"],
            704: [705, 0, 0, 471, 467, "", b"", False,  True, False, "Babel: Map 227 to Map 225 (bottom)"],
            705: [704, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 225 to Map 227 (bottom)"],
            706: [707, 0, 0, 468, 472, "", b"", False,  True, False, "Babel: Map 225 to Map 227 (top)"],
            707: [706, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 227 to Map 225 (top)"],
            708: [709, 0, 0, 472, 473, "", b"", False,  True, False, "Babel: Map 227 to Map 222"],
            709: [708, 0, 0,   0,   0, "", b"", False,  True, False, "Babel: Map 222 to Map 227"],

            # Jeweler's Mansion
            720: [721, 0, 0, 8, 480, "8d32a", b"", False,  True, True, "Mansion entrance"],
            721: [720, 0, 0, 0,   0, "8fcb4", b"", False,  True, True, "Mansion exit"]

        }


        # Database of special map exits that don't conform to the typical "02 26" format, IDs correspond to self.exits
        # FORMAT: { ID: [MapAddr, Xaddr, Yaddr, FaceDirAddr, CameraAddr]}
        self.exits_detailed = {
            14: ["8ce31", "8ce37", "8ce40", "", "8ce49"]    # Mummy Queen exit
        }

        self.graph_viz = graphviz.Digraph(graph_attr=[('concentrate','true'),
                                                      ('rankdir', 'TB')], strict=True)
