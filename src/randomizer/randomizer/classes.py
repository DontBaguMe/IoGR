import copy
import time
from datetime import datetime
import binascii
import graphviz
import random

from .models.enums.start_location import StartLocation
from .models.enums.goal import Goal
from .models.enums.statue_req import StatueReq
from .models.enums.entrance_shuffle import EntranceShuffle
from .models.enums.dungeon_shuffle import DungeonShuffle
from .models.enums.orb_rando import OrbRando
from .models.enums.darkrooms import DarkRooms
from .models.enums.enemizer import Enemizer
from .models.enums.logic import Logic
from .models.randomizer_data import RandomizerData

MAX_INVENTORY = 15
PROGRESS_ADJ = [1.5, 1.25, 1, 0.75]  # Required items are more likely to be placed in easier modes
MAX_CYCLES = 500
INACCESSIBLE = -1


class World:
    # Severity: 0 = error/breakpoint, 1 = warning, 2 = info, 3 = verbose.
    def log(self, message, severity=0):
        if severity > self.print_log:
            return
        prefixes = ["Error: ", "Warning: ", "", ""]
        prefix = prefixes[severity]
        print(prefix+message)
        if severity == 0:
            breakpoint()
            pass
        return
    # Aliases, if using them is clearer to you
    def verbose(self, message):
        return self.log(message, 3)
    def info(self, message):
        return self.log(message, 2)
    def warn(self, message):
        return self.log(message, 1)
    def error(self, message):
        return self.log(message, 0)
    
    # Assigns item to location
    def fill_item(self, item, location=-1,test=False,override_restrictions=False):
        if location == -1:
            return False
        elif self.item_locations[location][2]:
            self.info("Tried to place an item in a full location: "+str(self.item_pool[item][3])+" "+str(self.item_locations[location][6]))
            return False
        elif item in self.item_locations[location][4] and not override_restrictions:
            self.info("Tried to place item in a restricted location: "+str(self.item_pool[item][3])+" "+str(self.item_locations[location][6]))
            return False
        elif test:
            return True

        self.item_pool[item][0] -= 1
        self.item_locations[location][2] = True
        self.item_locations[location][3] = item

        self.info("  "+str(self.item_pool[item][3])+" -> "+str(self.item_locations[location][6]))

        if self.is_accessible(self.item_locations[location][0]):
            self.items_collected.append(item)
            self.open_locations[self.item_locations[location][7]].remove(location)

        self.placement_log.append([item, location])
        return True


    # Removes an assigned item and returns it to item pool
    def unfill_item(self, location=-1):
        if location == -1:
            return -1
        elif not self.item_locations[location][2]:
            return -1

        item = self.item_locations[location][3]
        self.item_locations[location][2] = False
        self.item_locations[location][3] = 0
        self.item_pool[item][0] += 1

        self.info("  "+str(self.item_pool[item][3])+"<-"+str(self.item_locations[location][6])+" removed")

        if self.is_accessible(self.item_locations[location][0]):
            if item in self.items_collected:
                self.items_collected.remove(item)
            pool = self.get_pool_id(item=item)
            if location not in self.open_locations[pool]:
                self.open_locations[pool].append(location)

        for x in self.placement_log:
            if x[1] == location:
                self.placement_log.remove(x)

        return item

    # Map a type/item/location to a shuffle pool ID.
    # Returns pool 0 if a type/item/location isn't shuffled.
    def get_pool_id(self, type=-1, item=-1, loc=-1):
        if type < 0:
            if item in self.item_pool:
                type = self.item_pool[item][1]
            elif loc in self.item_locations:
                type = self.item_locations[loc][1]
            else:
                return 0
        if type == 1:
            return 1
        elif type == 2:
            return 2
        #elif type == 3:
        #    pass   # Statues aren't shuffled
        #elif type == 4:
        #    pass   # Artificial event flags aren't shuffled
        elif type == 5:
            if self.orb_rando == "Basic":
                return 5
            elif self.orb_rando == "Orbsanity":
                return 1
        elif type > self.get_max_pool_id():
            self.error("Type "+str(type)+" exceeds max pool ID")
            return 0
        return 0
    # Many lists are instantiated with one element per pool, so we need to know how
    # large to make those lists. This constant is validated via get_pool_id.
    def get_max_pool_id(self):
        return 6

    # Returns whether the item and location are in the same shuffle pool
    def are_item_loc_pooled(self, item, loc):
        return (self.get_pool_id(item=item) == self.get_pool_id(loc=loc))

    # Get list of items of given or all types, of any or all progression types.
    def list_typed_items(self, types, progress_type=0, shuffled_only=False, incl_placed=False):
        item_list = []
        for x in self.item_pool:
            if not types or self.item_pool[x][1] in types:
                if not progress_type or progress_type == self.item_pool[x][5]:
                    if not shuffled_only or self.item_pool[x][6] > 0:
                        for _ in range(self.item_pool[x][0]):
                            item_list.append(x)
                        if incl_placed:
                            for _ in [loc for loc in self.item_locations if self.item_locations[loc][3] == x]:
                                item_list.append(x)
        return item_list
    # Get list of items shuffled with given or all types, of any or all progression types.
    # If shuffled_only, items that aren't randomized (based on seed settings) are omitted.
    def list_pooled_items(self, types, progress_type=0, shuffled_only=False, incl_placed=False):
        if not types:
            return self.list_typed_items([], progress_type, shuffled_only, incl_placed)
        pools = set(self.get_pool_id(type=x) for x in types)
        item_list = []
        for x in self.item_pool:
            if self.item_pool[x][6] in pools:
                if not progress_type or progress_type == self.item_pool[x][5]:
                    if not shuffled_only or self.item_pool[x][6] > 0:
                        for _ in range(self.item_pool[x][0]):
                            item_list.append(x)
                        if incl_placed:
                            for _ in [loc for loc in self.item_locations if self.item_locations[loc][3] == x]:
                                item_list.append(x)
        return item_list

    # Returns all item locations
    def list_item_locations(self, shuffled_only=True):
        locations = []
        for x in self.item_locations:
            if self.item_locations[x][7] or not shuffled_only:
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


    # Returns graph node of an item location
    def location_node(self, location_id=-1):
        if location_id not in self.item_locations:
            self.error("Invalid item location "+str(location_id))
            return False
        else:
            return self.item_locations[location_id][0]


    # Returns whether an item location is already filled with an item
    def is_filled(self, location_id=-1):
        if location_id not in self.item_locations:
            self.error("Invalid item location "+str(location_id))
            return False
        else:
            return self.item_locations[location_id][2]


    # Returns whether the node is within the currently-accessible subgraph
    def is_accessible(self, node_id=-1):
        if node_id not in self.graph:
            return False
        elif self.graph[node_id][0]:
            return True
        else:
            return False


    # Zeroes out accessible flags for all world regions
    def unsolve(self,reset_graph=False):
        for x in self.graph:
            self.graph[x][0] = False
            if reset_graph:
                self.graph[x][4] = 0
                self.graph[x][8].clear()
                self.graph[x][9].clear()
                self.graph[x][10] = self.graph[x][1][:]
        for x in self.logic:
            if self.logic[x][0] == 1:
                self.logic[x][0] = 0
        return True


    # Resets collected items and other traversal data
    def reset_progress(self,reset_graph=False):
        self.visited.clear()
        self.items_collected.clear()
        self.item_destinations.clear()
        self.open_locations = [ [] for _ in range(self.item_pool_count)]
        self.open_edges = []
        self.unsolve(reset_graph)
        return True


    # Returns every accessible node from to_visit. Marks edges as traversed. 
    # If not test: marks nodes as traversed, collects self.items_collected/self.open_edges,
    # adds graph connections, and updates DS access.
    def traverse(self,to_visit=[],test=False):
        self.info(" Beginning traversal...")

        visited = []
        new_items = []
        if not to_visit:
            to_visit.append(0)
        while to_visit:
            node = to_visit.pop(0)
            visited.append(node)
            self.info("  Visiting node "+str(node)+" "+str(self.graph[node][5]))

            # If we haven't been here yet...
            if not self.graph[node][0]:
                # Get the newly-accessible items and record open item/ability locations
                new_items += self.visit_node(node,test)

                # Queue up newly-accessible nodes to visit
                for x in self.graph[node][10]:
                    if x != node and not self.is_accessible(x) and x not in to_visit+visited:
                        to_visit.insert(0,x)
                        self.verbose("  -Found node "+str(x)+" "+str(self.graph[x][5]))

            # If we've run out of nodes to visit, check if logic has opened up any new nodes
            if not to_visit:
                open_edges = self.get_open_edges(visited,True)
                bad_edges = []
                self.info(" All known nodes checked. Traversing edges...")
                for edge in open_edges:
                    dest = self.logic[edge][2]
                    if self.check_edge(edge,[],not test):
                        self.logic[edge][0] = 1
                        if dest not in to_visit:
                            to_visit.append(dest)
                            self.verbose("  -Found node "+str(dest)+" "+str(self.graph[dest][5]))
                    else:
                        bad_edges.append(edge)
                if not test:
                    self.open_edges = bad_edges

        return [visited,new_items]


    # Return list of logic edges that originate in an accessible node in nodes, and
    # either are locked or terminate outside of nodes.
    # include_redundant to include edges whose destination is already traversed.
    def get_open_edges(self,nodes=[],include_redundant=False):
        test_edges = self.open_edges[:]
        open_edges = []
        for x in nodes:
            if not self.is_accessible(x):
                test_edges += self.graph[x][12]
        for edge in test_edges:
            origin = self.logic[edge][1]
            dest = self.logic[edge][2]
            if self.logic[edge][0] >= 0 and edge not in open_edges and (include_redundant or not self.is_accessible(dest)) and (dest not in nodes or self.logic[edge][0] == 0):
                open_edges.append(edge)
        return open_edges


    # Visit a node, update graph info, return new items collected
    def visit_node(self,node,test=False):
        if not test and not self.graph[node][0]:
            self.graph[node][0] = True
            self.visited.append(node)
            self.item_destinations += self.graph[node][6]
            self.open_edges += self.graph[node][12]
        return self.collect_items(node,test)


    # Collect all items in given node
    def collect_items(self,node=-1,test=False):
        if node not in self.graph:
            return False
        items_found = []
        for location in self.graph[node][11]:
            if self.item_locations[location][2]:
                items_found.append(self.item_locations[location][3])
                if not test:
                    self.items_collected.append(self.item_locations[location][3])
                self.info("  -Got item "+str(self.item_locations[location][3])+" "+str(self.item_pool[self.item_locations[location][3]][3])+" from loc "+str(location)+" "+str(self.item_locations[location][6]).strip()+" in node "+str(node)+" "+str(self.graph[node][5]).strip())
            elif not test:
                self.open_locations[self.item_locations[location][7]].append(location)
                self.info("  -Found empty loc "+str(location)+" "+str(self.item_locations[location][6]))
        return items_found

    # Returns full list of accessible locations
    def accessible_locations(self, item_locations):
        accessible = []
        for x in item_locations:
            region = self.item_locations[x][0]
            if self.is_accessible(region):
                accessible.append(x)
        return accessible

    # Returns full list of inaccessible locations
    def inaccessible_locations(self, item_locations):
        inaccessible = []
        for x in item_locations:
            region = self.item_locations[x][0]
            if not self.is_accessible(region):
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
                    if not filled and self.are_item_loc_pooled(item,dest) and item not in restrictions:
                        if not accessible or region != INACCESSIBLE:
                            if self.fill_item(item, dest, False, False):
                                to_fill.remove(dest)
                                placed = True

        return True

    # Place list of items into random accessible locations
    def forward_fill(self, items=[], item_locations=[], test=False, override_restrictions=False):
        if not items:
            return True
        elif not item_locations:
            self.info("forward_fill given items but no locations")
            return False

        to_place = items[:]
        to_fill = [ [] for _ in range(self.item_pool_count)]
        quarantine = [ [] for _ in range(self.item_pool_count)]
        for loc in item_locations:
            if not self.item_locations[loc][2] and self.is_accessible(self.item_locations[loc][0]):
                to_fill[self.item_locations[loc][7]].append(loc)

        filled_locations = []
        while to_place:
            item = to_place.pop(0)
            pool = self.item_pool[item][6]
            filled = False
            while not filled and to_fill[pool]:
                location = to_fill[pool].pop(0)
                if self.fill_item(item,location,test,override_restrictions):
                    filled = True
                    filled_locations.append(location)
                    to_fill[pool] += quarantine[pool]
                else:
                    quarantine[pool].append(location)
                    items.append(item)
            if not filled:
                self.info("Not enough room to place item "+str(item))
                return False

        return True


    # Convert a prerequisite to a list of items needed to fulfill it
    def items_needed(self, edge=0):
        if not edge:
            return []

        prereq = []
        for req in self.logic[edge][4]:
            item = req[0]
            ct = req[1]
            i = 0
            while i < ct:
                prereq.append(item)
                i += 1

        if not self.items_collected:
            return prereq

        prereq_new = []
        items_new = self.items_collected[:]

        while prereq:
            x = prereq.pop(0)
            if x in items_new:
                items_new.remove(x)
            else:
                prereq_new.append(x)

        return prereq_new

    # Returns list of item combinations that grant progression
    # Returns progression list in the following categories: [[available],[not enough room],[too many inventory items]]
    def progression_list(self,open_edges=[]):
        if not open_edges:
            open_edges = self.get_open_edges()
        all_items = self.list_pooled_items(types=[], shuffled_only=True)
        prereq_list = [[],[],[]]    # [[available],[not enough room],[too many inventory items]]
        ds_list = []

        for edge in open_edges:
            prereq = self.items_needed(edge)
            if prereq and prereq not in prereq_list[0] and self.is_sublist(all_items, prereq):
                all_open_locs = []
                for locpool in self.open_locations:
                    all_open_locs.extend(locpool)
                if prereq not in prereq_list[1] and not self.forward_fill(prereq,all_open_locs,True,self.logic_mode == "Chaos"):
                    prereq_list[1].append(prereq)
                elif prereq not in prereq_list[2]:
                    dest = self.logic[edge][2]
                    traverse_result = self.traverse([dest],True)
                    new_nodes = traverse_result[0]
                    start_items_temp = self.items_collected[:] + prereq + traverse_result[1]
                    item_destinations_temp = self.item_destinations[:]
                    for x in new_nodes:
                        item_destinations_temp += self.graph[x][6]
                    inv_temp = self.get_inventory(start_items_temp,item_destinations_temp)
                    if len(inv_temp) <= MAX_INVENTORY:
                        if self.entrance_shuffle == "None" or self.check_ds_access(dest,False,True,[]):
                            prereq_list[0].append(prereq)
                        else:
                            ds_list.append(prereq)
                    else:
                        prereq_list[2].append(prereq)

        if prereq_list == [[],[],[]]:
            prereq_list[0] += ds_list

        return prereq_list



    # Find and clear non-progression item to make room for progression item
    def make_room(self, progression_result):
        # For inventory bottlenecks, remove one inventory item and try again
        if not progression_result[1] and progression_result[2]:
            return self.remove_nonprog(1,0,True)

        success = False
        for node in self.visited:
            if not success:
                for x in self.graph[node][11]:
                    if self.is_filled(x) and self.item_pool[self.item_locations[x][3]][5]>1 and self.item_pool[self.item_locations[x][3]][6]>0:
                        if self.unfill_item(x):
                            success = True
        return success


    # Remove accessible non-progression items to make room for a progression item.
    # All nonprog items are coalesced into a "non-ability" group and an "ability" group.
    # The nonprog ability is Nothing.
    def remove_nonprog(self,item_ct=0,ability_ct=0,inv=False):
        junk_locations = [ [], [] ]
        quest_locations = [ [], [] ]

        for location in self.item_locations:
            if self.item_locations[location][2] and self.item_locations[location][7] and self.is_accessible(self.item_locations[location][0]):
                item = self.item_locations[location][3]
                shuffle_pool = self.item_locations[location][7]
                type = self.item_pool[item][1]
                prog_type = self.item_pool[item][5]
                inv_type = self.item_pool[item][4]
                if shuffle_pool:
                    loc_pool = 0
                    if shuffle_pool == 2:
                        loc_pool = 1    # Remove Nothing abilities separately from other things
                    if prog_type == 2:
                        quest_locations[loc_pool].append(location)
                    elif prog_type == 3:
                        if not inv or inv_type:
                            junk_locations[loc_pool].append(location)
        random.shuffle(junk_locations[0])
        random.shuffle(quest_locations[0])
        random.shuffle(junk_locations[1])
        random.shuffle(quest_locations[1])

        quest = False
        pool = 0
        locations = junk_locations[pool]
        count = item_ct
        done = False
        items_removed = []
        while not done:
            if not count and pool == 0:
                pool = 1
                count = ability_ct
                quest = False
                locations = junk_locations[1]
            if not count and pool == 1:
                done = True
            else:
                if not locations and not quest:
                    quest = True
                    locations = quest_locations[pool]
                if not locations:
                    self.error("No room for prog items and no nonprog items to remove")
                    return False
                location = locations.pop(0)
                items_removed.append(self.unfill_item(location))
                count -= 1

        self.info("   Removed nonprog items: "+str(items_removed))
        return items_removed


    # Converts a progression list into a normalized Monte Carlo distribution
    def monte_carlo(self, progression_ls=[], start_items=[]):
        if not progression_ls:
            return []

        progression = progression_ls[:]

        items = self.list_typed_items(types=[1], shuffled_only=True)
        abilities = self.list_typed_items(types=[2], shuffled_only=True)
        orbs = self.list_typed_items(types=[5], shuffled_only=True)
        all_items = items + abilities + orbs
        sum_items = len(items)
        sum_abilities = len(abilities)
        sum_orbs = len(orbs)

        probability = []

        monte_carlo = []
        sum_prob = 0
        sum_edges = 0

        probabilities = []
        idx = 0
        while progression:
            current_prereq = progression.pop(0)
            prereqs = current_prereq[:]
            probability = 1.0
            i = 0
            j = 0
            k = 0
            while prereqs:
                item = prereqs.pop(0)
                if item in all_items:
                    if self.item_pool[item][1] == 1:
                        probability *= float(self.item_pool[item][0]) / float((sum_items - i))
                        i += 1
                    elif self.item_pool[item][1] == 2:
                        probability *= float(self.item_pool[item][0]) / float((sum_abilities - j))
                        j += 1
                    elif self.item_pool[item][1] == 5:
                        probability *= float(self.item_pool[item][0]) / float((sum_orbs - k))
                        k += 1
                    if item in self.required_items:
                        probability *= PROGRESS_ADJ[self.difficulty]
            probabilities.append([probability, idx])
            sum_prob += probability
            sum_edges += 1
            idx += 1

        prob_adj = 100.0 / sum_prob
        rolling_sum = 0.0
        for x in probabilities:
            x[0] = x[0] * prob_adj + rolling_sum
            rolling_sum = x[0]

        # print probabilities
        return probabilities

    # Returns a list of map lists, by boss
    def get_maps(self):
        maps = [[], [], [], [], [], [], []]
        for map in self.maps:
            if self.maps[map][0] >= 0 and (self.dungeon_shuffle == "None" or not self.maps[map][8]):    # Jumbo maps don't get rewards in dungeon shuffles
                boss = self.maps[map][1]
                maps[boss].append(map)
        maps.pop(0)    # Non-dungeon maps aren't included
        return maps

    # Randomize map-clearing rewards
    def map_rewards(self):
        maps = self.get_maps()
        for area in maps:
            random.shuffle(area)

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
        if self.statue_req == StatueReq.PLAYER_CHOICE.value:
            return self.random_fill([106]*6, locations)
        return self.random_fill([100, 101, 102, 103, 104, 105], locations)

    
    # Guarantee Freedan access to nodes that have a Freedan edge and no alternative non-Freedan edge.
    # Here we fix a subset of transformation DS nodes from which all Freedan edges are accessible.
    # The graph should be open and have fully-resolved DS data before calling this.
    def lock_dark_spaces(self):
        f_logic = {e: [self.logic[e][1], self.logic[e][2]] for e in self.logic if self.logic[e][0] >-1 and self.logic[e][3]}
        nf_logic = {e: [self.logic[e][1], self.logic[e][2]] for e in self.logic if self.logic[e][0] >-1 and not self.logic[e][3]}
        if self.logic_mode == "Completable":
            # Completable logic requires F access to F edges even if there's an alternative non-F path.
            freedan_required_nodes = set(edef[0] for edef in f_logic.values())
        else:
            freedan_required_nodes = set(edef[0] for edef in f_logic.values() if not any(edef[0] == altdef[0] and (edef[1] == altdef[1] or edef[1] in self.graph[altdef[1]][1]) for altdef in nf_logic.values()))
        f_nodes_under_ds_node = {}
        for node in freedan_required_nodes:
            if not self.check_ds_access(start_node=node, need_freedan=True, do_recurse=False, visited=[]):
                self.error("Freedan can't reach "+str(node)+" "+str(self.graph[node]))
                return False
            else:
                for ds_node in self.graph[node][9]:
                    if ds_node not in f_nodes_under_ds_node:
                        f_nodes_under_ds_node[ds_node] = set()
                    f_nodes_under_ds_node[ds_node].add(node)
        # The Pyramid upper foyer is (currently) special and doesn't need to be handled
        pyramid_upper_nodes = [n for n in self.graph if self.graph[n][3][3] in [0xcc,0xcd,0xdd] and not any(n == locdata[0] for locdata in self.item_locations.values() if locdata[1] == 2)]
        for node in pyramid_upper_nodes:
            if node in f_nodes_under_ds_node:
                del f_nodes_under_ds_node[node]
            if node in freedan_required_nodes:
                freedan_required_nodes.remove(node)
        # Completable logic sets certain specific DSes as txform DSes
        if self.logic_mode == "Completable":
            for loc in self.completable_guaranteed_freedan_locations:
                self.item_locations[loc][2] = True
                if self.item_locations[loc][3]:
                    self.unfill_item(loc)
                self.item_locations[loc][7] = 0
            completable_txform_nodes = [self.item_locations[loc][0] for loc in self.completable_guaranteed_freedan_locations]
            for node in completable_txform_nodes:
                if node in f_nodes_under_ds_node:
                    covered_nodes = f_nodes_under_ds_node[node]
                    freedan_required_nodes = freedan_required_nodes.difference(f_nodes_under_ds_node[node])
                    del f_nodes_under_ds_node[node]
        # Lock the DS that covers the greatest number of remaining F nodes, breaking ties randomly
        while freedan_required_nodes and f_nodes_under_ds_node:
            lock_node = max(f_nodes_under_ds_node, key=lambda ds_node : len(freedan_required_nodes.intersection(f_nodes_under_ds_node[ds_node]))+random.random() )
            lock_loc = next(loc for loc in self.item_locations if self.item_locations[loc][0] == lock_node)
            self.item_locations[lock_loc][2] = True   # Mark the DS as occupied, remove it from the pool, and clear its contents if any
            if self.item_locations[lock_loc][3]:
                self.unfill_item(lock_loc)
            self.item_locations[lock_loc][7] = 0
            self.info(" -Locked: "+str(self.item_locations[lock_loc][6]))
            freedan_required_nodes = freedan_required_nodes.difference(f_nodes_under_ds_node[lock_node])
            del f_nodes_under_ds_node[lock_node]
        if freedan_required_nodes:
            return False
        return True



    # If the vanilla exit is two-way (i.e. has a paired exit), returns the paired exit.
    # Otherwise, returns 0 to indicate the exit is one-way or doesn't exist.
    def is_exit_coupled(self,exit):
        if exit not in self.exits:
            return 0
        if self.exits[exit][0]:
            sister_exit = self.exits[exit][0]
            if self.exits[sister_exit][0] == exit:
                return sister_exit
            else:
                self.warn("Exits linked incorrectly "+str(exit)+" "+str(sister_exit))
                return sister_exit
        return 0


    # Determine an exit's direction (e.g. outside to inside).
    # An exit from a "roof" (type-3 node) always counts as going outside,
    # to discourage attaching dead-end interior rooms to roof exits.
    def exit_direction(self,exit):
        if exit not in self.exits:
            return False
        origin = self.exits[exit][3]
        dest = self.exits[exit][4]
        if self.graph[origin][2] == 2:
            o_type = 2
        else:
            o_type = 1
        if self.graph[origin][3] == 3:
            d_type = 1
        else:
            if self.graph[dest][2] == 2:
                d_type = 2
            else:
                d_type = 1
        if o_type == 2 and d_type == 2:
            return (1,1)
        else:
            return d_type


    # Link one exit to another, making origin_exit act like dest_exit; that is,
    # replace the transition data of origin_exit with the vanilla transition data of dest_exit.
    def link_exits(self, origin_exit, dest_exit, check_connections=True, update_graph=True):
        if origin_exit not in self.exits:
            self.error("Invalid origin (link) "+str(origin_exit))
            return False
        if dest_exit not in self.exits:
            self.error("Invalid destination (link) "+str(dest_exit))
            return False
        if self.exits[origin_exit][1] > 0 and origin_exit > 21:
            self.error("Origin already linked: "+str(origin_exit)+" "+str(self.exits[origin_exit]))
            return False
        if self.exits[dest_exit][2] > 0 and dest_exit > 21:
            self.error("Destination already linked: "+str(dest_exit)+" "+str(self.exits[dest_exit]))
            return False
        self.exits[origin_exit][1] = dest_exit
        self.exits[dest_exit][2] = origin_exit
        self.exit_log.append([origin_exit,dest_exit])
        self.info("   Linked "+str(origin_exit)+" "+str(self.exits[origin_exit][10])+" - "+str(dest_exit)+" "+str(self.exits[dest_exit][10]))
        if update_graph and self.exits[origin_exit][5]:
            origin = self.exits[origin_exit][3]
            dest = self.exits[dest_exit][4]
            if dest not in self.graph[origin][1]:
                self.graph[origin][1].append(dest)
            self.new_connection(origin,dest)
            if self.is_accessible(origin) and not self.is_accessible(dest):
                self.traverse([dest],test=False)
        if (origin_exit <= 21 or self.entrance_shuffle != "Uncoupled") and check_connections and self.is_exit_coupled(origin_exit) and self.is_exit_coupled(dest_exit):
            new_origin = self.exits[dest_exit][0]
            new_dest = self.exits[origin_exit][0]
            if new_origin <= 21:  # Boss exits
                if self.exits[new_origin][5]:
                    self.link_exits(new_origin, new_dest, False, update_graph)
            else:
                if self.exits[new_origin][1] != -1 or self.exits[new_dest][2] != -1:
                    self.error("Return exit already linked: "+str(new_origin)+" "+str(new_dest))
                    return False
                else:
                    self.link_exits(new_origin, new_dest, False, update_graph)
        return True


    # Unlinks two previously linked exits
    def unlink_exits(self, origin_exit, dest_exit, check_connections=True, update_graph=True):
        if origin_exit not in self.exits:
            self.error("Invalid origin (unlink) "+str(origin_exit))
            return False
        if dest_exit and dest_exit not in self.exits:
            self.error("Invalid destination (unlink) "+str(dest_exit))
            return False
        if dest_exit and (self.exits[origin_exit][1] != dest_exit or self.exits[dest_exit][2] != origin_exit):
            self.warn("Attempted to unlink exits that are not correctly linked: "+str(origin_exit)+" "+str(dest_exit))
        if not dest_exit:
            dest_exit = origin_exit
        self.exits[origin_exit][1] = -1
        self.exits[dest_exit][2] = -1
        for x in self.exit_log:
            if x[0] == origin_exit:
                self.exit_log.remove(x)
        self.info("   Unlinked "+str(origin_exit)+" "+str(self.exits[origin_exit][10])+" - "+str(dest_exit)+" "+str(self.exits[dest_exit][10]))
        if update_graph and self.exits[origin_exit][5]:
            origin = self.exits[origin_exit][3]
            dest = self.exits[dest_exit][4]
            if dest in self.graph[origin][1]:
                self.graph[origin][1].remove(dest)
            if dest in self.graph[origin][10]:
                self.graph[origin][10].remove(dest)
        if self.entrance_shuffle != "Uncoupled" and check_connections and self.is_exit_coupled(origin_exit) and self.is_exit_coupled(dest_exit):
            new_origin = self.exits[dest_exit][0]
            new_dest = self.exits[origin_exit][0]
            self.unlink_exits(new_origin, new_dest, False, update_graph)
        if check_connections and update_graph:
            self.update_graph(True,True,True)
        return True


    # Bidirectional exit link. Make exit1 send the player to where exit2 is, and vice versa.
    def join_exits(self, exit1, exit2):
        return (self.link_exits(exit1, self.exits[exit2][0], False, False) and self.link_exits(exit2, self.exits[exit1][0], False, False))

    # Unlink both sides of a bidirectional exit.
    def unjoin_exit(self, exit):
        linked_exit = self.exits[exit][1]
        joined_exit = self.exits[self.exits[exit][0]][2]
        joined_linked_exit = self.exits[joined_exit][1]
        return (self.unlink_exits(exit, linked_exit, False, False) and self.unlink_exits(joined_exit, joined_linked_exit, False, False))

    # Append/insert bidirectional exits. Joins base_exit to new_exit1.
    # If base_exit was already joined, its former partner is joined to new_exit2.
    def insert_exit(self, base_exit, new_exit1, new_exit2 = 0):
        if any(x not in self.exits for x in [base_exit, new_exit1]) or (new_exit2 > 0 and new_exit2 not in self.exits):
            self.error("Can't insert nonexistent exit, one of: "+str(base_exit)+" "+str(new_exit1)+" "+str(new_exit2))
            return False
        if self.exits[new_exit1][1] > 0:
            self.error("Can't insert exit that's already joined: "+str(new_exit1))
            return False
        if self.exits[base_exit][1] < 0:   # Append.
            return self.join_exits(base_exit, new_exit1)
        else:   # Insert.
            if (new_exit2 == 0) or (self.exits[new_exit2][1] > 0):
                self.error("Can't insert nonexistent or joined exit: "+str(new_exit2))
                return False
            joined_exit = self.exits[self.exits[base_exit][0]][2]
            self.unjoin_exit(base_exit)
            return (self.join_exits(base_exit, new_exit1) and self.join_exits(joined_exit, new_exit2))


    def print_exit_log(self,exit_log=[]):
        for origin,dest in exit_log:
            self.info(str(self.exits[origin][10])+" - "+str(self.exits[dest][10]))


    # Returns lists of origin exits and destination exits that open up new nodes
    def get_open_exits(self,check_progression=False):
        open_exits = [[],[]]
        for node in self.graph:
            if not check_progression or self.is_accessible(node):
                for exit in self.graph[node][14]:
                    if self.exits[exit][1] == -1:
                        open_exits[0].append(exit)
            if not check_progression or not self.is_accessible(node):
                for exit in self.graph[node][15]:
                    if self.exits[exit][2] == -1:
                        open_exits[1].append(exit)
        return open_exits


    # Takes a list of origin and destination exits, returns a suitable match
    def find_exit(self,origin_exits_ls=[],dest_exits_ls=[],check_direction=False,check_progression=False,check_ds_access=False,test=False):
        if not origin_exits_ls:
            self.info("  No more accessible exits available")
            return False
        elif not dest_exits_ls:
            self.info("  No destination exits available from "+str(origin_exits_ls))
            return False

        origin_exits = origin_exits_ls[:]
        dest_exits = dest_exits_ls[:]

        done = False
        quarantine_o = []
        while not done and origin_exits:
            origin_exit = 0
            while not origin_exit and origin_exits:
                origin_exit = origin_exits.pop(0)
                origin = self.exits[origin_exit][3]
                sister_exit = self.exits[origin_exit][0]
                if self.exits[origin_exit][1] != -1 or (check_progression and not self.is_accessible(origin)):
                    origin_exit = 0

            if not origin_exit:
                self.info("  No more accessible exits available")
                return False

            direction = self.exit_direction(origin_exit)
            dest_exit = 0
            quarantine_d = []
            while not done and dest_exits:
                try_link = False
                while not dest_exit and dest_exits:
                    dest_exit = dest_exits.pop(0)
                    dest = self.exits[dest_exit][4]
                    if self.exits[dest_exit][2] != -1 or not self.check_dungeon(origin_exit, dest_exit) or (check_progression and self.is_accessible(dest)):
                        dest_exit = 0

                if not dest_exit:
                    self.info("  No destination exits available from "+str(origin_exit))
                    return False

                direction_new = self.exit_direction(dest_exit)
                if dest_exit != sister_exit and (not check_direction or direction_new == direction):
                    try_link = True
                    if self.link_exits(origin_exit,dest_exit,self.entrance_shuffle != "Uncoupled",True):
                        if True: # or not check_ds_access or self.check_ds_access(dest):
                            done = True
                            origin_final = origin_exit
                            dest_final = dest_exit

                if not done:
                    quarantine_d.append(dest_exit)
                    if try_link:
                        self.unlink_exits(origin_exit,dest_exit,True,True)
                    dest_exit = 0


            if not done:
                quarantine_o.append(origin_exit)
                dest_exits += quarantine_d
                quarantine_d.clear()

        if not done:
            self.info("No suitable links could be found - in quarantine: "+str(quarantine_o))
            return False

        # Clean up O/D lists
        origin_exits += quarantine_o
        for exit in origin_exits:
            if self.exits[exit][1] != -1:
                origin_exits.remove(exit)
        for exit in dest_exits:
            if self.exits[exit][2] != -1:
                dest_exits.remove(exit)

        return [origin_final,dest_final,origin_exits,dest_exits]


    # Check if you can access one node from another
    def check_access(self,origin=-1,dest=-1,check_mutual=False):
        if origin not in self.graph or dest not in self.graph:
            return False

        if self.graph[origin][7] or self.graph[dest][7]:
            return False

        success =  False
        if origin == dest or dest in self.graph[origin][10]:
            success = True

        to_visit = self.graph[origin][10][:]
        visited = [origin]
        while not success and to_visit:
            node = to_visit.pop(0)
            visited.append(node)
            if not self.graph[node][7] and dest in self.graph[node][10]:
                success = True
            else:
                for x in self.graph[node][10]:
                    if x not in to_visit+visited:
                        to_visit.append(x)

        if not check_mutual or not success:
            return success

        return self.check_access(dest,origin,False)

    # Build islands, i.e. groups of nodes accessible from each other, generally assuming all progression.
    # With require_mutual, island nodes are mutually accessible, with no one-way drops or similar.
    # Examples: Freejia-Exterior; north half of Sky Garden SW Top.
    def build_islands(self, require_mutual=True):
        islands = [[] for _ in range(13)]
        visited = []
        start_island = []
        for node in self.graph:
            if node not in visited and self.graph[node][2]:
                to_visit = [node]
                new_nodes = []
                origin_exits = []
                dest_exits = []
                origin_logic = []
                dest_logic = []
                is_start = False
                dungeon = 9999
                while to_visit:
                    x = to_visit.pop(0)
                    visited.append(x)
                    new_nodes.append(x)
                    if 0 in self.graph[x][8]:
                        is_start = True
                    for exit in self.graph[x][14]:
                        if self.exits[exit][1] == -1:
                            origin_exits.append(exit)
                            dungeon = min(dungeon,self.exit_dungeon(exit))
                    for exit in self.graph[x][15]:
                        if self.exits[exit][2] == -1:
                            dest_exits.append(exit)
                    for edge in self.graph[x][12]:
                        if self.logic[edge][0] == 0:
                            origin_logic.append(edge)
                    for edge in self.graph[x][13]:
                        if self.logic[edge][0] == 0:
                            dest_logic.append(edge)
                    for y in self.graph[x][10]:
                        if y not in visited+to_visit and self.check_access(x,y,require_mutual):
                            to_visit.append(y)
                    if not require_mutual:
                        for y in self.graph[x][8]:
                            if y not in visited+to_visit and self.check_access(y,x,False):
                                to_visit.append(y)
                island = [new_nodes,origin_exits,dest_exits,origin_logic,dest_logic]
                if is_start:
                    start_island = island
                if dungeon == 9999 or self.dungeon_shuffle == "None":
                    dungeon = 0
                islands[dungeon].append(island)

        return [start_island,islands]


    def exit_dungeon(self,exit=-1):
        if exit not in self.exits:
            self.error("Exit not in database")
            return -1
        if self.dungeon_shuffle == "Chaos":
            return 1
        return self.exits[exit][8]

    def check_dungeon(self,exit1=-1,exit2=-1):
        if exit1 not in self.exits or exit2 not in self.exits:
            self.error("Exit not in database")
            return -1
        if self.exit_dungeon(exit1) != self.exit_dungeon(exit2):
            return False
        if self.dungeon_shuffle != "Chaos":   # Only link Mu rooms of the same water level
            origin1 = self.exits[exit1][3]
            origin2 = self.exits[exit2][3]
            dest1 = self.exits[exit1][4]
            dest2 = self.exits[exit2][4]
            if self.graph[origin1][3][2] != self.graph[origin2][3][2] or self.graph[dest1][3][2] != self.graph[dest2][3][2]:
                return False
        return True

    # Returns -1 if the exit shouldn't be shuffled.
    # Otherwise returns the (arbitrary) ID of the pool it should be shuffled with, based on self.exits:
    # ER, no DS:  PoolType=1; one pool
    # ER and DSB: PoolType>0; pool all having PoolType=1, then pool PoolType>1 by DungeonID
    # ER and DSC: PoolType>0; pool by PoolType
    # DSB, no ER: PoolType>1, DungeonID>0; pool by DungeonID
    # DSC, no ER: PoolType>1, DungeonID>0; pool by PoolType
    def get_exit_pool(self, exit):
        if (exit not in self.exits) or (self.entrance_shuffle == "None" and self.dungeon_shuffle == "None"):
            return -1
        dungeon = self.exits[exit][8]
        pooltype = self.exits[exit][9]
        ER = (self.entrance_shuffle != "None")
        DSB = (self.dungeon_shuffle == "Basic")
        DSC = (self.dungeon_shuffle == "Chaos")
        if ER and (pooltype == 1):
            return 1
        if DSB and (pooltype > 1) and (dungeon > 0):
            return 100+dungeon
        if DSC and (pooltype > 1) and (dungeon > 0):
            return pooltype
        return -1
    
    
    def shuffle_chaos_dungeon(self):
        # Temporarily add Freedan edges without Freedan for dungeon construction
        freedan_edges = [edge for edge in self.logic if self.logic[edge][3]]
        artificial_freedan_edges = []
        for edge in freedan_edges:
            new_edge_id = 1+max(self.logic)
            self.logic[new_edge_id] = [ self.logic[edge][0], self.logic[edge][1], self.logic[edge][2], False, self.logic[edge][4], False ]
            artificial_freedan_edges.append(new_edge_id)
        
        # Build dungeon node islands for skeleton assuming all items and game states
        self.reset_progress(True)
        self.items_collected = [800]+self.list_typed_items(types=[1, 2, 4, 5], shuffled_only=False, incl_placed=True)
        for inca_orb in [707,708,709]:   # Due to awkward orb placement, it's best to treat Inca's exterior as three corridors
            self.items_collected.remove(inca_orb)
        self.update_graph(True,True,True)
        self.unsolve()
        island_result = self.build_islands()
        islands = island_result[1].pop(1) # pop(1) = list of all islands assigned to the chaos dungeon
        # An island is: [ [nodes], [origin_exits], [dest_exits], [origin_logic], [dest_logic] ].
        # For dungeon construction, we want islands grouped by count of dungeon-internal exits.
        dungeon_exit_keys = [exit for exit in self.exits if self.exits[exit][9] == 3]
        deadend_islands = []
        corridor_islands = []
        branch_islands = []
        foyer_islands = []
        random.shuffle(islands)
        for island in islands:
            internal_exits = [exit for exit in island[1] if self.exits[exit][9] == 2 and self.is_exit_coupled(exit)]
            if not internal_exits:
                continue
            random.shuffle(internal_exits)
            for exit in internal_exits:
                dungeon_exit_keys.append(exit)
            subisland = [[x for x in island[0]], internal_exits, [] ]   # [nodes, unmapped-exits, mapped-exits]
            if len(subisland[1]) == 1:
                deadend_islands.append( subisland )
            elif len(subisland[1]) == 2:
                corridor_islands.append( subisland )
            else:
                if any(region in subisland[0] for region in [170,212,413]):   # SkGn, Mu, and Pymd have branching foyers
                    foyer_islands.append( subisland )
                else:
                    branch_islands.append( subisland )
        # At this point a "deadend" may be the bottom or top of a ledge, or behind or in front of a button.
        # Such one-way exits are functionally part of a corridor or branch, except that the low/back exit
        # can't be appended to an opening to grow the dungeon.
        # So, we coalesce the islands by one-way accessibility, keeping track of the "blocked" exits.
        blocked_exits = []
        merged_islands_for_deletion = []
        all_islands = deadend_islands+corridor_islands+foyer_islands+branch_islands
        for lower_i in deadend_islands:
            lower_n = lower_i[0][0]
            lower_map = self.graph[lower_n][3][3]   # One-way access must be within the same map
            upper_i = next((i for i in all_islands if i != lower_i and any((lower_map == self.graph[upper_n][3][3]) and self.check_access(upper_n,lower_n,False) for upper_n in i[0])), [])
            if upper_i:   # Merge the lower island into the upper one, and record the lower exit
                upper_i[0].append(lower_i[0][0])
                upper_i[1].append(lower_i[1][0])
                blocked_exits.append(lower_i[1][0])
                merged_islands_for_deletion.append(lower_i)
        for island in merged_islands_for_deletion:   # Removed merged deadends
            deadend_islands.remove(island)
        for exit in blocked_exits:   # If any islands grew, move them to the correct list
            grown_island = next(i for i in deadend_islands+corridor_islands+branch_islands if exit in i[1])
            if grown_island in deadend_islands and len(grown_island[1]) > 1:
                deadend_islands.remove(grown_island)
                if len(grown_island[1]) == 2:
                    corridor_islands.append(grown_island)
                else:
                    branch_islands.append(grown_island)
            elif grown_island in corridor_islands and len(grown_island[1]) > 2:
                corridor_islands.remove(grown_island)
                branch_islands.append(grown_island)
        # Various special exits that aren't detected programmatically: 126 behind D.Block, 234 Mine behind fences,
        # 293/295 SkGn SE Top behind robot / SW Top behind N pegs, 534/538 Kress behind drops 1/2.
        blocked_exits.extend([126, 234, 293, 295, 534, 538])
        # Promote a random branch to a foyer for dungeons that don't have a branching foyer
        for exit in [x for x in self.exits if self.exits[x][9] == 3]:
            new_foyer_island = branch_islands.pop()
            new_entr = next(x for x in new_foyer_island[1] if x not in blocked_exits)
            new_foyer_island[1].remove(new_entr)
            new_foyer_island[2].append(new_entr)
            self.join_exits(exit, new_entr)
            foyer_islands.append(new_foyer_island)
        # The foyers are our nascent (as-yet-unconnected) skeleton
        skeleton = foyer_islands
        # Append one-way corridor islands to the skeleton, spreading them out
        #oneway_corridor_islands = [i for i in corridor_islands if any(x in blocked_exits for x in i[1])]
        #this_base_island_idx = -1
        #while oneway_corridor_islands:
        #    this_base_island_idx += 1
        #    while (not skeleton[this_base_island_idx][1]) or (this_base_island_idx == len(skeleton)):
        #        this_base_island_idx = (this_base_island_idx + 1) % len(skeleton)
        #    corridor = oneway_corridor_islands.pop()
        #    corridor_islands.remove(corridor)
        #    upper_exit = next(exit in corridor[1] for exit not in blocked_exits)
        #    corridor[1].remove(upper_exit)
        #    corridor[2].append(upper_exit)
        #    base_exit = skeleton[this_base_island_idx][1].pop()
        #    skeleton[this_base_island_idx][2].append(base_exit)
        #    self.join_exits(upper_exit, base_exit)
        #    skeleton.append(corridor)
        # Append all branches and one-way corridors to the skeleton, to make all openings accessible;
        # then append deadends to all openings
        oneway_corridor_islands = [i for i in corridor_islands if any(x in blocked_exits for x in i[1])]
        while branch_islands+oneway_corridor_islands+deadend_islands and any(len(island[1]) > 0 for island in skeleton):
            if branch_islands+oneway_corridor_islands:
                if (not oneway_corridor_islands) or (branch_islands and (random.randint(0,1) == 1)):
                    new_island = branch_islands.pop()
                else:
                    new_island = oneway_corridor_islands.pop()
                    corridor_islands.remove(new_island)
            else:   # Deadends are the last type appended
                new_island = deadend_islands.pop()
            new_exit = next(exit for exit in new_island[1] if exit not in blocked_exits)
            new_island[1].remove(new_exit)
            new_island[2].append(new_exit)
            base_island = next(island for island in skeleton if len(island[1]) > 0)
            skeleton.remove(base_island)
            base_exit = base_island[1].pop()
            base_island[2].append(base_exit)
            skeleton.append(new_island)
            skeleton.append(base_island)
            self.join_exits(base_exit, new_exit)
        # Calculate how many loops we need to create
        num_deadends = len(deadend_islands)
        num_openings = 0
        for island in skeleton:
            num_openings += len(island[1])
        if (num_deadends - num_openings) % 2 == 1:
            # Discard one deadend and one Nothing to match parity of deadends to openings
            # (I don't think this state is possible in IOG if the above code works)
            if any(442 in x[0] for x in skeleton):
                discard_island = next(x for x in skeleton if 442 in x[0])
                skeleton.remove(discard_island)
                joined_exit = self.exits[self.exits[641][0]][2]
                joined_island = next(x for x in skeleton if joined_exit in x[2])
                joined_island[2].remove(joined_exit)
                joined_island[1].append(joined_exit)
                self.unjoin_exit(641)
                num_openings += 1
            else:
                discard_island = next(x for x in deadend_islands if 442 in x[0])
                deadend_islands.remove(discard_island)
                num_deadends -= 1
            self.item_pool[0][0] -= 1
            self.item_locations[132][2] = True
            self.item_locations[132][3] = 0
            self.item_locations[132][7] = 0
            self.optional_nodes.append(442)
            self.link_exits(641, self.exits[641][0], False, False)
        if num_deadends > num_openings:
            self.error("Not enough dungeon exits: need "+str(num_deadends-num_openings)+" more")
            ## Insert pairs of deadends into internal skeleton exits.
            #int_skel_exits = [x for x in dungeon_exit_keys if self.exits[x][1] > 0 and any(x in island[2] for island in skeleton) and self.exits[self.exits[self.exits[x][0]][2]][9] == 2]
            #random.shuffle(int_skel_exits)
            #if (num_deadends - num_openings) > len(int_skel_exits):
            #    self.error("Too many dungeon deadends to build a connected graph")
            #    return False
            #remaining_inserts = (num_deadends - num_openings) / 2
            #while remaining_inserts:
            #    new_island1 = deadend_islands.pop()
            #    new_island2 = deadend_islands.pop()
            #    new_exit1 = new_island1[1].pop()
            #    new_exit2 = new_island2[1].pop()
            #    new_island1[2].append(new_exit1)
            #    new_island2[2].append(new_exit2)
            #    base_exit = int_skel_exits.pop()
            #    int_skel_exits.remove(self.exits[self.exits[base_exit][0]][2])
            #    self.insert_exit(base_exit, new_exit1, new_exit2)
            #    skeleton.append(new_island1)
            #    skeleton.append(new_island2)
            #    remaining_inserts -= 1
        elif num_deadends < num_openings:
            # Create loops by connecting openings with corridors
            remaining_inserts = (num_openings - num_deadends) / 2
            random.shuffle(skeleton)
            while remaining_inserts:
                loop_island1 = next(x for x in skeleton if len(x[1]) > 0)
                skeleton.remove(loop_island1)
                loop_island2 = next((x for x in skeleton if len(x[1]) > 0),loop_island1)
                # Allow for the case where one island remains and has 2 open exits
                if loop_island2 != loop_island1:
                    skeleton.remove(loop_island2)
                corridor_island = corridor_islands.pop()
                loop_exit1 = loop_island1[1].pop()
                loop_exit2 = loop_island2[1].pop()
                corridor_exit1 = corridor_island[1].pop()
                corridor_exit2 = corridor_island[1].pop()
                self.join_exits(loop_exit1, corridor_exit1)
                self.join_exits(loop_exit2, corridor_exit2)
                loop_island1[2].append(loop_exit1)
                loop_island2[2].append(loop_exit2)
                skeleton.append(loop_island1)
                if loop_island2 != loop_island1:
                    skeleton.append(loop_island2)
                skeleton.append(corridor_island)
                remaining_inserts -= 1
        ## Join remaining deadends to remaining openings
        #random.shuffle(skeleton)
        #while deadend_islands:
        #    new_island = deadend_islands.pop()
        #    new_exit = new_island[1].pop()
        #    new_island[2].append(new_exit)
        #    opening_island = next(x for x in skeleton if len(x[1]) > 0)
        #    skeleton.remove(opening_island)
        #    opening_exit = opening_island[1].pop()
        #    opening_island[2].append(opening_exit)
        #    self.join_exits(new_exit, opening_exit)
        #    skeleton.append(new_island)
        #    skeleton.append(opening_island)
        # Finally, insert corridors randomly
        random.shuffle(skeleton)
        random.shuffle(dungeon_exit_keys)
        while corridor_islands:
            new_island = corridor_islands.pop()
            new_exit1 = new_island[1].pop()
            new_exit2 = new_island[1].pop()
            new_island[2].append(new_exit1)
            new_island[2].append(new_exit2)
            new_is_underwater = any(self.graph[node][3][2] > 0 for node in new_island[0])
            base_water_level_okay = False
            while not base_water_level_okay:
                base_exit = next(x for x in dungeon_exit_keys if self.exits[x][1] > 0 and any(x in island[2] for island in skeleton))
                base_island = next(island for island in skeleton if base_exit in island[2])
                base_can_be_underwater = all(self.graph[node][3][2] > -1 for node in base_island[0])
                if not new_is_underwater or base_can_be_underwater:
                    base_water_level_okay = True
                else:
                    random.shuffle(dungeon_exit_keys)
            self.insert_exit(base_exit, new_exit1, new_exit2)
            skeleton.append(new_island)
        # Clean up the artificial Freedan edges and DSC items
        self.delete_objects(items=[800],locs=[],nodes=[],edges=artificial_freedan_edges,exits=[],with_close=True)

    # Entrance randomizer
    def shuffle_exits(self):
        # Map passages and all fixed exits to graph.
        one_way_exits = []
        for x in self.exits:
            if self.exits[x][1] < 0:
                if not self.is_exit_coupled(x):
                    one_way_exits.append(x)
                self.graph[self.exits[x][3]][14].append(x)
                self.graph[self.exits[x][4]][15].append(x)

        # Set aside Jeweler's final exit in RJH seeds
        if self.goal == "Red Jewel Hunt":
            self.link_exits(720, 720, False)
            self.link_exits(721, 721, False)

        # Special case for Slider exits in Angel Dungeon
        if self.dungeon_shuffle != "None":
            if random.randint(0,1):
                self.link_exits(408,414,False)
                self.link_exits(409,415,False)
                self.link_exits(414,408,False)
                self.link_exits(415,409,False)
            else:
                self.link_exits(408,408,False)
                self.link_exits(409,409,False)
                self.link_exits(414,414,False)
                self.link_exits(415,415,False)

        # Coupled Dungeon Chaos uses a special algorithm to build the dungeon
        if self.dungeon_shuffle == "Chaos" and self.entrance_shuffle != "Uncoupled":
            # Link Pyramid room-pairs as in vanilla, reducing Pymd corridor count from 13 to 6.
            dc_exits_within_pyramid_rooms = [638, 644, 650, 656, 658, 664, 670]
            for exitnum in dc_exits_within_pyramid_rooms:
                self.join_exits(exitnum, self.exits[exitnum][0])
            self.shuffle_chaos_dungeon()
            
        # If using a coupled shuffle, map one-way exits to one-way dests
        exit_log = []
        if self.entrance_shuffle != "Uncoupled":
            one_way_dest = one_way_exits[:]
            random.shuffle(one_way_dest)
            while one_way_exits:
                o_exit = one_way_exits.pop()
                found_oneway = False
                while not found_oneway:
                    d_exit = one_way_dest.pop()
                    if self.check_dungeon(o_exit, d_exit):
                        self.link_exits(o_exit, d_exit, False)
                        exit_log.append([o_exit,d_exit])
                        found_oneway = True
                    else:
                        one_way_dest.append(d_exit)
                        random.shuffle(one_way_dest)
            self.info( "One-way exits mapped")

        # Assume all items and abilities
        self.info("Beginning non-dungeon exit shuffle...")
        self.reset_progress(True)
        self.items_collected = self.list_typed_items(types=[1, 2, 4, 5], shuffled_only=False, incl_placed=True)
        self.update_graph(True,True,True)

        # Build world skeleton with islands
        self.unsolve()
        island_result = self.build_islands()
        islands = island_result[1].pop(0) # pop(0) = all non-dungeon islands

        traverse_result = self.traverse()
        visited = traverse_result[0]
        origin_exits = []
        for node in visited:
            origin_exits += self.graph[node][14]

        i = 0
        for x in islands:
            i += 1
            self.info("Initial island "+str(i)+" ("+str(x[1])+","+str(x[2])+"):")
            for y in x[0]:
                self.info(" - "+self.graph[y][5])
        self.info(" Joining initial islands...")

        check_direction = True
        check_progression = True
        quarantine = []
        while islands:
            random.shuffle(islands)
            island = islands.pop(0)
            nodes_new = island[0]
            origin_exits_new = island[1]
            dest_exits_new = island[2]

            if not dest_exits_new or not origin_exits_new or self.is_accessible(nodes_new[0]):
                pass
                #self.info("  NOT ELIGIBLE")
            else:
                if (check_progression and not origin_exits_new) or (self.entrance_shuffle != "Uncoupled" and (len(origin_exits_new) < 2 or len(dest_exits_new) < 2)):
                    quarantine.append(island)
                    #self.info("  REJECTED")
                else:
                    random.shuffle(origin_exits)
                    random.shuffle(dest_exits_new)

                    result = self.find_exit(origin_exits,dest_exits_new,check_direction,True)
                    if not result:
                        #self.info("  Quarantined",island)
                        quarantine.append(island)
                    else:
                        self.info("NEW ISLAND:")
                        for y in nodes_new:
                            self.info(" - "+str(self.graph[y][5]))
                        traverse_result = self.traverse(island[0])
                        visited += traverse_result[0]
                        progression_result = self.get_open_exits()
                        origin_exits = progression_result[0]
                        check_direction = True

            if not islands:
                if check_direction:
                    check_direction = False
                    islands += quarantine
                    quarantine.clear()
                elif check_progression:
                    check_progression = False
                    check_direction = True
                    islands += quarantine
                    quarantine.clear()
            if not islands and island_result[1]:
                islands = island_result[1].pop(0)
                check_direction = True
                check_progression = True
                quarantine = []

        self.info(" Island construction complete")

        # Check island Dark Space access, map exits accordingly
        self.reset_progress()
        self.update_graph(True,True,True)

        island_result = self.build_islands()
        islands = island_result[1].pop(0)

        islands_no_ds = []
        ds_check_visited = []
        for island in islands:
            if self.is_accessible(island[0][0]) and not self.check_ds_access(island[0][0], False, True, ds_check_visited):
                islands_no_ds.append(island)

        if islands_no_ds:
            self.info("Islands with no DS access:")
            i = 0
            for x in islands_no_ds:
                i += 1
                self.info("Island "+str(x))
                for y in x[0]:
                    self.info("- "+str(self.graph[y][5]))

            dest_exits_ds = []
            for node in self.graph:
                if node not in visited and self.check_ds_access(node, False, True, ds_check_visited):
                    for exit in self.graph[node][15]:
                        if self.exits[exit][2] == -1:
                            dest_exits_ds.append(exit)

            while islands_no_ds:
                island = islands_no_ds.pop(0)
                result = self.find_exit(island[1],dest_exits_ds,check_direction)
                if not result:
                    self.error("Could not find Dark Space access")
                    return False
                else:
                    dest_exits_ds = result[3]

        self.info(" Dark Space access check successful")

        # Clean up the rest of the exits
        self.reset_progress()
        self.update_graph(True,True,True)
        self.traverse()

        check_progression = True
        check_direction = True
        while origin_exits:
            progression_result = self.get_open_exits(check_progression)
            origin_exits = progression_result[0]
            dest_exits = progression_result[1]
            random.shuffle(origin_exits)
            random.shuffle(dest_exits)
            if origin_exits:
                result = self.find_exit(origin_exits,dest_exits,check_direction,check_progression,True,False)
                if result:
                    origin_exit = result[0]
                    dest_exit = result[1]
                    dest = self.exits[dest_exit][4]
                    self.traverse([dest])
                elif check_direction:
                    check_direction = False
                elif check_progression:
                    check_progression = False
                    check_direction = True
                    self.info("  Finished mapping progression exits")
                else:
                    self.warn("This shouldn't happen")
                    origin_exits = []

        # Randomly link any leftover exits
        origin_exits = []
        dest_exits = []
        for exit in self.exits:
            if self.exits[exit][1] == -1:
                self.info(" Unmapped exit: "+str(exit)+" "+str(self.exits[exit]))
                origin_exits.append(exit)
            if self.exits[exit][2] == -1:
                self.info(" No exit mapped to: "+str(exit)+" "+str(self.exits[exit]))
                dest_exits.append(exit)
            if origin_exits:
                random.shuffle(origin_exits)
            if dest_exits:
                random.shuffle(dest_exits)

        while origin_exits:
            origin_exit = origin_exits.pop(0)
            if not dest_exits:
                self.error("Entrance rando failed: no remaining exits to map to")
                return False
            candidate_dest_exit_idx = 0
            fallback_dest_exit_idx = -1
            while candidate_dest_exit_idx < len(dest_exits) - 1:
                candidate_dest_exit = dest_exits[candidate_dest_exit_idx]
                # Prefer mapping to an exit other than itself in the same dungeon.
                if self.check_dungeon(origin_exit, candidate_dest_exit):
                    if candidate_dest_exit == self.exits[origin_exit][0]:
                        fallback_dest_exit_idx = candidate_dest_exit_idx
                    else:    # If we get here, candidate_dest_exit_idx meets both criteria, so use it.
                        fallback_dest_exit_idx = -1
                        break
                candidate_dest_exit_idx += 1
            if fallback_dest_exit_idx > -1:
                dest_exit = dest_exits.pop(fallback_dest_exit_idx)
            else:
                dest_exit = dest_exits.pop(candidate_dest_exit_idx)
            self.link_exits(origin_exit,dest_exit,False)
            if self.entrance_shuffle != "Uncoupled" and origin_exit != self.exits[dest_exit][0]:  # Map reverse direction.
                self.link_exits(self.exits[dest_exit][0], self.exits[origin_exit][0], False)
                origin_exits.remove(self.exits[dest_exit][0])
                dest_exits.remove(self.exits[origin_exit][0])

        # Clean up entrance rando artificial edges for upcoming item rando
        self.delete_objects(items=[800],locs=[],nodes=[],edges=[],exits=[], with_close=True)
        #self.reset_progress()
        #self.update_graph(True,True,True)
        self.info("Entrance rando successful!")
        #self.print_exit_graph()

        return True


    def print_exit_graph_from_node(self, node, visited=[], known_exits=[]):
        for exit in self.exits:
            if self.exits[exit][1] > 0 and self.exits[exit][3] == node and exit not in known_exits:
                known_exits.append(exit)
                if self.entrance_shuffle != "Uncoupled":
                    known_exits.append(self.exits[self.exits[exit][1]][0])
                dest_node = self.exits[self.exits[exit][1]][4]
                self.info(str(node)+" "+str(self.graph[node][5])+" -> "+str(exit)+" "+str(self.exits[exit][10])+" -> "+str(dest_node)+" "+str(self.graph[dest_node][5]))
                if dest_node in visited:
                    self.info("   Looped to "+str(dest_node)+" "+str(self.graph[dest_node][5]))
                else:
                    visited.append(dest_node)
                    self.print_exit_graph_from_node(dest_node,visited,known_exits)
        return True


    def print_exit_graph(self):
        for node in self.graph:
            self.print_exit_graph_from_node(node,[node],[])
        return True


    # Currently this identifies txform DSes as all those that don't contain an item, don't restrict a Freedan ability,
    # and are on the list of completable guaranteed non-ability DSes -- could be improved
    def initialize_ds(self):
        # Clear DS access data from graph
        for x in self.graph:
            self.graph[x][4] = 0
            self.graph[x][9].clear()

        # Find nodes that contain Dark Spaces
        pyramid_ds_id = 130          # Special case for Pyramid DS, which has item type 1 instead of 2
        self.ds_locations = [pyramid_ds_id]
        self.ds_nodes = [self.item_locations[pyramid_ds_id][0]]
        self.freedan_locations = [pyramid_ds_id]
        self.freedan_locations.extend(self.completable_guaranteed_freedan_locations)
        self.freedan_nodes = [self.item_locations[loc][0] for loc in self.freedan_locations]
        for x in self.item_locations:
            if self.item_locations[x][1] == 2:
                self.ds_locations.append(x)
                self.ds_nodes.append(self.item_locations[x][0])
                # If a F ability can be here, and the DS doesn't have an ability, then it's a transformation DS = a F loc
                if not self.is_sublist(self.item_locations[x][4], [64, 65, 66]) and self.item_locations[x][3] not in [61,62,63,64,65,66] and x not in self.freedan_locations:
                    self.freedan_locations.append(x)
                    self.freedan_nodes.append(self.item_locations[x][0])
        return True


    # Translates logic and exits to world graph
    def update_graph(self,update_logic=True,update_ds=True,update_exits=False):
        self.info("Updating graph...")
        if update_exits:
            for exit in self.exits:
                if exit > 21 or self.exits[exit][5]:
                    # Check if exit has been shuffled
                    if self.exits[exit][1] > 0:
                        new_exit = self.exits[exit][1]
                    elif self.exits[exit][1] == 0:
                        new_exit = exit
                    else:
                        new_exit = -1

                    # Get exit origin
                    if new_exit > 0:
                        origin = self.exits[exit][3]
                        if not origin and self.is_exit_coupled(exit):
                            sister_exit = self.exits[exit][0]
                            origin = self.exits[sister_exit][4]
                            self.exits[exit][3] = origin

                        # Get (new) exit destination
                        if self.exits[new_exit][2] == 0 or self.exits[new_exit][2] == exit:
                            dest = self.exits[new_exit][4]
                            if not dest and self.is_exit_coupled(new_exit):
                                sister_exit = self.exits[new_exit][0]
                                dest = self.exits[sister_exit][3]
                                self.exits[new_exit][4] = dest

                            # Translate link into world graph
                            if origin and dest and (dest not in self.graph[origin][1]):
                                self.graph[origin][1].append(dest)

            self.info(" Graph exits updated")

        # Update logic edges (except those requiring Freedan access)
        if update_logic:
            for edge in self.logic:
                if not self.logic[edge][3]:
                    self.check_edge(edge)
            self.info(" Graph logic updated (item/abilities)")

        for node in self.graph:
            for x in self.graph[node][1]:
                if x not in self.graph[node][10]:
                    self.graph[node][10].append(x)
            for y in self.graph[node][10]:
                if node not in self.graph[y][8]:
                    self.graph[y][8].append(node)
            for z in self.graph[node][8]:
                if node not in self.graph[z][10]:
                    self.graph[z][10].append(node)
        self.info(" Node-node connections updated")

        if update_ds:
            # Clear and recalculate DS access for all nodes (recursively from DS nodes)
            self.initialize_ds()
            for node in self.ds_nodes:
                self.update_ds_access([node],1,[])
            for node in self.freedan_nodes:
                self.update_ds_access([node],2,[node])
            self.info(" DS access updated")

        # Update logic requiring Freedan access, repeatedly until access stops growing
        if update_logic:
            all_f_edges = [e for e in self.logic if self.logic[e][3]]
            checked_f_edges = []
            checked_new_edge = True
            while checked_new_edge:
                checked_new_edge = False
                for edge in all_f_edges:
                    if self.check_edge(edge) and edge not in checked_f_edges:
                        checked_f_edges.append(edge)
                        checked_new_edge = True
            self.info(" Graph logic updated (DS access)")

        return True


    # Check whether a node's DS access data needs to be updated
    def consider_ds_node(self,node,access_mode,ds_nodes):
        if access_mode == 3:
            return (self.consider_ds_node(node,1,[]) | self.consider_ds_node(node,2,ds_nodes))
        elif access_mode == 2:
            if not self.graph[node][2] or self.graph[node][7]:
                return False   # Freedan never needs to reach type-Other or forced-Will nodes
            if not (self.graph[node][4] & 0x02):
                return True
            if any(ds_node not in self.graph[node][9] for ds_node in ds_nodes):
                return True
        elif access_mode == 1:
            if not (self.graph[node][4] & 0x01):
                return True
        return False


    # Check if start_node can reach a Dark Space or is reachable by Freedan/Shadow
    def check_ds_access(self, start_node, need_freedan, do_recurse, visited):
        if start_node not in self.graph:
            return False
        if not self.graph[start_node][2]:
            return True    # Assumed true for type-Other nodes
        elif (not need_freedan and self.graph[start_node][4] & 0x01) or (need_freedan and self.graph[start_node][4] & 0x02):
            return True    # Node has already been evaluated to have the right DS access
        elif not do_recurse:
            return False   # Caller only wants to check this node's evaluated access
        elif start_node in visited:
            return False   # We've already recursed through this node
        else:
            to_visit = [start_node]
            while to_visit:
                node = to_visit.pop(0)
                if node not in visited+[start_node] and self.check_ds_access(node,need_freedan,do_recurse,visited):
                    self.verbose("Node "+str(self.graph[start_node][5])+" has DS access via node "+str(self.graph[node][5]))
                    return True
                else:
                    if node not in visited:
                        visited.append(node)
                    if need_freedan:
                        possible_origins = self.graph[node][8][:]
                        for edge in self.graph[node][13]:
                            if self.logic[edge][0] > 0:
                                possible_origins.append(self.logic[edge][1])
                        for origin in possible_origins:
                            if origin not in visited+to_visit:
                                to_visit.append(origin)
                    else:
                        possible_dests = self.graph[node][1][:]+self.graph[node][10][:]
                        for edge in self.graph[node][12]:
                            if self.logic[edge][0] > 0:
                                possible_dests.append(self.logic[edge][2])
                        for dest in possible_dests:
                            if dest not in visited+to_visit:
                                to_visit.append(dest)

            return False

    # Update DS access data for nodes, recursively to all connected nodes
    def update_ds_access(self, nodes, access_mode, ds_nodes):
        if not nodes:
            return True
        to_visit_forward = []
        to_visit_reverse = []
        for node in nodes:
            self.graph[node][4] |= access_mode
            self.graph[node][9].extend([ds_node for ds_node in ds_nodes if ds_node not in self.graph[node][9]])
            if access_mode & 0x01:    # "Can reach DS from here"
                to_visit_reverse = [x for x in self.graph[node][8] if self.consider_ds_node(x,0x01,[])]
            if access_mode & 0x02:    # "Freedan can reach here"
                possible_dests = self.graph[node][10][:]
                for forward_edge in self.graph[node][12]:
                    if self.check_edge(forward_edge,[],False):
                        if not any(s[0] in [61,62,63] for s in self.logic[forward_edge][4]):   # Freedan can't take edges that require a Will ability
                            possible_dests.append(self.logic[forward_edge][2])
                for x in possible_dests:
                    if x not in to_visit_forward and self.consider_ds_node(x,0x02,ds_nodes):
                        to_visit_forward.append(x)
        return (self.update_ds_access(to_visit_forward,2,ds_nodes) | self.update_ds_access(to_visit_reverse,1,[]))

    # Check a logic edge to see if prerequisites have been met based on self.items_collected + items
    def check_edge(self, edge, items=[], update_graph=True):
        success = False
        if edge not in self.logic:
            self.warn("Not a valid logic ID: "+str(edge))
            return False
        elif self.logic[edge][0] == -1:
            return False
        elif self.logic[edge][0] > 0:
            success = True

        req_items = []
        for req in self.logic[edge][4]:
            i = 0
            while i < req[1]:
                req_items.append(req[0])
                i += 1
        if self.is_sublist(self.items_collected+items, req_items) and (not self.logic[edge][3] or self.check_ds_access(self.logic[edge][1],True,False,[])):
            success = True

        if success and update_graph:
            self.open_edge(edge)

        return success


    # Open a logic edge and translate results to graph
    def open_edge(self, edge):
        if edge not in self.logic:
            return False
        if self.logic[edge][0] == -1:
            self.warn("Tried to open an edge that is restricted")
            return False
        if not self.logic[edge][0]:
            self.logic[edge][0] = 1
        return self.new_connection(self.logic[edge][1],self.logic[edge][2])


    # Map a new connection (i.e. exit, logic) to graph
    def new_connection(self, origin, dest):
        # To/from data
        if dest not in self.graph[origin][10]:
            self.graph[origin][10].append(dest)
        if origin not in self.graph[dest][8]:
            self.graph[dest][8].append(origin)
        # Propagate Dark Space access
        if self.graph[dest][4] & 0x01 and not self.graph[origin][4] & 0x01:
            self.update_ds_access([dest],1,[])
        if self.graph[origin][4] & 0x02 and not self.graph[dest][4] & 0x02:
            self.update_ds_access([origin],2,self.graph[origin][9])
        return True


    def restrict_edge(self, edge=-1):
        try:
            self.logic[edge][0] = -1
            return True
        except:
            return False

    def unrestrict_edge(self, edge=-1):
        try:
            self.logic[edge][0] = 0 if self.logic[edge][0] != 1 else self.logic[edge][0]
            return True
        except:
            return False

    # Set up the databases as required by this seed.
    def initialize(self):
        # Will delete several database objects that aren't needed by this seed
        free_items = []    # Items given for free, whose edges should be kept
        unused_items = []  # Inaccessible items, whose edges should be deleted
        unused_locs = []
        unused_nodes = []
        unused_edges = []
        
        # Prevent some seed generation failures by pre-empting bad, moderate-probability ability placement.
        if self.dungeon_shuffle == "None":
            no_friar_ds_maps = []
            no_slider_ds_maps = []
            no_spindash_ds_maps = list(range(160,170))   # Kress
            if self.orb_rando == "None":
                if not self.firebird:
                    no_friar_ds_maps.append(136)   # End of Great Wall
                no_slider_ds_maps.extend(list(range(176,192)))   # Angkor Wat
                no_spindash_ds_maps.extend(list(range(176,192)))   # Angkor Wat
            no_friar_nodes = [n for n in self.graph if any(self.graph[n][3][3] == map for map in no_friar_ds_maps)]
            no_slider_nodes = [n for n in self.graph if any(self.graph[n][3][3] == map for map in no_slider_ds_maps)]
            no_spindash_nodes = [n for n in self.graph if any(self.graph[n][3][3] == map for map in no_spindash_ds_maps)]
            no_friar_locs = [loc for loc in self.item_locations if self.item_locations[loc][0] in no_friar_nodes and 64 not in self.item_locations[loc][4]]
            no_slider_locs = [loc for loc in self.item_locations if self.item_locations[loc][0] in no_slider_nodes and 62 not in self.item_locations[loc][4]]
            no_spindash_locs = [loc for loc in self.item_locations if self.item_locations[loc][0] in no_spindash_nodes and 63 not in self.item_locations[loc][4]]
            for loc in no_friar_locs:
                self.item_locations[loc][4].append(64)
            for loc in no_slider_locs:
                self.item_locations[loc][4].append(62)
            for loc in no_spindash_locs:
                self.item_locations[loc][4].append(63)
        
        # Save item shuffle pools in the database
        for item in self.item_pool:
            self.item_pool[item][6] = self.get_pool_id(item=item)
        for loc in self.item_locations:
            self.item_locations[loc][7] = self.get_pool_id(loc=loc)
        
        # Save implicit FromRegion/ToRegion for coupled exits, and mark exits for randomization
        for x in self.exits:
            if self.is_exit_coupled(x) and (not self.exits[x][3] or not self.exits[x][4]):
                xprime = self.exits[x][0]
                self.exits[x][3] = self.exits[xprime][4]
                self.exits[x][4] = self.exits[xprime][3]
            if (not self.exits[x][1]) and (self.get_exit_pool(x) > -1):   # Can only shuffle unmapped, pooled exits.
                self.exits[x][1] = -1
                self.exits[x][2] = -1

        # Random start location
        if self.start_mode != "South Cape":
            self.start_loc = self.random_start()
            self.info("Start location: "+str(self.item_locations[self.start_loc][6]))
            if self.start_loc == 47:  # Diamond Mine behind fences
                self.graph[131][1].append(130)
        if self.start_mode == "South Cape" and self.entrance_shuffle == "None":
            self.graph[0][1].append(22)    # Starts in school
        else:
            self.graph[0][1].append(self.item_locations[self.start_loc][0])
        start_map = self.spawn_locations[self.start_loc][1]
        if start_map in self.maps:
            self.maps[start_map][4] = 1   # Can only start in a dark map if cursed

        # Add darkroom edges
        if self.darkroom_level not in ["None","All"]:
            if self.darkroom_level == "Few":
                self.max_darkrooms = 7
            elif self.darkroom_level == "Some":
                self.max_darkrooms = 14
            elif self.darkroom_level == "Many":
                self.max_darkrooms = 21
            if self.darkroom_cursed:
                self.max_darkrooms *= 2
            self.dr_randomize()
        
        # Convert exits that have logic requirements into graph nodes with logic edges
        coupled_exit_logics = [edge for edge in self.exit_logic if self.exit_logic[edge][3]]
        for edge in coupled_exit_logics:
            this_exit = self.exit_logic[edge][0]
            sister_exit = self.exits[this_exit][0]
            if sister_exit > 0:
                new_edge_id = 1+max(self.exit_logic)
                new_edge = [sister_exit, self.exit_logic[edge][1][:], self.exit_logic[edge][2], False]
                self.exit_logic[new_edge_id] = new_edge
                self.exit_logic[edge][3] = False
        exits_with_logic = set(self.exit_logic[edge][0] for edge in self.exit_logic)
        for exit in exits_with_logic:
            src_node_id = self.exits[exit][3]
            src_node_type = self.graph[src_node_id][2]
            src_node_info = self.graph[src_node_id][3]
            new_node_id = 1+max(self.graph)
            new_node = [False, [], src_node_type, src_node_info[:], 0, self.exits[exit][10], [], False, [], [], [], [], [], [], [], []]
            self.graph[new_node_id] = new_node
            self.exits[exit][3] = new_node_id
            sister_exit = self.exits[exit][0]
            if sister_exit and self.exits[sister_exit][4] == src_node_id:
                self.exits[sister_exit][4] = new_node_id
            exit_edges = [e for e in self.exit_logic if self.exit_logic[e][0] == exit]
            for edge in exit_edges:
                new_edge_id = 1+max(self.logic)
                if self.exit_logic[edge][2] == 0:   # Logic is to reach the exit; exit->room is free
                    new_edge = [0, src_node_id, new_node_id, False, self.exit_logic[edge][1][:], False]
                    self.graph[new_node_id][1].append(src_node_id)
                elif self.exit_logic[edge][2] == 1:   # Logic is to reach the room; room->exit is free
                    new_edge = [0, new_node_id, src_node_id, False, self.exit_logic[edge][1][:], False]
                    self.graph[src_node_id][1].append(new_node_id)
                elif self.exit_logic[edge][2] == 2:   # Logic blocks both room->exit and exit->room
                    new_edge = [0, new_node_id, src_node_id, False, self.exit_logic[edge][1][:], True]
                else:    # Something's wrong
                    self.error("exit_logic contains invalid directionality")
                    return False
                self.logic[new_edge_id] = new_edge        
        
        # Decompose bidirectional or artificial-item edges to unidirectional with real items;
        # the former are easier to maintain, the latter allow simpler code
        bidirectional_edges = [edge for edge in self.logic if self.logic[edge][5]]
        for edge in bidirectional_edges:
            self.logic[edge][5] = False
            new_edge_id = 1+max(self.logic)
            self.logic[new_edge_id] = [ self.logic[edge][0], self.logic[edge][2], self.logic[edge][1], self.logic[edge][3], self.logic[edge][4][:], False ]
        any_will_ability_edges = [edge for edge in self.logic if any(req[0] == 608 for req in self.logic[edge][4])]
        any_ranged_ability_edges = [edge for edge in self.logic if any(req[0] == 610 for req in self.logic[edge][4])]
        for edge in any_will_ability_edges:
            self.logic[edge][4].remove([608,1])
            for will_ability in [61,62,63]:
                new_edge_id = 1+max(self.logic)
                self.logic[new_edge_id] = [ self.logic[edge][0], self.logic[edge][1], self.logic[edge][2], self.logic[edge][3], self.logic[edge][4][:]+[[will_ability,1]], self.logic[edge][5] ]
        for edge in any_ranged_ability_edges:
            self.logic[edge][4].remove([610,1])
            for freedan_ranged_ability in [64,67]:   # Friar-0, Firebird; both require "Freedan"
                new_edge_id = 1+max(self.logic)
                self.logic[new_edge_id] = [ self.logic[edge][0], self.logic[edge][1], self.logic[edge][2], True, self.logic[edge][4][:]+[[freedan_ranged_ability,1]], self.logic[edge][5] ]
        unused_items.extend([608,610])
        unused_locs.extend([608,610])
        unused_nodes.extend([608,610])
        unused_edges.extend(any_will_ability_edges)
        unused_edges.extend(any_ranged_ability_edges)
        
        # If no orb rando, put monster orbs in their default locations; assumes that orb item ID = orb loc ID
        if self.orb_rando == "None":
            for loc in self.item_locations:
                item = loc
                if self.item_locations[loc][1] in [5]:
                    self.unfill_item(loc)
                    self.fill_item(item, loc, False, True)
        
        # Manage required items
        if 1 in self.dungeons_req:
            self.required_items += [3, 4, 7, 8]
        if 2 in self.dungeons_req:
            self.required_items += [14]
        if 3 in self.dungeons_req:
            self.required_items += [18, 19]
        if 5 in self.dungeons_req:
            self.required_items += [38, 30, 31, 32, 33, 34, 35]
        if 6 in self.dungeons_req:
            self.required_items += [39]
        if self.kara == 1:
            self.required_items += [2, 9, 23]
        elif self.kara == 2:
            self.required_items += [11, 12, 15]
        elif self.kara == 4:
            self.required_items += [26]
        elif self.kara == 5:
            self.required_items += [28, 66]

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

        # Non-Extreme logic won't assume you can get to Babel via Solid Arm
        if self.difficulty < 3:
            self.exits[21][4] = self.exits[21][3]

        # Allow glitches
        if "Allow Glitches" in self.variant:
            free_items.append(601)
            self.item_locations[124][2] = False   # Ankor Wat: Dropdown DS has abilities
            self.item_locations[142][2] = False   # Pyramid: Bottom DS can have abilities
            if not self.fluteless:
                self.item_locations[94][2] = False    # Great Wall: Slider glitch
        else:
            unused_items.append(601)
            unused_locs.append(601)
            unused_nodes.append(601)

        # Early Firebird
        if self.firebird:
            free_items.append(602)
        else:
            unused_items.append(602)
            unused_locs.append(602)
            unused_nodes.append(602)

        # Zelda 3 Mode
        if "Z3 Mode" in self.variant:
            # Update item pool
            self.item_pool[1][0] = 29  # Red Jewels
            self.item_pool[50][0] = 5  # HP upgrades
            self.item_pool[51][0] = 2  # DEF upgrades
            self.item_pool[52][0] = 3  # STR upgrades
            self.item_pool[55][0] = 12  # HP Pieces
        else:
            unused_items.append(55)   # Heart pieces don't exist

        # Open Mode
        if "Open Mode" in self.variant:
            # Set all travel item edges open (Letter, M.Melody, Teapot, Will, Roast)
            for travel_edge in [30,31,32,33,36,38,39,40]:
                self.logic[travel_edge][0] = 2
            # Remove travel items from pool and add some replacements
            free_items.extend([10,13,24,25,37])
            self.item_pool[6][0] += 4  # Herbs
            self.item_pool[0][0] += 1  # Nothing

        # Red Jewel Hunts repoint Jeweler Reward 7 edges to winning the game
        if self.goal == "Red Jewel Hunt":
            for jeweler_final_edge in [24,25,26,27]:
                self.logic[jeweler_final_edge][2] = 492
            unused_edges.extend([406,407])

        # Change graph logic depending on Kara's location
        unused_kara_edges = [400,401,402,403,404]
        if self.kara == 1:
            kara_edge = 400
            self.graph[49][6].append(20)
        elif self.kara == 2:
            kara_edge = 401
            self.graph[150][6].append(20)
            self.area_short_name[45] = "Samlet"  # instead of "Sam"
        elif self.kara == 3:
            kara_edge = 402
            self.graph[270][6].append(20)
        elif self.kara == 4:
            kara_edge = 403
            self.graph[345][6].append(20)
        elif self.kara == 5:
            kara_edge = 404
            self.graph[391][6].append(20)
        self.unrestrict_edge(kara_edge)
        unused_kara_edges.remove(kara_edge)
        unused_edges.extend(unused_kara_edges)

        # Change logic based on which dungeons are required
        for x in self.statues:
            self.logic[406][4][x][1] = 1

        # Change item pool for "player choice" statue requirement variant
        if self.statue_req == StatueReq.PLAYER_CHOICE.value:
            self.item_pool[106][0] = 6
            unused_items.extend([100,101,102,103,104,105])
        else:
            unused_items.append(106)

        # Fluteless gets free Psycho Dash, non-Fluteless gets Flute.
        # The artificial Flute loc and node aren't currently used.
        unused_locs.append(604)
        unused_nodes.append(604)
        if self.fluteless:
            self.fill_item(61,self.start_loc,False,True)
            unused_items.append(604)
        else:
            free_items.append(604)

        # Dungeon Shuffle.
        # Clean up dungeon shuffle artificial items
        dungeon_shuffle_unused_ids = [605,606,607]
        if self.dungeon_shuffle == "None" or self.dungeon_shuffle == "Basic":
            unused_items.extend([800])
            free_items.append(525)   # Pyramid portals open
            unused_locs.append(525)  # Loc is unused as item is free
            unused_nodes.append(525) # Node is unused as item is free
            if self.dungeon_shuffle == "None":
                world_dungeon_shuffle_id = 605
            elif self.dungeon_shuffle == "Basic":
                world_dungeon_shuffle_id = 606
        elif self.dungeon_shuffle == "Chaos":
            world_dungeon_shuffle_id = 607
        self.graph[0][1].append(world_dungeon_shuffle_id)
        dungeon_shuffle_unused_ids.remove(world_dungeon_shuffle_id)
        unused_items.extend(dungeon_shuffle_unused_ids)
        unused_locs.extend(dungeon_shuffle_unused_ids)
        unused_nodes.extend(dungeon_shuffle_unused_ids)
        if self.dungeon_shuffle == "Chaos":
            # Reduce walking times by removing some empty corridors; stabilize dungeon generation by removing lower Mu corridors.
            # 69 Inca U-turn room; 79 Inca statue "puzzle"; 140,141,144,145 Mine elevator; 259 Angl empty water room;
            # Wat: 375,379 hall before and road to main hall; 390 corridor before spirit;
            # Mu: 224,235,730,736 are the lower corridor nodes.
            self.soft_delete_objects(locs=[], nodes=[69, 79, 140, 141, 144, 145, 224, 235, 259, 375, 379, 390, 730, 736], exits=[])
        
        # Clean up the objects so designated based on seed settings
        self.delete_objects(items=unused_items,locs=unused_locs,nodes=unused_nodes,edges=unused_edges,exits=[],with_close=True)
        self.delete_objects(items=free_items,locs=[],nodes=[],edges=[],exits=[],with_close=False)
        
        # Clean up edges that now require neither items nor Freedan
        free_edges = [edge for edge in self.logic if not (self.logic[edge][3] or self.logic[edge][4])]
        for edge in free_edges:
            here_node = self.logic[edge][1]
            other_node = self.logic[edge][2]
            self.graph[here_node][1].append(other_node)
        self.delete_objects(items=[],locs=[],nodes=[],edges=free_edges,exits=[],with_close=True)

        # Incorporate item locations and logic edges into world graph
        for x in self.item_locations:
            self.graph[self.item_locations[x][0]][11].append(x)
        for y in self.logic:
            if self.logic[y][0] != -1:
                self.graph[self.logic[y][1]][12].append(y)
                self.graph[self.logic[y][2]][13].append(y)
        
        # Boss Shuffle -- boss order is imposed by the World creator, not here
        if "Boss Shuffle" in self.variant:
            boss_entrance_idx = [1,4,7,10,13,16,19]
            boss_exit_idx = [3,6,9,12,15,18,21]
            dungeon = 0
            self.info("Boss order: "+str(self.boss_order))
            while dungeon < 7:
                boss = self.boss_order[dungeon]
                entrance_old = boss_entrance_idx[dungeon]
                entrance_new = boss_entrance_idx[boss-1]
                exit_old = boss_exit_idx[boss-1]
                exit_new = boss_exit_idx[dungeon]
                self.link_exits(entrance_old,entrance_new)
                if self.exits[exit_old][5]:
                    self.link_exits(exit_old,exit_new)
                dungeon += 1
        
        # Cache the number of item pools, and create empty loc lists for them
        self.item_pool_count = 1 + self.get_max_pool_id()
        self.open_locations = [ [] for _ in range(self.item_pool_count) ]

        self.reset_progress(True)          # Initialize graph with no items or logic
        self.update_graph(True,True,True)  # Build basic graph connections from any unrandomized elements

        return True


    # Delete sets of objects and linked objects. If with_close, an edge is deleted if any
    # required item is deleted; otherwise the item is just removed as a requirement.
    # To prevent referential integrity issues, use soft_delete_objects instead for exits and nodes connected to exits.
    def delete_objects(self, items, locs, nodes, edges, exits, with_close):
        del_items = [x for x in items if x in self.item_pool]
        del_locs = [x for x in locs if x in self.item_locations]
        del_nodes = [x for x in nodes if x in self.graph]
        del_edges = [x for x in edges if x in self.logic]
        del_exits = [x for x in exits if x in self.exits]
        for item in set(del_items):
            del self.item_pool[item]
            for node in [n for n in self.graph if item in self.graph[n][6]]:
                self.graph[node][6].remove(item)
            affected_edges = [e for e in self.logic if any(item == req[0] for req in self.logic[e][4])]
            for edge in affected_edges:
                if with_close:
                    del_edges.append(edge)
                else:
                    req = next(r for r in self.logic[edge][4] if r[0] == item)
                    self.logic[edge][4].remove(req)
        for node in set(del_nodes):
            del self.graph[node]
            affected_locs = [loc for loc in self.item_locations if self.item_locations[loc][0] == node]
            affected_nodes = [n for n in self.graph if node in self.graph[n][1] + self.graph[n][8] + self.graph[n][9] + self.graph[n][10]]
            affected_edges = [e for e in self.logic if node == self.logic[e][1] or node == self.logic[e][2]]
            del_locs.extend(affected_locs)
            del_edges.extend(affected_edges)
            for other_node in affected_nodes:
                for subidx in [1, 8, 9, 10]:
                    if node in self.graph[other_node][subidx]:
                        self.graph[other_node][subidx].remove(node)
        for loc in set(del_locs):
            del self.item_locations[loc]
            affected_nodes = [n for n in self.graph if loc in self.graph[n][11]]
            for node in affected_nodes:
                self.graph[node][11].remove(loc)
        for exit in set(del_exits):
            del self.exits[exit]
            affected_nodes = [n for n in self.graph if exit in self.graph[n][14] + self.graph[n][15]]
            for node in affected_nodes:
                for subidx in [14,15]:
                    if exit in self.graph[node][subidx]:
                        self.graph[node][subidx].remove(exit)
        for edge in set(del_edges):
            del self.logic[edge]
            affected_nodes = [n for n in self.graph if edge in self.graph[n][12] + self.graph[n][13]]
            for node in affected_nodes:
                for subidx in [12,13]:
                    if edge in self.graph[node][subidx]:
                        self.graph[node][subidx].remove(edge)
    
    # Remove objects and linked objects from logic, while leaving them in the database for referential integrity.
    def soft_delete_objects(self, locs, nodes, exits):
        del_locs = [x for x in locs if x in self.item_locations]
        del_nodes = [x for x in nodes if x in self.graph]
        del_exits = [x for x in exits if x in self.exits]
        for loc in set(del_locs):
            self.item_locations[loc][2] = True
            self.item_locations[loc][3] = 0
            self.item_locations[loc][7] = 0
        for node in set(del_nodes):
            self.optional_nodes.append(node)
            affected_exits = [x for x in self.exits if self.exits[x][3] == node]
            del_exits.extend(affected_exits)
        for exit in set(del_exits):
            if self.exits[exit][1] < 0:
                self.link_exits(exit, self.exits[exit][0], False, False)

    # Simulate inventory
    def get_inventory(self,start_items=[],item_destinations=[],new_nodes=[]):
        if not start_items:
            start_items = self.items_collected[:]
        if not item_destinations:
            item_destinations = self.item_destinations[:]
        inventory_temp = []
        for item in start_items:
            if self.item_pool[item][4]:
                inventory_temp.append(item)
        inventory = []
        while inventory_temp:
            item = inventory_temp.pop(0)
            if item in item_destinations:
                item_destinations.remove(item)
            else:
                inventory.append(item)
        return inventory


    # Return list of accessible nodes
    def list_accessible_nodes(self):
        accessible = []
        for x in self.graph:
            if self.is_accessible(x):
                accessible.append(x)
        return accessible


    def print_accessible_nodes(self):
        self.info("Accessible nodes:")
        for x in self.graph:
            if self.is_accessible(x):
                self.info(str(self.graph[x][5]))


    def print_inaccessible_nodes(self):
        self.info("Inccessible nodes:")
        for x in self.graph:
            if not self.is_accessible(x):
                self.info(str(self.graph[x][5]))


    # Takes a random seed and builds out a randomized world
    def randomize(self, seed_adj=0, print_log=-1):
        self.print_log = print_log
        
        random.seed(self.seed + seed_adj)
        if self.race_mode:
            for i in range(random.randint(100, 1000)):
                _ = random.randint(0, 10000)

        if self.race_mode:
            for i in range(random.randint(100, 1000)):
                _ = random.randint(0,10000)

        if not self.initialize():
            self.error("Could not initialize world")
            return False
        self.info("Initialization complete")

        # Overworld shuffle
        if "Overworld Shuffle" in self.variant:
            if not self.shuffle_overworld():
                self.error("Overworld shuffle failed")
                return False

        # Shuffle exits
        if self.entrance_shuffle != "None" or self.dungeon_shuffle != "None":
            if not self.shuffle_exits():
                self.error("Entrance rando failed")
                return False

        self.reset_progress(True)           # Forget items and logic used for ER/DS skeleton construction
        self.update_graph(True,True,True)   # Rebuild graph connections with exits

        # Initialize and shuffle location list
        item_locations = self.list_item_locations(shuffled_only=True)
        random.shuffle(item_locations)

        # Populate various pseudo-item pools
        self.fill_statues()
        self.map_rewards()

        # Will forward-fill progression items with Monte Carlo method, placing items until goal is reached.
        # Abilities are placed first, assuming all items are held, so transformation DSes can be locked in.
        done = False
        goal = False
        cycle = 0
        place_abilities = True
        self.items_collected = self.list_typed_items(types=[1,2,4,5], shuffled_only=False, incl_placed=True)   # Assume all items for ability placement
        self.update_graph(True,True,True)   # Build all logical connections into graph for DS locking
        if (self.logic_mode == "Completable" or self.dungeon_shuffle != "None") and not self.lock_dark_spaces():
            self.error("Couldn't lock DSes with open graph")
            return False
        self.info("Beginning ability placement...")
        while not done:
            cycle += 1
            self.info(" Cycle "+str(cycle))
            if (self.dungeon_shuffle == "None" and cycle > MAX_CYCLES) or (cycle > 1 * MAX_CYCLES):
                self.error("Max cycles exceeded")
                return False

            self.traverse()
            if place_abilities:
                to_place = self.list_typed_items(types=[2], shuffled_only=True)
                if not to_place:
                    done = True
                else:
                    random.shuffle(to_place)
                    progress = False
                    while not progress and to_place:
                        ability = to_place.pop(0)
                        progress = self.forward_fill([ability],item_locations,False,self.logic_mode == "Chaos")
                    if not progress:
                        self.error("Could not place any abilities")
                        return False

                if done:
                    place_abilities = False
                    done = False
                    self.info("  Finished placing abilities")
                    self.info("Beginning item placement...")

                    # Randomly place non-progression items in the open graph
                    self.traverse()
                    non_prog_items = self.list_typed_items(types=[], progress_type=3, shuffled_only=True)
                    for item in non_prog_items:
                        if item in self.items_collected:
                            self.items_collected.remove(item)
                    self.forward_fill(non_prog_items, item_locations, False, self.logic_mode == "Chaos")

                    # Forget collected items and edges; rebuild the graph with DSes set, ready to place items
                    self.reset_progress(True)
                    self.update_graph(True,True,False)   # no need to recalculate exits again
            else:
                if len(self.get_inventory()) > MAX_INVENTORY:
                    goal = False
                    self.warn("Inventory capacity exceeded")
                else:
                    goal = self.is_accessible(492)

                progression_result = self.progression_list()
                self.info("Progression options: {")
                self.info(" "+str(progression_result[0]))   # Available
                self.info(" "+str(progression_result[1]))   # Not enough locs
                self.info(" "+str(progression_result[2]))   # Not enough inv space
                self.info("}")
                progression_list = progression_result[0]
                is_progression = (progression_result != [[],[],[]])
                done = goal and (self.logic_mode != "Completable" or not is_progression)

                if not done:
                    if not is_progression:
                        self.error("Couldn't progress any further")
                        self.print_graph()
                        return False

                    progress = False
                    key = random.uniform(0,100)
                    while not progress and progression_list:
                        progression_mc = self.monte_carlo(progression_list)
                        idx = 0
                        for x in progression_mc:
                            if key <= x[0] and not idx:
                                idx = x[1]

                        items = progression_list.pop(idx)
                        if self.forward_fill(items, item_locations, False, self.logic_mode == "Chaos"):
                            progress = True
                            self.info("  Placed progression items successfully")

                    if not progress:
                        self.info("  No suitable progression found, attempting to make room...")
                        if not self.make_room(progression_result):
                            self.error("Could not find progression")
                            self.print_graph()
                            return False

        self.info("Placing junk items...")
        junk_items = self.list_typed_items(types=[], shuffled_only=True)
        self.random_fill(junk_items, item_locations, False)

        self.info("Item placement complete, beginning final traversal...")

        self.reset_progress(True)
        self.update_graph()
        self.traverse([])    # Fresh traverse with no nodes queued to visit

        if self.logic_mode == "Completable" and self.goal != "Red Jewel Hunt":
            completed = all(self.graph[node][0] for node in self.graph if node not in self.optional_nodes)
        else:
            completed = self.graph[492][0]
        if not completed:
            #self.print_graph()
            unreachable = [node for node in self.graph if not self.graph[node][0] and node not in self.optional_nodes]
            for node in unreachable:
                self.info("Can't reach node "+str(node)+" "+str(self.graph[node]))
            self.error("ERROR: Seed failed, trying again...\n")
            return False

        self.info("Writing hints...")
        placement_log = self.placement_log[:]
        random.shuffle(placement_log)
        self.in_game_spoilers(placement_log)

        self.info("Randomization complete!")

        return True


    def print_graph(self):
        self.info("Open edges: "+str(self.open_edges))
        self.info("Open locations: "+str(self.open_locations))
        for node in self.graph:
            self.info(str(node)+" "+str(self.graph[node]))


    # Prepares dataset to give in-game spoilers
    def in_game_spoilers(self, placement_log=[]):
        for x in placement_log:
            item = x[0]
            location = x[1]

            if location not in self.free_locations and location in self.area_short_name:
                if item in self.required_items or item in self.good_items or location in self.trolly_locations:
                    spoiler_str = self.area_short_name[location] + " has ]"   # ']' is a newline
                    if len(self.item_pool[item][3]) >= 26:
                        spoiler_str += self.item_pool[item][3].replace(' ','_',2).replace(' ',']',1)
                    else:
                        spoiler_str += self.item_pool[item][3]
                    # No in-game spoilers in Expert mode
                    if self.difficulty >= 3:
                        spoiler_str = "nice try dodongo!"
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
        spoiler["start_location"] = self.item_locations[self.start_loc][6].strip()
        spoiler["logic"] = str(self.logic_mode)
        spoiler["difficulty"] = str(difficulty_txt)
        if self.statue_req == StatueReq.PLAYER_CHOICE.value:
            spoiler["statues_required"] = self.statues_required
        else:
            spoiler["statues_required"] = self.statues
        spoiler["boss_order"] = self.boss_order
        spoiler["kara_location"] = kara_txt
        spoiler["jeweler_amounts"] = self.gem
        spoiler["inca_tiles"] = self.incatile
        spoiler["hieroglyph_order"] = self.hieroglyphs

        items = []
        for x in self.item_locations:
            if x < 500 or x >= 700:
                item = self.item_locations[x][3]
                location_name = self.item_locations[x][6].strip()
                item_name = self.item_pool[item][3]
                items.append({"location": location_name, "name": item_name})
        spoiler["items"] = items

        if "Overworld Shuffle" in self.variant:
            overworld_links = []
            for continent_id, continent_data in self.overworld_menus.items():
                continent_name = continent_data[5]
                region_name = self.overworld_menus[continent_data[0]][6]
                region_name = region_name.replace('_','')
                overworld_links.append({"region": region_name, "continent": continent_name})
            spoiler["overworld_entrances"] = overworld_links

        if self.entrance_shuffle != "None" or self.dungeon_shuffle != "None":
            exit_links = []
            for exit in self.exits:
                exit_name = self.exits[exit][10]
                linked_exit = self.exits[exit][1]
                if not linked_exit:
                    exit_linked_name = exit_name
                else:
                    exit_linked_name = self.exits[linked_exit][10]
                exit_links.append({"entrance": exit_name, "exit": exit_linked_name})
            spoiler["exit_links"] = exit_links

        self.spoiler = spoiler
        #self.complete_graph_visualization()

    def complete_graph_visualization(self):
        self.graph_viz = graphviz.Digraph(graph_attr=[('concentrate','true'),
                                                      ('rankdir', 'TB')], strict=True)
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
                    self.info("Missing info about item: "+str(item_id))
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

        self.info("")
        self.info("Seed                                   >  "+str(self.seed))
        self.info("Statues Required                       >  "+str(self.statues))
        self.info("Kara Location                          >  "+str(kara_txt))
        self.info("Jeweler Reward Amounts                 >  "+str(self.gem))
        self.info("Inca Tile (column, row)                >  "+str(self.incatile))
        self.info("Hieroglyph Order                       >  "+str(self.hieroglyphs))
        self.info("")

        for x in self.item_locations:
            item = self.item_locations[x][3]
            location_name = self.item_locations[x][6]
            item_name = self.item_pool[item][3]
            self.info(str(location_name)+"  >  "+str(item_name))

    # Generate assembly define dict based on World state
    def populate_asar_defines(self):
        # Room-clearing rewards
        for i in range(0x100):
            self.asar_defines["RoomClearReward"+format(i,"02X")] = 0
        idx_tier2 = 1
        idx_tier3 = 1
        idx_tier4 = 1
        for i in range(1,7):
            self.asar_defines["RemovedRoomRewardExpertFlag"+str(i)] = 0
            self.asar_defines["RemovedRoomRewardAdvancedFlag"+str(i)] = 0
            self.asar_defines["RemovedRoomRewardIntermediateFlag"+str(i)] = 0
        for map in self.maps:
            reward_tier = self.maps[map][2][1]
            if reward_tier > 0:
                reward = self.maps[map][2][0]
                self.asar_defines["RoomClearReward"+format(map,"02X")] = reward

                # Populate player level logic
                if reward_tier == 4:
                    self.asar_defines["RemovedRoomRewardIntermediateFlag"+str(idx_tier2)] = 0x300 + map
                    idx_tier2 += 1
                elif reward_tier == 3:
                    self.asar_defines["RemovedRoomRewardAdvancedFlag"+str(idx_tier3)] = 0x300 + map
                    idx_tier3 += 1
                elif reward_tier == 2:
                    self.asar_defines["RemovedRoomRewardExpertFlag"+str(idx_tier4)] = 0x300 + map
                    idx_tier4 += 1

        # Items and abilities
        for x in self.item_locations:
            loc_type = self.item_locations[x][1]
            loc_label = self.item_locations[x][5]

            # Handle items and orbs
            if loc_type == 1 or loc_type == 5:
                item = self.item_locations[x][3]
                
                if self.item_pool[item][1] == 5:
                    item_id = 0x1000 + self.item_pool[item][2]
                else:
                    item_id = self.item_pool[item][2]
                self.asar_defines[loc_label] = item_id
                
                if x in [0,1,2,3,4,5]:    # Jeweler items
                    if self.item_pool[item][1] == 5:
                        item_name = "Open a Door"
                    else:
                        item_name = self.item_pool[item][3]
                    self.asar_defines["Jeweler"+str(x+1)+"RowText"] = item_name
                
            # Handle abilities
            elif loc_type == 2:
                ability = self.item_locations[x][3]
                map = self.spawn_locations[x][1]

                if ability in [61, 62, 63, 64, 65, 66]:
                    self.asar_defines[loc_label] = 0x05
                    if ability == 61:  # Psycho Dash
                        ds_label = "DSPsychoDashMap"
                    if ability == 62:  # Psycho Slide
                        ds_label = "DSPsychoSliderMap"
                    if ability == 63:  # Spin Dash
                        ds_label = "DSSpinDashMap"
                    if ability == 64:  # Dark Friar
                        ds_label = "DSDarkFriarMap"
                    if ability == 65:  # Aura Barrier
                        ds_label = "DSAuraBarrierMap"
                    if ability == 66:  # Earthquaker
                        ds_label = "DSEarthquakerMap"
                    self.asar_defines[ds_label] = map
                elif x in [10,14,22,39,57,66,77,88,103,114,129,145,146]:
                    # Non-ability DSes in towns are empty
                    self.asar_defines[loc_label] = 0x01
                else:
                    self.asar_defines[loc_label] = 0x03
                    
        # Write in-game spoilers
        i = 0
        for label in self.spoiler_labels:
            if i < len(self.spoilers):
                self.asar_defines[self.spoiler_labels[label]] = self.spoilers[i]
                i += 1

        # Enemizer; labels are generated in the routine
        if self.enemizer != "None":
            self.enemize()

        # Start location handling for random start or entrance rando
        self.asar_defines["StartAtWarpLocation"] = 0
        self.asar_defines["StartDsIndex"] = self.spawn_locations[-1][2]
        self.asar_defines["StartLocationName"] = "South Cape"
        self.asar_defines["StartLocationId"] = 10
        if self.start_mode != "South Cape" or self.entrance_shuffle != "None":
            self.asar_defines["StartAtWarpLocation"] = 1
            self.asar_defines["StartDsIndex"] = self.spawn_locations[self.start_loc][2]
            self.asar_defines["StartLocationName"] = self.area_short_name[self.start_loc]
            self.asar_defines["StartLocationId"] = self.start_loc
        
        # Overworld
        for entry in self.overworld_menus:
            new_entry = entry
            if self.overworld_menus[entry][0] > 0:
                new_entry = self.overworld_menus[entry][0]
            old_label = self.overworld_menus[entry][4]
            new_label = self.overworld_menus[new_entry][4]
            self.asar_defines["OverworldShuffle"+old_label+"Label"] = new_label
            self.asar_defines["OverworldShuffle"+old_label+"Text"] = self.overworld_menus[new_entry][6]
            self.asar_defines["OverworldShuffle"+new_label+"MenuId"] = self.overworld_menus[entry][1]
        
        # Entrances
        for exit in self.exits:
            new_exit = self.exits[exit][1]
            if new_exit > 0:
                old_exit_label = self.exits[exit][5]
                new_exit_string_label = self.exits[new_exit][5]
                self.asar_defines[old_exit_label] = "!Default"+new_exit_string_label
        
        # Dark rooms
        if self.darkroom_level != "None":
            self.asar_defines["SettingDarkRoomsLevel"] = { "None": 0, "Few": 1, "Some": 2, "Many": 3, "All": 4 }[self.darkroom_level]
            if len(self.all_darkrooms) > 0:
                darkroom_str = ""
                for room in self.all_darkrooms:
                    darkroom_str += str(room) + ","
                    self.asar_defines["IsMap"+format(room,"02X")+"Dark"] = 1
                darkroom_str += "$ff"
                self.asar_defines["DarkMapList"] = darkroom_str

        # print "ROM successfully created"


    # Pick random start location
    def random_start(self):
        locations = []
        for loc in self.spawn_locations:
            if (self.start_mode == "Forced Unsafe" and self.spawn_locations[loc][0] == "Unsafe") or (
                    self.start_mode != "Forced Unsafe" and self.spawn_locations[loc][0] == "Safe") or (
                    self.spawn_locations[loc][0] == self.start_mode):
                locations.append(loc)
        if not locations:
            self.error("Something is fishy with start locations")
            return -1
        else:
            return locations[random.randint(0, len(locations) - 1)]
    
    
    # Dark rooms.
    def dr_randomize(self):
        if self.darkroom_cursed:
            max_cluster_size = 5
        else:
            max_cluster_size = 3
        darkness_clusters = []
        curr_cluster_idx = -1
        while len(self.all_darkrooms) < self.max_darkrooms:
            # If exactly 1 more room is needed, try growing an existing cluster
            if len(self.all_darkrooms) == self.max_darkrooms - 1:
                this_cluster_idx = 0
                while this_cluster_idx < len(darkness_clusters)-1:
                    candidate_cluster = darkness_clusters[this_cluster_idx]
                    if len(candidate_cluster) < max_cluster_size:
                        if self.dr_spread_once(candidate_cluster):
                            break   # It grew
                    this_cluster_idx += 1
            # If that didn't work or doesn't apply, add a new cluster
            if len(self.all_darkrooms) < self.max_darkrooms:
                darkness_sources = [m for m in self.maps if self.maps[m][4] == 3 and m not in self.all_darkrooms]
                random.shuffle(darkness_sources)
                new_cluster = []
                new_source = darkness_sources.pop(0)
                if any(abs(m - new_source) < 4 for m in self.all_darkrooms):
                    # Try not to put clusters too close together
                    darkness_sources.append(new_source)
                    new_source = darkness_sources.pop(0)
                new_cluster.append(new_source)
                self.all_darkrooms.append(new_source)
                # Spread to a random size between max/2 and max (or to the room cap or its boundary)
                new_cluster_size = random.randint(1+int(max_cluster_size/2),max_cluster_size)
                while (len(new_cluster) <= new_cluster_size) and (len(self.all_darkrooms) < self.max_darkrooms):
                    if not self.dr_spread_once(new_cluster):
                        break    # The cluster hit a wall (e.g. a type-1 room if uncursed) and can't grow
                # We're done with this cluster
                darkness_clusters.append(new_cluster)
        # If uncursed, add logic edges for darkness
        if not self.darkroom_cursed:
            dark_nodes = [n for n in self.graph if any(darkroom == self.graph[n][3][3] for darkroom in self.all_darkrooms)]
            dark_exits = [x for x in self.exits if self.exits[x][3] in dark_nodes]
            for exit in dark_exits:
                new_logic_id = 1+max(self.exit_logic)
                new_logic = [exit, [[28, 1], [39, 1]], 2, False]   # Dark Glasses, Crystal Ring
                self.exit_logic[new_logic_id] = new_logic
        
    # Returns a list of non-dark rooms that darkness can spread to from cluster, of requested or default types.
    def dr_get_nondark_sinks(self, cluster, types):
        if not types:
            if not self.darkroom_cursed:
                types = [2,3,4]
            else:
                types = [1,2,3,4]
        return [sink for src in cluster for sink in self.maps[src][9] if self.maps[sink][4] in types and sink not in self.all_darkrooms]
    
    # Expands the darkness cluster into all adjacent rooms that inherit darkness.
    def dr_spread_to_free_sinks(self, cluster):
        new_free_sinks = [0]
        while new_free_sinks:
            new_free_sinks = self.dr_get_nondark_sinks(cluster, [4])
            cluster.extend(new_free_sinks)
            self.all_darkrooms.extend(new_free_sinks)
    
    # Expands the darkness cluster by one room (plus any adjacent free sinks).
    def dr_spread_once(self, cluster):
        self.dr_spread_to_free_sinks(cluster)
        all_sinks = self.dr_get_nondark_sinks(cluster, [])
        if not all_sinks:
            return False
        random.shuffle(all_sinks)
        new_room = all_sinks.pop()
        self.all_darkrooms.append(new_room)
        cluster.append(new_room)
        self.dr_spread_to_free_sinks(cluster)
        return True


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

        self.graph[10][1].clear()
        self.graph[11][1].clear()
        self.graph[12][1].clear()
        self.graph[13][1].clear()
        self.graph[14][1].clear()

        self.graph[10][10].clear()
        self.graph[11][10].clear()
        self.graph[12][10].clear()
        self.graph[13][10].clear()
        self.graph[14][10].clear()

        # Add new overworld to the graph
        for entry in self.overworld_menus:
            new_entry = self.overworld_menus[entry][0]
            self.graph[self.overworld_menus[entry][2]][1].append(self.overworld_menus[new_entry][3])
            self.graph[self.overworld_menus[new_entry][3]][1].remove(self.overworld_menus[new_entry][2])
            self.graph[self.overworld_menus[new_entry][3]][1].append(self.overworld_menus[entry][2])

        return True


    # Check whether this monster ID is compatible with this enemy type.
    def can_monster_be_type(self, monster_id, enemy_type):
        if monster_id in self.enemizer_restricted_enemies:
            if enemy_type in self.enemizer_restricted_enemies[monster_id]:
                return False
        return True

    # Shuffle enemies in ROM
    def enemize(self):
        complex_enemies = [4, 15, 53, 62, 88]  # Enemies with many sprites, or are no fun
        max_complex = 5

        # Get list of enemysets
        enemysets = []
        for set in self.enemysets:
            enemysets.append(set)

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
            if self.maps[map][0] < 0:
                continue
            complex_ct = 0
            oldset = self.maps[map][0]
            # Determine new enemyset for map
            if self.enemizer == "Limited":
                sets = [oldset]
            else:
                sets = [set for set in enemysets if set not in self.maps[map][7]]

            random.shuffle(sets)
            newset = sets[0]

            # Gather enemies from old and new sets
            old_enemies = []
            new_enemies = []
            for enemy in self.enemies:
                if self.enemies[enemy][0] == oldset:
                    old_enemies.append(enemy)
                if self.enemies[enemy][0] == newset and self.enemies[enemy][5]:
                    new_enemies.append(enemy)

            # Update map header to reflect new enemyset
            self.asar_defines["Map"+format(map,"02X")+"CardMonsters"] = "!"+self.enemysets[newset][0]

            # Randomize each enemy in map
            first_monster_id = self.maps[map][5]
            last_monster_id = self.maps[map][6]
            this_monster_id = first_monster_id
            while this_monster_id <= last_monster_id:
                if this_monster_id not in self.default_enemies:
                    this_monster_id += 1
                    continue
                old_enemy = self.default_enemies[this_monster_id]
                enemytype = self.enemies[old_enemy][3]
                walkable = self.enemies[old_enemy][4]
                
                random.shuffle(new_enemies)
                i = 0
                found_enemy = False
                while not found_enemy:
                    new_enemy = new_enemies[i]
                    new_enemytype = self.enemies[new_enemy][3]
                    new_walkable = self.enemies[new_enemy][4]
                    if (i == len(new_enemies) - 1) or (this_monster_id in self.enemizer_restricted_enemies and self.can_monster_be_type(this_monster_id,new_enemy)) or ((this_monster_id not in self.enemizer_restricted_enemies) and (complex_ct < max_complex or new_enemy not in complex_enemies) and (walkable or new_enemytype == 3 or walkable == new_walkable)):
                        found_enemy = True
                        # Limit number of complex enemies per map
                        if new_enemy in complex_enemies:
                            complex_ct += 1
                    i += 1
                self.asar_defines["Monster"+format(this_monster_id,"04X")+"Addr"] = "!"+self.enemies[new_enemy][1]
                if map == 27:   # Moon Tribe doesn't shuffle stats
                    new_enemy_stat_block = self.enemies[old_enemy][2]
                elif self.enemizer == "Balanced":   # Balanced enemizer doesn't shuffle stats--
                    new_enemy_stat_block = self.enemies[old_enemy][2]
                    if old_enemy == 102:   # --except that we use the cyclops stat block for replaced zombies
                        new_enemy_stat_block = 0x47
                elif self.enemizer == "Insane" and new_enemy != 102:   # Insane uses random stat blocks for non-zombies
                    new_enemy_stat_block = insane_dictionary[new_enemy]
                else:   # Otherwise (Limited, Full, and zombies in Insane) the new monster uses its normal stat block
                    new_enemy_stat_block = self.enemies[new_enemy][2]
                self.asar_defines["Monster"+format(this_monster_id,"04X")+"Stats"] = new_enemy_stat_block

                # Nearly all monsters use Param to set layer priority (o = $00/$10/$20/$30),
                # so should not override the Param (priority) of the monster they're replacing.
                # Wat wall skulls use Param = 0/2/4/6 to set their movement direction.
                # Inca statues with Param > 0 are frozen until a certain flag is set.
                # So for wall skulls we want Param = a random direction, for Inca statues we want Param = 0,
                # and for others we want to retain the priority bits but zero out the wall skull bits.
                if new_enemy == 108:
                    self.asar_defines["Monster"+format(this_monster_id,"04X")+"Param"] = random.randint(0,3) * 2
                elif new_enemy in [16,17,18,19,20,21,22]:
                    self.asar_defines["Monster"+format(this_monster_id,"04X")+"Param"] = 0
                else:
                    self.asar_defines["Monster"+format(this_monster_id,"04X")+"Param"] = "!DefaultMonster"+format(this_monster_id,"04X")+"Param&$F0"
                
                this_monster_id += 1

    # Build world
    def __init__(self, settings: RandomizerData, statues_required=6, statues=[1,2,3,4,5,6], statue_req=StatueReq.GAME_CHOICE.value, kara=3, gem=[3,5,8,12,20,30,50], incatile=[9,5], hieroglyphs=[1,2,3,4,5,6], boss_order=[1,2,3,4,5,6,7]):

        self.seed = settings.seed
        self.race_mode = settings.race_mode
        self.fluteless = settings.fluteless
        self.statues = statues
        self.statues_required = statues_required
        self.statue_req = statue_req
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
        
        if settings.orb_rando.value == OrbRando.NONE.value:
            self.orb_rando = "None"
        elif settings.orb_rando.value == OrbRando.BASIC.value:
            self.orb_rando = "Basic"
        else:
            self.orb_rando = "Orbsanity"
        
        if abs(settings.darkrooms.value) == DarkRooms.NONE.value:
            self.darkroom_level = "None"
        elif abs(settings.darkrooms.value) == DarkRooms.FEW.value:
            self.darkroom_level = "Few"
        elif abs(settings.darkrooms.value) == DarkRooms.SOME.value:
            self.darkroom_level = "Some"
        elif abs(settings.darkrooms.value) == DarkRooms.MANY.value:
            self.darkroom_level = "Many"
        elif abs(settings.darkrooms.value) == DarkRooms.ALL.value:
            self.darkroom_level = "All"
        if settings.darkrooms.value >= 0:
            self.darkroom_cursed = False
        else:
            self.darkroom_cursed = True
 
        if settings.dungeon_shuffle.value == DungeonShuffle.NONE.value:
            self.dungeon_shuffle = "None"
        elif settings.dungeon_shuffle.value == DungeonShuffle.BASIC.value:
            self.dungeon_shuffle = "Basic"
        elif settings.dungeon_shuffle.value == DungeonShuffle.CHAOS.value:
            self.dungeon_shuffle = "Chaos"
        elif settings.dungeon_shuffle.value == DungeonShuffle.CLUSTERED.value:
            self.dungeon_shuffle = "Clustered"

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
        self.exit_log = []
        self.spoilers = []
        self.required_items = [20, 36]
        self.good_items = [10, 13, 24, 25, 37, 62, 63, 64]
        self.trolly_locations = [32, 45, 64, 65, 102, 108, 121, 128, 136, 147]
        self.free_locations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 24, 33, 34, 35, 36, 37, 38, 39]
        self.completable_guaranteed_freedan_locations = [19,29,74,94,122,142]    # Completable logic requires these particular ones to be transformation DSes
        self.optional_nodes = [INACCESSIBLE, 491, 600, 601, 602, 604, 605, 606, 607]  # Artificial nodes, not required by competable logic
        self.map_patches = []
        self.visited = []
        self.items_collected = []
        self.item_destinations = []
        self.open_locations = []   # Pool sublists are added to this in initialization
        self.open_edges = []
        self.graph_viz = None
        self.all_darkrooms = []
        self.max_darkrooms = 0
        self.asar_defines = { "DummyDefine": "DummyDefine" }

        # Dark Space info required for random start.
        # ID is shared with the DS's entry in item_locations (or -1 for School).
        # Format: { ID: [0: Safety type,
        #                1: Map ID outside DS,
        #                2: DS index in-game
        #               ] }
        self.spawn_locations = {
            -1:  ["",       0x08, 0x00],  # School
            10:  ["Safe",   0x01, 0x00],  # Cape exterior
            14:  ["",       0x0b, 0x01],  # Prison
            19:  ["Unsafe", 0x12, 0x02],  # EdDg final
            22:  ["Safe",   0x15, 0x03],  # Itory
            29:  ["Unsafe", 0x28, 0x04],  # Inca near melody
            30:  ["Unsafe", 0x26, 0x05],  # Inca slug DS
            31:  ["",       0x1e, 0x06],  # Inca Castoth
            39:  ["Safe",   0x34, 0x07],  # Freejia
            46:  ["Unsafe", 0x40, 0x08],  # Mine hidden
            47:  ["Unsafe", 0x3d, 0x09],  # Mine near false wall
            48:  ["",       0x42, 0x0a],  # Mine behind false wall
            57:  ["Safe",   0x4c, 0x0b],  # SkGn foyer
            58:  ["Unsafe", 0x56, 0x0c],  # SkGn blue room
            59:  ["",       0x51, 0x0d],  # SkGn inside fence
            60:  ["Unsafe", 0x54, 0x0e],  # SkGn NW dark side
            66:  ["Safe",   0x5a, 0x0f],  # SeaPal
            74:  ["",       0x60, 0x10],  # Mu NE
            75:  ["",       0x62, 0x11],  # Mu W
            77:  ["Safe",   0x6c, 0x12],  # Angl
            88:  ["Safe",   0x7c, 0x13],  # Wtrm
            93:  ["Unsafe", 0x85, 0x14],  # GtWl 1
            94:  ["Unsafe", 0x86, 0x15],  # GtWl Spin Dash
            95:  ["",       0x88, 0x16],  # GtWl final
            103: ["Safe",   0x99, 0x17],  # Euro
            109: ["Unsafe", 0xa1, 0x18],  # Kress 1
            110: ["Unsafe", 0xa3, 0x19],  # Kress 2
            111: ["",       0xa7, 0x1a],  # Kress 3
            114: ["Safe",   0xac, 0x1b],  # NtVl
            122: ["Unsafe", 0xb6, 0x1c],  # Ankr Garden
            123: ["",       0xb8, 0x1d],  # Ankr inner east
            124: ["Unsafe", 0xbb, 0x1e],  # Ankr dropdown
            129: ["Safe",   0xc3, 0x1f],  # Dao
            130: ["",       0xcc, 0x20],  # Pymd upper
            142: ["Unsafe", 0xcc, 0x21],  # Pymd lower
            145: ["Forced Unsafe", 0xdf, 0x22],  # Babel lower
            146: ["Safe",   0xe3, 0x23]   # Babel upper
        }

        # Initialize item pool
        # Format = { ID: [0: Quantity
        #                 1: Type (1=item, 2=ability, 3=statue, 4=game state, 5=monster orb, 6=artificial),
        #                 2: Engine item ID, 
        #                 3: Name, 
        #                 4: TakesInventorySpace,
        #                 5: ProgressionType (1=unlocks new locations,2=quest item,3=no progression),
        #                 6: ShufflePool (populated during world initialization)
        #                ] }
        self.item_pool = {
            # Items
            0: [2, 1,  0x00, "Nothing", False, 3, 0],
            1: [45, 1, 0x01, "Red Jewel", False, 1, 0],
            2: [1, 1,  0x02, "Prison Key", True, 1, 0],
            3: [1, 1,  0x03, "Inca Statue A", True, 1, 0],
            4: [1, 1,  0x04, "Inca Statue B", True, 2, 0],
            #5: [0, 1,  0x05, "Inca Melody", True, 3, 0],  # Not implemented
            6: [12, 1, 0x06, "Herb", False, 3, 0],
            7: [1, 1,  0x07, "Diamond Block", True, 1, 0],
            8: [1, 1,  0x08, "Wind Melody", True, 1, 0],
            9: [1, 1,  0x09, "Lola's Melody", True, 1, 0],
            10: [1, 1, 0x0a, "Large Roast", True, 1, 0],
            11: [1, 1, 0x0b, "Mine Key A", True, 1, 0],
            12: [1, 1, 0x0c, "Mine Key B", True, 2, 0],
            13: [1, 1, 0x0d, "Memory Melody", True, 1, 0],
            14: [4, 1, 0x0e, "Crystal Ball", True, 2, 0],
            15: [1, 1, 0x0f, "Elevator Key", True, 1, 0],
            16: [1, 1, 0x10, "Mu Palace Key", True, 1, 0],
            17: [1, 1, 0x11, "Purity Stone", True, 1, 0],
            18: [2, 1, 0x12, "Hope Statue", True, 1, 0],
            19: [2, 1, 0x13, "Rama Statue", False, 2, 0],
            20: [1, 1, 0x14, "Magic Dust", True, 2, 0],
            21: [0, 1, 0x15, "Blue Journal", False, 3, 0],
            22: [1, 1, 0x16, "Lance Letter", False, 3, 0],
            23: [1, 1, 0x17, "Necklace", True, 1, 0],
            24: [1, 1, 0x18, "Will", True, 1, 0],
            25: [1, 1, 0x19, "Teapot", True, 1, 0],
            26: [3, 1, 0x1a, "Mushroom Drops", True, 1, 0],
            #27: [0, 1, 0x1b, "Bag of Gold", False, 3, 0],  # Not implemented
            28: [1, 1, 0x1c, "Black Glasses", False, 1, 0],
            29: [1, 1, 0x1d, "Gorgon Flower", True, 1, 0],
            30: [1, 1, 0x1e, "Hieroglyph", False, 2, 0],
            31: [1, 1, 0x1f, "Hieroglyph", False, 2, 0],
            32: [1, 1, 0x20, "Hieroglyph", False, 2, 0],
            33: [1, 1, 0x21, "Hieroglyph", False, 2, 0],
            34: [1, 1, 0x22, "Hieroglyph", False, 2, 0],
            35: [1, 1, 0x23, "Hieroglyph", False, 2, 0],
            36: [1, 1, 0x24, "Aura", True, 1, 0],
            37: [1, 1, 0x25, "Lola's Letter", False, 1, 0],
            38: [1, 1, 0x26, "Journal", False, 2, 0],
            39: [1, 1, 0x27, "Crystal Ring", False, 1, 0],
            40: [1, 1, 0x28, "Apple", True, 1, 0],
            41: [1, 1, 0x2e, "2 Red Jewels", False, 1, 0],
            42: [1, 1, 0x2f, "3 Red Jewels", False, 1, 0],

            # Status Upgrades
            # Mapped to artificial items whose IDs are $5E lower (e.g. $87 -> $29),
            # so $8c/$8d are skipped since they'd map to $2e/$2f which are in use.
            50: [3, 1, 0x87, "HP Upgrade", False, 3, 0],
            51: [1, 1, 0x89, "DEF Upgrade", False, 3, 0],
            52: [2, 1, 0x88, "STR Upgrade", False, 3, 0],
            53: [1, 1, 0x8a, "Dash Upgrade", False, 3, 0],
            54: [2, 1, 0x8b, "Friar Upgrade", False, 3, 0],
            55: [0, 1, 0x8e, "Heart Piece", False, 3, 0],

            # Abilities
            60: [0, 2, "", "Nothing", False, 3, 0],
            61: [1, 2, "", "Psycho Dash", False, 1, 0],
            62: [1, 2, "", "Psycho Slider", False, 1, 0],
            63: [1, 2, "", "Spin Dash", False, 1, 0],
            64: [1, 2, "", "Dark Friar", False, 1, 0],
            65: [1, 2, "", "Aura Barrier", False, 1, 0],
            66: [1, 2, "", "Earthquaker", False, 1, 0],
            67: [0, 2, "", "Firebird", False, 3, 0],

            # Mystic Statues
            100: [1, 3, "", "Mystic Statue 1", False, 2, 0],
            101: [1, 3, "", "Mystic Statue 2", False, 2, 0],
            102: [1, 3, "", "Mystic Statue 3", False, 2, 0],
            103: [1, 3, "", "Mystic Statue 4", False, 2, 0],
            104: [1, 3, "", "Mystic Statue 5", False, 2, 0],
            105: [1, 3, "", "Mystic Statue 6", False, 2, 0],
            106: [0, 3, "", "Mystic Statue", False, 2, 0],

            # Event Switches
            500: [1, 4, "", "Kara Released", False, 1, 0],
            501: [1, 4, "", "Itory: Got Lilly", False, 1, 0],
            502: [1, 4, "", "Moon Tribe: Healed Spirits", False, 1, 0],
            503: [1, 4, "", "Inca: Beat Castoth", False, 1, 0],
            504: [1, 4, "", "Freejia: Found Laborer", False, 1, 0],
            505: [1, 4, "", "Neil's: Memory Restored", False, 1, 0],
            506: [1, 4, "", "Sky Garden: Map 82 NW Switch", False, 1, 0],
            507: [1, 4, "", "Sky Garden: Map 82 NE Switch", False, 1, 0],
            508: [1, 4, "", "Sky Garden: Map 82 SE Switch", False, 1, 0],
            509: [1, 4, "", "Sky Garden: Map 84 Switch", False, 1, 0],
            510: [1, 4, "", "Seaside: Fountain Purified", False, 1, 0],
            511: [1, 4, "", "Mu: Water Lowered 1", False, 1, 0],
            512: [1, 4, "", "Mu: Water Lowered 2", False, 1, 0],
            513: [1, 4, "", "Angel: Puzzle Complete", False, 1, 0],
            514: [1, 4, "", "Mt Kress: Drops Used 1", False, 1, 0],
            515: [1, 4, "", "Mt Kress: Drops Used 2", False, 1, 0],
            516: [1, 4, "", "Mt Kress: Drops Used 3", False, 1, 0],
            517: [1, 4, "", "Pyramid: Hieroglyphs Placed", False, 1, 0],
            518: [1, 4, "", "Babel: Castoth Defeated", False, 1, 0],
            519: [1, 4, "", "Babel: Viper Defeated", False, 1, 0],
            520: [1, 4, "", "Babel: Vampires Defeated", False, 1, 0],
            521: [1, 4, "", "Babel: Sand Fanger Defeated", False, 1, 0],
            522: [1, 4, "", "Babel: Mummy Queen Defeated", False, 1, 0],
            523: [1, 4, "", "Mansion: Solid Arm Defeated", False, 1, 0],
            524: [1, 4, "", "Inca: Diamond Block Placed", False, 1, 0],
            525: [1, 4, "", "Pyramid: Portals open", False, 1, 0],
            526: [1, 4, "", "Mu: Access to Hope Room 1", False, 1, 0],
            527: [1, 4, "", "Mu: Access to Hope Room 2", False, 1, 0],

            # Misc. game states
            600: [0, 6, "", "Freedan Access", False, 1, 0],
            601: [1, 6, "", "Glitches", False, 1, 0],
            602: [1, 6, "", "Early Firebird enabled", False, 1, 0],
            #603: [0, 6, "", "Firebird", False, 1, 0],   # Firebird item is 67 instead of this
            604: [1, 6, "", "Flute", False, 1, 0],
            605: [1, 6, "", "Dungeon Shuffle: No", False, 1, 0],
            606: [1, 6, "", "Dungeon Shuffle: Basic", False, 1, 0],
            607: [1, 6, "", "Dungeon Shuffle: Chaos", False, 1, 0],
            608: [0, 6, "", "Has Any Will Ability", False, 1, 0],
            #609: [0, 6, "", "Has Any Attack", False, 1, 0],
            610: [0, 6, "", "Has Any Ranged Attack", False, 1, 0],
            
            # Orbs that open doors
            700: [1, 5, 0x01, "Open Underground Tunnel Skeleton Cage", False, 3, 0],
            701: [1, 5, 0x02, "Open Underground Tunnel First Worm Door", False, 1, 0],
            702: [1, 5, 0x03, "Open Underground Tunnel Second Worm Door", False, 1, 0],
            703: [1, 5, 0x05, "Open Underground Tunnel West Room Bat Door", False, 1, 0],
            704: [1, 5, 0x16, "Open Underground Tunnel Hidden Dark Space", False, 1, 0],
            705: [1, 5, 0x17, "Open Underground Tunnel Red Skeleton Barrier 1", False, 1, 0],
            706: [1, 5, 0x18, "Open Underground Tunnel Red Skeleton Barrier 2", False, 1, 0],
            707: [1, 5, 0x0d, "Open Incan Ruins West Ladder", False, 3, 0],
            708: [1, 5, 0x0e, "Open Incan Ruins Final Ladder", False, 3, 0],
            709: [1, 5, 0x0f, "Open Incan Ruins Entrance Ladder", False, 3, 0],
            710: [1, 5, 0x0c, "Open Incan Ruins Water Room Ramp", False, 1, 0],
            711: [1, 5, 0x0b, "Open Incan Ruins East-West Freedan Ramp", False, 1, 0],
            712: [1, 5, 0x0a, "Open Incan Ruins Diamond Block Stairs", False, 3, 0],
            713: [1, 5, 0x10, "Open Incan Ruins Singing Statue Stairs", False, 3, 0],
            714: [1, 5, 0x34, "Open Diamond Mine Tunnel Middle Fence", False, 1, 0],
            715: [1, 5, 0x35, "Open Diamond Mine Tunnel South Fence", False, 1, 0],
            716: [1, 5, 0x36, "Open Diamond Mine Tunnel North Fence", False, 1, 0],
            717: [1, 5, 0x22, "Open Diamond Mine Big Room Monster Cage", False, 3, 0],
            718: [1, 5, 0x32, "Open Diamond Mine Hidden Dark Space", False, 1, 0],
            719: [1, 5, 0x23, "Open Diamond Mine Ramp Room Worm Fence", False, 1, 0],
            720: [1, 5, 0x37, "Open Sky Garden SE Topside Friar Barrier", False, 1, 0],
            721: [1, 5, 0x30, "Open Sky Garden SE Darkside Chest Barrier", False, 1, 0],
            722: [1, 5, 0x24, "Open Sky Garden SW Topside Cyber Barrier", False, 1, 0],
            723: [1, 5, 0x2b, "Open Sky Garden SW Topside Cyber Ledge", False, 3, 0],
            724: [1, 5, 0x2c, "Open Sky Garden SW Topside Worm Barrier", False, 3, 0],
            725: [1, 5, 0x31, "Open Sky Garden SW Darkside Fire Cages", False, 3, 0],
            726: [1, 5, 0x3d, "Open Mu Entrance Room Barrier", False, 1, 0],
            727: [1, 5, 0x3e, "Open Mu Northeast Room Rock 1", False, 1, 0],
            728: [1, 5, 0x3f, "Open Mu Northeast Room Rock 2", False, 1, 0],
            729: [1, 5, 0x42, "Open Mu West Room Slime Cages", False, 3, 0],
            730: [1, 5, 0x41, "Open Mu East-Facing Stone Head", False, 3, 0],
            731: [1, 5, 0x40, "Open Mu South-Facing Stone Head", False, 3, 0],
            732: [1, 5, 0x53, "Open Great Wall Archer Friar Barrier", False, 1, 0],
            #733: [1, 5, 0x6a, "Open Great Wall Fanger Arena Exit", False, 1, 0], # Probably shouldn't randomize this...
            734: [1, 5, 0x68, "Open Mt. Temple West Chest Shortcut", False, 3, 0],
            735: [1, 5, 0x6c, "Open Ankor Wat Entrance Stairs", False, 1, 0],
            736: [1, 5, 0x6b, "Open Ankor Wat Outer East Slider Hole", False, 1, 0],
            #737: [1, 5, 0x6d, "Open Ankor Wat Pit Exit", False, 1, 0], # Probably shouldn't randomize this...
            738: [1, 5, 0x6f, "Open Ankor Wat Dark Space Corridor", False, 1, 0],
            739: [1, 5, 0x73, "Open Pyramid Foyer Upper Dark Space", False, 1, 0],
            740: [1, 5, 0x9a, "Open Jeweler's Mansion First Barrier", False, 1, 0],
            741: [1, 5, 0x9b, "Open Jeweler's Mansion Second Barrier", False, 1, 0],
            
            800: [1, 6, "", "Dungeon Shuffle artificial logic", False, 3, 0]
        }

        # Define Item/Ability/Statue locations
        # Format: { ID: [0: Region, 
        #                1: Type (1=item, 2=ability, 3=statue, 4=game state, 5=monster orb, 6=artificial),
        #                2: Filled Flag, 
        #                3: Filled Item,
        #                4: [Restricted Items],
        #                5: ASM ID label,
        #                6: Name,
        #                7: ShufflePool (populated during world initialization)
        #               ] }
        self.item_locations = {
            # Jeweler
            0:   [2, 1, False, 0, [], "Jeweler1Item", "Jeweler Reward 1                    ", 0],
            1:   [3, 1, False, 0, [], "Jeweler2Item", "Jeweler Reward 2                    ", 0],
            2:   [4, 1, False, 0, [], "Jeweler3Item", "Jeweler Reward 3                    ", 0],
            3:   [5, 1, False, 0, [], "Jeweler4Item", "Jeweler Reward 4                    ", 0],
            4:   [6, 1, False, 0, [], "Jeweler5Item", "Jeweler Reward 5                    ", 0],
            5:   [7, 1, False, 0, [], "Jeweler6Item", "Jeweler Reward 6                    ", 0],

            # South Cape
            6:   [21, 1, False, 0, [], "CapeTowerItem",       "South Cape: Bell Tower              ", 0],
            7:   [20, 1, False, 0, [], "CapeFisherItem",      "South Cape: Fisherman               ", 0],
            8:   [26, 1, False, 0, [], "CapeLancesHouseItem", "South Cape: Lance's House           ", 0],
            9:   [23, 1, False, 0, [], "CapeLolaItem",        "South Cape: Lola                    ", 0],

            10:  [21, 2, False, 0, [64, 65, 66], "DkSpSouthCapeType", "South Cape: Dark Space              ", 0],

            # Edward's
            11:  [30, 1, False, 0, [], "ECHiddenGuardItem", "Edward's Castle: Hidden Guard       ", 0],
            12:  [30, 1, False, 0, [], "ECBasementItem",    "Edward's Castle: Basement           ", 0],
            13:  [32, 1, False, 0, [], "EDHamletItem",      "Edward's Prison: Hamlet             ", 0],

            14:  [32, 2, False, 0, [64, 65, 66], "DkSpPrisonCellType", "Edward's Prison: Dark Space         ", 0],

            # Underground Tunnel
            15:  [42, 1, False, 0, [], "EDSpikeChestItem",     "Underground Tunnel: Spike's Chest   ", 0],
            16:  [44, 1, False, 0, [], "EDSmallRoomChestItem", "Underground Tunnel: Small Room Chest", 0],
            17:  [705,1, False, 0, [], "EDEndChestItem",       "Underground Tunnel: Ribber's Chest  ", 0],
            18:  [49, 1, False, 0, [], "EDEndBarrelsItem",     "Underground Tunnel: Barrels         ", 0],

            19:  [720,2, False, 0, [61, 62, 63, 64, 65, 66], "DkSpPrisonEndType", "Underground Tunnel: Dark Space      ", 0],
            
            700: [41, 5, False, 0, [],  "EDCageWormItem",      "Underground Tunnel: Worm for East Skeleton Cage", 0],
            701: [41, 5, False, 0, [],  "EDSoutheastWormItem", "Underground Tunnel: Worm for East Door", 0],
            702: [42, 5, False, 0, [],  "EDSouthwestWormItem", "Underground Tunnel: Worm for South Door", 0],
            703: [43, 5, False, 0, [],  "EDDoorBatItem",       "Underground Tunnel: Bat for West Door", 0],
            704: [47, 5, False, 0, [],  "EDDarkSpaceWormItem", "Underground Tunnel: Worm for Appearing Dark Space", 0],
            705: [704, 5, False, 0, [], "EDSkeleton1Item",     "Underground Tunnel: Red Skeleton 1", 0],
            706: [705, 5, False, 0, [], "EDSkeleton2Item",     "Underground Tunnel: Red Skeleton 2", 0],

            # Itory
            20:  [51, 1, False, 0, [], "ItoryLogsItem", "Itory Village: Logs                 ", 0],
            21:  [58, 1, False, 0, [], "ItoryCaveItem", "Itory Village: Cave                 ", 0],

            22:  [51, 2, False, 0, [64, 65, 66], "DkSpItoryType", "Itory Village: Dark Space           ", 0],

            # Moon Tribe
            23:  [62, 1, False, 0, [], "MoonTribeCaveItem", "Moon Tribe: Cave                    ", 0],

            # Inca
            24:  [71, 1, False, 0, [], "IncaDiamondBlockChestItem", "Inca Ruins: Diamond-Block Chest     ", 0],
            25:  [92, 1, False, 0, [], "IncaMazeChestItem",         "Inca Ruins: Broken Statues Chest    ", 0],
            26:  [83, 1, False, 0, [], "IncaStatueChestItem",       "Inca Ruins: Stone Lord Chest        ", 0],
            27:  [93, 1, False, 0, [], "IncaWormChestItem",         "Inca Ruins: Slugger Chest           ", 0],
            28:  [76, 1, False, 0, [], "IncaCliffItem",             "Inca Ruins: Singing Statue          ", 0],

            29:  [96, 2, False, 0, [61, 62, 63, 64, 65, 66], "DkSpInca1Type", "Inca Ruins: Dark Space 1            ", 0],
            30:  [93, 2, False, 0, [], "DkSpInca2Type",                       "Inca Ruins: Dark Space 2            ", 0],
            31:  [77, 2, False, 0, [], "DkSpIncaEndType",                     "Inca Ruins: Final Dark Space        ", 0],

            707: [700, 5, False, 0, [],  "IncaWestLadderItem",      "Inca Ruins: 4-Way for West Ladder", 0],
            708: [75, 5, False, 0, [],  "IncaSoutheastLadderItem", "Inca Ruins: 4-Way for SE Ladder", 0],
            709: [72, 5, False, 0, [],  "IncaNortheastLadderItem", "Inca Ruins: 4-Way for NE Ladder", 0],
            710: [82, 5, False, 0, [],  "IncaNSRampItem",          "Inca Ruins: Whirligig for N/S Ramp", 0],
            711: [707, 5, False, 0, [], "IncaEWRampItem",          "Inca Ruins: Whirligig for E/W Ramp", 0],
            712: [94, 5, False, 0, [],  "IncaDBlockMonsterItem",   "Inca Ruins: 4-Way West of Diamond Block Room", 0],
            713: [96, 5, False, 0, [],  "IncaWMelodyMonsterItem",  "Inca Ruins: 4-Way Before Singing Statue", 0],
            
            # Gold Ship
            32:  [100, 1, False, 0, [], "IncaGoldShipItem", "Gold Ship: Seth                     ", 0],

            # Diamond Coast
            33:  [102, 1, False, 0, [], "DiamondCoastJarItem", "Diamond Coast: Jar                  ", 0],

            # Freejia
            34:  [121, 1, False, 0, [], "FrejHotelItem",      "Freejia: Hotel                      ", 0],
            35:  [110, 1, False, 0, [], "FrejEastSlaverItem", "Freejia: Creepy Guy                 ", 0],
            36:  [110, 1, False, 0, [], "FrejBin1Item",       "Freejia: Trash Can 1                ", 0],
            37:  [110, 1, False, 0, [], "FrejBin2Item",       "Freejia: Trash Can 2                ", 0],
            38:  [115, 1, False, 0, [], "FrejSnitchItem",     "Freejia: Snitch                     ", 0],

            39:  [125, 2, False, 0, [64, 65, 66], "DkSpFreejiaType", "Freejia: Dark Space                 ", 0],

            # Diamond Mine
            40:  [134, 1, False, 0, [], "MineChestItem",       "Diamond Mine: Chest                 ", 0],
            41:  [137, 1, False, 0, [], "MineWallSlaveItem",   "Diamond Mine: Trapped Laborer       ", 0],
            42:  [143, 1, False, 0, [], "MineRampSlaveItem",   "Diamond Mine: Laborer w/Elevator Key", 0],
            43:  [148, 1, False, 0, [], "MineMorgueItem",      "Diamond Mine: Morgue                ", 0],
            44:  [149, 1, False, 0, [], "MineCombatSlaveItem", "Diamond Mine: Laborer w/Mine Key    ", 0],
            45:  [150, 1, False, 0, [], "MineSamItem",         "Diamond Mine: Sam                   ", 0],

            46:  [721, 2, False, 0, [], "DkSpMineAppearingType", "Diamond Mine: Appearing Dark Space  ", 0],
            47:  [131, 2, False, 0, [], "DkSpMineAtWallType",    "Diamond Mine: Dark Space at Wall    ", 0],
            48:  [142, 2, False, 0, [], "DkSpMineBehindType",    "Diamond Mine: Dark Space behind Wall", 0],

            714: [701, 5, False, 0, [], "MineMidFenceItem",      "Diamond Mine: Lizard for Tunnel Middle Fence", 0],
            715: [130, 5, False, 0, [], "MineSouthFenceItem",    "Diamond Mine: Eye for Tunnel South Fence", 0],
            716: [709, 5, False, 0, [], "MineNorthFenceItem",    "Diamond Mine: Eye for Tunnel North Fence", 0],
            717: [134, 5, False, 0, [], "MineWormCageItem",      "Diamond Mine: Worm for Big Room Cage", 0],
            718: [136, 5, False, 0, [], "MineWormDarkSpaceItem", "Diamond Mine: Worm for Appearing Dark Space", 0],
            719: [710, 5, False, 0, [], "MineFriarFenceItem",    "Diamond Mine: Worm for Friar Ramp Fence", 0],

            # Sky Garden
            49:  [172, 1, False, 0, [], "SGNENorthChestItem",  "Sky Garden: (NE) Platform Chest     ", 0],
            50:  [173, 1, False, 0, [], "SGNEWestChestItem",   "Sky Garden: (NE) Blue Cyber Chest   ", 0],
            51:  [174, 1, False, 0, [], "SGNEStatueChestItem", "Sky Garden: (NE) Statue Chest       ", 0],
            52:  [716, 1, False, 0, [], "SGSEChestItem",       "Sky Garden: (SE) Dark Side Chest    ", 0],
            53:  [185, 1, False, 0, [], "SGSWTopChestItem",    "Sky Garden: (SW) Ramp Chest         ", 0],
            54:  [186, 1, False, 0, [], "SGSWBotChestItem",    "Sky Garden: (SW) Dark Side Chest    ", 0],
            55:  [194, 1, False, 0, [], "SGNWTopChestItem",    "Sky Garden: (NW) Top Chest          ", 0],
            56:  [194, 1, False, 0, [], "SGNWBotChestItem",    "Sky Garden: (NW) Bottom Chest       ", 0],

            57:  [170, 2, False, 0, [64, 65, 66], "DkSpSGFoyerType", "Sky Garden: Dark Space (Foyer)      ", 0],
            58:  [169, 2, False, 0, [], "DkSpSGSEType", "Sky Garden: Dark Space (SE)         ", 0],  # in the room
            59:  [183, 2, False, 0, [], "DkSpSGSWType", "Sky Garden: Dark Space (SW)         ", 0],
            60:  [195, 2, False, 0, [], "DkSpSGNWType", "Sky Garden: Dark Space (NW)         ", 0],

            720: [711, 5, False, 0, [], "SGSETopBarrierItem", "Sky Garden: (SE) Top Robot for Center Barrier", 0],
            721: [180, 5, False, 0, [], "SGSEBotBarrierItem", "Sky Garden: (SE) Bottom Robot for Chest", 0],
            722: [181, 5, False, 0, [], "SGSWTopPegGateItem", "Sky Garden: (SW) Top Robot for Peg Gate", 0],
            723: [168, 5, False, 0, [], "SGSWTopRobotRampItem", "Sky Garden: (SW) Top Robot for Robot Ramp", 0],
            724: [182, 5, False, 0, [], "SGSWTopWormGateItem", "Sky Garden: (SW) Top Worm for West Gate", 0],
            725: [187, 5, False, 0, [], "SGSWBotFireCageItem", "Sky Garden: (SW) Bot Robot for Fire Cages", 0],

            # Seaside Palace
            61:  [202, 1, False, 0, [], "SeaPalSideChestItem", "Seaside Palace: Side Room Chest     ", 0],
            62:  [200, 1, False, 0, [], "SeaPalTopChestItem", "Seaside Palace: First Area Chest    ", 0],
            63:  [205, 1, False, 0, [], "SeaPalBotChestItem", "Seaside Palace: Second Area Chest   ", 0],
            64:  [206, 1, False, 0, [], "SeaPalBuffyItem", "Seaside Palace: Buffy               ", 0],
            65:  [208, 1, False, 0, [], "SeaPalCoffinItem", "Seaside Palace: Coffin              ", 0],

            66:  [200, 2, False, 0, [64, 65, 66], "DkSpSeaPalType", "Seaside Palace: Dark Space          ", 0],

            # Mu
            67:  [217, 1, False, 0, [], "MuEmptyChest1Item", "Mu: Empty Chest 1                   ", 0],
            68:  [220, 1, False, 0, [], "MuEmptyChest2Item", "Mu: Empty Chest 2                   ", 0],
            69:  [225, 1, False, 0, [], "MuHopeStatue1Item", "Mu: Hope Statue 1                   ", 0],
            70:  [236, 1, False, 0, [], "MuHopeStatue2Item", "Mu: Hope Statue 2                   ", 0],
            71:  [215, 1, False, 0, [], "MuHopeRoomChestItem", "Mu: Chest s/o Hope Room 2           ", 0],
            72:  [214, 1, False, 0, [], "MuRamaChestNItem", "Mu: Rama Chest N                    ", 0],
            73:  [219, 1, False, 0, [], "MuRamaChestEItem", "Mu: Rama Chest E                    ", 0],

            74:  [218, 2, False, 0, [61, 62, 63, 64, 65, 66], "DkSpMuTransformType", "Mu: Open Dark Space                 ", 0],
            75:  [228, 2, False, 0, [], "DkSpMuSliderType", "Mu: Slider Dark Space               ", 0],

            726: [212, 5, False, 0, [], "MuEntranceGolemItem", "Mu: Entrance Golem for Gate", 0],
            727: [726, 5, False, 0, [], "MuDroplet1Item", "Mu: NE Droplet for Rock 1", 0],
            728: [724, 5, False, 0, [], "MuDroplet2Item", "Mu: NE Droplet for Rock 2", 0],
            729: [227, 5, False, 0, [], "MuSlimeCageItem", "Mu: West Slime for Slime Cages", 0],
            730: [236, 5, False, 0, [], "MuEastFacingHeadGolemItem", "Mu: SE Golem for East-facing Head", 0],
            731: [236, 5, False, 0, [], "MuSouthFacingHeadGolemItem", "Mu: SE Golem for South-facing Head", 0],

            # Angel Village
            76:  [254, 1, False, 0, [], "AnglDanceHallItem", "Angel Village: Dance Hall           ", 0],
            77:  [255, 2, False, 0, [64, 65, 66], "DkSpAngelVillageType", "Angel Village: Dark Space           ", 0],

            # Angel Dungeon
            78:  [265, 1, False, 0, [], "AnglSliderChestItem", "Angel Dungeon: Slider Chest         ", 0],
            79:  [271, 1, False, 0, [], "AnglIshtarSidePotItem", "Angel Dungeon: Ishtar's Room        ", 0],
            80:  [274, 1, False, 0, [], "AnglPuzzleChest1Item", "Angel Dungeon: Puzzle Chest 1       ", 0],
            81:  [274, 1, False, 0, [], "AnglPuzzleChest2Item", "Angel Dungeon: Puzzle Chest 2       ", 0],
            82:  [273, 1, False, 0, [], "AnglIshtarWinChestItem", "Angel Dungeon: Ishtar's Chest       ", 0],

            # Watermia
            83:  [280, 1, False, 0, [], "WtrmWestJarItem", "Watermia: West Jar                  ", 0],
            85:  [286, 1, False, 0, [], "WtrmLanceItem", "Watermia: Lance                     ", 0],
            86:  [283, 1, False, 0, [], "WtrmDesertJarItem", "Watermia: Gambling House            ", 0],
            87:  [280, 1, False, 0, [], "WtrmRussianGlassItem", "Watermia: Russian Glass             ", 0],

            88:  [282, 2, False, 0, [64, 65, 66], "DkSpWatermiaType", "Watermia: Dark Space                ", 0],

            # Great Wall
            89:  [290, 1, False, 0, [], "GtWlNecklace1Item", "Great Wall: Necklace 1              ", 0],
            90:  [292, 1, False, 0, [], "GtWlNecklace2Item", "Great Wall: Necklace 2              ", 0],
            91:  [292, 1, False, 0, [], "GtWlChest1Item", "Great Wall: Chest 1                 ", 0],
            92:  [294, 1, False, 0, [], "GtWlChest2Item", "Great Wall: Chest 2                 ", 0],

            93:  [295, 2, False, 0, [], "DkSpGreatWall1Type", "Great Wall: Archer Dark Space       ", 0],
            94:  [297, 2, False, 0, [61, 62, 63, 64, 65, 66], "DkSpGreatWallSpinType", "Great Wall: Platform Dark Space     ", 0],
            95:  [300, 2, False, 0, [], "DkSpGreatWallEndType", "Great Wall: Appearing Dark Space    ", 0],

            732: [712, 5, False, 0, [], "GtWlArcherItem", "Great Wall: Archer for Friar Gate", 0],

            # Euro
            96:  [310, 1, False, 0, [], "EuroAlleyItem", "Euro: Alley                         ", 0],
            97:  [310, 1, False, 0, [], "EuroAppleVendorItem", "Euro: Apple Vendor                  ", 0],
            98:  [320, 1, False, 0, [], "EuroHiddenHouseItem", "Euro: Hidden House                  ", 0],
            99:  [323, 1, False, 0, [], "EuroShop1Item", "Euro: Store Item 1                  ", 0],
            100: [323, 1, False, 0, [], "EuroShop2Item", "Euro: Store Item 2                  ", 0],
            101: [321, 1, False, 0, [], "EuroSlaveRoomBarrelItem", "Euro: Shrine                        ", 0],
            102: [315, 1, False, 0, [], "EuroAnnItem", "Euro: Ann                           ", 0],

            103: [325, 2, False, 0, [64, 65, 66], "DkSpEuroType", "Euro: Dark Space                    ", 0],

            # Mt Temple
            104: [336, 1, False, 0, [], "KressChest1Item", "Mt. Temple: Red Jewel Chest         ", 0],
            105: [338, 1, False, 0, [], "KressChest2Item", "Mt. Temple: Drops Chest 1           ", 0],
            106: [342, 1, False, 0, [], "KressChest3Item", "Mt. Temple: Drops Chest 2           ", 0],
            107: [343, 1, False, 0, [], "KressChest4Item", "Mt. Temple: Drops Chest 3           ", 0],
            108: [345, 1, False, 0, [], "KressChest5Item", "Mt. Temple: Final Chest             ", 0],

            109: [332, 2, False, 0, [], "DkSpKress1Type", "Mt. Temple: Dark Space 1            ", 0],
            110: [337, 2, False, 0, [], "DkSpKress2Type", "Mt. Temple: Dark Space 2            ", 0],
            111: [343, 2, False, 0, [], "DkSpKress3Type", "Mt. Temple: Dark Space 3            ", 0],

            734: [338, 5, False, 0, [], "KressSkullShortcutItem", "Mt. Temple: Skull for Drops Chest 1 Shortcut", 0],

            # Natives'
            112: [353, 1, False, 0, [], "NativesPotItem", "Natives' Village: Statue Room       ", 0],
            113: [354, 1, False, 0, [], "NativesGirlItem", "Natives' Village: Statue            ", 0],

            114: [350, 2, False, 0, [64, 65, 66], "DkSpNativesType", "Natives' Village: Dark Space        ", 0],

            # Ankor Wat
            115: [361, 1, False, 0, [], "WatChest1Item", "Ankor Wat: Ramp Chest               ", 0],
            116: [370, 1, False, 0, [], "WatChest2Item", "Ankor Wat: Flyover Chest            ", 0],
            117: [378, 1, False, 0, [], "WatChest3Item", "Ankor Wat: U-Turn Chest             ", 0],
            118: [382, 1, False, 0, [], "WatChest4Item", "Ankor Wat: Drop Down Chest          ", 0],
            119: [389, 1, False, 0, [], "WatChest5Item", "Ankor Wat: Forgotten Chest          ", 0],
            120: [380, 1, False, 0, [], "WatGlassesItem", "Ankor Wat: Glasses Location         ", 0],
            121: [391, 1, False, 0, [], "WatSpiritItem", "Ankor Wat: Spirit                   ", 0],

            122: [372, 2, False, 0, [61, 62, 63, 64, 65, 66], "DkSpWatGardenType", "Ankor Wat: Garden Dark Space        ", 0],
            123: [377, 2, False, 0, [], "DkSpWatQuakeType", "Ankor Wat: Earthquaker Dark Space   ", 0],
            124: [383, 2, False, 0, [], "DkSpWatDropType", "Ankor Wat: Drop Down Dark Space     ", 0],

            735: [739, 5, False, 0, [], "WatSouthScarabItem", "Ankor Wat: Scarab for Outer South Stair", 0],
            736: [364, 5, False, 0, [], "WatEastSliderHoleItem", "Ankor Wat: Scarab for Outer East Slider Hole", 0],
            738: [727, 5, False, 0, [], "WatDarkSpaceHallItem", "Ankor Wat: Skull for Inner East DS Hall", 0],

            # Dao
            125: [400, 1, False, 0, [], "DaoEntrance1Item", "Dao: Entrance Item 1                ", 0],
            126: [400, 1, False, 0, [], "DaoEntrance2Item", "Dao: Entrance Item 2                ", 0],
            127: [400, 1, False, 0, [], "DaoGrassItem", "Dao: East Grass                     ", 0],
            128: [403, 1, False, 0, [], "DaoSnakeGameItem", "Dao: Snake Game                     ", 0],

            129: [400, 2, False, 0, [64, 65, 66], "DkSpDaoType", "Dao: Dark Space                     ", 0],

            # Pyramid
            130: [713, 1, False, 0, [], "PyramidGaiaItem", "Pyramid: Dark Space Top             ", 0],
            131: [412, 1, False, 0, [], "PyramidFoyerItem", "Pyramid: Hidden Platform            ", 0],
            132: [442, 1, False, 0, [], "PyramidHiero1Item", "Pyramid: Hieroglyph 1               ", 0],
            133: [422, 1, False, 0, [], "PyramidRoom2ChestItem", "Pyramid: Room 2 Chest               ", 0],
            134: [443, 1, False, 0, [], "PyramidHiero2Item", "Pyramid: Hieroglyph 2               ", 0],
            135: [432, 1, False, 0, [], "PyramidRoom3ChestItem", "Pyramid: Room 3 Chest               ", 0],
            136: [444, 1, False, 0, [], "PyramidHiero3Item", "Pyramid: Hieroglyph 3               ", 0],
            137: [439, 1, False, 0, [], "PyramidRoom4ChestItem", "Pyramid: Room 4 Chest               ", 0],
            138: [445, 1, False, 0, [], "PyramidHiero4Item", "Pyramid: Hieroglyph 4               ", 0],
            139: [428, 1, False, 0, [], "PyramidRoom5ChestItem", "Pyramid: Room 5 Chest               ", 0],
            140: [446, 1, False, 0, [], "PyramidHiero5Item", "Pyramid: Hieroglyph 5               ", 0],
            141: [447, 1, False, 0, [], "PyramidHiero6Item", "Pyramid: Hieroglyph 6               ", 0],

            142: [413, 2, True, 0, [61, 62, 63, 64, 65, 66], "DkSpPyramidBotType", "Pyramid: Dark Space Bottom          ", 0],

            739: [411, 5, False, 0, [], "PyramidEntranceOrbsItem", "Pyramid: Entrance Orbs for DS Gate", 0],

            # Babel
            143: [461, 1, False, 0, [], "BabelPillowItem", "Babel: Pillow                       ", 0],
            144: [461, 1, False, 0, [], "BabelForceFieldItem", "Babel: Force Field                  ", 0],

            145: [461, 2, False, 0, [64, 65, 66], "DkSpBabelBotType", "Babel: Dark Space Bottom            ", 0],
            146: [472, 2, False, 0, [64, 65, 66], "DkSpBabelTopType", "Babel: Dark Space Top               ", 0],

            # Jeweler's Mansion
            147: [715, 1, False, 0, [], "MansionChestItem", "Jeweler's Mansion: Chest            ", 0],

            740: [480, 5, False, 0, [], "MansionEastGateItem", "Jeweler's Mansion: Enemy for East Gate", 0],
            741: [714, 5, False, 0, [], "MansionWestGateItem", "Jeweler's Mansion: Enemy for West Gate", 0],

            # Mystic Statues
            148: [101, 3, False, 0, [101, 102, 103, 104, 105], "", "Castoth Prize                       ", 0],
            149: [198, 3, False, 0, [100, 102, 103, 104, 105], "", "Viper Prize                         ", 0],
            150: [244, 3, False, 0, [100, 101, 103, 104, 105], "", "Vampires Prize                      ", 0],
            151: [302, 3, False, 0, [100, 101, 102, 104, 105], "", "Sand Fanger Prize                   ", 0],
            152: [448, 3, False, 0, [100, 101, 102, 103, 105], "", "Mummy Queen Prize                   ", 0],
            153: [479, 3, False, 0, [100, 101, 102, 103, 104], "", "Babel Prize                         ", 0],

            # Event Switches
            500: [500, 4, True, 500, [], "", "Kara                                ", 0],
            501: [501, 4, True, 501, [], "", "Lilly                               ", 0],
            502: [502, 4, True, 502, [], "", "Moon Tribe: Spirits Healed          ", 0],
            503: [503, 4, True, 503, [], "", "Inca: Castoth defeated              ", 0],
            504: [504, 4, True, 504, [], "", "Freejia: Found Laborer              ", 0],
            505: [505, 4, True, 505, [], "", "Neil's Memory Restored              ", 0],
            506: [506, 4, True, 506, [], "", "Sky Garden: Map 82 NW Switch        ", 0],
            507: [507, 4, True, 507, [], "", "Sky Garden: Map 82 NE Switch        ", 0],
            508: [508, 4, True, 508, [], "", "Sky Garden: Map 82 SE Switch        ", 0],
            509: [509, 4, True, 509, [], "", "Sky Garden: Map 84 Switch           ", 0],
            510: [510, 4, True, 510, [], "", "Seaside: Fountain Purified          ", 0],
            511: [511, 4, True, 511, [], "", "Mu: Water Lowered 1                 ", 0],
            512: [512, 4, True, 512, [], "", "Mu: Water Lowered 2                 ", 0],
            513: [513, 4, True, 513, [], "", "Angel: Puzzle Complete              ", 0],
            514: [514, 4, True, 514, [], "", "Mt Kress: Drops used 1              ", 0],
            515: [515, 4, True, 515, [], "", "Mt Kress: Drops used 2              ", 0],
            516: [516, 4, True, 516, [], "", "Mt Kress: Drops used 3              ", 0],
            517: [517, 4, True, 517, [], "", "Pyramid: Hieroglyphs placed         ", 0],
            518: [518, 4, True, 518, [], "", "Babel: Castoth defeated             ", 0],
            519: [519, 4, True, 519, [], "", "Babel: Viper defeated               ", 0],
            520: [520, 4, True, 520, [], "", "Babel: Vampires defeated            ", 0],
            521: [521, 4, True, 521, [], "", "Babel: Sand Fanger defeated         ", 0],
            522: [522, 4, True, 522, [], "", "Babel: Mummy Queen defeated         ", 0],
            523: [523, 4, True, 523, [], "", "Mansion: Solid Arm defeated         ", 0],
            524: [524, 4, True, 524, [], "", "Inca: Diamond Block Placed          ", 0],
            525: [525, 4, True, 525, [], "", "Pyramid: Portals open               ", 0],
            526: [526, 4, True, 526, [], "", "Mu: Access to Hope Room 1           ", 0],
            527: [527, 4, True, 527, [], "", "Mu: Access to Hope Room 2           ", 0],

            # Misc
            600: [600, 6, True, 600, [], "", "Freedan Access                          ", 0],
            601: [601, 6, True, 601, [], "", "Glitches                                ", 0],
            602: [602, 6, True, 602, [], "", "Early Firebird enabled                  ", 0],
            603: [491, 6, True, 67,  [], "", "Firebird access                         ", 0],
            604: [604, 6, True, 604, [], "", "Flute                                   ", 0],
            605: [605, 6, True, 605, [], "", "Dungeon Shuffle: No                     ", 0],
            606: [606, 6, True, 606, [], "", "Dungeon Shuffle: Basic                  ", 0],
            607: [607, 6, True, 607, [], "", "Dungeon Shuffle: Chaos                  ", 0],
            608: [608, 6, True, 608, [], "", "Has Any Will Ability                    ", 0],
            #609: [609, 6, True, 609, [], "", "Has Any Attack                          ", 0],
            610: [610, 6, True, 610, [], "", "Has Any Ranged Attack                   ", 0]
        }

        # Shell world graph. Nodes for exits are added during initialization.
        # Format: { Region ID: [
        #                   0: Traversed_flag,
        #                   1: [AccessibleRegions],
        #                   2: type(0=other/misc,1=exterior,2=interior,3=roof),
        #                   3: [continentID (unused), areaID (unused), layer (for dungeon shuffle), MapID (for darkrooms)],
        #                   4: DS_access (0x01 = can reach DS from here; 0x02 = Freedan can reach here),
        #                   5: RegionName,
        #                   6: [ItemsToRemove],
        #                   7: ForceFormChange,
        #                   8: [AccessibleFromNodes],
        #                   9: [Accessible_DS_nodes],
        #                   10: [Accessible_Nodes_w_Logic],
        #                   11: [item_locations],
        #                   12: [origin_logic],
        #                   13: [dest_logic],
        #                   14: [origin_exits],
        #                   15: [dest_exits]
        #                   ] }
        self.graph = {
            INACCESSIBLE: [False, [], 0, [0,0,0,0], 0, "Inaccessible", [], False, [], [], [], [], [], [], [], []],
            
            # Game Start
            0: [False, [], 0, [0,0,0,0], 0, "Game Start", [], True, [], [], [], [], [], [], [], []],

            # Jeweler
            1: [False, [], 0, [0,0,0,0], 0, "Jeweler Access", [], False, [], [], [], [], [], [], [], []],
            2: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 1", [], False, [], [], [], [], [], [], [], []],
            3: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 2", [], False, [], [], [], [], [], [], [], []],
            4: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 3", [], False, [], [], [], [], [], [], [], []],
            5: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 4", [], False, [], [], [], [], [], [], [], []],
            6: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 5", [], False, [], [], [], [], [], [], [], []],
            7: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 6", [], False, [], [], [], [], [], [], [], []],
            8: [False, [], 0, [0,0,0,0], 0, "Jeweler Reward 7", [], False, [], [], [], [], [], [], [], []],

            # Overworld Menus
            10: [False, [20,30,50,60,63],      0, [1,0,0,0], 0, "Overworld: SW Continent", [], True, [], [], [], [], [], [], [], []],
            11: [False, [102,110,133,160,162], 0, [2,0,0,0], 0, "Overworld: SE Continent", [], True, [], [], [], [], [], [], [], []],
            12: [False, [250,280,290],         0, [3,0,0,0], 0, "Overworld: NE Continent", [], True, [], [], [], [], [], [], [], []],
            13: [False, [310,330,350,360],     0, [4,0,0,0], 0, "Overworld: N Continent", [], True, [], [], [], [], [], [], [], []],
            14: [False, [400,410],             0, [5,0,0,0], 0, "Overworld: NW Continent", [], True, [], [], [], [], [], [], [], []],

            # Passage Menus
            15: [False, [], 0, [0,0,0,0], 0, "Passage: Seth", [], True, [], [], [], [], [], [], [], []],
            16: [False, [], 0, [0,0,0,0], 0, "Passage: Moon Tribe", [], True, [], [], [], [], [], [], [], []],
            17: [False, [], 0, [0,0,0,0], 0, "Passage: Neil", [], True, [], [], [], [], [], [], [], []],

            # South Cape
            20: [False, [1,10],  1, [1,1,0,1], 0, "South Cape: Main Area", [], False, [], [], [], [], [], [], [], []],
            21: [False, [20],    3, [1,1,0,1], 0, "South Cape: School Roof", [], False, [], [], [], [], [], [], [], []],
            22: [False, [],      2, [1,1,0,8], 0, "South Cape: School", [], False, [], [], [], [], [], [], [], []],
            23: [False, [],      2, [1,1,0,6], 0, "South Cape: Will's House", [], False, [], [], [], [], [], [], [], []],
            24: [False, [],      2, [1,1,0,7], 0, "South Cape: East House", [], False, [], [], [], [], [], [], [], []],
            25: [False, [],      2, [1,1,0,5], 0, "South Cape: Seth's House", [], False, [], [], [], [], [], [], [], []],
            26: [False, [],      2, [1,1,0,3], 0, "South Cape: Lance's House", [], False, [], [], [], [], [], [], [], []],
            27: [False, [],      2, [1,1,0,4], 0, "South Cape: Erik's House", [], False, [], [], [], [], [], [], [], []],
            28: [False, [],      2, [1,1,0,2], 0, "South Cape: Seaside Cave", [], False, [], [], [], [], [], [], [], []],

            # Edward's / Prison
            30: [False, [10], 1, [1,2,0,10], 0, "Edward's Castle: Main Area", [], False, [], [], [], [], [], [], [], []],
            31: [False, [30], 3, [1,2,0,10], 0, "Edward's Castle: Behind Guard", [], False, [], [], [], [], [], [], [], []],
            32: [False, [],   2, [1,2,0,11], 0, "Edward's Prison: Will's Cell", [2], False, [], [], [], [], [], [], [], []],
            33: [False, [],   2, [1,2,0,11], 0, "Edward's Prison: Prison Main", [2], False, [], [], [], [], [], [], [], []],

            # Underground Tunnel
            40: [False, [],   2, [1,2,0,12], 0, "Underground Tunnel: Map 12", [], False, [], [], [], [], [], [], [], []],
            41: [False, [],   2, [1,2,0,13], 0, "Underground Tunnel: Map 13", [], False, [], [], [], [], [], [], [], []],
            42: [False, [],   2, [1,2,0,14], 0, "Underground Tunnel: Map 14", [], False, [], [], [], [], [], [], [], []],
            43: [False, [],   2, [1,2,0,15], 0, "Underground Tunnel: Map 15", [], False, [], [], [], [], [], [], [], []],
            44: [False, [],   2, [1,2,0,16], 0, "Underground Tunnel: Map 16", [], False, [], [], [], [], [], [], [], []],
            45: [False, [],   2, [1,2,0,17], 0, "Underground Tunnel: Map 17", [], False, [], [], [], [], [], [], [], []],
            47: [False, [],   2, [1,2,0,18], 0, "Underground Tunnel: Map 18 (entrance)", [], False, [], [], [], [], [], [], [], []],
            720: [False, [],  2, [1,2,0,18], 0, "Underground Tunnel: Map 18 (Dark Space)", [], False, [], [], [], [], [], [], [], []],
            704: [False, [],  2, [1,2,0,18], 0, "Underground Tunnel: Map 18 (Skeleton 1 area)", [], False, [], [], [], [], [], [], [], []],
            705: [False, [],  2, [1,2,0,18], 0, "Underground Tunnel: Map 18 (Skeleton 2 area)", [], False, [], [], [], [], [], [], [], []],
            706: [False, [],  2, [1,2,0,18], 0, "Underground Tunnel: Map 18 (Ending area)", [], False, [], [], [], [], [], [], [], []],
            49: [False, [],   2, [1,2,0,19], 0, "Underground Tunnel: Exit", [], True, [], [], [], [], [], [], [], []],

            # Itory
            50: [False, [10],     1, [1,3,0,21], 0, "Itory: Entrance", [9], False, [], [], [], [], [], [], [], []],
            51: [False, [50],     1, [1,3,0,21], 0, "Itory: Main Area", [], False, [], [], [], [], [], [], [], []],
            52: [False, [],       1, [1,3,0,21], 0, "Itory: Lilly's Back Porch", [], False, [], [], [], [], [], [], [], []],
            53: [False, [],       2, [1,3,0,22], 0, "Itory: West House", [], False, [], [], [], [], [], [], [], []],
            54: [False, [],       2, [1,3,0,24], 0, "Itory: North House", [], False, [], [], [], [], [], [], [], []],
            55: [False, [],       2, [1,3,0,23], 0, "Itory: Lilly's House", [23], False, [], [], [], [], [], [], [], []],
            56: [False, [],       2, [1,3,0,25], 0, "Itory: Cave (entrance)", [], False, [], [], [], [], [], [], [], []],
            58: [False, [],       2, [1,3,0,25], 0, "Itory: Cave (secret room)", [], False, [], [], [], [], [], [], [], []],
            59: [False, [55,501], 0, [1,3,0,23], 0, "Itory: Got Lilly", [], False, [], [], [], [], [], [], [], []],

            # Moon Tribe / Inca Entrance
            60: [False, [10],     1, [1,4,0,26], 0, "Moon Tribe: Main Area", [25], False, [], [], [], [], [], [], [], []],
            61: [False, [],       2, [1,4,0,27], 0, "Moon Tribe: Cave", [], False, [], [], [], [], [], [], [], []],
            62: [False, [61],     2, [1,4,0,27], 0, "Moon Tribe: Cave (Pedestal)", [], False, [], [], [], [], [], [], [], []],
            63: [False, [10],     1, [1,5,0,28], 0, "Inca: Entrance", [], False, [], [], [], [], [], [], [], []],
            64: [False, [60,502], 0, [1,4,0,26], 0, "Moon Tribe: Spirits Awake", [], False, [], [], [], [], [], [], [], []],

            # Inca Ruins
            70: [False, [],       2, [1,5,0,29], 0, "Inca: Map 29 (NE)", [], False, [], [], [], [], [], [], [], []],
            71: [False, [],       2, [1,5,0,29], 0, "Inca: Map 29 (NW)", [], False, [], [], [], [], [], [], [], []],
            72: [False, [73],     2, [1,5,0,29], 0, "Inca: Map 29 (N)", [], False, [], [], [], [], [], [], [], []],
            73: [False, [],       2, [1,5,0,29], 0, "Inca: Map 29 (center)", [], False, [], [], [], [], [], [], [], []],
            74: [False, [700],    2, [1,5,0,29], 0, "Inca: Map 29 (W)", [], False, [], [], [], [], [], [], [], []],
            700: [False, [],      2, [1,5,0,29], 0, "Inca: Map 29 (W 4-Way with orb)", [], False, [], [], [], [], [], [], [], []],
            75: [False, [99],     2, [1,5,0,29], 0, "Inca: Map 29 (S)", [], False, [], [], [], [], [], [], [], []],
            76: [False, [],       2, [1,5,0,29], 0, "Inca: Map 29 (statue head)", [], False, [], [], [], [], [], [], [], []],
            77: [False, [],       2, [1,5,0,30], 0, "Inca: Map 30 (E)", [3, 4], False, [], [], [], [], [], [], [], []],
            78: [False, [77],     2, [1,5,0,30], 0, "Inca: Map 30 (W)", [], False, [], [], [], [], [], [], [], []],
            79: [False, [],       2, [1,5,0,31], 0, "Inca: Map 31 (statue area)", [], False, [], [], [], [], [], [], [], []],
            69: [False, [],       2, [1,5,0,31], 0, "Inca: Map 31 (U-turn)", [], False, [], [], [], [], [], [], [], []],
            80: [False, [],       2, [1,5,0,32], 0, "Inca: Map 32 (S)", [], False, [], [], [], [], [], [], [], []],
            81: [False, [],       2, [1,5,0,32], 0, "Inca: Map 32 (N)", [], False, [], [], [], [], [], [], [], []],
            82: [False, [],       2, [1,5,0,33], 0, "Inca: Map 33 (N)", [], False, [], [], [], [], [], [], [], []],
            83: [False, [82],     2, [1,5,0,33], 0, "Inca: Map 33 (over ramp)", [], False, [], [], [], [], [], [], [], []],
            84: [False, [],       2, [1,5,0,34], 0, "Inca: Map 34", [], False, [], [], [], [], [], [], [], []],
            85: [False, [],       2, [1,5,0,35], 0, "Inca: Map 35 (E)", [], False, [], [], [], [], [], [], [], []],
            707: [False, [],      2, [1,5,0,35], 0, "Inca: Map 35 (Whirligig)", [], False, [], [], [], [], [], [], [], []],
            86: [False, [85],     2, [1,5,0,35], 0, "Inca: Map 35 (W)", [], False, [], [], [], [], [], [], [], []],
            87: [False, [],       2, [1,5,0,36], 0, "Inca: Map 36 (main)", [8], False, [], [], [], [], [], [], [], []],
            89: [False, [],       2, [1,5,0,37], 0, "Inca: Map 37 (main)", [7], False, [], [], [], [], [], [], [], []],
            91: [False, [],       2, [1,5,0,38], 0, "Inca: Map 38 (south section)", [], False, [], [], [], [], [], [], [], []],
            92: [False, [91],     2, [1,5,0,38], 0, "Inca: Map 38 (behind statues)", [], False, [], [], [], [], [], [], [], []],
            93: [False, [],       2, [1,5,0,38], 0, "Inca: Map 38 (north section)", [], False, [], [], [], [], [], [], [], []],
            94: [False, [],       2, [1,5,0,39], 0, "Inca: Map 39", [], False, [], [], [], [], [], [], [], []],
            95: [False, [96],     2, [1,5,0,40], 0, "Inca: Map 40 (entrance)", [], False, [], [], [], [], [], [], [], []],
            96: [False, [],       2, [1,5,0,40], 0, "Inca: Map 40 (past tiles)", [], False, [], [], [], [], [], [], [], []],
            97: [False, [98,503], 2, [1,5,0,41], 0, "Inca: Boss Room", [], True, [], [], [], [], [], [], [], []],
            98: [False, [97],     2, [1,5,0,41], 0, "Inca: Behind Boss Room", [], False, [], [], [], [], [], [], [], []],
            99: [False, [],       2, [1,5,0,29], 0, "Inca: Map 29 (SE door)", [], False, [], [], [], [], [], [], [], []],

            # Gold Ship / Diamond Coast
            100: [False, [104], 1, [1,5,0,44], 0, "Gold Ship: Deck", [], False, [], [], [], [], [], [], [], []],
            101: [False, [],    2, [1,5,0,46], 0, "Gold Ship: Interior", [], False, [], [], [], [], [], [], [], []],
            102: [False, [11],  1, [2,6,0,48], 0, "Diamond Coast: Main Area", [], False, [], [], [], [], [], [], [], []],
            103: [False, [],    2, [2,6,0,49], 0, "Diamond Coast: House", [], False, [], [], [], [], [], [], [], []],
            104: [False, [],    0, [1,5,0,44], 0, "Gold Ship: Crow's Nest Passage", [], False, [], [], [], [], [], [], [], []],

            # Freejia
            110: [False, [11],       1, [2,7,0,50], 0, "Freejia: Main Area", [], False, [], [], [], [], [], [], [], []],
            111: [False, [1, 110],   3, [2,7,0,50], 0, "Freejia: 2-story House Roof", [], False, [], [], [], [], [], [], [], []],
            112: [False, [],         1, [2,7,0,50], 0, "Freejia: Laborer House Roof", [], False, [], [], [], [], [], [], [], []],
            113: [False, [110, 114], 3, [2,7,0,50], 0, "Freejia: Labor Trade Roof", [], False, [], [], [], [], [], [], [], []],
            114: [False, [110, 112], 1, [2,7,0,50], 0, "Freejia: Back Alley", [], False, [], [], [], [], [], [], [], []],
            115: [False, [110],      0, [2,7,0,50], 0, "Freejia: Slaver", [], False, [], [], [], [], [], [], [], []],
            116: [False, [],         2, [2,7,0,54], 0, "Freejia: West House", [], False, [], [], [], [], [], [], [], []],
            117: [False, [],         2, [2,7,0,55], 0, "Freejia: 2-story House", [], False, [], [], [], [], [], [], [], []],
            118: [False, [],         2, [2,7,0,56], 0, "Freejia: Lovers' House", [], False, [], [], [], [], [], [], [], []],
            119: [False, [],         2, [2,7,0,57], 0, "Freejia: Hotel (common area)", [], False, [], [], [], [], [], [], [], []],
            120: [False, [],         2, [2,7,0,57], 0, "Freejia: Hotel (west room)", [], False, [], [], [], [], [], [], [], []],
            121: [False, [],         2, [2,7,0,57], 0, "Freejia: Hotel (east room)", [], False, [], [], [], [], [], [], [], []],
            122: [False, [504],      2, [2,7,0,58], 0, "Freejia: Laborer House", [], False, [], [], [], [], [], [], [], []],
            123: [False, [],         2, [2,7,0,59], 0, "Freejia: Messy House", [], False, [], [], [], [], [], [], [], []],
            124: [False, [],         2, [2,7,0,51], 0, "Freejia: Erik House", [], False, [], [], [], [], [], [], [], []],
            125: [False, [],         2, [2,7,0,52], 0, "Freejia: Dark Space House", [], False, [], [], [], [], [], [], [], []],
            126: [False, [],         2, [2,7,0,53], 0, "Freejia: Labor Trade House", [], False, [], [], [], [], [], [], [], []],
            127: [False, [],         2, [2,7,0,60], 0, "Freejia: Labor Market", [], False, [], [], [], [], [], [], [], []],

            # Diamond Mine
            130: [False, [],    2,     [2,8,0,61], 0, "Diamond Mine: Map 61 (entrance)", [], False, [], [], [], [], [], [], [], []],
            708: [False, [701], 2,     [2,8,0,61], 0, "Diamond Mine: Map 61 (behind fence 1)", [], False, [], [], [], [], [], [], [], []],
            701: [False, [],    2,     [2,8,0,61], 0, "Diamond Mine: Map 61 (lizard with orb)", [], False, [], [], [], [], [], [], [], []],
            709: [False, [],    2,     [2,8,0,61], 0, "Diamond Mine: Map 61 (behind fence 2)", [], False, [], [], [], [], [], [], [], []],
            131: [False, [],    2,     [2,8,0,61], 0, "Diamond Mine: Map 61 (behind fence 3)", [], False, [], [], [], [], [], [], [], []],
            133: [False, [11],  2,     [2,8,0,62], 0, "Diamond Mine: Map 62", [], False, [], [], [], [], [], [], [], []],
            134: [False, [],    2,     [2,8,0,63], 0, "Diamond Mine: Map 63 (main)", [], False, [], [], [], [], [], [], [], []],
            136: [False, [],    2,     [2,8,0,64], 0, "Diamond Mine: Map 64 (main)", [], False, [], [], [], [], [], [], [], []],
            137: [False, [136], 2,     [2,8,0,64], 0, "Diamond Mine: Map 64 (trapped laborer)", [], False, [], [], [], [], [], [], [], []],
            721: [False, [],    2,     [2,8,0,64], 0, "Diamond Mine: Map 64 (Dark Space)", [], False, [], [], [], [], [], [], [], []],
            138: [False, [],    2,     [2,8,0,65], 0, "Diamond Mine: Map 65 (main)", [], False, [], [], [], [], [], [], [], []],
            710: [False, [138], 2,     [2,8,0,65], 0, "Diamond Mine: Map 65 (worm for ramp)", [], False, [], [], [], [], [], [], [], []],
            139: [False, [138,710], 2, [2,8,0,65], 0, "Diamond Mine: Map 65 (behind ramp)", [], False, [], [], [], [], [], [], [], []],
            140: [False, [],    2,     [2,8,0,66], 0, "Diamond Mine: Map 66 (elevator 1)", [], False, [], [], [], [], [], [], [], []],
            141: [False, [],    2,     [2,8,0,66], 0, "Diamond Mine: Map 66 (elevator 2)", [], False, [], [], [], [], [], [], [], []],
            142: [False, [],    2,     [2,8,0,66], 0, "Diamond Mine: Map 66 (Dark Space)", [], False, [], [], [], [], [], [], [], []],
            143: [False, [],    2,     [2,8,0,66], 0, "Diamond Mine: Map 66 (laborer)", [], False, [], [], [], [], [], [], [], []],
            144: [False, [145], 2,     [2,8,0,67], 0, "Diamond Mine: Map 67 (entrance)", [], False, [], [], [], [], [], [], [], []],
            145: [False, [144], 2,     [2,8,0,67], 0, "Diamond Mine: Map 67 (exit)", [], False, [], [], [], [], [], [], [], []],         # potential softlock?
            146: [False, [],    2,     [2,8,0,68], 0, "Diamond Mine: Map 68 (main)", [], False, [], [], [], [], [], [], [], []],
            148: [False, [],    2,     [2,8,0,69], 0, "Diamond Mine: Map 69", [], False, [], [], [], [], [], [], [], []],
            149: [False, [],    2,     [2,8,0,70], 0, "Diamond Mine: Map 70", [], False, [], [], [], [], [], [], [], []],
            150: [False, [],    2,     [2,8,0,71], 0, "Diamond Mine: Map 71", [], False, [], [], [], [], [], [], [], []],

            # Neil's Cottage / Nazca
            160: [False, [11],         2, [2,9,0,73],  0, "Neil's Cottage", [13], False, [], [], [], [], [], [], [], []],
            161: [False, [17,160,505], 2, [2,9,0,73],  0, "Neil's Cottage: Neil", [], False, [], [], [], [], [], [], [], []],
            162: [False, [11],         1, [2,10,0,75], 0, "Nazca Plain", [], False, [], [], [], [], [], [], [], []],

            # Sky Garden
            167: [False, [],         2, [2,10,0,83], 0, "Sky Garden: Map 83 (SE)", [], False, [], [], [], [], [], [], [], []],
            168: [False, [],         2, [2,10,0,81], 0, "Sky Garden: Map 81 (north)", [], False, [], [], [], [], [], [], [], []],
            169: [False, [],         2, [2,10,0,86], 0, "Sky Garden: Map 86 (DS Room)", [], False, [], [], [], [], [], [], [], []],
            170: [False, [],         1, [2,10,0,76], 0, "Sky Garden: Foyer", [14, 14, 14, 14], False, [], [], [], [], [], [], [], []],
            171: [False, [],         1, [2,10,0,76], 0, "Sky Garden: Boss Entrance", [], False, [], [], [], [], [], [], [], []],
            172: [False, [],         2, [2,10,0,77], 0, "Sky Garden: Map 77 (main)", [], False, [], [], [], [], [], [], [], []],
            173: [False, [],         2, [2,10,0,77], 0, "Sky Garden: Map 77 (SW)", [], False, [], [], [], [], [], [], [], []],
            174: [False, [],         2, [2,10,0,77], 0, "Sky Garden: Map 77 (SE)", [], False, [], [], [], [], [], [], [], []],
            175: [False, [],         2, [2,10,0,78], 0, "Sky Garden: Map 78", [], False, [], [], [], [], [], [], [], []],
            176: [False, [],         2, [2,10,0,79], 0, "Sky Garden: Map 79 (main)", [], False, [], [], [], [], [], [], [], []],
            177: [False, [],         2, [2,10,0,79], 0, "Sky Garden: Map 79 (center)", [], False, [], [], [], [], [], [], [], []],
            711: [False, [],         2, [2,10,0,79], 0, "Sky Garden: Map 79 (robot for barrier)", [], False, [], [], [], [], [], [], [], []],
            178: [False, [],         2, [2,10,0,79], 0, "Sky Garden: Map 79 (behind barrier)", [], False, [], [], [], [], [], [], [], []],
            179: [False, [],         2, [2,10,0,80], 0, "Sky Garden: Map 80 (north)", [], False, [], [], [], [], [], [], [], []],
            180: [False, [],         2, [2,10,0,80], 0, "Sky Garden: Map 80 (south)", [], False, [], [], [], [], [], [], [], []],
            716: [False, [],         2, [2,10,0,80], 0, "Sky Garden: Map 80 (chest behind barrier)", [], False, [], [], [], [], [], [], [], []],
            181: [False, [],         2, [2,10,0,81], 0, "Sky Garden: Map 81 (main)", [], False, [], [], [], [], [], [], [], []],
            182: [False, [181],      2, [2,10,0,81], 0, "Sky Garden: Map 81 (west)", [], False, [], [], [], [], [], [], [], []],
            183: [False, [182],      2, [2,10,0,81], 0, "Sky Garden: Map 81 (Dark Space cage)", [], False, [], [], [], [], [], [], [], []],
            184: [False, [182],      2, [2,10,0,81], 0, "Sky Garden: Map 81 (SE platform)", [], False, [], [], [], [], [], [], [], []],
            185: [False, [182],      2, [2,10,0,81], 0, "Sky Garden: Map 81 (SW chest)", [], False, [], [], [], [], [], [], [], []],
            186: [False, [506],      2, [2,10,0,82], 0, "Sky Garden: Map 82 (north)", [], False, [], [], [], [], [], [], [], []],
            187: [False, [],         2, [2,10,0,82], 0, "Sky Garden: Map 82 (south)", [], False, [], [], [], [], [], [], [], []],
            188: [False, [],         2, [2,10,0,82], 0, "Sky Garden: Map 82 (NE)", [], False, [], [], [], [], [], [], [], []],
            189: [False, [188,507],  2, [2,10,0,82], 0, "Sky Garden: Map 82 (switch cage)", [], False, [], [], [], [], [], [], [], []],
            190: [False, [191],      2, [2,10,0,83], 0, "Sky Garden: Map 83 (NE)", [], False, [], [], [], [], [], [], [], []],
            191: [False, [190, 192], 2, [2,10,0,83], 0, "Sky Garden: Map 83 (NW)", [], False, [], [], [], [], [], [], [], []],
            192: [False, [],         2, [2,10,0,83], 0, "Sky Garden: Map 83 (center)", [], False, [], [], [], [], [], [], [], []],
            193: [False, [194],      2, [2,10,0,83], 0, "Sky Garden: Map 83 (SW)", [], False, [], [], [], [], [], [], [], []],
            194: [False, [167],      2, [2,10,0,83], 0, "Sky Garden: Map 83 (chests)", [], False, [], [], [], [], [], [], [], []],
            195: [False, [196],      2, [2,10,0,84], 0, "Sky Garden: Map 84 (main)", [], False, [], [], [], [], [], [], [], []],
            196: [False, [],         2, [2,10,0,84], 0, "Sky Garden: Map 84 (NE)", [], False, [], [], [], [], [], [], [], []],
            197: [False, [],         2, [2,10,0,84], 0, "Sky Garden: Map 84 (behind statue)", [], False, [], [], [], [], [], [], [], []],
            198: [False, [],         2, [2,10,0,85], 0, "Sky Garden: Boss Room", [], True, [], [], [], [], [], [], [], []],
            199: [False, [197,509],  2, [2,10,0,84], 0, "Sky Garden: Map 84 (statue)", [], False, [], [], [], [], [], [], [], []],

            # Seaside Palace
            200: [False,    [], 1, [3,11,0,90], 0, "Seaside Palace: Area 1", [16], False, [], [], [], [], [], [], [], []],
            202: [False,    [], 2, [3,11,0,91], 0, "Seaside Palace: Area 1 NE Room", [], False, [], [], [], [], [], [], [], []],
            203: [False,    [], 2, [3,11,0,91], 0, "Seaside Palace: Area 1 NW Room", [], False, [], [], [], [], [], [], [], []],
            204: [False,    [], 2, [3,11,0,91], 0, "Seaside Palace: Area 1 SE Room", [], False, [], [], [], [], [], [], [], []],
            205: [False,    [], 1, [3,11,0,92], 0, "Seaside Palace: Area 2", [], False, [], [], [], [], [], [], [], []],
            206: [False, [200], 2, [3,11,0,90], 0, "Seaside Palace: Buffy", [], False, [], [], [], [], [], [], [], []],
            207: [False,    [], 2, [3,11,0,92], 0, "Seaside Palace: Area 2 SW Room", [], False, [], [], [], [], [], [], [], []],
            208: [False, [205], 2, [3,11,0,92], 0, "Seaside Palace: Coffin", [], False, [], [], [], [], [], [], [], []],
            209: [False,    [], 2, [3,11,0,93], 0, "Seaside Palace: Fountain", [17], False, [], [], [], [], [], [], [], []],
            210: [False,    [], 2, [3,11,0,94], 0, "Seaside Palace: Mu Passage", [16], False, [], [], [], [], [], [], [], []],
            
            # Mu
            212: [False, [],         2, [3,12,0,95], 0, "Mu: Map 95 (entrance)", [], False, [], [], [], [], [], [], [], []],
            722: [False, [],         2, [3,12,0,95], 0, "Mu: Map 95 (past barrier)", [], False, [], [], [], [], [], [], [], []],
            213: [False, [],         2, [3,12,1,95], 0, "Mu: Map 95 (middle E)", [], False, [], [], [], [], [], [], [], []],
            214: [False, [],         2, [3,12,1,95], 0, "Mu: Map 95 (middle W)", [], False, [], [], [], [], [], [], [], []],
            215: [False, [],         2, [3,12,2,95], 0, "Mu: Map 95 (bottom E)", [], False, [], [], [], [], [], [], [], []],
            216: [False, [],         2, [3,12,2,95], 0, "Mu: Map 95 (bottom W)", [], False, [], [], [], [], [], [], [], []],
            217: [False, [726],      2, [3,12,0,96], 0, "Mu: Map 96 (top N)", [], False, [], [], [], [], [], [], [], []],
            726: [False, [],         2, [3,12,0,96], 0, "Mu: Map 96 (top monster orb N)", [], False, [], [], [], [], [], [], [], []],
            725: [False, [724,726],  2, [3,12,0,96], 0, "Mu: Map 96 (top between rocks)", [], False, [], [], [], [], [], [], [], []],
            724: [False, [],         2, [3,12,0,96], 0, "Mu: Map 96 (top monster orb S)", [], False, [], [], [], [], [], [], [], []],
            723: [False, [724],      2, [3,12,0,96], 0, "Mu: Map 96 (top S)", [], False, [], [], [], [], [], [], [], []],
            218: [False, [],         2, [3,12,1,96], 0, "Mu: Map 96 (middle)", [], False, [], [], [], [], [], [], [], []],
            219: [False, [],         2, [3,12,2,96], 0, "Mu: Map 96 (bottom)", [], False, [], [], [], [], [], [], [], []],
            220: [False, [],         2, [3,12,0,97], 0, "Mu: Map 97 (top main)", [], False, [], [], [], [], [], [], [], []],
            221: [False, [222,223],  2, [3,12,0,97], 0, "Mu: Map 97 (top island)", [], False, [], [], [], [], [], [], [], []],
            222: [False, [],         2, [3,12,1,97], 0, "Mu: Map 97 (middle N)", [], False, [], [], [], [], [], [], [], []],
            223: [False, [221],      2, [3,12,1,97], 0, "Mu: Map 97 (middle W)", [], False, [], [], [], [], [], [], [], []],
            224: [False, [],         2, [3,12,2,97], 0, "Mu: Map 97 (bottom)", [], False, [], [], [], [], [], [], [], []],
            225: [False, [],         2, [3,12,0,98], 0, "Mu: Map 98 (top S)", [], False, [], [], [], [], [], [], [], []],
            226: [False, [],         2, [3,12,0,98], 0, "Mu: Map 98 (top N)", [], False, [], [], [], [], [], [], [], []],
            227: [False, [],         2, [3,12,1,98], 0, "Mu: Map 98 (middle E)", [], False, [], [], [], [], [], [], [], []],
            229: [False, [],         2, [3,12,2,98], 0, "Mu: Map 98 (bottom E)", [], False, [], [], [], [], [], [], [], []],
            230: [False, [],         2, [3,12,2,98], 0, "Mu: Map 98 (bottom W)", [], False, [], [], [], [], [], [], [], []],
            228: [False, [],         2, [3,12,1,98], 0, "Mu: Map 98 (middle W)", [], False, [], [], [], [], [], [], [], []],
            231: [False, [526],      2, [3,12,0,99], 0, "Mu: Map 99 (Room of Hope 1)", [18], False, [], [], [], [], [], [], [], []],
            232: [False, [527],      2, [3,12,0,99], 0, "Mu: Map 99 (Room of Hope 2)", [18], False, [], [], [], [], [], [], [], []],
            233: [False, [],         2, [3,12,1,100], 0, "Mu: Map 100 (middle E)", [], False, [], [], [], [], [], [], [], []],
            234: [False, [],         2, [3,12,1,100], 0, "Mu: Map 100 (middle W)", [], False, [], [], [], [], [], [], [], []],
            235: [False, [],         2, [3,12,2,100], 0, "Mu: Map 100 (bottom)", [], False, [], [], [], [], [], [], [], []],
            236: [False, [238],      2, [3,12,0,101], 0, "Mu: Map 101 (top)", [], False, [], [], [], [], [], [], [], []],
            237: [False, [],         2, [3,12,1,101], 0, "Mu: Map 101 (middle W)", [], False, [], [], [], [], [], [], [], []],
            238: [False, [236],      2, [3,12,1,101], 0, "Mu: Map 101 (middle E)", [], False, [], [], [], [], [], [], [], []],
            239: [False, [],         2, [3,12,2,101], 0, "Mu: Map 101 (bottom)", [], False, [], [], [], [], [], [], [], []],
            240: [False, [],         2, [3,12,0,102], 0, "Mu: Map 102 (pedestal room)", [19, 19], False, [], [], [], [], [], [], [], []],
            241: [False, [],         2, [3,12,0,102], 0, "Mu: Map 102 (statues placed)", [], False, [], [], [], [], [], [], [], []],
            242: [False, [],         2, [3,12,0,102], 0, "Mu: Map 102 (statue get)", [], False, [], [], [], [], [], [], [], []],
            243: [False, [244],      2, [3,12,0,103], 0, "Mu: Boss Room (entryway)", [], False, [], [], [], [], [], [], [], []],
            244: [False, [242,243],  2, [3,12,0,103], 0, "Mu: Boss Room (main)", [], True, [], [], [], [], [], [], [], []],
            247: [False, [511],      0, [3,12,0,0], 0, "Mu: Water lowered 1", [], False, [], [], [], [], [], [], [], []],
            248: [False, [512],      0, [3,12,0,0], 0, "Mu: Water lowered 2", [], False, [], [], [], [], [], [], [], []],

            # Angel Village
            250: [False, [12], 1, [3,13,0,105], 0, "Angel Village: Outside", [], True, [], [], [], [], [], [], [], []],
            251: [False, [1],  1, [3,13,0,107], 0, "Angel Village: Underground", [], False, [], [], [], [], [], [], [], []],
            252: [False, [],   2, [3,13,0,108], 0, "Angel Village: Room 1", [], False, [], [], [], [], [], [], [], []],
            253: [False, [],   2, [3,13,0,108], 0, "Angel Village: Room 2", [], False, [], [], [], [], [], [], [], []],
            254: [False, [],   2, [3,13,0,108], 0, "Angel Village: Dance Hall", [], False, [], [], [], [], [], [], [], []],
            255: [False, [],   2, [3,13,0,108], 0, "Angel Village: DS Room", [], False, [], [], [], [], [], [], [], []],
            #256: [False, [],   2, [3,13,0,0], 0, "Angel Village: Room 3", [], False, [], [], [], [], [], [], [], []],

            # Angel Dungeon
            260: [False,    [], 2, [3,13,0,109], 0, "Angel Dungeon: Map 109", [], False, [], [], [], [], [], [], [], []],
            261: [False, [278], 2, [3,13,0,110], 0, "Angel Dungeon: Map 110 (main)", [], False, [], [], [], [], [], [], [], []],
            278: [False, [261], 2, [3,13,0,110], 0, "Angel Dungeon: Map 110 (past Draco)", [], False, [], [], [], [], [], [], [], []],
            262: [False,    [], 2, [3,13,0,111], 0, "Angel Dungeon: Map 111", [], False, [], [], [], [], [], [], [], []],
            259: [False,    [], 2, [3,13,0,112], 0, "Angel Dungeon: Map 112 (entryway)", [], False, [], [], [], [], [], [], [], []],
            263: [False, [279], 2, [3,13,0,112], 0, "Angel Dungeon: Map 112 (main)", [], False, [], [], [], [], [], [], [], []],
            279: [False, [263], 2, [3,13,0,112], 0, "Angel Dungeon: Map 112 (past Draco)", [], False, [], [], [], [], [], [], [], []],
            265: [False,    [], 2, [3,13,0,112], 0, "Angel Dungeon: Map 112 (alcove)", [], False, [], [], [], [], [], [], [], []],
            266: [False,    [], 2, [3,13,0,113], 0, "Angel Dungeon: Map 113", [], False, [], [], [], [], [], [], [], []],
            267: [False,    [], 2, [3,13,0,114], 0, "Angel Dungeon: Map 114 (main)", [], False, [], [], [], [], [], [], [], []],
            277: [False,    [], 2, [3,13,0,115], 0, "Angel Dungeon: Map 115 (foyer)", [], False, [], [], [], [], [], [], [], []],
            269: [False,    [], 2, [3,13,0,115], 0, "Angel Dungeon: Map 115 (main)", [], False, [], [], [], [], [], [], [], []],
            270: [False,    [], 2, [3,13,0,116], 0, "Angel Dungeon: Map 116 (portrait room)", [], False, [], [], [], [], [], [], [], []],
            271: [False,    [], 2, [3,13,0,116], 0, "Angel Dungeon: Map 116 (side room)", [], False, [], [], [], [], [], [], [], []],
            272: [False,    [], 2, [3,13,0,116], 0, "Angel Dungeon: Map 116 (Ishtar's room)", [], False, [], [], [], [], [], [], [], []],
            273: [False,    [], 2, [3,13,0,116], 0, "Angel Dungeon: Map 116 (Ishtar's chest)", [], False, [], [], [], [], [], [], [], []],
            274: [False, [513], 2, [3,13,0,117], 0, "Angel Dungeon: Puzzle Room", [], False, [], [], [], [], [], [], [], []],

            # Watermia
            280: [False,     [12], 1, [3,14,0,120], 0, "Watermia: Main Area", [24], False, [], [], [], [], [], [], [], []],
            #281: [False, [15,280], 0, [3,14,0,0], 0, "Watermia: Bridge Man", [], False, [], [], [], [], [], [], [], []],
            282: [False,       [], 2, [3,14,0,124], 0, "Watermia: DS House", [], False, [], [], [], [], [], [], [], []],
            283: [False,      [1], 2, [3,14,0,123], 0, "Watermia: Gambling House", [], False, [], [], [], [], [], [], [], []],
            284: [False,       [], 2, [3,14,0,126], 0, "Watermia: West House", [], False, [], [], [], [], [], [], [], []],
            285: [False,       [], 2, [3,14,0,125], 0, "Watermia: East House", [], False, [], [], [], [], [], [], [], []],
            286: [False,       [], 2, [3,14,0,121], 0, "Watermia: Lance's House", [], False, [], [], [], [], [], [], [], []],
            287: [False,       [], 2, [3,14,0,122], 0, "Watermia: NW House", [], False, [], [], [], [], [], [], [], []],
            288: [False,    [280], 0, [3,14,0,120], 0, "Watermia: Stablemaster", [], True, [], [], [], [], [], [], [], []],

            # Great Wall
            290: [False, [12],  2, [3,15,0,130], 0, "Great Wall: Map 130", [], False, [], [], [], [], [], [], [], []],
            291: [False, [292], 2, [3,15,0,131], 0, "Great Wall: Map 131 (NW)", [], False, [], [], [], [], [], [], [], []],
            292: [False, [293], 2, [3,15,0,131], 0, "Great Wall: Map 131 (S)", [], False, [], [], [], [], [], [], [], []],
            293: [False, [],    2, [3,15,0,131], 0, "Great Wall: Map 131 (NE)", [], False, [], [], [], [], [], [], [], []],
            294: [False, [296], 2, [3,15,0,133], 0, "Great Wall: Map 133 (W)", [], False, [], [], [], [], [], [], [], []],
            295: [False, [296], 2, [3,15,0,133], 0, "Great Wall: Map 133 (center)", [], False, [], [], [], [], [], [], [], []],
            296: [False, [],    2, [3,15,0,133], 0, "Great Wall: Map 133 (E)", [], False, [], [], [], [], [], [], [], []],
            297: [False, [],    2, [3,15,0,134], 0, "Great Wall: Map 134", [], False, [], [], [], [], [], [], [], []],
            298: [False, [],    2, [3,15,0,135], 0, "Great Wall: Map 135 (W)", [], False, [], [], [], [], [], [], [], []],
            712: [False, [],    2, [3,15,0,135], 0, "Great Wall: Map 135 (archer)", [], False, [], [], [], [], [], [], [], []],
            299: [False, [],    2, [3,15,0,135], 0, "Great Wall: Map 135 (E)", [], False, [], [], [], [], [], [], [], []],
            300: [False, [],    2, [3,15,0,136], 0, "Great Wall: Map 136 (W)", [], False, [], [], [], [], [], [], [], []],
            301: [False, [],    2, [3,15,0,136], 0, "Great Wall: Map 136 (E)", [], False, [], [], [], [], [], [], [], []],
            302: [False, [702], 2, [3,15,0,138], 0, "Great Wall: Fanger Room (entrance)", [], False, [], [], [], [], [], [], [], []],
            702: [False, [303], 2, [3,15,0,138], 0, "Great Wall: Fanger", [], False, [], [], [], [], [], [], [], []],
            303: [False, [],    2, [3,15,0,138], 0, "Great Wall: Fanger Room (exit)", [], False, [], [], [], [], [], [], [], []],

            # Euro
            310: [False, [13],  1, [4,16,0,145], 0, "Euro: Main Area", [24], False, [], [], [], [], [], [], [], []],
            311: [False, [310], 0, [4,16,0,145], 0, "Euro: Stablemaster", [], True, [], [], [], [], [], [], [], []],
            312: [False, [],    2, [4,16,0,148], 0, "Euro: Rolek Company", [], False, [], [], [], [], [], [], [], []],
            313: [False, [],    2, [4,16,0,152], 0, "Euro: West House", [], False, [], [], [], [], [], [], [], []],
            314: [False, [],    2, [4,16,0,149], 0, "Euro: Rolek Mansion", [40], False, [], [], [], [], [], [], [], []],
            315: [False, [314], 0, [4,16,0,149], 0, "Euro: Ann", [], False, [], [], [], [], [], [], [], []],
            316: [False, [],    2, [4,16,0,150], 0, "Euro: Guest Room", [], False, [], [], [], [], [], [], [], []],
            317: [False, [],    2, [4,16,0,146], 0, "Euro: Central House", [], False, [], [], [], [], [], [], [], []],
            318: [False, [1],   2, [4,16,0,155], 0, "Euro: Jeweler House", [], False, [], [], [], [], [], [], [], []],
            319: [False, [],    2, [4,16,0,156], 0, "Euro: Twins House", [], False, [], [], [], [], [], [], [], []],
            320: [False, [],    2, [4,16,0,147], 0, "Euro: Hidden House", [], False, [], [], [], [], [], [], [], []],
            321: [False, [],    2, [4,16,0,157], 0, "Euro: Shrine", [], False, [], [], [], [], [], [], [], []],
            322: [False, [],    2, [4,16,0,154], 0, "Euro: Explorer's House", [], False, [], [], [], [], [], [], [], []],
            323: [False, [324], 2, [4,16,0,151], 0, "Euro: Store Entrance", [], False, [], [], [], [], [], [], [], []],
            324: [False, [],    2, [4,16,0,151], 0, "Euro: Store Exit", [], False, [], [], [], [], [], [], [], []],
            325: [False, [],    2, [4,16,0,153], 0, "Euro: Dark Space House", [], False, [], [], [], [], [], [], [], []],

            # Mt. Kress
            330: [False, [13],        2, [4,17,0,160], 0, "Mt. Kress: Map 160", [], False, [], [], [], [], [], [], [], []],
            331: [False, [],          2, [4,17,0,161], 0, "Mt. Kress: Map 161 (E)", [], False, [], [], [], [], [], [], [], []],
            332: [False, [],          2, [4,17,0,161], 0, "Mt. Kress: Map 161 (W)", [], False, [], [], [], [], [], [], [], []],
            333: [False, [],          2, [4,17,0,162], 0, "Mt. Kress: Map 162 (main)", [26], False, [], [], [], [], [], [], [], []],
            334: [False, [333],       2, [4,17,0,162], 0, "Mt. Kress: Map 162 (S)", [], False, [], [], [], [], [], [], [], []],
            335: [False, [],          2, [4,17,0,162], 0, "Mt. Kress: Map 162 (NW)", [], False, [], [], [], [], [], [], [], []],
            336: [False, [],          2, [4,17,0,162], 0, "Mt. Kress: Map 162 (SE)", [], False, [], [], [], [], [], [], [], []],
            337: [False, [],          2, [4,17,0,163], 0, "Mt. Kress: Map 163", [], False, [], [], [], [], [], [], [], []],
            338: [False, [],          2, [4,17,0,164], 0, "Mt. Kress: Map 164", [], False, [], [], [], [], [], [], [], []],
            339: [False, [],          2, [4,17,0,165], 0, "Mt. Kress: Map 165 (S)", [26], False, [], [], [], [], [], [], [], []],
            340: [False, [],          2, [4,17,0,165], 0, "Mt. Kress: Map 165 (NE)", [26], False, [], [], [], [], [], [], [], []],
            341: [False, [339],       2, [4,17,0,165], 0, "Mt. Kress: Map 165 (NW)", [], False, [], [], [], [], [], [], [], []],
            342: [False, [],          2, [4,17,0,166], 0, "Mt. Kress: Map 166", [], False, [], [], [], [], [], [], [], []],
            343: [False, [],          2, [4,17,0,167], 0, "Mt. Kress: Map 167", [], False, [], [], [], [], [], [], [], []],
            344: [False, [],          2, [4,17,0,168], 0, "Mt. Kress: Map 168", [], False, [], [], [], [], [], [], [], []],
            345: [False, [],          2, [4,17,0,169], 0, "Mt. Kress: Map 169", [], False, [], [], [], [], [], [], [], []],

            # Natives' Village
            350: [False, [13],  1, [4,18,0,172], 0, "Natives' Village: Main Area", [10], False, [], [], [], [], [], [], [], []],
            351: [False, [],    0, [4,18,0,172], 0, "Natives' Village: Child Guide", [], True, [], [], [], [], [], [], [], []],
            352: [False, [],    2, [4,18,0,173], 0, "Natives' Village: West House", [], False, [], [], [], [], [], [], [], []],
            353: [False, [],    2, [4,18,0,174], 0, "Natives' Village: House w/Statues", [29], False, [], [], [], [], [], [], [], []],
            354: [False, [],    0, [4,18,0,174], 0, "Natives' Village: Statues Awake", [], False, [], [], [], [], [], [], [], []],

            # Ankor Wat
            360: [False, [13],  2, [4,19,0,176], 0, "Ankor Wat: Map 176", [], False, [], [], [], [], [], [], [], []],
            361: [False, [],    2, [4,19,0,177], 0, "Ankor Wat: Map 177 (E)", [], False, [], [], [], [], [], [], [], []],
            362: [False, [739], 2, [4,19,0,177], 0, "Ankor Wat: Map 177 (W)", [], False, [], [], [], [], [], [], [], []],
            739: [False, [],    2, [4,19,0,177], 0, "Ankor Wat: Map 177 Scarab Orb", [], False, [], [], [], [], [], [], [], []],
            363: [False, [],    2, [4,19,0,178], 0, "Ankor Wat: Map 178 (S)", [], False, [], [], [], [], [], [], [], []],
            364: [False, [363], 2, [4,19,0,178], 0, "Ankor Wat: Map 178 (center)", [], False, [], [], [], [], [], [], [], []],
            365: [False, [],    2, [4,19,0,178], 0, "Ankor Wat: Map 178 (N)", [], False, [], [], [], [], [], [], [], []],
            366: [False, [],    2, [4,19,0,179], 0, "Ankor Wat: Map 179 (E)", [], False, [], [], [], [], [], [], [], []],
            367: [False, [],    2, [4,19,0,179], 0, "Ankor Wat: Map 179 (W)", [], False, [], [], [], [], [], [], [], []],
            368: [False, [703], 2, [4,19,0,180], 0, "Ankor Wat: Map 180", [], False, [], [], [], [], [], [], [], []],
            703: [False, [368], 2, [4,19,0,180], 0, "Ankor Wat: Map 180 (scarab with orb)", [], False, [], [], [], [], [], [], [], []],
            369: [False, [],    2, [4,19,0,181], 0, "Ankor Wat: Map 181 (N)", [], False, [], [], [], [], [], [], [], []],
            370: [False, [],    2, [4,19,0,181], 0, "Ankor Wat: Map 181 (center)", [], False, [], [], [], [], [], [], [], []],
            371: [False, [],    2, [4,19,0,181], 0, "Ankor Wat: Map 181 (S)", [], False, [], [], [], [], [], [], [], []],
            372: [False, [],    2, [4,19,0,182], 0, "Ankor Wat: Map 182", [], False, [], [], [], [], [], [], [], []],
            373: [False, [],    2, [4,19,0,183], 0, "Ankor Wat: Map 183 (S)", [], False, [], [], [], [], [], [], [], []],
            374: [False, [373], 2, [4,19,0,183], 0, "Ankor Wat: Map 183 (NW)", [], False, [], [], [], [], [], [], [], []],
            375: [False, [],    2, [4,19,0,183], 0, "Ankor Wat: Map 183 (N)", [], False, [], [], [], [], [], [], [], []],
            376: [False, [],    2, [4,19,0,184], 0, "Ankor Wat: Map 184 (S)", [], False, [], [], [], [], [], [], [], []],
            727: [False, [],    2, [4,19,0,184], 0, "Ankor Wat: Map 184 (Wall skull)", [], False, [], [], [], [], [], [], [], []],
            377: [False, [],    2, [4,19,0,184], 0, "Ankor Wat: Map 184 (N)", [], False, [], [], [], [], [], [], [], []],
            378: [False, [],    2, [4,19,0,185], 0, "Ankor Wat: Map 185", [], False, [], [], [], [], [], [], [], []],
            379: [False, [],    2, [4,19,0,186], 0, "Ankor Wat: Map 186 (main)", [], False, [], [], [], [], [], [], [], []],
            380: [False, [],    2, [4,19,0,186], 0, "Ankor Wat: Map 186 (NE)", [], False, [], [], [], [], [], [], [], []],
            381: [False, [],    2, [4,19,0,187], 0, "Ankor Wat: Map 187 (main)", [], False, [], [], [], [], [], [], [], []],
            382: [False, [381], 2, [4,19,0,187], 0, "Ankor Wat: Map 187 (chest)", [], False, [], [], [], [], [], [], [], []],
            383: [False, [381], 2, [4,19,0,187], 0, "Ankor Wat: Map 187 (Dark Space)", [], False, [], [], [], [], [], [], [], []],
            384: [False, [],    2, [4,19,0,188], 0, "Ankor Wat: Map 188 (N)", [], False, [], [], [], [], [], [], [], []],
            385: [False, [],    2, [4,19,0,188], 0, "Ankor Wat: Map 188 (S)", [], False, [], [], [], [], [], [], [], []],
            386: [False, [],    2, [4,19,0,189], 0, "Ankor Wat: Map 189 (floor S)", [], False, [], [], [], [], [], [], [], []],
            387: [False, [],    2, [4,19,0,189], 0, "Ankor Wat: Map 189 (floor N)", [], False, [], [], [], [], [], [], [], []],
            388: [False, [386], 2, [4,19,0,189], 0, "Ankor Wat: Map 189 (platform)", [], False, [], [], [], [], [], [], [], []],
            389: [False, [],    2, [4,19,0,190], 0, "Ankor Wat: Map 190 (SE)", [], False, [], [], [], [], [], [], [], []],
            390: [False, [],    2, [4,19,0,190], 0, "Ankor Wat: Map 190 (N)", [], False, [], [], [], [], [], [], [], []],
            391: [False, [],    2, [4,19,0,191], 0, "Ankor Wat: Map 191", [], False, [], [], [], [], [], [], [], []],

            # Dao
            400: [False, [1,14], 1, [5,20,0,195], 0, "Dao: Main Area", [], False, [], [], [], [], [], [], [], []],
            401: [False, [],     2, [5,20,0,196], 0, "Dao: NW House", [], False, [], [], [], [], [], [], [], []],
            402: [False, [],     2, [5,20,0,200], 0, "Dao: Neil's House", [], False, [], [], [], [], [], [], [], []],
            403: [False, [],     2, [5,20,0,198], 0, "Dao: Snake Game", [], False, [], [], [], [], [], [], [], []],
            404: [False, [],     2, [5,20,0,199], 0, "Dao: SW House", [], False, [], [], [], [], [], [], [], []],
            405: [False, [],     2, [5,20,0,197], 0, "Dao: S House", [], False, [], [], [], [], [], [], [], []],
            406: [False, [],     2, [5,20,0,201], 0, "Dao: SE House", [], False, [], [], [], [], [], [], [], []],

            # Pyramid
            410: [False, [14],      2, [5,21,0,204], 0, "Pyramid: Entrance (main)", [], False, [], [], [], [], [], [], [], []],
            713: [False, [],        2, [5,21,0,204], 0, "Pyramid: Entrance (top Dark Space)", [], False, [], [], [], [], [], [], [], []],
            411: [False, [410],     2, [5,21,0,204], 0, "Pyramid: Entrance (behind orbs)", [], False, [], [], [], [], [], [], [], []],
            412: [False, [413],     2, [5,21,0,204], 0, "Pyramid: Entrance (hidden platform)", [], False, [], [], [], [], [], [], [], []],
            413: [False, [],        2, [5,21,0,204], 0, "Pyramid: Entrance (bottom)", [], False, [], [], [], [], [], [], [], []],
            414: [False, [],        2, [5,21,0,204], 0, "Pyramid: Entrance (boss entrance)", [], False, [], [], [], [], [], [], [], []],
            415: [False, [],        2, [5,21,0,205], 0, "Pyramid: Hieroglyph room", [30, 31, 32, 33, 34, 35, 38], False, [], [], [], [], [], [], [], []],
            416: [False, [],        2, [5,21,0,206], 0, "Pyramid: Map 206 (E)", [], False, [], [], [], [], [], [], [], []],
            417: [False, [416],     2, [5,21,0,206], 0, "Pyramid: Map 206 (W)", [], False, [], [], [], [], [], [], [], []],
            418: [False, [],        2, [5,21,0,207], 0, "Pyramid: Map 207 (NE)", [], False, [], [], [], [], [], [], [], []],
            419: [False, [],        2, [5,21,0,207], 0, "Pyramid: Map 207 (SW)", [], False, [], [], [], [], [], [], [], []],
            420: [False, [421],     2, [5,21,0,208], 0, "Pyramid: Map 208 (N)", [], False, [], [], [], [], [], [], [], []],
            421: [False, [420],     2, [5,21,0,208], 0, "Pyramid: Map 208 (S)", [], False, [], [], [], [], [], [], [], []],
            422: [False, [423],     2, [5,21,0,209], 0, "Pyramid: Map 209 (W)", [], False, [], [], [], [], [], [], [], []],
            423: [False, [422],     2, [5,21,0,209], 0, "Pyramid: Map 209 (E)", [], False, [], [], [], [], [], [], [], []],
            424: [False, [],        2, [5,21,0,210], 0, "Pyramid: Map 210", [], False, [], [], [], [], [], [], [], []],
            425: [False, [],        2, [5,21,0,211], 0, "Pyramid: Map 211", [], False, [], [], [], [], [], [], [], []],
            426: [False, [],        2, [5,21,0,212], 0, "Pyramid: Map 212 (N)", [], False, [], [], [], [], [], [], [], []],
            427: [False, [],        2, [5,21,0,212], 0, "Pyramid: Map 212 (center)", [], False, [], [], [], [], [], [], [], []],
            428: [False, [],        2, [5,21,0,212], 0, "Pyramid: Map 212 (SE chest)", [], False, [], [], [], [], [], [], [], []],
            429: [False, [],        2, [5,21,0,212], 0, "Pyramid: Map 212 (SW exit)", [], False, [], [], [], [], [], [], [], []],
            430: [False, [],        2, [5,21,0,213], 0, "Pyramid: Map 213", [], False, [], [], [], [], [], [], [], []],
            431: [False, [],        2, [5,21,0,214], 0, "Pyramid: Map 214 (Upper)", [], False, [], [], [], [], [], [], [], []],
            432: [False, [],        2, [5,21,0,214], 0, "Pyramid: Map 214 (NE chest)", [], False, [], [], [], [], [], [], [], []],
            433: [False, [431,434], 2, [5,21,0,214], 0, "Pyramid: Map 214 (E platform)", [], False, [], [], [], [], [], [], [], []],
            434: [False, [433],     2, [5,21,0,214], 0, "Pyramid: Map 214 (Lower)", [], False, [], [], [], [], [], [], [], []],
            435: [False, [],        2, [5,21,0,215], 0, "Pyramid: Map 215 (main)", [], False, [], [], [], [], [], [], [], []],
            436: [False, [437],     2, [5,21,0,216], 0, "Pyramid: Map 216 (N)", [], False, [], [], [], [], [], [], [], []],
            437: [False, [],        2, [5,21,0,216], 0, "Pyramid: Map 216 (S)", [], False, [], [], [], [], [], [], [], []],
            438: [False, [],        2, [5,21,0,217], 0, "Pyramid: Map 217 (W)", [], False, [], [], [], [], [], [], [], []],
            439: [False, [],        2, [5,21,0,217], 0, "Pyramid: Map 217 (E)", [], False, [], [], [], [], [], [], [], []],
            440: [False, [],        2, [5,21,0,219], 0, "Pyramid: Map 219 (W)", [], False, [], [], [], [], [], [], [], []],
            441: [False, [],        2, [5,21,0,219], 0, "Pyramid: Map 219 (E)", [], False, [], [], [], [], [], [], [], []],
            442: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 1", [], False, [], [], [], [], [], [], [], []],
            443: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 2", [], False, [], [], [], [], [], [], [], []],
            444: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 3", [], False, [], [], [], [], [], [], [], []],
            445: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 4", [], False, [], [], [], [], [], [], [], []],
            446: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 5", [], False, [], [], [], [], [], [], [], []],
            447: [False, [],        2, [5,21,0,218], 0, "Pyramid: Hieroglyph 6", [], False, [], [], [], [], [], [], [], []],
            448: [False, [],        2, [5,21,0,221], 0, "Pyramid: Boss Room", [], True, [], [], [], [], [], [], [], []],
            449: [False, [415,517], 0, [5,21,0,205], 0, "Pyramid: Hieroglyphs Placed", [], False, [], [], [], [], [], [], [], []],
            450: [False, [],        2, [5,21,0,215], 0, "Pyramid: Map 215 (past Killer 6)", [], False, [], [], [], [], [], [], [], []],

            # Babel
            460: [False, [],       2, [6,22,0,222], 0, "Babel: Foyer", [], False, [], [], [], [], [], [], [], []],
            461: [False, [],       2, [6,22,0,223], 0, "Babel: Map 223 (bottom)", [], False, [], [], [], [], [], [], [], []],
            462: [False, [461],    2, [6,22,0,223], 0, "Babel: Map 223 (top)", [], False, [], [], [], [], [], [], [], []],
            463: [False, [518,519],2, [6,22,0,224], 0, "Babel: Map 224 (bottom)", [], False, [], [], [], [], [], [], [], []],
            464: [False, [520,521],2, [6,22,0,224], 0, "Babel: Map 224 (top)", [], False, [], [], [], [], [], [], [], []],
            465: [False, [466],    2, [6,22,0,225], 0, "Babel: Map 225 (SW)", [], False, [], [], [], [], [], [], [], []],
            466: [False, [],       2, [6,22,0,225], 0, "Babel: Map 225 (NW)", [], False, [], [], [], [], [], [], [], []],
            467: [False, [468],    2, [6,22,0,225], 0, "Babel: Map 225 (SE)", [], False, [], [], [], [], [], [], [], []],
            468: [False, [],       2, [6,22,0,225], 0, "Babel: Map 225 (NE)", [], False, [], [], [], [], [], [], [], []],
            469: [False, [470],    2, [6,22,0,226], 0, "Babel: Map 226 (bottom)", [], False, [], [], [], [], [], [], [], []],
            470: [False, [],       2, [6,22,0,226], 0, "Babel: Map 226 (top)", [], False, [], [], [], [], [], [], [], []],
            471: [False, [522],    2, [6,22,0,227], 0, "Babel: Map 227 (bottom)", [], False, [], [], [], [], [], [], [], []],
            472: [False, [],       2, [6,22,0,227], 0, "Babel: Map 227 (top)", [], False, [], [], [], [], [], [], [], []],
            473: [False, [],       2, [6,22,0,222], 0, "Babel: Olman's Room", [], False, [], [], [], [], [], [], [], []],
            474: [False, [],       0, [6,22,0,242], 0, "Babel: Castoth", [], False, [], [], [], [], [], [], [], []],
            475: [False, [],       0, [6,22,0,243], 0, "Babel: Viper", [], False, [], [], [], [], [], [], [], []],
            476: [False, [],       0, [6,22,0,244], 0, "Babel: Vampires", [], False, [], [], [], [], [], [], [], []],
            477: [False, [],       0, [6,22,0,245], 0, "Babel: Sand Fanger", [], False, [], [], [], [], [], [], [], []],
            478: [False, [],       0, [6,22,0,246], 0, "Babel: Mummy Queen", [], False, [], [], [], [], [], [], [], []],
            479: [False, [473],    0, [6,22,0,246], 0, "Babel: Statue Get", [], False, [], [], [], [], [], [], [], []],

            # Jeweler's Mansion
            480: [False, [],    2, [6,23,0,233], 0, "Jeweler's Mansion: Entrance", [], False, [], [], [], [], [], [], [], []],
            714: [False, [],    2, [6,23,0,233], 0, "Jeweler's Mansion: Between Gates", [], False, [], [], [], [], [], [], [], []],
            715: [False, [],    2, [6,23,0,233], 0, "Jeweler's Mansion: Main", [], False, [], [], [], [], [], [], [], []],
            481: [False, [],    2, [6,23,0,233], 0, "Jeweler's Mansion: Behind Psycho Slider", [], False, [], [], [], [], [], [], [], []],
            482: [False, [523], 2, [6,23,0,234], 0, "Jeweler's Mansion: Solid Arm", [], False, [], [], [], [], [], [], [], []],

            # Game End
            490: [False, [500], 0, [0,0,0,0], 0, "Kara Released", [], False, [], [], [], [], [], [], [], []],
            491: [False,    [], 0, [0,0,0,0], 0, "Firebird access", [], False, [], [], [], [], [], [], [], []],
            492: [False,    [], 0, [0,0,0,0], 0, "Dark Gaia/End Game", [], False, [], [], [], [], [], [], [], []],

            # Event Switches
            500: [False, [], 0, [0,0,0,0], 0, "Kara                                ", [], False, [], [], [], [], [], [], [], []],
            501: [False, [], 0, [0,0,0,23], 0, "Lilly                               ", [], False, [], [], [], [], [], [], [], []],
            502: [False, [], 0, [0,0,0,26], 0, "Moon Tribe: Spirits Healed          ", [], False, [], [], [], [], [], [], [], []],
            503: [False, [], 0, [0,0,0,41], 0, "Inca: Castoth defeated              ", [], False, [], [], [], [], [], [], [], []],
            504: [False, [], 0, [0,0,0,58], 0, "Freejia: Found Laborer              ", [], False, [], [], [], [], [], [], [], []],
            505: [False, [], 0, [0,0,0,0], 0, "Neil's Memory Restored              ", [], False, [], [], [], [], [], [], [], []],
            506: [False, [], 0, [0,0,0,82], 0, "Sky Garden: Map 82 NW Switch        ", [], False, [], [], [], [], [], [], [], []],
            507: [False, [], 0, [0,0,0,82], 0, "Sky Garden: Map 82 NE Switch        ", [], False, [], [], [], [], [], [], [], []],
            508: [False, [], 0, [0,0,0,82], 0, "Sky Garden: Map 82 SE Switch        ", [], False, [], [], [], [], [], [], [], []],
            509: [False, [], 0, [0,0,0,84], 0, "Sky Garden: Map 84 Switch           ", [], False, [], [], [], [], [], [], [], []],
            510: [False, [], 0, [0,0,0,96], 0, "Seaside: Fountain Purified          ", [], False, [], [], [], [], [], [], [], []],
            511: [False, [], 0, [0,0,0,0], 0, "Mu: Water Lowered 1                 ", [], False, [], [], [], [], [], [], [], []],
            512: [False, [], 0, [0,0,0,0], 0, "Mu: Water Lowered 2                 ", [], False, [], [], [], [], [], [], [], []],
            513: [False, [], 0, [0,0,0,0], 0, "Angel: Puzzle Complete              ", [], False, [], [], [], [], [], [], [], []],
            514: [False, [], 0, [0,0,0,162], 0, "Mt Kress: Drops used 1              ", [], False, [], [], [], [], [], [], [], []],
            515: [False, [], 0, [0,0,0,165], 0, "Mt Kress: Drops used 2              ", [], False, [], [], [], [], [], [], [], []],
            516: [False, [], 0, [0,0,0,165], 0, "Mt Kress: Drops used 3              ", [], False, [], [], [], [], [], [], [], []],
            517: [False, [], 0, [0,0,0,205], 0, "Pyramid: Hieroglyphs placed         ", [], False, [], [], [], [], [], [], [], []],
            518: [False, [], 0, [0,0,0,242], 0, "Babel: Castoth defeated             ", [], False, [], [], [], [], [], [], [], []],
            519: [False, [], 0, [0,0,0,243], 0, "Babel: Viper defeated               ", [], False, [], [], [], [], [], [], [], []],
            520: [False, [], 0, [0,0,0,244], 0, "Babel: Vampires defeated            ", [], False, [], [], [], [], [], [], [], []],
            521: [False, [], 0, [0,0,0,245], 0, "Babel: Sand Fanger defeated         ", [], False, [], [], [], [], [], [], [], []],
            522: [False, [], 0, [0,0,0,246], 0, "Babel: Mummy Queen defeated         ", [], False, [], [], [], [], [], [], [], []],
            523: [False, [], 0, [0,0,0,234], 0, "Mansion: Solid Arm defeated         ", [], False, [], [], [], [], [], [], [], []],
            524: [False, [], 0, [0,0,0,0], 0, "Inca: Diamond Block Placed          ", [], False, [], [], [], [], [], [], [], []],
            525: [False, [], 0, [0,0,0,0], 0, "Pyramid: Portals Open               ", [], False, [], [], [], [], [], [], [], []],
            526: [False, [], 0, [0,0,0,0], 0, "Mu: Access to Hope Room 1           ", [], False, [], [], [], [], [], [], [], []],
            527: [False, [], 0, [0,0,0,0], 0, "Mu: Access to Hope Room 2           ", [], False, [], [], [], [], [], [], [], []],

            # Misc
            600: [False, [], 0, [0,0,0,0], 0, "Freedan Access                      ", [], False, [], [], [], [], [], [], [], []],
            601: [False, [], 0, [0,0,0,0], 0, "Glitches                            ", [], False, [], [], [], [], [], [], [], []],
            602: [False, [], 0, [0,0,0,0], 0, "Early Firebird enabled              ", [], False, [], [], [], [], [], [], [], []],
            #603: [False, [], 0, [0,0,0,0], 0, "Firebird access                    ", [], False, [], [], [], [], [], [], [], []],  # Not used; Firebird node is 491
            604: [False, [], 0, [0,0,0,0], 0, "Flute                               ", [], False, [], [], [], [], [], [], [], []],
            605: [False, [], 0, [0,0,0,0], 0, "Dungeon Shuffle: No                 ", [], False, [], [], [], [], [], [], [], []],
            606: [False, [], 0, [0,0,0,0], 0, "Dungeon Shuffle: Basic              ", [], False, [], [], [], [], [], [], [], []],
            607: [False, [], 0, [0,0,0,0], 0, "Dungeon Shuffle: Chaos              ", [], False, [], [], [], [], [], [], [], []],
            608: [False, [], 0, [0,0,0,0], 0, "Has Any Will Ability                ", [], False, [], [], [], [], [], [], [], []],
            #609: [False, [], 0, [0,0,0,0], 0, "Has Any Attack                      ", [], False, [], [], [], [], [], [], [], []],
            610: [False, [], 0, [0,0,0,0], 0, "Has Any Ranged Attack               ", [], False, [], [], [], [], [], [], [], []]

        }


        # Shell logical paths for the world graph. Edges for exits etc. are added during initialization.
        # IsBidirectional is only used during initialization, and is False afterward.
        # Format: { ID: [0: Status(-1=restricted,0=locked,1=unlocked,2=forced_open), 
        #                1: StartRegion, 
        #                2: DestRegion, 
        #                3: NeedFreedan, 
        #                4: [[item1, qty1],[item2,qty2],...],
        #                5: IsBidirectional
        #               ] }
        self.logic = {
            # Jeweler Rewards
            0:  [0, 1, 2, False, [[1, gem[0]]], False],  # Jeweler Reward 1
            1:  [0, 1, 2, False, [[1, gem[0] - 2], [41, 1]], False],
            2:  [0, 1, 2, False, [[1, gem[0] - 3], [42, 1]], False],
            3:  [0, 1, 2, False, [[1, gem[0] - 5], [41, 1], [42, 1]], False],
            4:  [0, 2, 3, False, [[1, gem[1]]], False],  # Jeweler Reward 2
            5:  [0, 2, 3, False, [[1, gem[1] - 2], [41, 1]], False],
            6:  [0, 2, 3, False, [[1, gem[1] - 3], [42, 1]], False],
            7:  [0, 2, 3, False, [[1, gem[1] - 5], [41, 1], [42, 1]], False],
            8:  [0, 3, 4, False, [[1, gem[2]]], False],  # Jeweler Reward 3
            9:  [0, 3, 4, False, [[1, gem[2] - 2], [41, 1]], False],
            10: [0, 3, 4, False, [[1, gem[2] - 3], [42, 1]], False],
            11: [0, 3, 4, False, [[1, gem[2] - 5], [41, 1], [42, 1]], False],
            12: [0, 4, 5, False, [[1, gem[3]]], False],  # Jeweler Reward 4
            13: [0, 4, 5, False, [[1, gem[3] - 2], [41, 1]], False],
            14: [0, 4, 5, False, [[1, gem[3] - 3], [42, 1]], False],
            15: [0, 4, 5, False, [[1, gem[3] - 5], [41, 1], [42, 1]], False],
            16: [0, 5, 6, False, [[1, gem[4]]], False],  # Jeweler Reward 5
            17: [0, 5, 6, False, [[1, gem[4] - 2], [41, 1]], False],
            18: [0, 5, 6, False, [[1, gem[4] - 3], [42, 1]], False],
            19: [0, 5, 6, False, [[1, gem[4] - 5], [41, 1], [42, 1]], False],
            20: [0, 6, 7, False, [[1, gem[5]]], False],  # Jeweler Reward 6
            21: [0, 6, 7, False, [[1, gem[5] - 2], [41, 1]], False],
            22: [0, 6, 7, False, [[1, gem[5] - 3], [42, 1]], False],
            23: [0, 6, 7, False, [[1, gem[5] - 5], [41, 1], [42, 1]], False],
            24: [0, 7, 8, False, [[1, gem[6]]], False],  # Jeweler Reward 7 (Mansion)
            25: [0, 7, 8, False, [[1, gem[6] - 2], [41, 1]], False],
            26: [0, 7, 8, False, [[1, gem[6] - 3], [42, 1]], False],
            27: [0, 7, 8, False, [[1, gem[6] - 5], [41, 1], [42, 1]], False],

            # Inter-Continental Travel
            30: [0, 28,   15, False, [[37, 1]], False],   # South Cape: Erik w/ Lola's Letter
            31: [0, 102,  15, False, [[37, 1]], False],   # Coast: Turbo w/ Lola's Letter
            32: [0, 280,  15, False, [[37, 1]], False],   # Watermia: Bridgeman w/ Lola's Letter
            33: [0, 160, 161, False, [[13, 1]], False],   # Neil's: Neil w/ Memory Melody
            34: [0, 314,  17, False, [[505, 1]], False],  # Euro: Neil w/ Memory restored
            35: [0, 402,  17, False, [[505, 1]], False],  # Dao: Neil w/ Memory restored
            36: [0,  60,  64, False, [[25, 1]], False],   # Moon Tribe healed w/ Teapot
            37: [0, 170,  16, False, [[502, 1]], False],  # Sky Garden: Spirits w/ spirits healed
            38: [0, 280, 288, False, [[24, 1]], False],   # Watermia: Stablemaster w/ Will
            39: [0, 310, 311, False, [[24, 1]], False],   # Euro: Stablemaster w/ Will
            40: [0, 350, 351, False, [[10, 1]], False],   # Natives': Child Guide w/ Large Roast

            # Edward's / Tunnel
            60: [0, 32, 33, False, [[2, 1]], True],     # Escape/Enter cell w/Prison Key
            703: [0,47, 720,False, [[704, 1]], True],   # Worm orb opens Dark Space
            63: [0, 47 ,704,  True, [], False],         # Bridge to second area via Freedan
            704: [0,704,705,False, [[705, 1]], True],   # Skeleton barrier between 2nd and 3rd areas
            705: [0,705,706,False, [[706, 1]], True],   # Skeleton barrier between 3rd and final areas

            # Itory
            70: [0, 50, 51, False, [[9, 1]], False],     # Town appears w/ Lola's Melody
            71: [0, 55, 59, False, [[23, 1]], False],    # Get Lilly w/ Necklace

            # Moon Tribe
            80: [0, 61, 62, False, [[608, 1]], False],   # Cave challenge w/ Will ability
            600:[0, 61, 62, False, [[601, 1]], False],   # Cave challenge itemless w/ glitches

            # Inca / Gold Ship / Freejia
            88:  [0,  89, 524, False, [[7, 1]], False],          # Map 37, place Diamond Block
            89:  [0,  72,  99, False, [[601, 1]], False],        # Map 29 progression w/ Z-ladder glitch
            706: [0,  72,  70, False, [[709, 1]], True],         # Inca exterior (29) N<->NE via 4-Way orb
            707: [0,  74,  72, False, [[707, 1]], True],         # Inca exterior (29) SW<->N via 4-Way orb
            708: [0,  75,  72, False, [[708, 1]], True],         # Inca exterior (29) SE<->N via 4-Way orb
            #700: [0,  73, 700, False, [[607, 1], [610, 1]], False], # Inca west 4-Way orb from C via ranged in DSC
            90:  [0,  77,  78, False, [[3, 1], [4, 1]], False],  # Map 30 progression w/ Inca Statues
            91:  [0,  80,  81, False, [[608, 1]], True],         # Map 32 break statue w/ Will ability
            710: [0,  82,  83, False, [[710, 1]], False],        # Inca N/S ramp (33) via whirligig orb
            94:  [0,  85, 707,  True, [], False],                # Map 35 progression w/ Freedan
            709: [0,  85,  86, False, [[711, 1]], False],        # Inca E/W ramp (35) via whirligig orb
            97:  [0,  91,  92, False, [[608, 1]], False],        # Map 38 break statues w/ Will ability
            711: [0,  96,  95, False, [[713, 1]], False],        # Map 40 reverse via 4-Way orb
            #100: [0, 100, 104, False, [[100, 1]], False],        # Gold Ship progression w/ Statue 1
            101: [0, 110, 115, False, [[504, 1]], False],        # Freejia: Slaver item w/ Laborer Found

            # Diamond Mine
            712: [0, 130, 708, False, [[715, 1]], True],            # Map 61 S fence progression via monster
            713: [0, 708, 709, False, [[714, 1]], True],            # Map 61 C fence progression via monster
            714: [0, 709, 131, False, [[716, 1]], True],            # Map 61 N fence progression via monster
            #702: [0, 709, 701, False, [[607, 1], [610, 1]], False], # Map 61 C lizard from N via ranged in DSC
            114: [0, 136, 137, False, [[608, 1]], False],           # Map 64 trapped laborer w/ Will ability
            715: [0, 136, 721, False, [[718, 1]], True],            # Map 64 appearing DS via worm orb
            117: [0, 138, 139, False, [[63, 1]], False],            # Map 65 ramp access via Spin Dash
            716: [0, 138, 139, False, [[719, 1]], False],           # Map 65 ramp access via worm orb
            118: [0, 138, 710, False, [[610, 1]], False],           # Map 65 worm access via ranged

            # Sky Garden
            130: [0, 170, 171, False, [[14, 4]], False],            # Boss access w/ Crystal Balls
            131: [0, 177, 711, False, [[610, 1]], False],           # SE Top (79) robot orb via ranged
            718: [0, 177, 178, False, [[720, 1]], True],            # SE Top (79) barrier via robot orb
            720: [0, 180, 716, False, [[721, 1]], True],            # SE Bot (80) chest via robot orb
            721: [0, 181, 168, False, [[722, 1]], True],            # SW Top (81) C<->N via robot orb
            723: [0, 181, 182, False, [[724, 1]], True],            # SW Top (81) C<->W via worm orb
            133: [0, 168, 182, False, [[506, 1]], True],            # Map 81 progression w/ switch 1
            134: [0, 182, 183, False, [[507, 1]], True],            # Map 81 progression w/ switch 2
            135: [0, 182, 184, False, [[608, 1]], True],            # Map 81 break statues w/ Will ability
            138: [0, 184, 185, False, [[508, 1], [608, 1]], False], # Map 81 progression w/ switch 3 & Will ability
            141: [0, 181, 182, False, [[63, 1]], False],            # Map 81 progression w/ Spin Dash
            142: [0, 181, 184, False, [[63, 1]], False],            # Map 81 progression w/ Spin Dash
            143: [0, 182, 185, False, [[63, 1]], False],            # Map 81 progression w/ Spin Dash
            601: [0, 181, 182, False, [[601, 1]], False],           # Map 81 ramps w/ glitches
            602: [0, 181, 184, False, [[601, 1]], False],           # Map 81 ramps w/ glitches
            603: [0, 182, 185, False, [[601, 1]], False],           # Map 81 ramps w/ glitches
            739: [0, 187, 508, False, [[725, 1]], False],           # Map 82 switch access via fire cage orb
            144: [0, 188, 189,  True, [], False],                   # Map 82 progression w/ Freedan
            145: [0, 188, 189, False, [[601, 1], [604, 1]], False], # Map 82 progression w/ Glitches + Flute
            146: [0, 192, 190, False, [[63, 1]], False],            # Map 83 progression w/ Spin Dash
            147: [0, 195, 199, False, [[610, 1]], False],           # Map 84 progression w/ ranged
            149: [0, 195, 199,  True, [[65, 1]], False],            # Map 84 progression w/ Aura Barrier
            152: [0, 170,  16, False, [[502, 1]], False],           # Moon Tribe passage w/ spirits healed

            # Seaside Palace
            160: [0, 205, 208, False, [[501, 1]], False],   # Coffin access w/ Lilly
            161: [0, 209, 510, False, [[17, 1]], False],    # Purify fountain w/stone
            162: [0, 200, 206, False, [[510, 1]], False],   # Buffy access w/ purified fountain

            # Mu
            724: [0, 212, 722, False, [[726, 1]], True],             # Mu entrance (95) gate via golem orb
            171: [0, 212, 213, False, [[511, 1]], True],             # Map 95 top-midE w/ water lowered 1
            172: [0, 213, 215, False, [[512, 1]], True],             # Map 95 midE-botE w/ water lowered 2
            173: [0, 214, 216, False, [[512, 1]], True],             # Map 95 midw-botW w/ water lowered 2
            174: [0, 217, 218, False, [[511, 1]], True],             # Map 96 top-mid w/ water lowered 1
            726: [0, 217, 725, False, [[727, 1]], True],             # Mu NE (96) N/S semiprogression via rocks
            727: [0, 723, 725, False, [[728, 1]], True],             # Mu NE (96) N/S semiprogression via rocks
            #753: [0, 723, 726, False, [[607, 1], [610, 1]], False],  # Mu NE, N orb from S, via ranged in DSC
            #754: [0, 217, 724, False, [[607, 1], [610, 1]], False],  # Mu NE, S orb from N, via ranged in DSC
            175: [0, 222, 221, False, [[511, 1], [610, 1]], False],  # Map 97 midN->island w/ water lowered 1 & ranged
            177: [0, 222, 221, False, [[511, 1], [601, 1]], False],  # Map 97 midN->island w/ water lowered 1 & glitches
            178: [0, 226, 227, False, [[511, 1]], True],             # Map 98 top-midE w/ water lowered 1
            179: [0, 227, 229, False, [[512, 1]], True],             # Map 98 midE-botE w/ water lowered 2
            180: [0, 228, 230, False, [[512, 1]], True],             # Map 98 midW-botW w/ water lowered 2
            181: [0, 229, 230, False, [[62, 1], [512, 1]], True],    # Map 98 W/E Slider hole
            184: [0, 237, 238, False, [[62, 1], [511, 1]], True],    # Map 101 midW-midE w/ Psycho Slider
            185: [0, 240, 241, False, [[19, 2]], False],             # Map 102 progression w/ Rama Statues
            186: [0, 526, 247, False, [[18, 1]], False],             # Water lowered 1 w/ Hope Statue
            187: [0, 527, 247, False, [[18, 1]], False],             # Water lowered 1 w/ Hope Statue
            188: [0, 526, 248, False, [[18, 2], [527, 1], [511, 1]], False],  # Water lowered 2 w/ Hope Statues, both rooms, and water lowered 1
            189: [0, 527, 248, False, [[18, 2], [526, 1], [511, 1]], False],  # Water lowered 2 w/ Hope Statues, both rooms, and water lowered 1

            # Angel Dungeon
            214: [0, 272, 273, False, [[513, 1]], False],   # Ishtar's chest w/ puzzle complete

            # Great Wall
            504: [0, 293, 291, False, [[63, 1]], False],            # Map 131 (drop room) backwards w/ Spin Dash
            220: [0, 296, 295, False, [[601, 1], [604, 1]], False], # Map 133 E->C w/ glitches and Flute
            221: [0, 296, 295, False, [[63, 1]], False],            # Map 133 E->C w/ Spin Dash
            222: [0, 296, 295,  True, [], False],                   # Map 133 E->C w/ Freedan
            228: [0, 295, 294, False, [[63, 1]], False],            # Map 133 C->W w/ Spin Dash
            728: [0, 298, 299, False, [[732, 1]], True],            # Map 135 progression w/ archer orb
            223: [0, 298, 712, False, [[610, 1]], False],           # Map 135 archer via ranged
            225: [0, 299, 712, False, [[610, 1]], False],           # Map 135 archer via ranged
            227: [0, 300, 301, False, [[63, 1]], True],             # Map 136 progression w/ Spin Dash

            # Euro
            230: [0, 314, 315, False, [[40, 1]], False],    # Ann item w/ Apple

            # Mt. Temple
            240: [0, 331, 332, False, [[63, 1]], True],              # Map 161 progression w/ Spin Dash
            242: [0, 333, 514, False, [[26, 1], [605, 1]], False],   # Use Mushroom drops 1, no dungeon shuffle
            510: [0, 333, 514, False, [[26, 3], [606, 1]], False],   # Use Mushroom drops in dungeon shuffle
            530: [0, 333, 514, False, [[26, 3], [607, 1]], False],   # Use Mushroom drops in dungeon shuffle
            750: [0, 333, 335, False, [[514, 1]], True],             # Drops vine 1
            244: [0, 339, 515, False, [[26, 2], [605, 1]], False],   # Use Mushroom drops 2, no dungeon shuffle
            511: [0, 339, 515, False, [[26, 3], [606, 1]], False],   # Use Mushroom drops in dungeon shuffle
            531: [0, 339, 515, False, [[26, 3], [607, 1]], False],   # Use Mushroom drops in dungeon shuffle
            751: [0, 339, 340, False, [[515, 1]], True],             # Drops vine 2
            246: [0, 340, 516, False, [[26, 3]], False],             # Use Mushroom drops 3
            752: [0, 340, 341, False, [[516, 1]], True],             # Drops vine 3

            # Natives'
            250: [0, 353, 354, False, [[29, 1]], False],    # Statues awake w/ Gorgon Flower

            # Ankor Wat
            #260: [0, 361, 739,  True, [[64, 1], [54, 2], [607, 1]], False],  # Map 177 orb w/ upgraded Friar and DSC
            729: [0, 361, 362, False, [[735, 1]], True],             # Wat Outer South (177) via scarab orb
            261: [0, 363, 364, False, [[63, 1]], False],             # Map 178 S->C w/ Spin Dash
            262: [0, 364, 365, False, [[62, 1], [736, 1]], False],   # Map 178 C->N w/ Psycho Slider and scarab key
            263: [0, 365, 364, False, [[62, 1]], False],             # Map 178 N->C w/ Psycho Slider
            264: [0, 367, 366, False, [[63, 1]], False],             # Map 179 W->E w/ Spin Dash
            265: [0, 369, 370, False, [[62, 1]], False],             # Map 181 N->C w/ Psycho Slider
            266: [0, 370, 371, False, [[63, 1]], False],             # Map 181 C->S w/ Spin Dash
            267: [0, 373, 374,  True, [[66, 1]], False],             # Map 183 SW->W w/ Earthquaker
            268: [0, 373, 374,  True, [[64, 1], [54, 2]], False],    # Map 183 SW->W w/ upgraded Friar
            269: [0, 373, 374,  True, [[64, 1], [601, 1]], False],   # Map 183 SW->W w/ Friar and glitches
            271: [0, 376, 727,  True, [[64, 1]], False],             # Map 184 orb access via Friar
            272: [0, 376, 727,  True, [[36, 1]], False],             # Map 184 orb access via Shadow
            731: [0, 376, 377, False, [[738, 1]], True],             # Map 184 S->N w/ skull orb
            276: [0, 384, 385, False, [[62, 1], [601, 1]], True],    # Map 188 S-N w/ Slider and glitches
            277: [0, 384, 385, False, [[62, 1], [28, 1]], True],     # Map 188 S-N w/ Slider and Glasses
            279: [0, 386, 387, False, [[62, 1]], True],              # Map 189 S-N w/ Slider

            # Pyramid
            290: [0, 410, 411, False, [[62, 1]], False],             # Map 204 progression w/ Slider
            291: [0, 410, 411, False, [[63, 1]], False],             # Map 204 progression w/ Spin
            292: [0, 410, 411, False, [[601, 1]], False],            # Map 204 progression w/ glitches
            736: [0, 411, 713, False, [[739, 1]], False],            # Map 204 top DS w/ orb orb
            293: [0, 713, 412, True , [[36, 1], [739, 1]], False],   # Map 204 progression w/ Aura and DS
            294: [0, 713, 413, True , [[36, 1], [739, 1]], False],   # Map 204 progression w/ Aura and DS
            295: [0, 415, 449, False, [[30, 1], [31, 1], [32, 1], [33, 1], [34, 1], [35, 1], [38, 1]], False],
                                                              # Boss door open w/ Hieroglyphs
            296: [0, 416, 417, False, [[63, 1]], True],              # Map 206 progression w/ Spin Dash
            298: [0, 418, 419, False, [[63, 1]], True],              # Map 207 progression w/ Spin Dash
            300: [0, 426, 427,  True, [[36, 1]], False],             # Map 212 progression w/ Aura
            301: [0, 426, 427,  True, [[66, 1]], False],             # Map 212 progression w/ Earthquaker
            302: [0, 427, 428,  True, [[36, 1]], False],             # Map 212 to SE chest w/ Aura
            303: [0, 427, 429,  True, [[36, 1]], False],             # Map 212 progression w/ Aura
            304: [0, 427, 429,  True, [[66, 1]], False],             # Map 212 progression w/ Earthquaker
            #812: [0, 429, 426, False, [[800, 1]], False],            # DSX: Handle map 212 as a corridor
            305: [0, 431, 432, False, [[63, 1]], True],              # Map 214 to NE chest w/ Spin Dash
            306: [0, 431, 434,  True, [[36, 1]], False],             # Map 214 progression w/ Aura
            307: [0, 431, 433,  True, [[64, 1]], False],             # Map 214 progression w/ Friar
            #810: [0, 437, 436, False, [[800, 1]], False],            # DSX: Handle map 216 as a corridor
            308: [0, 438, 439, False, [[63, 1]], True],              # Map 217 progression w/ Spin Dash
            310: [0, 440, 441, False, [[63, 1]], True],              # Map 219 progression w/ Spin Dash
            312: [0, 435, 450, False, [[6, 6], [50, 2], [51, 1], [52, 1]], True],
                                                              # Killer 6 w/ herbs and upgrades
            313: [0, 435, 450,  True, [[64, 1], [54, 1]], True],     # Killer 6 w/ Friar II
            314: [0, 411, 414, False, [[517, 1]], False],            # Pyramid to boss w/hieroglyphs placed
            516: [0, 413, 411, False, [[525, 1]], False],            # Pyramid portal
            517: [0, 419, 411, False, [[525, 1]], False],            # Pyramid portal
            518: [0, 423, 411, False, [[525, 1]], False],            # Pyramid portal
            519: [0, 425, 411, False, [[525, 1]], False],            # Pyramid portal
            520: [0, 428, 411, False, [[525, 1]], False],            # Pyramid portal
            521: [0, 430, 411, False, [[525, 1]], False],            # Pyramid portal
            522: [0, 437, 411, False, [[525, 1]], False],            # Pyramid portal
            523: [0, 441, 411, False, [[525, 1]], False],            # Pyramid portal
            524: [0, 450, 411, False, [[525, 1]], False],            # Pyramid portal
            525: [0,   0, 525, False, [[605, 1]], False],            # No shuffle: portals always open
            526: [0,   0, 525, False, [[606, 1]], False],            # Basic shuffle: portals always open
            527: [0,   0, 525, False, [[607, 1], [36, 1]], False],   # Dungeon Chaos: portals with Aura

            # Babel / Mansion items 740,741
            320: [0, 461, 462, False, [[36, 1], [39, 1]], False],    # Map 223 progression w/ Aura and Ring
            321: [0, 473, 479, False, [[522, 1]], False],            # Olman statue w/ Mummy Queen 2
            322: [0, 473, 479, False, [[523, 1]], False],            # Olman statue w/ Solid Arm
            732: [0, 480, 714, False, [[740, 1]], True],             # Mansion east gate with monster orb
            734: [0, 714, 715, False, [[741, 1]], True],             # Mansion west gate with monster orb
            323: [0, 715, 481, False, [[62, 1]], True],              # Mansion progression w/ Slider

            # Endgame / Misc
            400: [-1, 49, 490, False, [[20, 1]], False],                       # Rescue Kara from Edward's w/ Magic Dust
            401: [-1, 150, 490, False, [[20, 1]], False],                      # Rescue Kara from Mine w/ Magic Dust
            402: [-1, 270, 490, False, [[20, 1]], False],                      # Rescue Kara from Angel w/ Magic Dust
            403: [-1, 345, 490, False, [[20, 1]], False],                      # Rescue Kara from Mt. Temple w/ Magic Dust
            404: [-1, 391, 490, False, [[20, 1]], False],                      # Rescue Kara from Ankor Wat w/ Magic Dust
            405: [0, 490, 491, False, [[36, 1], [39, 1], [602, 1]], False],    # (Early) Firebird w/ Kara, Aura, Ring, and the setting
            406: [0, 490, 492, False, [[36, 1], [100, 0], [101, 0], [102, 0], [103, 0], [104, 0], [105, 0]], False],
                                                                        # Beat Game w/Mystic Statues and Aura
            407: [0, 490, 492, False, [[36, 1], [106, self.statues_required]], False],  # Beat Game w/Mystic Statues and Aura (player choice variant)
            
            408: [0, 0, 608, False, [[61, 1]], False],        # Got any Will ability
            409: [0, 0, 608, False, [[62, 1]], False],        # Got any Will ability
            410: [0, 0, 608, False, [[63, 1]], False]         # Got any Will ability
        }

        # Define addresses for in-game spoiler text
        self.spoiler_labels = {
            0: "SpoilerTextCastleGuard",
            1: "SpoilerTextItoryElder",
            2: "SpoilerTextGoldShipQueen",
            3: "SpoilerTextDiamondCoast",
            # 4: "SpoilerTextFreejiaSlave",
            5: "SpoilerTextSeaPalCoffin",
            6: "SpoilerTextIshtarsApprentice",
            7: "SpoilerTextKarasJournal",
            8: "SpoilerTextEuroOldMan",
            9: "SpoilerTextAngkorWatSpirit",
            10: "SpoilerTextDaoGirl",
            11: "SpoilerTextBabelSpirit"
        }
        
        # Area names for in-game spoilers
        self.area_short_name = {
            0: "Jeweler",
            1: "Jeweler",
            2: "Jeweler",
            3: "Jeweler",
            4: "Jeweler",
            5: "Jeweler",

            6:  "South Cape",
            7:  "South Cape",
            8:  "South Cape",
            9:  "South Cape",
            10: "South Cape",

            11: "Edward's Castle",
            12: "Edward's Castle",
            13: "Edward's Prison",
            14: "Edward's Prison",
            15: "Edward's Tunnel",
            16: "Edward's Tunnel",
            17: "Edward's Tunnel",
            18: "Edward's Tunnel",
            19: "Edward's Tunnel",
            700: "Edward's Tunnel",
            701: "Edward's Tunnel",
            702: "Edward's Tunnel",
            703: "Edward's Tunnel",
            704: "Edward's Tunnel",
            705: "Edward's Tunnel",
            706: "Edward's Tunnel",

            20: "Itory",
            21: "Itory",
            22: "Itory",

            23: "Moon Tribe",

            24: "Inca",
            25: "Inca",
            26: "Inca",
            27: "Inca",
            28: "Singing Statue",
            29: "Inca",
            30: "Inca",
            31: "Inca",
            707: "Inca",
            708: "Inca",
            709: "Inca",
            710: "Inca",
            711: "Inca",
            712: "Inca",
            713: "Inca",

            32: "Gold Ship",

            33: "Diamond Coast",

            34: "Freejia",
            35: "Freejia",
            36: "Freejia",
            37: "Freejia",
            38: "Freejia",
            39: "Freejia",

            40: "Diamond Mine",
            41: "Laborer",
            42: "Laborer",
            43: "Diamond Mine",
            44: "Laborer",
            45: "Sam",
            46: "Diamond Mine",
            47: "Diamond Mine",
            48: "Diamond Mine",
            714: "Diamond Mine",
            715: "Diamond Mine",
            716: "Diamond Mine",
            717: "Diamond Mine",
            718: "Diamond Mine",
            719: "Diamond Mine",

            49: "Sky Garden",
            50: "Sky Garden",
            51: "Sky Garden",
            52: "Sky Garden",
            53: "Sky Garden",
            54: "Sky Garden",
            55: "Sky Garden",
            56: "Sky Garden",
            57: "Sky Garden",
            58: "Sky Garden",
            59: "Sky Garden",
            60: "Sky Garden",
            720: "Sky Garden",
            721: "Sky Garden",
            722: "Sky Garden",
            723: "Sky Garden",
            724: "Sky Garden",
            725: "Sky Garden",

            61: "Seaside Palace",
            62: "Seaside Palace",
            63: "Seaside Palace",
            64: "Buffy",
            65: "Coffin",
            66: "Seaside Palace",

            67: "Mu",
            68: "Mu",
            69: "Mu",
            70: "Mu",
            71: "Mu",
            72: "Mu",
            73: "Mu",
            74: "Mu",
            75: "Mu",
            726: "Mu",
            727: "Mu",
            728: "Mu",
            729: "Mu",
            730: "Mu",
            731: "Mu",

            76: "Angel Village",
            77: "Angel Village",
            78: "Angel Village",
            79: "Angel Village",
            80: "Angel Village",
            81: "Angel Village",
            82: "Angel Village",

            83: "Watermia",
            84: "Watermia",
            85: "Lance",
            86: "Watermia",
            87: "Watermia",
            88: "Watermia",

            89: "Great Wall",
            90: "Great Wall",
            91: "Great Wall",
            92: "Great Wall",
            93: "Great Wall",
            94: "Great Wall",
            95: "Great Wall",
            732: "Great Wall",

            96:  "Euro",
            97:  "Euro",
            98:  "Euro",
            99:  "Euro",
            100: "Euro",
            101: "Euro",
            102: "Ann",
            103: "Euro",

            104: "Mt. Kress",
            105: "Mt. Kress",
            106: "Mt. Kress",
            107: "Mt. Kress",
            108: "Mt. Kress (end)",
            109: "Mt. Kress",
            110: "Mt. Kress",
            111: "Mt. Kress",
            734: "Mt. Kress",

            112: "Native Village",
            113: "Statue",
            114: "Native Village",

            115: "Ankor Wat",
            116: "Ankor Wat",
            117: "Ankor Wat",
            118: "Ankor Wat",
            119: "Ankor Wat",
            120: "Shrubber",
            121: "Spirit",
            122: "Ankor Wat",
            123: "Ankor Wat",
            124: "Ankor Wat",
            735: "Ankor Wat",
            736: "Ankor Wat",
            738: "Ankor Wat",

            125: "Dao",
            126: "Dao",
            127: "Dao",
            128: "Snake Game",
            129: "Dao",

            130: "Gaia",
            131: "Pyramid",
            132: "Pyramid",
            133: "Pyramid",
            134: "Pyramid",
            135: "Pyramid",
            136: "Killer 6",
            137: "Pyramid",
            138: "Pyramid",
            139: "Pyramid",
            140: "Pyramid",
            141: "Pyramid",
            142: "Pyramid",
            739: "Pyramid",

            143: "Babel",
            144: "Babel",
            145: "Babel",
            146: "Babel",

            147: "Mansion",
            740: "Mansion",
            741: "Mansion",

            148: "Castoth",
            149: "Viper",
            150: "Vampires",
            151: "Sand Fanger",
            152: "Mummy Queen",
            153: "Olman"
        }

        # Database of enemy groups and spritesets
        # FORMAT: { ID: [Header card define name, Friendly name]}
        self.enemysets = {
            0:  ["CardMonstersEdDg", "Underground Tunnel"],
            1:  ["CardMonstersIncaSpinners", "Inca Ruins (Mud Monster and Larva)"],
            2:  ["CardMonstersIncaStatues", "Inca Ruins (Statues)"],
            3:  ["CardMonstersMine", "Diamond Mine"],
            4:  ["CardMonstersSkGnTop", "Sky Garden (top)"],
            5:  ["CardMonstersSkGnBot", "Sky Garden (bottom)"],
            6:  ["CardMonstersMu", "Mu"],
            7:  ["CardMonstersAngl", "Angel Dungeon"],
            8:  ["CardMonstersGtWl", "Great Wall"],
            9:  ["CardMonstersKres", "Mt. Kress"],
            10: ["CardMonstersAnkrOuter", "Ankor Wat (outside)"],
            11: ["CardMonstersAnkrInner", "Ankor Wat (inside)"],
            12: ["CardMonstersPymd", "Pyramid"],
            13: ["CardMonstersJwlr", "Jeweler's Mansion"]
        }

        # Enemy map database
        # FORMAT: { ID: [0: EnemySet, 
        #                1: RewardBoss(0 for no reward), 
        #                2: Reward[type, tier], 
        #                3: FriendlyName,
        #                4: DarknessAllowedType (0 = never, 1 = cursed, 2 = possible, 3 = source, 4 = inherited), 
        #                5: FirstMonsterId, 
        #                6: LastMonsterId, 
        #                7: ForbiddenEnemysets, 
        #                8: Jumbo map (room clear is frustrating or requires multiple visits), 
        #                9: DarknessSinkMaps
        #               ] }
        self.maps = {
            # Underground Tunnel
            12: [0, 1, [0,0], "EdDg Entrance", 2, 0x0001, 0x0003, [], False, [13]],
            13: [0, 1, [0,0], "EdDg East",     2, 0x0004, 0x0012, [6, 10], False, [12,14]],
            14: [0, 1, [0,0], "EdDg South",    2, 0x0013, 0x0021, [6, 10], False, [13,15]],
            15: [0, 1, [0,0], "EdDg West",     2, 0x0022, 0x002e, [10], False, [14,17]],
            17: [-1,0, [0,0], "EdDg Flower",   4, 0,      0,      [], False, [15,18]],
            18: [0, 1, [0,0], "EdDg Big",      3, 0x002f, 0x0044, [6, 10], True, [17]],

            # Inca Ruins
            27: [1, 0, [0,0], "Moon Tribe Cave",     3, 0x0045, 0x004a, [10], False, []],
            29: [1, 1, [0,0], "Inca Exterior",       1, 0x004b, 0x0059, [10], True, [31,32,33,34,35,37,38]],
            30: [-1,0, [0,0], "Inca Near Castoth",   4, 0,      0,      [], False, [34,41]],
            31: [-1,0, [0,0], "Inca Statue Puzzle",  2, 0,      0,      [], False, [29,40]],
            32: [1, 1, [0,0], "Inca Will Ability",   1, 0x005e, 0x0065, [], False, [29,35]],
            33: [2, 1, [0,0], "Inca Water",          1, 0x0066, 0x007a, [6, 10], True, [29,35]],
            34: [2, 1, [0,0], "Inca Big",            2, 0x007b, 0x008e, [], True, [29,30,38]],
            35: [2, 1, [0,0], "Inca E/W Jump",       1, 0x008f, 0x009d, [6, 10], False, [29,32,33]],
            #36: [-1,0, [0,0], "Inca Golden Tile",    2, 0,      0,      [], False, [34,30]],
            37: [1, 1, [0,0], "Inca D.Block",        1, 0x009e, 0x00a9, [], False, [29,39]],
            38: [1, 1, [0,0], "Inca Divided",        3, 0x00aa, 0x00b3, [], True, [29,34]],
            39: [1, 1, [0,0], "Inca West of D.Block",2, 0x00b4, 0x00c4, [], False, [37]],
            40: [1, 1, [0,0], "Inca Before Melody",  3, 0x00c5, 0x00cc, [], False, [31]],
            41: [-1,0, [0,0], "Inca Castoth",        3, 0,      0,      [], False, [30]],

            # Diamond Mine 
            61: [3, 2, [0,0], "Mine Fences",    3, 0x00ce, 0x00d8, [10], False, [65,66]],
            62: [3, 2, [0,0], "Mine Entrance",  1, 0x00d9, 0x00df, [], False, [63]],
            63: [3, 2, [0,0], "Mine Big",       1, 0x00e0, 0x00f7, [], True, [62,64,67]],
            64: [3, 2, [0,0], "Mine Cave-in",   2, 0x00f8, 0x00fd, [10], False, [63,65]],
            65: [3, 2, [0,0], "Mine Friar",     2, 0x00fe, 0x0108, [1, 6, 7, 8, 9, 10, 12, 13], False, [61,64,66]],  # Stationary Grundit
            66: [-1,0, [0,0], "Mine Caverns",   4, 0,      0,      [], False, []],
            67: [-1,0, [0,0], "Mine Elevator",  4, 0,      0,      [], False, [66,63,68]],
            68: [-1,0, [0,0], "Mine End Branch",4, 0,      0,      [], False, [66,67,69,70]],
            69: [3, 2, [0,0], "Mine Morgue",    3, 0x0109, 0x010e, [], False, [68]],
            70: [3, 2, [0,0], "Mine Other Key", 3, 0x010f, 0x0117, [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12], False, [68]],
            71: [-1,0, [0,0], "Mine Sam",       4, 0,      0,      [], False, [70]],

            # Sky Garden 
            76: [-1,0, [0,0], "SkGn Entrance", 1, 0,      0,      [], False, [77,79,81,83,85]],
            77: [4, 2, [0,0], "SkGn NE Top",   2, 0x0118, 0x0129, [], True, [76, 78]],
            78: [5, 2, [0,0], "SkGn NE Bot",   3, 0x012a, 0x0136, [], True, [77]],
            79: [4, 2, [0,0], "SkGn SE Top",   2, 0x0137, 0x0143, [], True, [76, 80, 86]],
            80: [5, 2, [0,0], "SkGn SE Bot",   3, 0x0144, 0x014f, [10], True, [79]],
            81: [4, 2, [0,0], "SkGn SW Top",   2, 0x0150, 0x015c, [10], False, [76, 82]],
            82: [5, 2, [0,0], "SkGn SW Bot",   3, 0x015d, 0x0163, [0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13], True, [81]],
            83: [4, 2, [0,0], "SkGn NW Top",   2, 0x0164, 0x0172, [], True, [76, 84]],
            84: [5, 2, [0,0], "SkGn NW Bot",   3, 0x0173, 0x0182, [0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13], True, [83]],
            85: [-1,0, [0,0], "SkGn Viper",    3, 0,      0,      [], False, [76]],
            86: [-1,0, [0,0], "SkGn Blue Room",4, 0,      0,      [], False, [79]],

            # Mu
            95:  [6, 3, [0,0], "Mu NW", 1, 0x0193, 0x01a5, [10], True, [96,98]],
            96:  [6, 3, [0,0], "Mu NE", 1, 0x01a6, 0x01bf, [7, 8, 9, 12], True, [95,97]],
            97:  [6, 3, [0,0], "Mu E",  2, 0x01c0, 0x01d9, [7, 8, 9, 12], True, [96,98]],
            98:  [6, 3, [0,0], "Mu W",  2, 0x01da, 0x01e5, [], True, [95,97,100]],
            100: [6, 3, [0,0], "Mu SW", 2, 0x01e6, 0x01ed, [], True, [98,101]],
            101: [6, 3, [0,0], "Mu SE", 3, 0x01ee, 0x01fe, [7, 8, 9, 12], False, [100]],

            # Angel Dungeon
            109: [7, 3, [0,0], "Angel Entrance", 2, 0x0201, 0x020f, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], True, [110]],
            110: [7, 3, [0,0], "Angel Second",   2, 0x0210, 0x0222, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], True, [109,111]],
            111: [7, 3, [0,0], "Angel Dark",     2, 0x0223, 0x0228, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [110,112]],
            112: [7, 3, [0,0], "Angel Water",    2, 0x0229, 0x022f, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [111,113]],
            113: [7, 3, [0,0], "Angel Wind",     2, 0x0230, 0x0231, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [112,114]],
            114: [7, 3, [0,0], "Angel Final",    3, 0x0232, 0x0242, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [113]],

            # Great Wall
            130: [8, 4, [0,0], "GtWl Entrance",  1, 0x0243, 0x0262, [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13], True, [131]],
            131: [8, 4, [0,0], "GtWl Tall Drop", 1, 0x0263, 0x0277, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], True, [130,133]],
            133: [8, 4, [0,0], "GtWl Ramps",     1, 0x0278, 0x0291, [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13], True, [131,134]],
            134: [8, 4, [0,0], "GtWl Spin Dash", 1, 0x0292, 0x029a, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [133,135]],
            135: [8, 4, [0,0], "GtWl Friar",     2, 0x029b, 0x02a6, [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13], True, [134,136]],
            136: [8, 4, [0,0], "GtWl Final",     2, 0x02a7, 0x02b5, [0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13], True, [135,138]],
            138: [-1,0, [0,0], "GtWl Fanger",    3, 0,      0,      [], False, [136]],

            # Mt Temple 
            160: [9, 4, [0,0], "Kress Entrance",    1, 0x02b7, 0x02c1, [], False, [161]],
            161: [9, 4, [0,0], "Kress First DS",    1, 0x02c2, 0x02d9, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], True, [160,162]],
            162: [9, 4, [0,0], "Kress First Vine",  1, 0x02da, 0x02e7, [7, 11], True, [161,163,164,165]],
            163: [9, 4, [0,0], "Kress Second DS",   3, 0x02e8, 0x02fb, [], False, [162]],
            164: [9, 4, [0,0], "Kress West Chest",  3, 0x02fc, 0x0315, [6, 7], True, [162]],
            165: [9, 4, [0,0], "Kress Two Vines",   2, 0x0316, 0x032d, [7, 11], True, [162,166,167,168]],
            166: [9, 4, [0,0], "Kress Mushrooms",   3, 0x032e, 0x033c, [], True, [165]],
            167: [9, 4, [0,0], "Kress Final DS",    3, 0x033d, 0x0363, [7], True, [165]],
            168: [9, 4, [0,0], "Kress Last Combat", 3, 0x0364, 0x036b, [0, 1, 2, 3, 4, 5, 6, 11, 12, 13], False, [165,169]],
            169: [-1,0, [0,0], "Kress Final Chest", 4, 0,      0,      [], False, [168]],

            # Ankor Wat
            176: [10, 6, [0,0], "Wat Exterior",     1, 0x036c, 0x037a, [], True, [177]],
            177: [11, 6, [0,0], "Wat Outer South",  1, 0x037b, 0x038d, [6, 10], True, [176,178,181,182]],
            178: [11, 6, [0,0], "Wat Outer East",   1, 0x038e, 0x0398, [6, 10, 12], True, [177,179]],
            179: [11, 6, [0,0], "Wat Outer North",  1, 0x0399, 0x039f, [], True, [178,181]],
            180: [11, 6, [0,0], "Wat Outer Pit",    0, 0x03a0, 0x03a5, [6, 10, 12], False, []],
            181: [11, 6, [0,0], "Wat Outer West",   1, 0x03a6, 0x03b0, [], True, [177,179]],
            182: [10, 6, [0,0], "Wat Garden",       1, 0x03b1, 0x03d7, [7], True, [177,183]],
            183: [11, 6, [0,0], "Wat Inner South",  1, 0x03d8, 0x03e3, [], True, [182,184,185,186]],  # Earthquaker Golem
            184: [11, 6, [0,0], "Wat Inner East",   3, 0x03e4, 0x03e9, [2, 6, 10, 12], True, [183]],
            185: [11, 6, [0,0], "Wat Inner West",   1, 0x03ea, 0x03f1, [], False, [183]],
            186: [10, 6, [0,0], "Wat Road to Main", 4, 0x03f2, 0x03f6, [], True, [183,187]],
            187: [11, 6, [0,0], "Wat Main 1F",      2, 0x03f7, 0x03fc, [], False, [186,188]],
            188: [11, 6, [0,0], "Wat Main 2F",      2, 0x03fd, 0x0403, [], True, [187,189]],
            189: [11, 6, [0,0], "Wat Main 3F",      3, 0x0404, 0x040e, [], True, [188,190]],
            190: [11, 6, [0,0], "Wat Main 4F",      4, 0x040f, 0x0415, [], False, [189,191]],
            191: [-1, 0, [0,0], "Wat Spirit",       4, 0,      0,      [], False, [190]],

            # Pyramid
            204: [12, 5, [0,0], "Pyramid Foyer",   1, 0x0416, 0x0417, [], False, [206,208,210,212,214,216,221]],
            206: [12, 5, [0,0], "Pyramid Room 1A", 2, 0x0418, 0x0423, [], True, [204,207]],
            207: [12, 5, [0,0], "Pyramid Room 1B", 3, 0x0424, 0x0431, [], True, [206]],
            208: [12, 5, [0,0], "Pyramid Room 2A", 2, 0x0432, 0x0439, [], False, [204,209]],
            209: [12, 5, [0,0], "Pyramid Room 2B", 3, 0x043a, 0x044c, [], True, [208]],
            210: [12, 5, [0,0], "Pyramid Room 6A", 2, 0x044d, 0x0462, [], True, [204,211]],
            211: [12, 5, [0,0], "Pyramid Room 6B", 3, 0x0463, 0x0473, [], True, [210]],
            212: [12, 5, [0,0], "Pyramid Room 5A", 2, 0x0474, 0x0483, [], True, [204,213]],
            213: [12, 5, [0,0], "Pyramid Room 5B", 3, 0x0484, 0x0497, [], True, [212]],
            214: [12, 5, [0,0], "Pyramid Room 3A", 2, 0x0498, 0x04a8, [], True, [204,215]],
            215: [12, 5, [0,0], "Pyramid Room 3B", 3, 0x04a9, 0x04b8, [1, 7, 10], False, [214]],
            216: [12, 5, [0,0], "Pyramid Room 4A", 2, 0x04b9, 0x04db, [7], True, [204,217]],
            217: [12, 5, [0,0], "Pyramid Room 4B", 2, 0x04dc, 0x04f2, [], True, [216,219]],
            219: [12, 5, [0,0], "Pyramid Room 4C", 3, 0x04f3, 0x04f6, [1, 2, 3, 6, 7, 10, 13], False, [217]],  #Spike elevators
            221: [-1, 0, [0,0], "Pyramid MQ",      3, 0,      0,      [], False, [204]],

            # Jeweler's Mansion
            233: [13, 0, [0,0], "Mansion",   3, 0x04f9, 0x051e, [7, 10], True, [234]],
            234: [-1, 0, [0,0], "Solid Arm", 4, 0,      0,      [], False, [233]],
            
            # Babel bosses
            242: [-1, 0, [0,0], "Babel Castoth", 3, 0, 0, [], False, []],
            243: [-1, 0, [0,0], "Babel Viper",   3, 0, 0, [], False, []],
            245: [-1, 0, [0,0], "Babel Fanger",  3, 0, 0, [], False, []],
            246: [-1, 0, [0,0], "Babel MQ",      3, 0, 0, [], False, []]
        }

        # Database of enemy types
        # FORMAT: { ID: [0: Enemyset ID, 
        #                1: ASM define for addr, 
        #                2: Default stat block,
        #                3: Type(1=stationary,2=walking,3=flying),
        #                4: OnWalkableTile,
        #                5: CanBeRandom,
        #                6: Name
        #               ] }
        self.enemies = {
            # Underground Tunnel
            0: [0, "EnemizerBatAddr", 0x05, 2, True, True, "Bat"],  # a8755
            1: [0, "EnemizerRibberAddr", 0x01, 2, True, True, "Ribber"],
            2: [0, "EnemizerCanalWormAddr", 0x02, 1, False, True, "Canal Worm"],
            3: [0, "EnemizerKingBatAddr", 0x03, 2, True, False, "King Bat"],
            4: [0, "EnemizerSkullChaserAddr", 0x10, 2, True, True, "Skull Chaser"],
            5: [0, "EnemizerBatMinion1Addr", 0x04, 2, True, False, "Bat Minion 1"],
            6: [0, "EnemizerBatMinion2Addr", 0x04, 2, True, False, "Bat Minion 2"],
            7: [0, "EnemizerBatMinion3Addr", 0x04, 2, True, False, "Bat Minion 3"],
            8: [0, "EnemizerBatMinion4Addr", 0x04, 2, True, False, "Bat Minion 4"],

            # Inca Ruins
            10: [1, "EnemizerSluggerAddr", 0x0b, 2, True, True, "Slugger"],
            11: [1, "EnemizerScuttlebugAddr", 0x0b, 2, True, False, "Scuttlebug"],
            12: [1, "EnemizerMudpitAddr", 0x0a, 2, True, True, "Mudpit"],
            13: [1, "EnemizerFourWayAddr", 0x0c, 1, True, True, "Four Way"],
            14: [2, "EnemizerSplopAddr", 0x0f, 2, True, True, "Splop"],
            15: [2, "EnemizerWhirligigAddr", 0x0e, 3, False, True, "Whirligig"],
            16: [2, "EnemizerStoneLordRAddr", 0x0d, 2, True, False, "Stone Lord R"],  # shoots fire
            17: [2, "EnemizerStoneLordDAddr", 0x0d, 2, True, True, "Stone Lord D"],  # shoots fire
            18: [2, "EnemizerStoneLordUAddr", 0x0d, 2, True, False, "Stone Lord U"],  # shoots fire
            19: [2, "EnemizerStoneLordLAddr", 0x0d, 2, True, False, "Stone Lord L"],  # shoots fire
            20: [2, "EnemizerStoneGuardRAddr", 0x0d, 2, True, False, "Stone Guard R"],  # throws spears
            21: [2, "EnemizerStoneGuardLAddr", 0x0d, 2, True, False, "Stone Guard L"],  # throws spears
            22: [2, "EnemizerStoneGuardDAddr", 0x0d, 2, True, True, "Stone Guard D"],  # throws spears
            23: [2, "EnemizerWhirligigStationaryAddr", 0x0e, 1, False, False, "Whirligig (stationary)"],

            # Diamond Mine
            30: [3, "EnemizerFlayzer1Addr", 0x18, 2, True, True, "Flayzer 1"],
            31: [3, "EnemizerFlayzer2Addr", 0x18, 2, True, False, "Flayzer 2"],
            32: [3, "EnemizerFlayzer3Addr", 0x18, 2, True, False, "Flayzer 3"],
            33: [3, "EnemizerEyeStalker1Addr", 0x19, 2, True, True, "Eye Stalker"],
            34: [3, "EnemizerEyeStalkerstoneAddr", 0x19, 2, True, False, "Eye Stalker (stone)"],
            35: [3, "EnemizerGrunditAddr", 0x1a, 1, True, True, "Grundit"],
            #            36: [3,"\xf5\xa4\x8a",0x1a,"Grundit (stationary)"],  # Can't randomize this guy

            # Sky Garden
            40: [4, "EnemizerBlueCyberAddr", 0x1d, 2, True, True, "Blue Cyber"],
            41: [4, "EnemizerDynapede1Addr", 0x1b, 2, True, True, "Dynapede 1"],
            42: [4, "EnemizerDynapede2Addr", 0x1b, 2, True, False, "Dynapede 2"],
            43: [5, "EnemizerRedCyberAddr", 0x1e, 2, True, True, "Red Cyber"],
            44: [5, "EnemizerNitropedeAddr", 0x1c, 2, True, True, "Nitropede"],

            # Mu
            50: [6, "EnemizerSlipperAddr", 0x2b, 2, True, True, "Slipper"],
            51: [6, "EnemizerSkuddleAddr", 0x2a, 2, True, True, "Skuddle"],
            52: [6, "EnemizerCyclopsAddr", 0x28, 2, True, True, "Cyclops"],
            53: [6, "EnemizerFlasherAddr", 0x29, 3, True, True, "Flasher"],
            54: [6, "EnemizerCyclopsAsleepAddr", 0x28, 2, True, False, "Cyclops (asleep)"],
            55: [6, "EnemizerSlipperFallingAddr", 0x2b, 2, True, True, "Slipper (falling)"],

            # Angel Dungeon
            60: [7, "EnemizerDiveBatAddr", 0x2d, 3, False, True, "Dive Bat"],
            61: [7, "EnemizerSteelbonesAddr", 0x2c, 2, True, True, "Steelbones"],
            62: [7, "EnemizerDracoAddr", 0x2e, 1, True, True, "Draco"],
            63: [7, "EnemizerRamskullAddr", 0x2e, 1, True, True, "Ramskull"],

            # Great Wall
            70: [8, "EnemizerArcher1Addr", 0x33, 2, True, True, "Archer 1"],
            71: [8, "EnemizerArcherStatueAddr", 0x33, 2, True, False, "Archer Statue"],
            72: [8, "EnemizerEyesoreAddr", 0x34, 2, True, True, "Eyesore"],
            73: [8, "EnemizerFireBug1Addr", 0x35, 3, False, True, "Fire Bug 1"],
            74: [8, "EnemizerFireBug2Addr", 0x33, 3, False, False, "Fire Bug 2"],
            75: [8, "EnemizerAspAddr", 0x32, 2, True, True, "Asp"],
            76: [8, "EnemizerArcher2Addr", 0x33, 2, True, False, "Archer 2"],
            77: [8, "EnemizerArcher3Addr", 0x33, 2, True, False, "Archer 3"],
            78: [8, "EnemizerArcherStatueSwitch1Addr", 0x46, 2, True, False, "Archer Statue (switch) 1"],
            79: [8, "EnemizerArcherStatueSwitch2Addr", 0x33, 2, True, False, "Archer Statue (switch) 2"],

            # Mt. Kress
            80: [9, "EnemizerSkulkerNSAddr", 0x3e, 3, True, True, "Skulker (N/S)"],
            81: [9, "EnemizerSkulkerEW1Addr", 0x3e, 3, True, True, "Skulker (E/W) 1"],
            82: [9, "EnemizerSkulkerEW2Addr", 0x3e, 3, True, False, "Skulker (E/W) 2"],
            83: [9, "EnemizerSkulkerEW3Addr", 0x3e, 3, True, False, "Skulker (E/W) 3"],
            84: [9, "EnemizerYorrickEW1Addr", 0x3d, 3, False, True, "Yorrick (E/W) 1"],
            85: [9, "EnemizerYorrickEW2Addr", 0x3d, 3, False, False, "Yorrick (E/W) 2"],
            86: [9, "EnemizerYorrickNS1Addr", 0x3d, 3, False, True, "Yorrick (N/S) 1"],
            87: [9, "EnemizerYorrickNS2Addr", 0x3d, 3, False, False, "Yorrick (N/S) 2"],
            88: [9, "EnemizerFireSpriteAddr", 0x3f, 3, False, True, "Fire Sprite"],
            89: [9, "EnemizerAcidSplasherAddr", 0x3c, 2, True, True, "Acid Splasher"],
            90: [9, "EnemizerAcidSplasherStationaryEAddr", 0x3c, 2, True, False, "Acid Splasher (stationary E)"],
            91: [9, "EnemizerAcidSplasherStationaryWAddr", 0x3c, 2, True, False, "Acid Splasher (stationary W)"],
            92: [9, "EnemizerAcidSplasherStationarySAddr", 0x3c, 2, True, False, "Acid Splasher (stationary S)"],
            93: [9, "EnemizerAcidSplasherStationaryNAddr", 0x3c, 2, True, False, "Acid Splasher (stationary N)"],

            # Ankor Wat
            100: [10, "EnemizerShrubberAddr", 0x49, 2, True, True, "Shrubber"],
            101: [10, "EnemizerShrubber2Addr", 0x49, 2, True, False, "Shrubber 2"],
            102: [10, "EnemizerZombieAddr", 0x46, 2, True, True, "Zombie"],
            103: [10, "EnemizerZipFlyAddr", 0x4a, 3, True, True, "Zip Fly"],  # False for now...
            104: [11, "EnemizerGoldcapAddr", 0x42, 3, True, True, "Goldcap"],    # i.e. flying skull
            105: [11, "EnemizerGorgonAddr", 0x45, 2, True, True, "Gorgon"],
            106: [11, "EnemizerGorgonDropperAddr", 0x45, 2, True, False, "Gorgon Dropper"],
            107: [11, "EnemizerFrenzie1Addr", 0x43, 2, True, False, "Frenzie 1"],   # i.e. wall skull stationary
            108: [11, "EnemizerFrenzie2Addr", 0x43, 2, True, True, "Frenzie 2"],    # i.e. wall skull moving
            109: [11, "EnemizerWatScarab1Addr", 0x44, 1, False, True, "Wall Walker 1"],
            110: [11, "EnemizerWatScarab2Addr", 0x3a, 1, False, False, "Wall Walker 2"],
            111: [11, "EnemizerWatScarab3Addr", 0x44, 1, False, False, "Wall Walker 3"],
            112: [11, "EnemizerWatScarab4Addr", 0x3a, 1, False, False, "Wall Walker 4"],
            113: [11, "EnemizerGorgonBlockAddr", 0x45, 2, True, False, "Gorgon (block)"],

            # Pyramid
            120: [12, "EnemizerMysticBallStationaryAddr", 0x4f, 1, True, True, "Mystic Ball (stationary)"],
            121: [12, "EnemizerMysticBall1Addr", 0x4f, 2, True, True, "Mystic Ball 1"],
            122: [12, "EnemizerMysticBall2Addr", 0x4f, 2, True, True, "Mystic Ball 2"],
            123: [12, "EnemizerTutsAddr", 0x4e, 2, True, True, "Tuts"],   # i.e. spearman
            124: [12, "EnemizerBlasterAddr", 0x51, 1, True, True, "Blaster"],   # i.e. bird head
            125: [12, "EnemizerHauntStationaryAddr", 0x4c, 2, True, False, "Haunt (stationary)"],   # i.e. wall mummy
            126: [12, "EnemizerHauntAddr", 0x4c, 2, True, True, "Haunt"],   # i.e. loose mummy

            # Babel Tower
            #            130: [14,"\xd7\x99\x8a",0x5a,"Castoth (boss)"],
            #            131: [14,"\xd5\xd0\x8a",0x5b,"Viper (boss)"],
            #            132: [14,"\x50\xf1\x8a",0x5c,"Vampire (boss)"],
            #            133: [14,"\x9c\xf1\x8a",0x5c,"Vampire (boss)"],
            #            134: [14,"\x00\x80\x8",0x5d,"Sand Fanger (boss)"],
            #            135: [14,"\x1a\xa6\x8",0x5e,"Mummy Queen (boss)"],

            # Jeweler's Mansion
            140: [13, "EnemizerFlayzerAddr", 0x61, 2, True, True, "Mansion Flayzer"],
            141: [13, "EnemizerGrunditAddr", 0x63, 1, True, True, "Mansion Grundit"],
            142: [13, "EnemizerEyeStalker2Addr", 0x62, 2, True, False, "Mansion Eye Stalker 2"],
            143: [13, "EnemizerEyeStalker1Addr", 0x62, 2, True, True, "Mansion Eye Stalker 1"]
            # Bosses
            #            24: [15,"\x03\x9b\x8a",0x14,"Castoth (boss)"],
            #            45: [15,"\x6f\xd1\x8a",0x27,"Viper (boss)"],
            #            55: [15,"\xf7\xf1\x8a",0x2f,"Vampire (boss)"],
            #            56: [15,"\xc8\xf3\x8a",0x30,"Vampire (boss)"],
            #            79: [15,"\x5c\x81\x8",0x36,"Sand Fanger (boss)"],
            #            128: [15,"\xb6\xa6\x8",0x50,"Mummy Queen (boss)"],
            #            143: [15,"\x09\xf7\x88",0x5f,"Solid Arm (boss)"],
            #            140: [15,"\xaa\xee\x8c",0x54,"Dark Gaia"]
        }
        
        # Default (vanilla) enemy type for each non-boss monster ID
        self.default_enemies = {
            0x0001: 0,
            0x0002: 0,
            0x0003: 0,
            0x0004: 2,
            0x0005: 2,
            0x0006: 2,
            0x0007: 0,
            0x0008: 0,
            0x0009: 0,
            0x000A: 0,
            0x000B: 0,
            0x000C: 0,
            0x000D: 0,
            0x000E: 0,
            0x000F: 0,
            0x0010: 0,
            0x0011: 1,
            0x0012: 1,
            0x0013: 2,
            0x0014: 2,
            0x0015: 2,
            0x0016: 2,
            0x0017: 0,
            0x0018: 0,
            0x0019: 0,
            0x001A: 0,
            0x001B: 0,
            0x001C: 0,
            0x001D: 0,
            0x001E: 1,
            0x001F: 1,
            0x0020: 1,
            0x0021: 1,
            0x0022: 2,
            0x0023: 2,
            0x0024: 0,
            0x0025: 0,
            0x0026: 0,
            0x0027: 0,
            0x0028: 1,
            0x0029: 1,
            0x002A: 3,
            0x002B: 7,
            0x002C: 6,
            0x002D: 8,
            0x002E: 5,
            0x002F: 2,
            0x0030: 2,
            0x0031: 2,
            0x0032: 2,
            0x0033: 2,
            0x0034: 2,
            0x0035: 2,
            0x0036: 0,
            0x0037: 0,
            0x0038: 0,
            0x0039: 0,
            0x003A: 0,
            0x003B: 0,
            0x003C: 0,
            0x003D: 1,
            0x003E: 1,
            0x003F: 1,
            0x0040: 1,
            0x0041: 1,
            0x0042: 1,
            0x0043: 4,
            0x0044: 4,
            0x0045: 10,
            0x0046: 10,
            0x0047: 10,
            0x0048: 10,
            0x0049: 10,
            0x004A: 10,
            0x004B: 12,
            0x004C: 12,
            0x004D: 12,
            0x004E: 12,
            0x004F: 12,
            0x0050: 13,
            0x0051: 13,
            0x0052: 13,
            0x0053: 13,
            0x0054: 13,
            0x0055: 13,
            0x0056: 11,
            0x0057: 11,
            0x0058: 11,
            0x0059: 11,
            0x005A: 16,
            0x005B: 16,
            0x005C: 19,
            0x005D: 19,
            0x005E: 12,
            0x005F: 13,
            0x0060: 13,
            0x0061: 13,
            0x0062: 13,
            0x0063: 10,
            0x0064: 10,
            0x0065: 10,
            0x0066: 22,
            0x0067: 22,
            0x0068: 22,
            0x0069: 16,
            0x006A: 20,
            0x006B: 21,
            0x006C: 17,
            0x006D: 17,
            0x006E: 22,
            0x006F: 22,
            0x0070: 14,
            0x0071: 14,
            0x0072: 14,
            0x0073: 14,
            0x0074: 14,
            0x0075: 14,
            0x0076: 14,
            0x0077: 15,
            0x0078: 15,
            0x0079: 15,
            0x007A: 23,
            0x007B: 22,
            0x007C: 22,
            0x007D: 17,
            0x007E: 18,
            0x007F: 19,
            0x0080: 16,
            0x0081: 14,
            0x0082: 14,
            0x0083: 14,
            0x0084: 14,
            0x0085: 14,
            0x0086: 14,
            0x0087: 14,
            0x0088: 14,
            0x0089: 14,
            0x008A: 14,
            0x008B: 15,
            0x008C: 15,
            0x008D: 15,
            0x008E: 15,
            0x008F: 14,
            0x0090: 14,
            0x0091: 14,
            0x0092: 14,
            0x0093: 14,
            0x0094: 14,
            0x0095: 14,
            0x0096: 14,
            0x0097: 14,
            0x0098: 14,
            0x0099: 14,
            0x009A: 14,
            0x009B: 15,
            0x009C: 15,
            0x009D: 23,
            0x009E: 12,
            0x009F: 12,
            0x00A0: 12,
            0x00A1: 12,
            0x00A2: 12,
            0x00A3: 12,
            0x00A4: 12,
            0x00A5: 12,
            0x00A6: 13,
            0x00A7: 13,
            0x00A8: 13,
            0x00A9: 13,
            0x00AA: 12,
            0x00AB: 12,
            0x00AC: 12,
            0x00AD: 12,
            0x00AE: 10,
            0x00AF: 10,
            0x00B0: 11,
            0x00B1: 11,
            0x00B2: 11,
            0x00B3: 11,
            0x00B4: 12,
            0x00B5: 12,
            0x00B6: 12,
            0x00B7: 12,
            0x00B8: 13,
            0x00B9: 13,
            0x00BA: 13,
            0x00BB: 13,
            0x00BC: 13,
            0x00BD: 13,
            0x00BE: 13,
            0x00BF: 13,
            0x00C0: 10,
            0x00C1: 10,
            0x00C2: 10,
            0x00C3: 10,
            0x00C4: 10,
            0x00C5: 11,
            0x00C6: 11,
            0x00C7: 11,
            0x00C8: 13,
            0x00C9: 13,
            0x00CA: 13,
            0x00CB: 13,
            0x00CC: 13,
            0x00CE: 30,
            0x00CF: 30,
            0x00D0: 33,
            0x00D1: 33,
            0x00D2: 33,
            0x00D3: 34,
            0x00D4: 34,
            0x00D5: 34,
            0x00D6: 34,
            0x00D7: 35,
            0x00D8: 35,
            0x00D9: 35,
            0x00DA: 35,
            0x00DB: 35,
            0x00DC: 30,
            0x00DD: 30,
            0x00DE: 30,
            0x00DF: 30,
            0x00E0: 35,
            0x00E1: 35,
            0x00E2: 35,
            0x00E3: 35,
            0x00E4: 35,
            0x00E5: 35,
            0x00E6: 35,
            0x00E7: 35,
            0x00E8: 35,
            0x00E9: 33,
            0x00EA: 33,
            0x00EB: 33,
            0x00EC: 33,
            0x00ED: 33,
            0x00EE: 33,
            0x00EF: 33,
            0x00F0: 30,
            0x00F1: 30,
            0x00F2: 30,
            0x00F3: 30,
            0x00F4: 30,
            0x00F5: 30,
            0x00F6: 32,
            0x00F7: 32,
            0x00F8: 30,
            0x00F9: 30,
            0x00FA: 30,
            0x00FB: 33,
            0x00FC: 35,
            0x00FD: 35,
            0x00FE: 35,
            0x00FF: 35,
            0x0100: 35,
            0x0101: 35,
            #0x0102: xx,    # Friar worm fence worm; always a special stationary worm actor
            0x0103: 33,
            0x0104: 33,
            0x0105: 33,
            0x0106: 30,
            0x0107: 30,
            0x0108: 30,
            0x0109: 35,
            0x010A: 35,
            0x010B: 35,
            0x010C: 35,
            0x010D: 35,
            0x010E: 35,
            0x010F: 33,
            0x0110: 33,
            0x0111: 33,
            0x0112: 33,
            0x0113: 30,
            0x0114: 30,
            0x0115: 30,
            0x0116: 30,
            0x0117: 31,
            0x0118: 40,
            0x0119: 40,
            0x011A: 40,
            0x011B: 40,
            0x011C: 40,
            0x011D: 40,
            0x011E: 40,
            0x011F: 42,
            0x0120: 42,
            0x0121: 42,
            0x0122: 42,
            0x0123: 42,
            0x0124: 42,
            0x0125: 42,
            0x0126: 42,
            0x0127: 42,
            0x0128: 42,
            0x0129: 42,
            0x012A: 43,
            0x012B: 43,
            0x012C: 43,
            0x012D: 43,
            0x012E: 43,
            0x012F: 43,
            0x0130: 44,
            0x0131: 44,
            0x0132: 44,
            0x0133: 44,
            0x0134: 44,
            0x0135: 44,
            0x0136: 44,
            0x0137: 40,
            0x0138: 40,
            0x0139: 40,
            0x013A: 40,
            0x013B: 40,
            0x013C: 42,
            0x013D: 42,
            0x013E: 42,
            0x013F: 41,
            0x0140: 42,
            0x0141: 42,
            0x0142: 42,
            0x0143: 42,
            0x0144: 43,
            0x0145: 43,
            0x0146: 43,
            0x0147: 43,
            0x0148: 43,
            0x0149: 44,
            0x014A: 44,
            0x014B: 44,
            0x014C: 44,
            0x014D: 44,
            0x014E: 44,
            0x014F: 44,
            0x0150: 40,
            0x0151: 40,
            0x0152: 40,
            0x0153: 40,
            0x0154: 40,
            0x0155: 40,
            0x0156: 40,
            0x0157: 42,
            0x0158: 41,
            0x0159: 42,
            0x015A: 42,
            0x015B: 42,
            0x015C: 42,
            0x015D: 43,
            0x015E: 43,
            0x015F: 43,
            0x0160: 43,
            0x0161: 43,
            0x0162: 44,
            0x0163: 44,
            0x0164: 40,
            0x0165: 40,
            0x0166: 40,
            0x0167: 40,
            0x0168: 40,
            0x0169: 40,
            0x016A: 42,
            0x016B: 42,
            0x016C: 42,
            0x016D: 42,
            0x016E: 42,
            0x016F: 42,
            0x0170: 42,
            0x0171: 42,
            0x0172: 42,
            0x0173: 43,
            0x0174: 43,
            0x0175: 43,
            0x0176: 43,
            0x0177: 44,
            0x0178: 44,
            0x0179: 44,
            0x017A: 44,
            0x017B: 44,
            0x017C: 44,
            0x017D: 44,
            0x017E: 44,
            0x017F: 44,
            0x0180: 44,
            0x0181: 44,
            0x0182: 44,
            0x0184: 51,
            0x0185: 51,
            0x0186: 51,
            0x0187: 51,
            0x0188: 51,
            0x0189: 51,
            0x018A: 55,
            0x018B: 55,
            0x018C: 55,
            0x018D: 55,
            0x018E: 55,
            0x018F: 55,
            0x0190: 55,
            0x0191: 55,
            0x0192: 55,
            0x0193: 52,
            0x0194: 54,
            0x0195: 52,
            0x0196: 52,
            0x0197: 52,
            0x0198: 52,
            0x0199: 51,
            0x019A: 51,
            0x019B: 51,
            0x019C: 51,
            0x019D: 51,
            0x019E: 51,
            0x019F: 51,
            0x01A0: 51,
            0x01A1: 51,
            0x01A2: 51,
            0x01A3: 51,
            0x01A4: 51,
            0x01A5: 53,
            0x01A6: 50,
            0x01A7: 50,
            0x01A8: 50,
            0x01A9: 50,
            0x01AA: 50,
            0x01AB: 54,
            0x01AC: 52,
            0x01AD: 52,
            0x01AE: 52,
            0x01AF: 52,
            0x01B0: 52,
            0x01B1: 54,
            0x01B2: 54,
            0x01B3: 53,
            0x01B4: 53,
            0x01B5: 53,
            0x01B6: 53,
            0x01B7: 51,
            0x01B8: 51,
            0x01B9: 51,
            0x01BA: 51,
            0x01BB: 51,
            0x01BC: 51,
            0x01BD: 51,
            0x01BE: 51,
            0x01BF: 51,
            0x01C0: 50,
            0x01C1: 50,
            0x01C2: 50,
            0x01C3: 50,
            0x01C4: 52,
            0x01C5: 52,
            0x01C6: 54,
            0x01C7: 52,
            0x01C8: 54,
            0x01C9: 53,
            0x01CA: 53,
            0x01CB: 53,
            0x01CC: 53,
            0x01CD: 53,
            0x01CE: 51,
            0x01CF: 51,
            0x01D0: 51,
            0x01D1: 51,
            0x01D2: 51,
            0x01D3: 51,
            0x01D4: 51,
            0x01D5: 51,
            0x01D6: 51,
            0x01D7: 51,
            0x01D8: 51,
            0x01D9: 51,
            0x01DA: 51,
            0x01DB: 51,
            0x01DC: 51,
            0x01DD: 51,
            0x01DE: 51,
            0x01DF: 51,
            0x01E0: 51,
            0x01E1: 51,
            0x01E2: 51,
            0x01E3: 51,
            0x01E4: 53,
            0x01E5: 53,
            0x01E6: 52,
            0x01E7: 51,
            0x01E8: 51,
            0x01E9: 51,
            0x01EA: 51,
            0x01EB: 51,
            0x01EC: 53,
            0x01ED: 53,
            0x01EE: 54,
            0x01EF: 54,
            0x01F0: 54,
            0x01F1: 54,
            0x01F2: 54,
            0x01F3: 54,
            0x01F4: 53,
            0x01F5: 51,
            0x01F6: 51,
            0x01F7: 51,
            0x01F8: 51,
            0x01F9: 51,
            0x01FA: 50,
            0x01FB: 50,
            0x01FC: 50,
            0x01FD: 50,
            0x01FE: 50,
            0x0201: 61,
            0x0202: 61,
            0x0203: 61,
            0x0204: 61,
            0x0205: 61,
            0x0206: 61,
            0x0207: 60,
            0x0208: 60,
            0x0209: 60,
            0x020A: 60,
            0x020B: 60,
            0x020C: 60,
            0x020D: 60,
            0x020E: 60,
            0x020F: 60,
            0x0210: 61,
            0x0211: 61,
            0x0212: 61,
            0x0213: 61,
            0x0214: 61,
            0x0215: 61,
            0x0216: 61,
            0x0217: 61,
            0x0218: 60,
            0x0219: 60,
            0x021A: 60,
            0x021B: 60,
            0x021C: 60,
            0x021D: 60,
            0x021E: 60,
            0x021F: 60,
            0x0220: 62,
            0x0221: 62,
            0x0222: 62,
            0x0223: 60,
            0x0224: 60,
            0x0225: 60,
            0x0226: 60,
            0x0227: 60,
            0x0228: 60,
            0x0229: 61,
            0x022A: 60,
            0x022B: 60,
            0x022C: 60,
            0x022D: 62,
            0x022E: 62,
            0x022F: 63,
            0x0230: 63,
            0x0231: 63,
            0x0232: 61,
            0x0233: 61,
            0x0234: 60,
            0x0235: 60,
            0x0236: 60,
            0x0237: 60,
            0x0238: 60,
            0x0239: 60,
            0x023A: 60,
            0x023B: 60,
            0x023C: 60,
            0x023D: 63,
            0x023E: 63,
            0x023F: 63,
            0x0240: 63,
            0x0241: 63,
            0x0242: 63,
            0x0243: 77,
            0x0244: 77,
            0x0245: 77,
            0x0246: 77,
            0x0247: 77,
            0x0248: 70,
            0x0249: 70,
            0x024A: 70,
            0x024B: 70,
            0x024C: 70,
            0x024D: 76,
            0x024E: 76,
            0x024F: 76,
            0x0250: 76,
            0x0251: 76,
            0x0252: 76,
            0x0253: 76,
            0x0254: 73,
            0x0255: 73,
            0x0256: 73,
            0x0257: 73,
            0x0258: 73,
            0x0259: 73,
            0x025A: 72,
            0x025B: 72,
            0x025C: 72,
            0x025D: 72,
            0x025E: 72,
            0x025F: 72,
            0x0260: 72,
            0x0261: 72,
            0x0262: 72,
            0x0263: 77,
            0x0264: 77,
            0x0265: 70,
            0x0266: 70,
            0x0267: 70,
            0x0268: 76,
            0x0269: 76,
            0x026A: 76,
            0x026B: 76,
            0x026C: 76,
            0x026D: 71,
            0x026E: 73,
            0x026F: 73,
            0x0270: 72,
            0x0271: 72,
            0x0272: 72,
            0x0273: 75,
            0x0274: 75,
            0x0275: 75,
            0x0276: 75,
            0x0277: 75,
            0x0278: 75,
            0x0279: 75,
            0x027A: 75,
            0x027B: 75,
            0x027C: 75,
            0x027D: 75,
            0x027E: 75,
            0x027F: 75,
            0x0280: 75,
            0x0281: 75,
            0x0282: 72,
            0x0283: 72,
            0x0284: 72,
            0x0285: 72,
            0x0286: 72,
            0x0287: 72,
            0x0288: 72,
            0x0289: 72,
            0x028A: 73,
            0x028B: 73,
            0x028C: 76,
            0x028D: 76,
            0x028E: 76,
            0x028F: 76,
            0x0290: 76,
            0x0291: 76,
            0x0292: 71,
            0x0293: 71,
            0x0294: 75,
            0x0295: 75,
            0x0296: 75,
            0x0297: 75,
            0x0298: 75,
            0x0299: 75,
            0x029A: 75,
            0x029B: 70,
            0x029C: 76,
            0x029D: 76,
            0x029E: 76,
            0x029F: 76,
            0x02A0: 78,
            0x02A1: 78,
            0x02A2: 78,
            0x02A3: 78,
            0x02A4: 78,
            0x02A5: 78,
            0x02A6: 73,
            0x02A7: 77,
            0x02A8: 77,
            0x02A9: 70,
            0x02AA: 70,
            0x02AB: 76,
            0x02AC: 76,
            0x02AD: 79,
            0x02AE: 79,
            0x02AF: 79,
            0x02B0: 79,
            0x02B1: 79,
            0x02B2: 79,
            0x02B3: 75,
            0x02B4: 72,
            0x02B5: 72,
            0x02B7: 81,
            0x02B8: 81,
            0x02B9: 81,
            0x02BA: 81,
            0x02BB: 81,
            0x02BC: 80,
            0x02BD: 80,
            0x02BE: 89,
            0x02BF: 89,
            0x02C0: 89,
            0x02C1: 89,
            0x02C2: 88,
            0x02C3: 88,
            0x02C4: 88,
            0x02C5: 89,
            0x02C6: 92,
            0x02C7: 92,
            0x02C8: 91,
            0x02C9: 90,
            0x02CA: 81,
            0x02CB: 81,
            0x02CC: 81,
            0x02CD: 81,
            0x02CE: 80,
            0x02CF: 80,
            0x02D0: 86,
            0x02D1: 86,
            0x02D2: 86,
            0x02D3: 86,
            0x02D4: 85,
            0x02D5: 85,
            0x02D6: 85,
            0x02D7: 85,
            0x02D8: 85,
            0x02D9: 85,
            0x02DA: 89,
            0x02DB: 89,
            0x02DC: 89,
            0x02DD: 90,
            0x02DE: 90,
            0x02DF: 93,
            0x02E0: 80,
            0x02E1: 81,
            0x02E2: 81,
            0x02E3: 82,
            0x02E4: 82,
            0x02E5: 85,
            0x02E6: 84,
            0x02E7: 84,
            0x02E8: 82,
            0x02E9: 82,
            0x02EA: 82,
            0x02EB: 82,
            0x02EC: 82,
            0x02ED: 89,
            0x02EE: 89,
            0x02EF: 89,
            0x02F0: 89,
            0x02F1: 89,
            0x02F2: 90,
            0x02F3: 90,
            0x02F4: 90,
            0x02F5: 91,
            0x02F6: 91,
            0x02F7: 85,
            0x02F8: 84,
            0x02F9: 86,
            0x02FA: 86,
            0x02FB: 86,
            0x02FC: 82,
            0x02FD: 82,
            0x02FE: 81,
            0x02FF: 81,
            0x0300: 81,
            0x0301: 81,
            0x0302: 81,
            0x0303: 81,
            0x0304: 80,
            0x0305: 80,
            0x0306: 84,
            0x0307: 84,
            0x0308: 84,
            0x0309: 84,
            0x030A: 84,
            0x030B: 85,
            0x030C: 85,
            0x030D: 85,
            0x030E: 86,
            0x030F: 91,
            0x0310: 89,
            0x0311: 89,
            0x0312: 89,
            0x0313: 89,
            0x0314: 89,
            0x0315: 89,
            0x0316: 88,
            0x0317: 88,
            0x0318: 88,
            0x0319: 86,
            0x031A: 86,
            0x031B: 87,
            0x031C: 85,
            0x031D: 84,
            0x031E: 84,
            0x031F: 80,
            0x0320: 82,
            0x0321: 82,
            0x0322: 81,
            0x0323: 81,
            0x0324: 81,
            0x0325: 81,
            0x0326: 89,
            0x0327: 89,
            0x0328: 89,
            0x0329: 92,
            0x032A: 91,
            0x032B: 91,
            0x032C: 90,
            0x032D: 90,
            0x032E: 88,
            0x032F: 88,
            0x0330: 88,
            0x0331: 88,
            0x0332: 88,
            0x0333: 88,
            0x0334: 84,
            0x0335: 84,
            0x0336: 84,
            0x0337: 84,
            0x0338: 86,
            0x0339: 81,
            0x033A: 89,
            0x033B: 89,
            0x033C: 89,
            0x033D: 88,
            0x033E: 88,
            0x033F: 88,
            0x0340: 89,
            0x0341: 89,
            0x0342: 89,
            0x0343: 89,
            0x0344: 89,
            0x0345: 89,
            0x0346: 89,
            0x0347: 89,
            0x0348: 89,
            0x0349: 86,
            0x034A: 86,
            0x034B: 86,
            0x034C: 86,
            0x034D: 86,
            0x034E: 87,
            0x034F: 87,
            0x0350: 87,
            0x0351: 87,
            0x0352: 87,
            0x0353: 87,
            0x0354: 84,
            0x0355: 84,
            0x0356: 85,
            0x0357: 85,
            0x0358: 83,
            0x0359: 83,
            0x035A: 82,
            0x035B: 82,
            0x035C: 82,
            0x035D: 82,
            0x035E: 82,
            0x035F: 81,
            0x0360: 81,
            0x0361: 81,
            0x0362: 81,
            0x0363: 91,
            0x0364: 88,
            0x0365: 88,
            0x0366: 88,
            0x0367: 88,
            0x0368: 86,
            0x0369: 86,
            0x036A: 86,
            0x036B: 86,
            0x036C: 103,
            0x036D: 103,
            0x036E: 103,
            0x036F: 103,
            0x0370: 103,
            0x0371: 100,
            0x0372: 100,
            0x0373: 100,
            0x0374: 102,
            0x0375: 102,
            0x0376: 102,
            0x0377: 102,
            0x0378: 102,
            0x0379: 102,
            0x037A: 102,
            0x037B: 104,
            0x037C: 104,
            0x037D: 104,
            0x037E: 108,
            0x037F: 108,
            0x0380: 108,
            0x0381: 107,
            0x0382: 107,
            0x0383: 107,
            0x0384: 107,
            0x0385: 107,
            0x0386: 107,
            0x0387: 107,
            0x0388: 111,
            0x0389: 109,
            0x038A: 105,
            0x038B: 105,
            0x038C: 105,
            0x038D: 105,
            0x038E: 104,
            0x038F: 104,
            0x0390: 108,
            0x0391: 107,
            0x0392: 107,
            0x0393: 109,
            0x0394: 109,
            0x0395: 109,
            0x0396: 105,
            0x0397: 105,
            0x0398: 105,
            0x0399: 104,
            0x039A: 108,
            0x039B: 108,
            0x039C: 109,
            0x039D: 109,
            0x039E: 109,
            0x039F: 109,
            0x03A0: 111,
            0x03A1: 104,
            0x03A2: 104,
            0x03A3: 104,
            0x03A4: 108,
            0x03A5: 108,
            0x03A6: 109,
            0x03A7: 109,
            0x03A8: 108,
            0x03A9: 108,
            0x03AA: 107,
            0x03AB: 106,
            0x03AC: 106,
            0x03AD: 105,
            0x03AE: 105,
            0x03AF: 106,
            0x03B0: 106,
            0x03B1: 103,
            0x03B2: 103,
            0x03B3: 103,
            0x03B4: 103,
            0x03B5: 103,
            0x03B6: 103,
            0x03B7: 103,
            0x03B8: 103,
            0x03B9: 100,
            0x03BA: 100,
            0x03BB: 100,
            0x03BC: 100,
            0x03BD: 100,
            0x03BE: 100,
            0x03BF: 100,
            0x03C0: 101,
            0x03C1: 101,
            0x03C2: 101,
            0x03C3: 101,
            0x03C4: 101,
            0x03C5: 101,
            0x03C6: 101,
            0x03C7: 101,
            0x03C8: 101,
            0x03C9: 101,
            0x03CA: 101,
            0x03CB: 101,
            0x03CC: 101,
            0x03CD: 101,
            0x03CE: 101,
            0x03CF: 101,
            0x03D0: 102,
            0x03D1: 102,
            0x03D2: 102,
            0x03D3: 102,
            0x03D4: 102,
            0x03D5: 102,
            0x03D6: 102,
            0x03D7: 102,
            0x03D8: 113,
            0x03D9: 106,
            0x03DA: 105,
            0x03DB: 111,
            0x03DC: 109,
            0x03DD: 108,
            0x03DE: 108,
            0x03DF: 108,
            0x03E0: 108,
            0x03E1: 108,
            0x03E2: 107,
            0x03E3: 107,
            0x03E4: 106,
            0x03E5: 106,
            0x03E6: 111,
            0x03E7: 111,
            0x03E8: 108,
            0x03E9: 108,
            0x03EA: 104,
            0x03EB: 104,
            0x03EC: 108,
            0x03ED: 108,
            0x03EE: 105,
            0x03EF: 105,
            0x03F0: 109,
            0x03F1: 109,
            0x03F2: 101,
            0x03F3: 102,
            0x03F4: 102,
            0x03F5: 102,
            0x03F6: 102,
            0x03F7: 104,
            0x03F8: 104,
            0x03F9: 104,
            0x03FA: 104,
            0x03FB: 108,
            0x03FC: 108,
            0x03FD: 104,
            0x03FE: 104,
            0x03FF: 108,
            0x0400: 108,
            0x0401: 108,
            0x0402: 108,
            0x0403: 108,
            0x0404: 104,
            0x0405: 104,
            0x0406: 104,
            0x0407: 107,
            0x0408: 107,
            0x0409: 107,
            0x040A: 107,
            0x040B: 107,
            0x040C: 106,
            0x040D: 105,
            0x040E: 105,
            0x040F: 107,
            0x0410: 107,
            0x0411: 107,
            0x0412: 107,
            0x0413: 107,
            0x0414: 104,
            0x0415: 105,
            0x0416: 120,
            0x0417: 120,
            0x0418: 123,
            0x0419: 122,
            0x041A: 122,
            0x041B: 122,
            0x041C: 122,
            0x041D: 122,
            0x041E: 121,
            0x041F: 121,
            0x0420: 121,
            0x0421: 121,
            0x0422: 121,
            0x0423: 121,
            0x0424: 121,
            0x0425: 121,
            0x0426: 121,
            0x0427: 121,
            0x0428: 122,
            0x0429: 122,
            0x042A: 120,
            0x042B: 120,
            0x042C: 120,
            0x042D: 120,
            0x042E: 120,
            0x042F: 120,
            0x0430: 123,
            0x0431: 123,
            0x0432: 120,
            0x0433: 120,
            0x0434: 121,
            0x0435: 121,
            0x0436: 121,
            0x0437: 121,
            0x0438: 121,
            0x0439: 123,
            0x043A: 120,
            0x043B: 120,
            0x043C: 120,
            0x043D: 120,
            0x043E: 120,
            0x043F: 120,
            0x0440: 120,
            0x0441: 120,
            0x0442: 120,
            0x0443: 120,
            0x0444: 122,
            0x0445: 122,
            0x0446: 122,
            0x0447: 121,
            0x0448: 121,
            0x0449: 121,
            0x044A: 123,
            0x044B: 123,
            0x044C: 123,
            0x044D: 125,
            0x044E: 125,
            0x044F: 125,
            0x0450: 125,
            0x0451: 125,
            0x0452: 125,
            0x0453: 125,
            0x0454: 125,
            0x0455: 125,
            0x0456: 125,
            0x0457: 125,
            0x0458: 122,
            0x0459: 122,
            0x045A: 121,
            0x045B: 121,
            0x045C: 121,
            0x045D: 121,
            0x045E: 121,
            0x045F: 124,
            0x0460: 124,
            0x0461: 124,
            0x0462: 123,
            0x0463: 125,
            0x0464: 125,
            0x0465: 125,
            0x0466: 125,
            0x0467: 125,
            0x0468: 125,
            0x0469: 125,
            0x046A: 125,
            0x046B: 125,
            0x046C: 122,
            0x046D: 122,
            0x046E: 122,
            0x046F: 122,
            0x0470: 121,
            0x0471: 124,
            0x0472: 123,
            0x0473: 123,
            0x0474: 122,
            0x0475: 122,
            0x0476: 122,
            0x0477: 122,
            0x0478: 121,
            0x0479: 121,
            0x047A: 121,
            0x047B: 121,
            0x047C: 121,
            0x047D: 121,
            0x047E: 123,
            0x047F: 123,
            0x0480: 123,
            0x0481: 124,
            0x0482: 124,
            0x0483: 124,
            0x0484: 121,
            0x0485: 122,
            0x0486: 126,
            0x0487: 126,
            0x0488: 125,
            0x0489: 125,
            0x048A: 125,
            0x048B: 125,
            0x048C: 125,
            0x048D: 125,
            0x048E: 125,
            0x048F: 125,
            0x0490: 125,
            0x0491: 125,
            0x0492: 123,
            0x0493: 123,
            0x0494: 123,
            0x0495: 123,
            0x0496: 124,
            0x0497: 124,
            0x0498: 120,
            0x0499: 120,
            0x049A: 120,
            0x049B: 120,
            0x049C: 122,
            0x049D: 121,
            0x049E: 121,
            0x049F: 121,
            0x04A0: 121,
            0x04A1: 123,
            0x04A2: 123,
            0x04A3: 123,
            0x04A4: 124,
            0x04A5: 124,
            0x04A6: 124,
            0x04A7: 124,
            0x04A8: 124,
            0x04A9: 121,
            0x04AA: 121,
            0x04AB: 120,
            0x04AC: 120,
            0x04AD: 120,
            0x04AE: 120,
            0x04AF: 120,
            0x04B0: 120,
            0x04B1: 120,
            0x04B2: 120,
            0x04B3: 120,
            0x04B4: 120,
            0x04B5: 120,
            0x04B6: 124,
            0x04B7: 124,
            0x04B8: 124,
            0x04B9: 125,
            0x04BA: 125,
            0x04BB: 125,
            0x04BC: 125,
            0x04BD: 125,
            0x04BE: 125,
            0x04BF: 125,
            0x04C0: 125,
            0x04C1: 125,
            0x04C2: 125,
            0x04C3: 125,
            0x04C4: 125,
            0x04C5: 122,
            0x04C6: 122,
            0x04C7: 122,
            0x04C8: 122,
            0x04C9: 121,
            0x04CA: 121,
            0x04CB: 121,
            0x04CC: 121,
            0x04CD: 121,
            0x04CE: 121,
            0x04CF: 121,
            0x04D0: 121,
            0x04D1: 126,
            0x04D2: 126,
            0x04D3: 126,
            0x04D4: 126,
            0x04D5: 123,
            0x04D6: 123,
            0x04D7: 123,
            0x04D8: 124,
            0x04D9: 124,
            0x04DA: 124,
            0x04DB: 124,
            0x04DC: 120,
            0x04DD: 120,
            0x04DE: 120,
            0x04DF: 120,
            0x04E0: 120,
            0x04E1: 122,
            0x04E2: 122,
            0x04E3: 121,
            0x04E4: 121,
            0x04E5: 121,
            0x04E6: 121,
            0x04E7: 121,
            0x04E8: 124,
            0x04E9: 124,
            0x04EA: 124,
            0x04EB: 124,
            0x04EC: 123,
            0x04ED: 126,
            0x04EE: 126,
            0x04EF: 126,
            0x04F0: 126,
            0x04F1: 126,
            0x04F2: 126,
            0x04F3: 124,
            0x04F4: 124,
            0x04F5: 122,
            0x04F6: 122,
            0x04F9: 140,
            0x04FA: 140,
            0x04FB: 140,
            0x04FC: 140,
            0x04FD: 140,
            0x04FE: 140,
            0x04FF: 140,
            0x0500: 140,
            0x0501: 140,
            0x0502: 140,
            0x0503: 140,
            0x0504: 140,
            0x0505: 143,
            0x0506: 143,
            0x0507: 143,
            0x0508: 143,
            0x0509: 143,
            0x050A: 143,
            0x050B: 143,
            0x050C: 143,
            0x050D: 143,
            0x050E: 143,
            0x050F: 143,
            0x0510: 143,
            0x0511: 143,
            0x0512: 142,
            0x0513: 142,
            0x0514: 142,
            0x0515: 142,
            0x0516: 141,
            0x0517: 141,
            0x0518: 141,
            0x0519: 141,
            0x051A: 141,
            0x051B: 141,
            0x051C: 141,
            0x051D: 141,
            0x051E: 141
        }
        
        # List of disallowed enemy types at each monster ID, for ensuring that orbs are reachable
        # and solid monsters can't softlock you, etc.
        self.enemizer_restricted_enemies = {
            0x0004: [53,60,73,80,81,102,103,104],  # U.Tunnel Skeleton Cage
            0x0006: [53,60,73,80,81,102,103,104],  # U.Tunnel First Door
            0x0016: [53,60,73,80,81,102,103,104],  # U.Tunnel Second Door
            0x002A: [53,60,73,80,81,102,103,104],  # U.Tunnel Bat Door
            0x0034: [53,60,73,80,81,102,103,104],  # U.Tunnel Dark Space
            0x0043: [53,60,73,80,81,102,103,104],  # U.Tunnel Skeleton Door 1
            0x0044: [53,60,73,80,81,102,103,104],  # U.Tunnel Skeleton Door 2
            0x0051: [53,60,73,80,81,102,103,104],  # Inca West Ladder
            0x0052: [53,60,73,80,81,102,103,104],  # Inca Entrance Ladder
            0x0055: [53,60,73,80,81,102,103,104],  # Inca Final Ladder
            0x007A: [53,60,73,80,81,102,103,104],  # Inca N/S Ramp Room Ramp
            0x009D: [14,33,52,53,60,73,80,81,102,103,104,143],  # Inca E/W Ramp Room Ramp
            0x00BF: [53,60,73,80,81,102,103,104],  # Inca Diamond Block Stair
            0x00CA: [53,60,73,80,81,102,103,104],  # Inca Singing Statue Stair
            0x00CF: [53,60,73,80,81,102,103,104],  # Mine Tunnel Middle Fence
            0x00D2: [53,60,73,80,81,102,103,104],  # Mine Tunnel South Fence
            0x00D3: [53,60,73,80,81,102,103,104],  # Mine Tunnel North Fence
            0x00E0: [53,60,73,80,81,102,103,104],  # Mine Big Room Cage
            0x00FD: [53,60,73,80,81,102,103,104],  # Mine Appearing Dark Space
            #0x0102: [],   # Friar worm fence worm is never randomized
            0x013B: [2,14,17,22,33,35,41,43,52,53,55,60,62,73,80,81,102,103,104,123,141,143],  # Garden SE Top Gate
            0x0148: [53,60,73,80,81,102,103,104],  # Garden SE Darkside Chest
            0x0150: [53,60,73,80,81,102,103,104],  # Garden SW Top Robot Gate
            0x0153: [53,60,73,80,81,102,103,104],  # Garden SW Top Robot Ramp
            0x015C: [53,60,73,80,81,102,103,104],  # Garden SW Top Worm Gate
            0x0161: [53,60,73,80,81,102,103,104],  # Garden SW Darkside Cage
            0x0194: [53,60,73,80,81,102,103,104],  # Mu Entrance Gate
            0x01A7: [2,14,17,22,33,35,41,43,52,53,55,60,62,73,80,81,102,103,104,123,141,143],  # Mu NE First Rock
            0x01A9: [2,14,17,22,33,35,41,43,52,53,55,60,62,73,80,81,102,103,104,123,141,143],  # Mu NE Second Rock
            0x01DE: [53,60,73,80,81,102,103,104],  # Mu West Slime Cages
            0x01EE: [53,60,73,80,81,102,103,104],  # Mu SE East-facing Head
            0x01FC: [53,60,73,80,81,102,103,104],  # Mu SE South-facing Head
            0x029B: [2,14,17,22,33,35,41,43,52,53,55,60,62,73,80,81,102,103,104,123,141,143],  # Great Wall Friar Gate
            #0x02B6: [],   # Fanger is never randomized
            0x030A: [53,60,73,80,81,102,103,104],  # Kress West Room Shortcut
            0x0388: [53,60,73,80,81,102,103,104],  # Wat Entrance Stair
            0x0395: [53,60,73,80,81,102,103,104],  # Wat East Slider Hole
            0x03A0: [53,60,73,80,81,102,103,104],  # Ankor Wat Pit Exit
            0x03E9: [2,14,17,22,33,35,41,43,52,53,55,60,62,73,80,81,102,103,104,123,141,143],  # Wat Dark Space Corridor
            0x0417: [53,60,73,80,81,102,103,104],  # Pyramid Foyer Dark Space
            0x04FA: [53,60,73,80,81,102,103,104],  # Mansion First Barrier
            0x0505: [53,60,73,80,81,102,103,104]   # Mansion Second Barrier
        }

        # Database of overworld menus
        # FORMAT: { ID: [ShuffleID (0=no shuffle), Menu_ID, FromRegion, ToRegion, AssemblyLabel, ContinentName, AreaName]}
        # Names are 10 characters, padded with white space (underscores).
        self.overworld_menus = {
            # SW Continent "\x01"
            1:  [0, 1, 10, 20, "Cape", "SW Continent", "South Cape"],
            2:  [0, 1, 10, 30, "Ed",   "SW Continent", "Edward's__"],
            3:  [0, 1, 10, 50, "Itry", "SW Continent", "Itory_____"],
            4:  [0, 1, 10, 60, "Moon", "SW Continent", "Moon Tribe"],
            5:  [0, 1, 10, 63, "Inca", "SW Continent", "Inca______"],

            # SE Continent "\x02"
            6:  [0, 2, 11, 102, "DCst", "SE Continent", "D. Coast__"],
            7:  [0, 2, 11, 110, "Frej", "SE Continent", "Freejia___"],
            8:  [0, 2, 11, 133, "Mine", "SE Continent", "D. Mine___"],
            9:  [0, 2, 11, 160, "Neil", "SE Continent", "Neil's____"],
            10: [0, 2, 11, 162, "Nzca", "SE Continent", "Nazca_____"],

            # NE Continent "\x03"
            11: [0, 3, 12, 250, "Angl", "NE Continent", "Angel Vil."],
            12: [0, 3, 12, 280, "Wtma", "NE Continent", "Watermia__"],
            13: [0, 3, 12, 290, "GtWl", "NE Continent", "Great Wall"],

            # N Continent "\x04"
            14: [0, 4, 13, 310, "Euro", "N Continent", "Euro______"],
            15: [0, 4, 13, 330, "Kres", "N Continent", "Mt. Temple"],
            16: [0, 4, 13, 350, "NtVl", "N Continent", "Natives'__"],
            17: [0, 4, 13, 360, "Ankr", "N Continent", "Ankor Wat_"],

            # NW Continent Overworld "\x05"
            18: [0, 5, 14, 400, "Dao",  "NW Continent", "Dao_______"],
            19: [0, 5, 14, 410, "Pymd", "NW Continent", "Pyramid___"]
        }


        # Database of map exits
        # FORMAT: { ID: [0: Vanilla exit that reverses this one (0 if one-way), 
        #                1: ShuffleTo/ActLike (0 if no shuffle), 
        #                2: ShuffleFrom/BeActedLikeBy (0 if no shuffle), 
        #                3: FromRegion, 
        #                4: ToRegion,
        #                5: AssemblyLabel, 
        #                6: Unused,
        #                7: BossFlag, 
        #                8: DungeonID (1 = EdDg, ..., 12 = Mansion), 
        #                9: PoolType (0 = never, 1 = ER pool, 2 = dungeon internal pool, 3 = dungeon entrance pool) 
        #                10: Name
        #               ] }
        self.exits = {
            # Bosses; due to boss shuffle, each needs a return exit and a post-defeat exit, even if artificial
            1:  [ 2, 0, 0,  78,  97, "Map1EExit02", "", True, 2, 0, "Castoth entrance (in)" ],
            2:  [ 1, 0, 0,   0,   0, "Map29Exit01", "", True, 2, 0, "Castoth entrance (out)" ],
            3:  [ 0, 0, 0, 104, 102, "MapShipExitString", "", True, 2, 0, "Diamond Coast passage (Gold Ship)" ],
            
            4:  [ 5, 0, 0, 171, 198, "Map4CExit01", "", True, 4, 0, "Viper entrance (in)" ],
            5:  [ 4, 0, 0,   0,   0, "Map55Exit01", "", True, 4, 0, "Viper entrance (out)" ],
            6:  [ 0, 0, 0, 198, 200, "MapViperExitString", "", True, 4, 0, "Seaside Palace passage (Viper)" ],
            
            7:  [ 8, 0, 0, 241, 243, "MapVampEntranceString", "", True, 5, 0, "Vampires entrance (in)" ],
            8:  [ 7, 0, 0,   0,   0, "Map67Exit01", "", True, 5, 0, "Vampires entrance (out)" ],
            9:  [ 0, 0, 0, 242, 212, "Map66Exit03", "", True, 5, 0, "Vampires exit" ],
            
            10: [11, 0, 0, 301, 302, "Map88Exit02", "", True, 7, 0, "Sand Fanger entrance (in)" ],
            11: [10, 0, 0,   0,   0, "Map8AExit01", "", True, 7, 0, "Sand Fanger entrance (out)" ],
            12: [ 0, 0, 0, 303, 290, "Map8AExit02", "", True, 7, 0, "Sand Fanger exit" ],
            
            13: [14, 0, 0, 414, 448, "MapMQEntranceString", "", True, 10, 0, "Mummy Queen entrance (in)" ],
            14: [13, 0, 0,   0,   0, "MapMQReturnString", "", True, 10, 0, "Mummy Queen entrance (out)" ],
            15: [ 0, 0, 0, 448, 415, "MapMQExitString", "", True, 10, 0, "Mummy Queen exit" ],

            16: [17, 0, 0, 470, 471, "MapE2Exit02", "", True, 11, 0, "Babel entrance (in)" ],
            17: [16, 0, 0,   0,   0, "MapE3Exit01", "", True, 11, 0, "Babel entrance (out)" ],
            18: [ 0, 0, 0, 472, 400, "MapBabelDaoWarpString", "", True, 11, 0, "Dao passage (Babel)" ],

            19: [20, 0, 0, 481, 482, "MapE9Exit01", "", True, 12, 0, "Solid Arm entrance (in)" ],
            20: [19, 0, 0,   0,   0, "MapSolidArmReturnString", "", True, 12, 0, "Solid Arm entrance (out)" ],
            21: [ 0, 0, 0, 472, 400, "MapBabelDaoWarpString", "", True, 12, 0, "Dao passage (Solid Arm)" ],

            # Passage Menus
            22: [0, 0, 0, 15,  28, "", "", False, 0, 0, "Seth: Passage 1 (South Cape)" ],
            23: [0, 0, 0, 15, 102, "", "", False, 0, 0, "Seth: Passage 2 (Diamond Coast)" ],
            24: [0, 0, 0, 15, 280, "", "", False, 0, 0, "Seth: Passage 3 (Watermia)" ],
            25: [0, 0, 0, 16,  60, "", "", False, 0, 0, "Moon Tribe: Passage 1 (Moon Tribe)" ],
            26: [0, 0, 0, 16, 200, "", "", False, 0, 0, "Moon Tribe: Passage 2 (Seaside Palace)" ],
            27: [0, 0, 0, 17, 161, "", "", False, 0, 0, "Neil: Passage 1 (Neil's)" ],
            28: [0, 0, 0, 17, 314, "", "", False, 0, 0, "Neil: Passage 2 (Euro)" ],
            29: [0, 0, 0, 17, 402, "", "", False, 0, 0, "Neil: Passage 3 (Dao)" ],
            30: [0, 0, 0, 17, 460, "", "", False, 0, 0, "Neil: Passage 4 (Babel)" ],

            # South Cape
            31: [32, 0, 0, 20, 22, "Map01Exit02", "", False, 0, 1, "South Cape: School main (in)" ],
            32: [31, 0, 0,  0,  0, "Map08Exit02", "", False, 0, 1, "South Cape: School main (out)" ],
            33: [34, 0, 0, 21, 22, "Map01Exit09", "", False, 0, 1, "South Cape: School roof (in)" ],
            34: [33, 0, 0,  0,  0, "Map08Exit01", "", False, 0, 1, "South Cape: School roof (out)" ],
            35: [36, 0, 0, 20, 23, "Map01Exit06", "", False, 0, 1, "South Cape: Will's House (in)" ],
            36: [35, 0, 0,  0,  0, "Map06Exit01", "", False, 0, 1, "South Cape: Will's House (out)" ],
            37: [38, 0, 0, 20, 24, "Map01Exit07", "", False, 0, 1, "South Cape: East House (in)" ],
            38: [37, 0, 0,  0,  0, "Map07Exit01", "", False, 0, 1, "South Cape: East House (out)" ],
            39: [40, 0, 0, 20, 27, "Map01Exit04", "", False, 0, 1, "South Cape: Erik's House main (in)" ],
            40: [39, 0, 0,  0,  0, "Map04Exit01", "", False, 0, 1, "South Cape: Erik's House main (out)" ],
            41: [42, 0, 0, 20, 27, "Map01Exit0A", "", False, 0, 1, "South Cape: Erik's House roof (in)" ],
            42: [41, 0, 0,  0,  0, "Map04Exit02", "", False, 0, 1, "South Cape: Erik's House roof (out)" ],
            43: [44, 0, 0, 20, 26, "Map01Exit03", "", False, 0, 1, "South Cape: Lance's House (in)" ],
            44: [43, 0, 0,  0,  0, "Map03Exit01", "", False, 0, 1, "South Cape: Lance's House (out)" ],
            45: [46, 0, 0, 20, 25, "Map01Exit05", "", False, 0, 1, "South Cape: Seth's House (in)" ],
            46: [45, 0, 0,  0,  0, "Map05Exit01", "", False, 0, 1, "South Cape: Seth's House (out)" ],
            47: [48, 0, 0, 20, 28, "Map01Exit08", "", False, 0, 1, "South Cape: Seaside Cave (in)" ],
            48: [47, 0, 0,  0,  0, "Map02Exit01", "", False, 0, 1, "South Cape: Seaside Cave (out)" ],

            # Edward's / Prison
            50: [51, 0, 0, 31, 49, "Map0AExit01", "", False, 1, 1, "Tunnel back entrance (in)" ],
            51: [50, 0, 0,  0,  0, "Map13Exit02", "", False, 1, 1, "Tunnel back entrance (out)" ],
            52: [53, 0, 0, 33, 40, "Map0BExit01", "", False, 1, 1, "Tunnel entrance (in)" ],
            53: [52, 0, 0,  0,  0, "Map0CExit01", "", False, 1, 1, "Tunnel entrance (out)" ],
            54: [ 0, 0, 0, 30, 32, "MapPrisonWarpString", "", False, 0, 1, "Prison entrance (king)" ],

            # Tunnel
            60: [61, 0, 0, 40, 41, "Map0CExit02", "", False, 1, 3, "Tunnel: Map 12 to Map 13" ],
            61: [60, 0, 0,  0,  0, "Map0DExit01", "", False, 1, 2, "Tunnel: Map 13 to Map 12" ],
            62: [63, 0, 0, 41, 42, "Map0DExit02", "", False, 1, 2, "Tunnel: Map 13 to Map 14" ],
            63: [62, 0, 0,  0,  0, "Map0EExit01", "", False, 1, 2, "Tunnel: Map 14 to Map 13" ],
            64: [65, 0, 0, 42, 43, "Map0EExit02", "", False, 1, 2, "Tunnel: Map 14 to Map 15" ],
            65: [64, 0, 0,  0,  0, "Map0FExit02", "", False, 1, 2, "Tunnel: Map 15 to Map 14" ],
            66: [67, 0, 0, 43, 44, "Map0FExit03", "", False, 1, 2, "Tunnel: Map 15 to Map 16" ],
            67: [66, 0, 0,  0,  0, "Map10Exit01", "", False, 1, 2, "Tunnel: Map 16 to Map 15" ],
            68: [69, 0, 0, 43, 45, "Map0FExit01", "", False, 1, 2, "Tunnel: Map 15 to Map 17" ],
            69: [68, 0, 0,  0,  0, "Map11Exit01", "", False, 1, 2, "Tunnel: Map 17 to Map 15" ],
            70: [71, 0, 0, 45, 47, "Map11Exit02", "", False, 1, 2, "Tunnel: Map 17 to Map 18" ],
            71: [70, 0, 0,  0,  0, "Map12Exit01", "", False, 1, 2, "Tunnel: Map 18 to Map 17" ],
            72: [73, 0, 0,706, 49, "Map12Exit02", "", False, 1, 2, "Tunnel: Map 18 to Map 19" ],
            73: [72, 0, 0,  0,  0, "Map13Exit01", "", False, 1, 3, "Tunnel: Map 19 to Map 18" ],  # Consider changing this to dungeon-internal
            
            # Itory
            80: [81, 0, 0, 51, 53, "Map15Exit01", "", False, 0, 1, "Itory: West House (in)" ],
            81: [80, 0, 0,  0,  0, "Map16Exit01", "", False, 0, 1, "Itory: West House (out)" ],
            82: [83, 0, 0, 51, 54, "Map15Exit04", "", False, 0, 1, "Itory: North House (in)" ],
            83: [82, 0, 0,  0,  0, "Map18Exit01", "", False, 0, 1, "Itory: North House (out)" ],
            84: [85, 0, 0, 51, 55, "Map15Exit02", "", False, 0, 1, "Itory: Lilly Front Door (in)" ],
            85: [84, 0, 0,  0,  0, "Map17Exit01", "", False, 0, 1, "Itory: Lilly Front Door (out)" ],
            86: [87, 0, 0, 52, 55, "Map15Exit03", "", False, 0, 1, "Itory: Lilly Back Door (in)" ],
            87: [86, 0, 0,  0,  0, "Map17Exit02", "", False, 0, 1, "Itory: Lilly Back Door (out)" ],
            88: [89, 0, 0, 51, 56, "Map15Exit05", "", False, 0, 1, "Itory Cave (in)" ],
            89: [88, 0, 0,  0,  0, "Map19Exit01", "", False, 0, 1, "Itory Cave (out)" ],
            90: [91, 0, 0, 56, 58, "Map19Exit02", "", False, 0, 1, "Itory Cave Hidden Room (in)" ],  # always linked?
            91: [90, 0, 0,  0,  0, "Map19Exit03", "", False, 0, 1, "Itory Cave Hidden Room (out)" ],
            
            # Moon Tribe
            100: [101, 0, 0, 60,  61, "Map1AExit02", "", False, 0, 1, "Moon Tribe Cave (in)" ],
            101: [100, 0, 0,  0,   0, "Map1BExit01", "", False, 0, 1, "Moon Tribe Cave (out)" ],
            102: [  0, 0, 0, 64, 170, "MapMoonWarpString", "", False, 4,  1, "Moon Tribe: Sky Garden passage" ],
            
            # Inca foyer
            110: [111, 0, 0, 63,  70, "Map1CExit01", "", False, 2, 1, "Inca Ruins entrance (in)" ],
            111: [110, 0, 0,  0,   0, "Map1DExit01", "", False, 2, 1, "Inca Ruins entrance (out)" ],
            #114: [  0, 0, 0, 65, 102, "", "", False, False,  True, "Inca: Diamond Coast passage" ],
            
            # Inca Ruins
            118: [119, 0, 0, 79,  69, "Map1FExit02", "", False,  2, 2, "Inca: Map 31 to Map 31 (U-turn)" ],
            119: [118, 0, 0,  0,   0, "Map1FExit03", "", False,  2, 2, "Inca: Map 31 (U-turn) to Map 31" ],
            120: [121, 0, 0, 70,  89, "Map1DExit07", "", False,  2, 2, "Inca: Map 29 to Map 37 (E)" ],
            121: [120, 0, 0,  0,   0, "Map25Exit01", "", False,  2, 2, "Inca: Map 37 to Map 29 (E)" ],
            122: [123, 0, 0, 89,  94, "Map25Exit03", "", False,  2, 2, "Inca: Map 37 to Map 39" ],
            123: [122, 0, 0,  0,   0, "Map27Exit01", "", False,  2, 2, "Inca: Map 39 to Map 37" ],
            124: [125, 0, 0, 94,  71, "Map27Exit02", "", False,  2, 2, "Inca: Map 39 to Map 29" ],
            125: [124, 0, 0,  0,   0, "Map1DExit0A", "", False,  2, 2, "Inca: Map 29 to Map 39" ],
            126: [127, 0, 0, 89,  72, "Map25Exit02", "", False,  2, 2, "Inca: Map 37 to Map 29 (W)" ],
            127: [126, 0, 0,  0,   0, "Map1DExit08", "", False,  2, 2, "Inca: Map 29 to Map 37 (W)" ],
            128: [129, 0, 0, 72,  91, "Map1DExit09", "", False,  2, 2, "Inca: Map 29 to Map 38" ],
            129: [128, 0, 0,  0,   0, "Map26Exit02", "", False,  2, 2, "Inca: Map 38 to Map 29" ],
            130: [131, 0, 0, 73,  80, "Map1DExit03", "", False,  2, 2, "Inca: Map 29 to Map 32" ],
            131: [130, 0, 0,  0,   0, "Map20Exit01", "", False,  2, 2, "Inca: Map 32 to Map 29" ],
            132: [133, 0, 0, 81,  85, "Map20Exit02", "", False,  2, 2, "Inca: Map 32 to Map 35" ],
            133: [132, 0, 0,  0,   0, "Map23Exit01", "", False,  2, 2, "Inca: Map 35 to Map 32" ],
            134: [135, 0, 0, 85,  74, "Map23Exit03", "", False,  2, 2, "Inca: Map 35 to Map 29" ],
            135: [134, 0, 0,  0,   0, "Map1DExit06", "", False,  2, 2, "Inca: Map 29 to Map 35" ],
            136: [137, 0, 0, 74,  79, "Map1DExit02", "", False,  2, 2, "Inca: Map 29 to Map 31" ],
            137: [136, 0, 0,  0,   0, "Map1FExit04", "", False,  2, 2, "Inca: Map 31 to Map 29" ],
            138: [139, 0, 0, 69,  95, "Map1FExit01", "", False,  2, 2, "Inca: Map 31 to Map 40" ],
            139: [138, 0, 0,  0,   0, "Map28Exit01", "", False,  2, 2, "Inca: Map 40 to Map 31" ],
            140: [141, 0, 0, 96,  76, "Map28Exit02", "", False,  2, 2, "Inca: Map 40 to Map 29" ],
            141: [140, 0, 0,  0,   0, "Map1DExit0B", "", False,  2, 2, "Inca: Map 29 to Map 40" ],
            142: [143, 0, 0, 86,  82, "Map23Exit02", "", False,  2, 2, "Inca: Map 35 to Map 33" ],
            143: [142, 0, 0,  0,   0, "Map21Exit02", "", False,  2, 2, "Inca: Map 33 to Map 35" ],
            144: [145, 0, 0, 83,  75, "Map21Exit01", "", False,  2, 2, "Inca: Map 33 to Map 29" ],
            145: [144, 0, 0,  0,   0, "Map1DExit04", "", False,  2, 2, "Inca: Map 29 to Map 33" ],
            146: [147, 0, 0, 99,  84, "Map1DExit05", "", False,  2, 2, "Inca: Map 29 to Map 34" ],  # Special case to allow for Z-ladder glitch
            147: [146, 0, 0, 84,  75, "Map22Exit01", "", False,  2, 2, "Inca: Map 34 to Map 29" ],
            148: [149, 0, 0, 84,  93, "Map22Exit03", "", False,  2, 2, "Inca: Map 34 to Map 38" ],
            149: [148, 0, 0,  0,   0, "Map26Exit01", "", False,  2, 2, "Inca: Map 38 to Map 34" ],
            150: [151, 0, 0, 84,  87, "Map22Exit02", "", False,  2, 2, "Inca: Map 34 to Map 36" ],
            151: [150, 0, 0,  0,   0, "Map24Exit01", "", False,  2, 2, "Inca: Map 36 to Map 34" ],
            152: [153, 0, 0, 87,  77, "Map24Exit02", "", False,  2, 2, "Inca: Map 36 to Map 30" ],
            153: [152, 0, 0,  0,   0, "Map1EExit01", "", False,  2, 2, "Inca: Map 30 to Map 36" ],
            154: [  0, 0, 0, 98, 100, "", "", False,  0, 0, "Gold Ship entrance" ],
            
            # Gold Ship
            160: [161, 0, 0, 100, 101, "", "", False, 0, 0, "Gold Ship Interior (in)" ],
            161: [160, 0, 0,   0,   0, "", "", False, 0, 0, "Gold Ship Interior (out)" ],
            
            # Diamond Coast
            172: [173, 0, 0, 102, 103, "Map30Exit01", "", False, 0, 1, "Coast House (in)" ],
            173: [172, 0, 0,   0,   0, "Map31Exit01", "", False, 0, 1, "Coast House (out)" ],
            
            # Freejia
            182: [183, 0, 0, 110, 116, "Map32Exit05", "", False, 0, 1, "Freejia: West House (in)" ],
            183: [182, 0, 0,   0,   0, "Map36Exit01", "", False, 0, 1, "Freejia: West House (out)" ],
            184: [185, 0, 0, 110, 117, "Map32Exit06", "", False, 0, 1, "Freejia: 2-story House (in)" ],
            185: [184, 0, 0,   0,   0, "Map37Exit01", "", False, 0, 1, "Freejia: 2-story House (out)" ],
            186: [187, 0, 0, 111, 117, "Map32Exit07", "", False, 0, 1, "Freejia: 2-story Roof (in)" ],
            187: [186, 0, 0,   0,   0, "Map37Exit02", "", False, 0, 1, "Freejia: 2-story Roof (out)" ],
            188: [189, 0, 0, 110, 118, "Map32Exit08", "", False, 0, 1, "Freejia: Lovers' House (in)" ],
            189: [188, 0, 0,   0,   0, "Map38Exit01", "", False, 0, 1, "Freejia: Lovers' House (out)" ],
            190: [191, 0, 0, 110, 119, "Map32Exit09", "", False, 0, 1, "Freejia: Hotel (in)" ],
            191: [190, 0, 0,   0,   0, "Map39Exit01", "", False, 0, 1, "Freejia: Hotel (out)" ],
            192: [193, 0, 0, 119, 120, "Map39Exit02", "", False, 0, 1, "Freejia: Hotel West Room (in)" ],
            193: [192, 0, 0,   0,   0, "Map39Exit04", "", False, 0, 1, "Freejia: Hotel West Room (out)" ],
            194: [195, 0, 0, 119, 121, "Map39Exit03", "", False, 0, 1, "Freejia: Hotel East Room (in)" ],
            195: [194, 0, 0,   0,   0, "Map39Exit05", "", False, 0, 1, "Freejia: Hotel East Room (out)" ],
            196: [197, 0, 0, 110, 122, "Map32Exit0A", "", False, 0, 1, "Freejia: Laborer House (in)" ],    # might take this out?
            197: [196, 0, 0,   0,   0, "Map3AExit02", "", False, 0, 1, "Freejia: Laborer House (out)" ],
            198: [199, 0, 0, 112, 122, "Map32Exit0B", "", False, 0, 1, "Freejia: Laborer Roof (in)" ],
            199: [198, 0, 0,   0,   0, "Map3AExit01", "", False, 0, 1, "Freejia: Laborer Roof (out)" ],
            200: [201, 0, 0, 110, 123, "Map32Exit0C", "", False, 0, 1, "Freejia: Messy House (in)" ],
            201: [200, 0, 0,   0,   0, "Map3BExit01", "", False, 0, 1, "Freejia: Messy House (out)" ],
            202: [203, 0, 0, 110, 124, "Map32Exit01", "", False, 0, 1, "Freejia: Erik House (in)" ],
            203: [202, 0, 0,   0,   0, "Map33Exit01", "", False, 0, 1, "Freejia: Erik House (out)" ],
            204: [205, 0, 0, 110, 125, "Map32Exit02", "", False, 0, 1, "Freejia: Dark Space House (in)" ],
            205: [204, 0, 0,   0,   0, "Map34Exit01", "", False, 0, 1, "Freejia: Dark Space House (out)" ],
            206: [207, 0, 0, 110, 126, "Map32Exit03", "", False, 0, 1, "Freejia: Labor Trade House (in)" ],
            207: [206, 0, 0,   0,   0, "Map35Exit01", "", False, 0, 1, "Freejia: Labor Trade House (out)" ],
            208: [209, 0, 0, 113, 126, "Map32Exit04", "", False, 0, 1, "Freejia: Labor Trade Roof (in)" ],
            209: [208, 0, 0,   0,   0, "Map35Exit02", "", False, 0, 1, "Freejia: Labor Trade Roof (out)" ],
            210: [211, 0, 0, 114, 127, "Map32Exit0D", "", False, 0, 1, "Freejia: Labor Market (in)" ],
            211: [210, 0, 0,   0,   0, "Map3CExit01", "", False, 0, 1, "Freejia: Labor Market (out)" ],
            
            # Diamond Mine
            222: [223, 0, 0, 133, 134, "Map3EExit01", "", False,  3, 3, "Diamond Mine: Map 62 to Map 63" ],
            223: [222, 0, 0,   0,   0, "Map3FExit01", "", False,  3, 2, "Diamond Mine: Map 63 to Map 62" ],
            224: [225, 0, 0, 134, 140, "Map3FExit03", "", False,  3, 2, "Diamond Mine: Map 63 to Map 66" ],
            225: [224, 0, 0,   0,   0, "Map42Exit01", "", False,  3, 2, "Diamond Mine: Map 66 to Map 63" ],
            226: [227, 0, 0, 134, 136, "Map3FExit02", "", False,  3, 2, "Diamond Mine: Map 63 to Map 64" ],
            227: [226, 0, 0,   0,   0, "Map40Exit01", "", False,  3, 2, "Diamond Mine: Map 64 to Map 63" ],
            228: [229, 0, 0, 136, 138, "Map40Exit02", "", False,  3, 2, "Diamond Mine: Map 64 to Map 65" ],
            229: [228, 0, 0,   0,   0, "Map41Exit01", "", False,  3, 2, "Diamond Mine: Map 65 to Map 64" ],
            230: [231, 0, 0, 139, 143, "Map41Exit02", "", False,  3, 2, "Diamond Mine: Map 65 to Map 66" ],
            231: [230, 0, 0,   0,   0, "Map42Exit06", "", False,  3, 2, "Diamond Mine: Map 66 to Map 65" ],
            232: [233, 0, 0, 138, 130, "Map41Exit03", "", False,  3, 2, "Diamond Mine: Map 65 to Map 61" ],
            233: [232, 0, 0,   0,   0, "Map3DExit01", "", False,  3, 2, "Diamond Mine: Map 61 to Map 65" ],
            234: [235, 0, 0, 131, 142, "Map3DExit02", "", False,  3, 2, "Diamond Mine: Map 61 to Map 66" ],
            235: [234, 0, 0,   0,   0, "Map42Exit05", "", False,  3, 2, "Diamond Mine: Map 66 to Map 61" ],
            236: [237, 0, 0, 140, 144, "Map42Exit02", "", False,  3, 2, "Diamond Mine: Map 66 to Map 67 (1)" ],
            237: [236, 0, 0,   0,   0, "Map43Exit01", "", False,  3, 2, "Diamond Mine: Map 67 to Map 66 (1)" ],
            238: [239, 0, 0, 145, 141, "Map43Exit02", "", False,  3, 2, "Diamond Mine: Map 67 to Map 66 (2)" ],
            239: [238, 0, 0,   0,   0, "Map42Exit03", "", False,  3, 2, "Diamond Mine: Map 66 to Map 67 (2)" ],
            240: [241, 0, 0, 141, 146, "Map42Exit04", "", False,  3, 2, "Diamond Mine: Map 66 to Map 68" ],
            241: [240, 0, 0,   0,   0, "Map44Exit01", "", False,  3, 2, "Diamond Mine: Map 68 to Map 66" ],
            242: [243, 0, 0, 146, 148, "Map44Exit02", "", False,  3, 2, "Diamond Mine: Map 68 to Map 69" ],
            243: [242, 0, 0,   0,   0, "Map45Exit01", "", False,  3, 2, "Diamond Mine: Map 69 to Map 68" ],
            244: [245, 0, 0, 146, 149, "Map44Exit04", "", False,  3, 2, "Diamond Mine: Map 68 to Map 70" ],
            245: [244, 0, 0,   0,   0, "Map46Exit01", "", False,  3, 2, "Diamond Mine: Map 70 to Map 68" ],
            246: [247, 0, 0, 146, 150, "Map44Exit03", "", False,  3, 2, "Diamond Mine: Map 68 to Map 71" ],
            247: [246, 0, 0,   0,   0, "Map47Exit01", "", False,  3, 2, "Diamond Mine: Map 71 to Map 68" ],
            
            # Nazca
            260: [261, 0, 0, 162, 170, "MapGardenEntranceString", "", False, 4, 1, "Nazca: Sky Garden entrance" ],
            261: [260, 0, 0,   0,   0, "MapGardenExitString", "", False, 4, 1, "Nazca: Sky Garden exit" ],
            
            # Sky Garden
            #270: [  0, 0, 0, 171,  16, "", "", False,  4,  True, "Moon Tribe: Sky Garden passage" ],
            273: [274, 0, 0, 170, 172, "Map4CExit02", "", False,  4, 2, "Sky Garden: Map 76 to Map 77" ],
            274: [273, 0, 0,   0,   0, "Map4DExit01", "", False,  4, 2, "Sky Garden: Map 77 to Map 76" ],
            275: [276, 0, 0, 170, 176, "Map4CExit03", "", False,  4, 2, "Sky Garden: Map 76 to Map 79" ],
            276: [275, 0, 0,   0,   0, "Map4FExit01", "", False,  4, 2, "Sky Garden: Map 79 to Map 76" ],
            277: [278, 0, 0, 170, 181, "Map4CExit05", "", False,  4, 2, "Sky Garden: Map 76 to Map 81" ],
            278: [277, 0, 0,   0,   0, "Map51Exit01", "", False,  4, 2, "Sky Garden: Map 81 to Map 76" ],
            279: [280, 0, 0, 170, 190, "Map4CExit04", "", False,  4, 2, "Sky Garden: Map 76 to Map 83" ],
            280: [279, 0, 0,   0,   0, "Map53Exit01", "", False,  4, 2, "Sky Garden: Map 83 to Map 76" ],
            281: [282, 0, 0, 172, 175, "Map4DExit02", "", False,  4, 2, "Sky Garden: Map 77 to Map 78 (E)" ],   # Room 1
            282: [281, 0, 0,   0,   0, "Map4EExit01", "", False,  4, 2, "Sky Garden: Map 78 to Map 77 (W)" ],
            283: [284, 0, 0, 175, 173, "Map4EExit03", "", False,  4, 2, "Sky Garden: Map 78 to Map 77 (SE)" ],
            284: [283, 0, 0,   0,   0, "Map4DExit04", "", False,  4, 2, "Sky Garden: Map 77 to Map 78 (SW)" ],
            285: [286, 0, 0, 175, 174, "Map4EExit02", "", False,  4, 2, "Sky Garden: Map 78 to Map 77 (SW)" ],
            286: [285, 0, 0,   0,   0, "Map4DExit03", "", False,  4, 2, "Sky Garden: Map 77 to Map 78 (SE)" ],
            287: [288, 0, 0, 176, 169, "Map4FExit05", "", False,  4, 2, "Sky Garden: Map 79 to Map 86" ],       # Room 2
            288: [287, 0, 0,   0,   0, "Map56Exit01", "", False,  4, 2, "Sky Garden: Map 86 to Map 79" ],
            289: [290, 0, 0, 176, 179, "Map4FExit02", "", False,  4, 2, "Sky Garden: Map 79 to Map 80 (NE)" ],
            290: [289, 0, 0,   0,   0, "Map50Exit01", "", False,  4, 2, "Sky Garden: Map 80 to Map 79 (NW)" ],
            291: [292, 0, 0, 179, 177, "Map50Exit02", "", False,  4, 2, "Sky Garden: Map 80 to Map 79 (N)" ],
            292: [291, 0, 0,   0,   0, "Map4FExit03", "", False,  4, 2, "Sky Garden: Map 79 to Map 80 (N)" ],
            293: [294, 0, 0, 178, 180, "Map4FExit04", "", False,  4, 2, "Sky Garden: Map 79 to Map 80 (S)" ],
            294: [293, 0, 0,   0,   0, "Map50Exit03", "", False,  4, 2, "Sky Garden: Map 80 to Map 79 (S)" ],
            295: [296, 0, 0, 168, 186, "Map51Exit02", "", False,  4, 2, "Sky Garden: Map 81 to Map 82 (NE)" ],   # Room 3
            296: [295, 0, 0,   0,   0, "Map52Exit01", "", False,  4, 2, "Sky Garden: Map 82 to Map 81 (NW)" ],
            297: [298, 0, 0, 182, 188, "Map51Exit03", "", False,  4, 2, "Sky Garden: Map 81 to Map 82 (NW)" ],
            298: [297, 0, 0,   0,   0, "Map52Exit02", "", False,  4, 2, "Sky Garden: Map 82 to Map 81 (NE)" ],
            299: [300, 0, 0, 184, 187, "Map51Exit04", "", False,  4, 2, "Sky Garden: Map 81 to Map 82 (SE)" ],
            300: [299, 0, 0,   0,   0, "Map52Exit03", "", False,  4, 2, "Sky Garden: Map 82 to Map 81 (SW)" ],
            301: [302, 0, 0, 191, 196, "Map53Exit05", "", False,  4, 2, "Sky Garden: Map 83 to Map 84 (NW)" ],   # Room 4
            302: [301, 0, 0,   0,   0, "Map54Exit04", "", False,  4, 2, "Sky Garden: Map 84 to Map 83 (NE)" ],
            303: [304, 0, 0, 192, 195, "Map53Exit02", "", False,  4, 2, "Sky Garden: Map 83 to Map 84 (C)" ],
            304: [303, 0, 0,   0,   0, "Map54Exit01", "", False,  4, 2, "Sky Garden: Map 84 to Map 83 (C)" ],
            305: [306, 0, 0, 197, 193, "Map54Exit02", "", False,  4, 2, "Sky Garden: Map 84 to Map 83 (SE)" ],
            306: [305, 0, 0,   0,   0, "Map53Exit03", "", False,  4, 2, "Sky Garden: Map 83 to Map 84 (SW)" ],
            307: [308, 0, 0, 167, 195, "Map53Exit04", "", False,  4, 2, "Sky Garden: Map 83 to Map 84 (E)" ],
            308: [307, 0, 0,   0,   0, "Map54Exit03", "", False,  4, 2, "Sky Garden: Map 84 to Map 83 (W)" ],
            
            # Seaside Palace
            310: [311, 0, 0, 210, 200, "Map5EExit03", "", False, 0, 0, "Seaside entrance" ],  # always linked
            311: [310, 0, 0,   0,   0, "Map5AExit05", "", False, 0, 0, "Seaside exit" ],      # always linked
            312: [313, 0, 0, 200, 202, "Map5AExit02", "", False, 0, 1, "Seaside: Area 1 NE Room (in)" ],
            313: [312, 0, 0,   0,   0, "Map5BExit01", "", False, 0, 1, "Seaside: Area 1 NE Room (out)" ],
            314: [315, 0, 0, 200, 203, "Map5AExit03", "", False, 0, 1, "Seaside: Area 1 NW Room (in)" ],
            315: [314, 0, 0,   0,   0, "Map5BExit02", "", False, 0, 1, "Seaside: Area 1 NW Room (out)" ],
            316: [317, 0, 0, 200, 204, "Map5AExit04", "", False, 0, 1, "Seaside: Area 1 SE Room (in)" ],
            317: [316, 0, 0,   0,   0, "Map5BExit03", "", False, 0, 1, "Seaside: Area 1 SE Room (out)" ],
            318: [319, 0, 0, 200, 205, "Map5AExit01", "", False, 0, 1, "Seaside: Area 2 entrance" ],
            319: [318, 0, 0,   0,   0, "Map5CExit01", "", False, 0, 1, "Seaside: Area 2 exit" ],
            320: [321, 0, 0, 205, 207, "Map5CExit03", "", False, 0, 1, "Seaside: Area 2 SW Room (in)" ],
            321: [320, 0, 0,   0,   0, "Map5BExit04", "", False, 0, 1, "Seaside: Area 2 SW Room (out)" ],
            322: [323, 0, 0, 205, 209, "Map5CExit02", "", False, 0, 1, "Seaside: Fountain (in)" ],
            323: [322, 0, 0,   0,   0, "Map5DExit01", "", False, 0, 1, "Seaside: Fountain (out)" ],
            
            # Mu
            330: [331, 0, 0, 210, 212, "Map5EExit02", "", False,  5, 1, "Mu entrance" ],
            331: [330, 0, 0,   0,   0, "Map5FExit01", "", False,  5, 1, "Mu exit" ],
            332: [333, 0, 0, 722, 217, "Map5FExit02", "", False,  5, 2, "Mu: Map 95 to Map 96" ],
            333: [332, 0, 0,   0,   0, "Map60Exit01", "", False,  5, 2, "Mu: Map 96 to Map 95" ],
            334: [335, 0, 0, 723, 220, "Map60Exit02", "", False,  5, 2, "Mu: Map 96 to Map 97 (top)" ],
            335: [334, 0, 0,   0,   0, "Map61Exit01", "", False,  5, 2, "Mu: Map 97 to Map 96 (top)" ],
            336: [337, 0, 0, 220, 231, "Map61Exit07", "", False,  5, 2, "Mu: Map 97 to Map 99" ],
            337: [336, 0, 0,   0,   0, "Map63Exit01", "", False,  5, 2, "Mu: Map 99 to Map 97" ],
            338: [339, 0, 0, 220, 225, "Map61Exit04", "", False,  5, 2, "Mu: Map 97 to Map 98 (top)" ],
            339: [338, 0, 0,   0,   0, "Map62Exit02", "", False,  5, 2, "Mu: Map 98 to Map 97 (top)" ],
            340: [341, 0, 0, 218, 222, "Map60Exit03", "", False,  5, 2, "Mu: Map 96 to Map 97 (middle)" ],
            341: [340, 0, 0,   0,   0, "Map61Exit02", "", False,  5, 2, "Mu: Map 97 to Map 96 (middle)" ],
            342: [343, 0, 0, 223, 227, "Map61Exit05", "", False,  5, 2, "Mu: Map 97 to Map 98 (middle)" ],
            343: [342, 0, 0,   0,   0, "Map62Exit03", "", False,  5, 2, "Mu: Map 98 to Map 97 (middle)" ],
            346: [347, 0, 0, 227, 233, "Map62Exit06", "", False,  5, 2, "Mu: Map 98 to Map 100 (middle E)" ],
            347: [346, 0, 0,   0,   0, "Map64Exit01", "", False,  5, 2, "Mu: Map 100 to Map 98 (middle E)" ],
            348: [349, 0, 0, 233, 237, "Map64Exit04", "", False,  5, 2, "Mu: Map 100 to Map 101 (middle N)" ],
            349: [348, 0, 0,   0,   0, "Map65Exit01", "", False,  5, 2, "Mu: Map 101 to Map 100 (middle N)" ],
            350: [351, 0, 0, 237, 234, "Map65Exit03", "", False,  5, 2, "Mu: Map 101 to Map 100 (middle S)" ],
            351: [350, 0, 0,   0,   0, "Map64Exit06", "", False,  5, 2, "Mu: Map 100 to Map 101 (middle S)" ],
            352: [353, 0, 0, 234, 228, "Map64Exit03", "", False,  5, 2, "Mu: Map 100 to Map 98 (middle W)" ],
            353: [352, 0, 0,   0,   0, "Map62Exit08", "", False,  5, 2, "Mu: Map 98 to Map 100 (middle W)" ],
            354: [355, 0, 0, 213, 232, "Map5FExit05", "", False,  5, 2, "Mu: Map 95 to Map 99" ],
            355: [354, 0, 0,   0,   0, "Map63Exit02", "", False,  5, 2, "Mu: Map 99 to Map 95" ],
            356: [357, 0, 0, 722, 226, "",            "", False,  5, 0, "Mu: Map 95 to Map 98 (top)" ], # Slider, always linked
            357: [356, 0, 0,   0,   0, "",            "", False,  5, 0, "Mu: Map 98 to Map 95 (top)" ], # Slider, always linked
            358: [359, 0, 0, 229, 224, "Map62Exit04", "", False,  5, 2, "Mu: Map 98 to Map 97 (bottom)" ],
            359: [358, 0, 0,   0,   0, "Map61Exit06", "", False,  5, 2, "Mu: Map 97 to Map 98 (bottom)" ],
            360: [361, 0, 0, 224, 219, "Map61Exit03", "", False,  5, 2, "Mu: Map 97 to Map 96 (bottom)" ],
            361: [360, 0, 0,   0,   0, "Map60Exit04", "", False,  5, 2, "Mu: Map 96 to Map 97 (bottom)" ],
            362: [363, 0, 0, 230, 216, "Map62Exit01", "", False,  5, 2, "Mu: Map 98 to Map 95 (bottom)" ],
            363: [362, 0, 0,   0,   0, "Map5FExit03", "", False,  5, 2, "Mu: Map 95 to Map 98 (bottom)" ],
            364: [365, 0, 0, 230, 235, "Map62Exit07", "", False,  5, 2, "Mu: Map 98 to Map 100 (bottom)" ],
            365: [364, 0, 0,   0,   0, "Map64Exit02", "", False,  5, 2, "Mu: Map 100 to Map 98 (bottom)" ],
            366: [367, 0, 0, 235, 239, "Map64Exit05", "", False,  5, 2, "Mu: Map 100 to Map 101 (bottom)" ],
            367: [366, 0, 0,   0,   0, "Map65Exit02", "", False,  5, 2, "Mu: Map 101 to Map 100 (bottom)" ],
            368: [369, 0, 0, 239, 240, "Map65Exit04", "", False,  5, 0, "Mu: Map 101 to Map 102" ], # Not randomized; Mu boss always requires Hope+Rama Statues
            369: [368, 0, 0,   0,   0, "Map66Exit02", "", False,  5, 0, "Mu: Map 102 to Map 101" ],
            
            # Angel Village
            382: [383, 0, 0, 250, 210, "Map69Exit01", "", False, 0, 1, "Angel: Mu Passage (in)" ],
            383: [382, 0, 0,   0,   0, "Map5EExit01", "", False, 0, 1, "Angel: Mu Passage (out)" ], #custom
            384: [385, 0, 0, 250, 251, "Map69Exit02", "", False, 0, 1, "Angel: Underground entrance (in)" ],
            385: [384, 0, 0,   0,   0, "Map6BExit01", "", False, 0, 1, "Angel: Underground entrance (out)" ],
            386: [387, 0, 0, 251, 252, "Map6BExit02", "", False, 0, 1, "Angel: Room 1 (in)" ],
            387: [386, 0, 0,   0,   0, "Map6CExit01", "", False, 0, 1, "Angel: Room 1 (out)" ],
            388: [389, 0, 0, 251, 253, "Map6BExit05", "", False, 0, 1, "Angel: Room 2 (in)" ],
            389: [388, 0, 0,   0,   0, "Map6CExit04", "", False, 0, 1, "Angel: Room 2 (out)" ],
            390: [391, 0, 0, 251, 254, "Map6BExit03", "", False, 0, 1, "Angel: Dance Hall (in)" ],
            391: [390, 0, 0,   0,   0, "Map6CExit05", "", False, 0, 1, "Angel: Dance Hall (out)" ],
            392: [393, 0, 0, 251, 255, "Map6BExit04", "", False, 0, 1, "Angel: DS Room (in)" ],
            393: [392, 0, 0,   0,   0, "Map6CExit03", "", False, 0, 1, "Angel: DS Room (out)" ],
            
            # Angel Dungeon
            398: [399, 0, 0, 259, 263, "Map70Exit04", "", False, 6, 2, "Angel Dungeon: Map 112(N) to Map 112(main)" ],
            399: [398, 0, 0,   0,   0, "Map70Exit05", "", False, 6, 2, "Angel Dungeon: Map 112(main) to Map 112(N)" ],
            400: [401, 0, 0, 251, 260, "Map6BExit06", "", False, 6, 1, "Angel Dungeon entrance" ],
            401: [400, 0, 0,   0,   0, "Map6DExit02", "", False, 6, 1, "Angel Dungeon exit" ],
            402: [403, 0, 0, 260, 261, "Map6DExit01", "", False, 6, 3, "Angel Dungeon: Map 109 to Map 110" ],
            403: [402, 0, 0,   0,   0, "Map6EExit01", "", False, 6, 2, "Angel Dungeon: Map 110 to Map 109" ],
            404: [405, 0, 0, 278, 262, "Map6EExit02", "", False, 6, 2, "Angel Dungeon: Map 110 to Map 111" ],
            405: [404, 0, 0,   0,   0, "Map6FExit01", "", False, 6, 2, "Angel Dungeon: Map 111 to Map 110" ],
            406: [407, 0, 0, 262, 259, "Map6FExit02", "", False, 6, 2, "Angel Dungeon: Map 111 to Map 112(N)" ],
            407: [406, 0, 0,   0,   0, "Map70Exit01", "", False, 6, 2, "Angel Dungeon: Map 112(N) to Map 111" ],
            408: [409, 0, 0, 263, 265, "Map70Exit02", "", False, 6, 2, "Angel Dungeon: Map 112 to Chest" ],  # Slider
            409: [408, 0, 0,   0,   0, "Map70Exit03", "", False, 6, 2, "Angel Dungeon: Chest to Map 112" ],  # Slider
            410: [411, 0, 0, 279, 266, "Map70Exit06", "", False, 6, 2, "Angel Dungeon: Map 112 to Map 113" ],
            411: [410, 0, 0,   0,   0, "Map71Exit01", "", False, 6, 2, "Angel Dungeon: Map 113 to Map 112" ],
            412: [413, 0, 0, 266, 267, "Map71Exit02", "", False, 6, 2, "Angel Dungeon: Map 113 to Map 114" ],
            413: [412, 0, 0,   0,   0, "Map72Exit01", "", False, 6, 2, "Angel Dungeon: Map 114 to Map 113" ],
            414: [415, 0, 0, 267, 277, "Map72Exit02", "", False, 6, 2, "Angel Dungeon: Map 114 to Ishtar Foyer" ],  # Slider
            415: [414, 0, 0,   0,   0, "Map73Exit01", "", False, 6, 2, "Angel Dungeon: Ishtar Foyer to Map 114" ],  # Slider
            
            # Ishtar's Studio
            420: [421, 0, 0, 277, 269, "Map73Exit02", "", False, 6, 1, "Ishtar entrance" ],
            421: [420, 0, 0,   0,   0, "Map73Exit03", "", False, 6, 1, "Ishtar exit" ],
            422: [423, 0, 0, 269, 270, "Map73Exit04", "", False, 0, 1, "Ishtar: Portrait room (in)" ],
            423: [422, 0, 0,   0,   0, "Map74Exit01", "", False, 0, 1, "Ishtar: Portrait room (out)" ],
            424: [425, 0, 0, 269, 271, "Map73Exit05", "", False, 0, 1, "Ishtar: Side room (in)" ],
            425: [424, 0, 0,   0,   0, "Map74Exit02", "", False, 0, 1, "Ishtar: Side room (out)" ],
            426: [427, 0, 0, 269, 272, "Map73Exit06", "", False, 0, 1, "Ishtar: Ishtar's room (in)" ],
            427: [426, 0, 0,   0,   0, "Map74Exit03", "", False, 0, 1, "Ishtar: Ishtar's room (out)" ],
            428: [429, 0, 0, 272, 274, "Map74Exit04", "", False, 0, 1, "Ishtar: Puzzle room (in)" ],
            429: [428, 0, 0,   0,   0, "Map75Exit11", "", False, 0, 1, "Ishtar: Puzzle room (out)" ],
            
            # Watermia
            440: [441, 0, 0, 280, 286, "Map78Exit01", "", False, 0, 1, "Watermia: Lance House (in)" ],
            441: [440, 0, 0,   0,   0, "Map79Exit01", "", False, 0, 1, "Watermia: Lance House (out)" ],
            442: [443, 0, 0, 280, 282, "Map78Exit04", "", False, 0, 1, "Watermia: DS House (in)" ],
            443: [442, 0, 0,   0,   0, "Map7CExit01", "", False, 0, 1, "Watermia: DS House (out)" ],
            444: [445, 0, 0, 280, 283, "Map78Exit03", "", False, 0, 1, "Watermia: Gambling House (in)" ],
            445: [444, 0, 0,   0,   0, "Map7BExit01", "", False, 0, 1, "Watermia: Gambling House (out)" ],
            446: [447, 0, 0, 280, 284, "Map78Exit05", "", False, 0, 1, "Watermia: West House (in)" ],
            447: [446, 0, 0,   0,   0, "Map7DExit01", "", False, 0, 1, "Watermia: West House (out)" ],
            448: [449, 0, 0, 280, 285, "Map78Exit06", "", False, 0, 1, "Watermia: East House (in)" ],
            449: [448, 0, 0,   0,   0, "Map7EExit01", "", False, 0, 1, "Watermia: East House (out)" ],
            450: [451, 0, 0, 280, 287, "Map78Exit02", "", False, 0, 1, "Watermia: NW House (in)" ],
            451: [450, 0, 0,   0,   0, "Map7AExit01", "", False, 0, 1, "Watermia: NW House (out)" ],
            452: [453, 0, 0, 288, 311, "",            "", False, 0, 0, "Watermia: Euro passage" ],
            453: [452, 0, 0,   0,   0, "",            "", False, 0, 0, "Euro: Watermia passage" ],
            
            # Great Wall
            462: [463, 0, 0, 290, 291, "Map82Exit01", "", False, 7, 3, "Great Wall: Map 130 to Map 131" ],
            463: [462, 0, 0,   0,   0, "Map83Exit01", "", False, 7, 2, "Great Wall: Map 131 to Map 130" ],
            464: [465, 0, 0, 293, 294, "Map83Exit02", "", False, 7, 2, "Great Wall: Map 131 to Map 133" ],
            465: [464, 0, 0,   0,   0, "Map85Exit01", "", False, 7, 2, "Great Wall: Map 133 to Map 131" ],
            466: [467, 0, 0, 296, 297, "Map85Exit02", "", False, 7, 2, "Great Wall: Map 133 to Map 134" ],
            467: [466, 0, 0,   0,   0, "Map86Exit01", "", False, 7, 2, "Great Wall: Map 134 to Map 133" ],
            468: [469, 0, 0, 297, 298, "Map86Exit02", "", False, 7, 2, "Great Wall: Map 134 to Map 135" ],
            469: [468, 0, 0,   0,   0, "Map87Exit01", "", False, 7, 2, "Great Wall: Map 135 to Map 134" ],
            470: [471, 0, 0, 299, 300, "Map87Exit02", "", False, 7, 2, "Great Wall: Map 135 to Map 136" ],
            471: [470, 0, 0,   0,   0, "Map88Exit01", "", False, 7, 2, "Great Wall: Map 136 to Map 135" ],
            
            # Euro
            482: [483, 0, 0, 310, 312, "Map91Exit03", "", False, 0, 1, "Euro: Rolek Company (in)" ],
            483: [482, 0, 0,   0,   0, "Map94Exit01", "", False, 0, 1, "Euro: Rolek Company (out)" ],
            484: [485, 0, 0, 310, 313, "Map91Exit08", "", False, 0, 1, "Euro: West House (in)" ],
            485: [484, 0, 0,   0,   0, "Map98Exit01", "", False, 0, 1, "Euro: West House (out)" ],
            486: [487, 0, 0, 310, 314, "Map91Exit04", "", False, 0, 1, "Euro: Rolek Mansion West (in)" ],
            487: [486, 0, 0,   0,   0, "Map95Exit01", "", False, 0, 1, "Euro: Rolek Mansion West (out)" ],
            488: [489, 0, 0, 310, 314, "Map91Exit05", "", False, 0, 1, "Euro: Rolek Mansion East (in)" ],
            489: [488, 0, 0,   0,   0, "Map95Exit02", "", False, 0, 1, "Euro: Rolek Mansion East (out)" ],
            490: [491, 0, 0, 310, 317, "Map91Exit0A", "", False, 0, 1, "Euro: Central House (in)" ],
            491: [490, 0, 0,   0,   0, "Map9AExit01", "", False, 0, 1, "Euro: Central House (out)" ],
            492: [493, 0, 0, 310, 318, "Map91Exit0B", "", False, 0, 1, "Euro: Jeweler House (in)" ],
            493: [492, 0, 0,   0,   0, "Map9BExit01", "", False, 0, 1, "Euro: Jeweler House (out)" ],
            494: [495, 0, 0, 310, 319, "Map91Exit0C", "", False, 0, 1, "Euro: Twins House (in)" ],
            495: [494, 0, 0,   0,   0, "Map9CExit01", "", False, 0, 1, "Euro: Twins House (out)" ],
            496: [497, 0, 0, 310, 320, "Map91Exit02", "", False, 0, 1, "Euro: Hidden House (in)" ],
            497: [496, 0, 0,   0,   0, "Map93Exit01", "", False, 0, 1, "Euro: Hidden House (out)" ],
            498: [499, 0, 0, 310, 321, "Map91Exit0D", "", False, 0, 1, "Euro: Shrine (in)" ],
            499: [498, 0, 0,   0,   0, "Map9DExit01", "", False, 0, 1, "Euro: Shrine (out)" ],
            500: [501, 0, 0, 310, 322, "Map91Exit01", "", False, 0, 1, "Euro: Explorer's House (in)" ],
            501: [500, 0, 0,   0,   0, "Map92Exit01", "", False, 0, 1, "Euro: Explorer's House (out)" ],
            502: [  0, 0, 0, 310, 323, "Map91Exit06", "", False, 0, 1, "Euro: Store Entrance (in)" ],
            #503: [502, 0, 0,   0,   0, "",           "", False, 0, 0, "Euro: Store Entrance (out)" ], #this doesn't exist!
            504: [505, 0, 0, 310, 324, "Map91Exit07", "", False, 0, 1, "Euro: Store Exit (in)" ],
            505: [504, 0, 0,   0,   0, "Map97Exit01", "", False, 0, 1, "Euro: Store Exit (out)" ],
            506: [507, 0, 0, 314, 316, "Map95Exit03", "", False, 0, 1, "Euro: Guest Room (in)" ],
            507: [506, 0, 0,   0,   0, "Map96Exit01", "", False, 0, 1, "Euro: Guest Room (out)" ],
            508: [509, 0, 0, 310, 325, "Map91Exit09", "", False, 0, 1, "Euro: Dark Space House (in)" ],
            509: [508, 0, 0,   0,   0, "Map99Exit01", "", False, 0, 1, "Euro: Dark Space House (out)" ],
            
            # Mt. Kress
            522: [523, 0, 0, 330, 331, "MapA0Exit01", "", False, 8, 3, "Mt. Kress: Map 160 to Map 161" ],
            523: [522, 0, 0,   0,   0, "MapA1Exit01", "", False, 8, 2, "Mt. Kress: Map 161 to Map 160" ],
            524: [525, 0, 0, 332, 333, "MapA1Exit02", "", False, 8, 2, "Mt. Kress: Map 161 to Map 162 (W)" ],
            525: [524, 0, 0,   0,   0, "MapA2Exit01", "", False, 8, 2, "Mt. Kress: Map 162 to Map 161 (W)" ],
            526: [527, 0, 0, 332, 334, "MapA1Exit03", "", False, 8, 2, "Mt. Kress: Map 161 to Map 162 (E)" ],
            527: [526, 0, 0,   0,   0, "MapA2Exit02", "", False, 8, 2, "Mt. Kress: Map 162 to Map 161 (E)" ],
            528: [529, 0, 0, 333, 337, "MapA2Exit04", "", False, 8, 2, "Mt. Kress: Map 162 to Map 163 (N)" ],
            529: [528, 0, 0,   0,   0, "MapA3Exit02", "", False, 8, 2, "Mt. Kress: Map 163 to Map 162 (N)" ],
            530: [531, 0, 0, 337, 336, "MapA3Exit01", "", False, 8, 2, "Mt. Kress: Map 163 to Map 162 (S)" ],
            531: [530, 0, 0,   0,   0, "MapA2Exit03", "", False, 8, 2, "Mt. Kress: Map 162 to Map 163 (S)" ],
            532: [533, 0, 0, 333, 338, "MapA2Exit05", "", False, 8, 2, "Mt. Kress: Map 162 to Map 164" ],
            533: [532, 0, 0,   0,   0, "MapA4Exit01", "", False, 8, 2, "Mt. Kress: Map 164 to Map 162" ],
            534: [535, 0, 0, 335, 339, "MapA2Exit06", "", False, 8, 2, "Mt. Kress: Map 162 to Map 165" ],
            535: [534, 0, 0,   0,   0, "MapA5Exit01", "", False, 8, 2, "Mt. Kress: Map 165 to Map 162" ],
            536: [537, 0, 0, 339, 342, "MapA5Exit02", "", False, 8, 2, "Mt. Kress: Map 165 to Map 166" ],
            537: [536, 0, 0,   0,   0, "MapA6Exit01", "", False, 8, 2, "Mt. Kress: Map 166 to Map 165" ],
            538: [539, 0, 0, 340, 343, "MapA5Exit03", "", False, 8, 2, "Mt. Kress: Map 165 to Map 167" ],
            539: [538, 0, 0,   0,   0, "MapA7Exit01", "", False, 8, 2, "Mt. Kress: Map 167 to Map 165" ],
            540: [541, 0, 0, 341, 344, "MapA5Exit04", "", False, 8, 2, "Mt. Kress: Map 165 to Map 168" ],
            541: [540, 0, 0,   0,   0, "MapA8Exit01", "", False, 8, 2, "Mt. Kress: Map 168 to Map 165" ],
            542: [543, 0, 0, 344, 345, "MapA8Exit02", "", False, 8, 2, "Mt. Kress: Map 168 to Map 169" ],
            543: [542, 0, 0,   0,   0, "MapA9Exit01", "", False, 8, 2, "Mt. Kress: Map 169 to Map 168" ],
            
            # Native's Village
            552: [553, 0, 0, 350, 352, "MapACExit01", "", False, 0, 1, "Native's Village: West House (in)" ],
            553: [552, 0, 0,   0,   0, "MapADExit01", "", False, 0, 1, "Native's Village: West House (out)" ],
            554: [555, 0, 0, 350, 353, "MapACExit02", "", False, 0, 1, "Native's Village: House w/Statues (in)" ],
            555: [554, 0, 0,   0,   0, "MapAEExit01", "", False, 0, 1, "Native's Village: House w/Statues (out)" ],
            556: [557, 0, 0, 351, 400, "",            "", False, 0, 0, "Native's Village: Dao Passage" ],
            557: [556, 0, 0,   0,   0, "",            "", False, 0, 0, "Dao: Natives' Passage" ],
            
            # Ankor Wat
            562: [563, 0, 0, 360, 361, "MapB0Exit01", "", False, 9, 3, "Ankor Wat: Map 176 to Map 177" ],
            563: [562, 0, 0,   0,   0, "MapB1Exit01", "", False, 9, 2, "Ankor Wat: Map 177 to Map 176" ],
            564: [565, 0, 0, 361, 363, "MapB1Exit02", "", False, 9, 2, "Ankor Wat: Map 177 to Map 178" ],
            565: [564, 0, 0,   0,   0, "MapB2Exit01", "", False, 9, 2, "Ankor Wat: Map 178 to Map 177" ],
            566: [567, 0, 0, 365, 366, "MapB2Exit02", "", False, 9, 2, "Ankor Wat: Map 178 to Map 179" ],
            567: [566, 0, 0,   0,   0, "MapB3Exit01", "", False, 9, 2, "Ankor Wat: Map 179 to Map 178" ],
            568: [569, 0, 0, 368, 367, "MapB4Exit01", "", False, 9, 2, "Ankor Wat: Map 180 to Map 179" ],
            569: [568, 0, 0,   0,   0, "MapB3Exit03", "", False, 9, 2, "Ankor Wat: Map 179 to Map 180" ],
            570: [571, 0, 0, 367, 369, "MapB3Exit04", "", False, 9, 2, "Ankor Wat: Map 179 to Map 181" ],
            571: [570, 0, 0,   0,   0, "MapB5Exit01", "", False, 9, 2, "Ankor Wat: Map 181 to Map 179" ],
            572: [573, 0, 0, 371, 362, "MapB5Exit02", "", False, 9, 2, "Ankor Wat: Map 181 to Map 177" ],
            573: [572, 0, 0,   0,   0, "MapB1Exit04", "", False, 9, 2, "Ankor Wat: Map 177 to Map 181" ],
            574: [575, 0, 0, 362, 372, "MapB1Exit03", "", False, 9, 2, "Ankor Wat: Map 177 to Map 182" ],  # Garden
            575: [574, 0, 0,   0,   0, "MapB6Exit01", "", False, 9, 2, "Ankor Wat: Map 182 to Map 177" ],
            576: [577, 0, 0, 372, 373, "MapB6Exit02", "", False, 9, 2, "Ankor Wat: Map 182 to Map 183" ],
            577: [576, 0, 0,   0,   0, "MapB7Exit01", "", False, 9, 2, "Ankor Wat: Map 183 to Map 182" ],
            578: [579, 0, 0, 373, 376, "MapB7Exit04", "", False, 9, 2, "Ankor Wat: Map 183 to Map 184" ],
            579: [578, 0, 0,   0,   0, "MapB8Exit01", "", False, 9, 2, "Ankor Wat: Map 184 to Map 183" ],
            580: [581, 0, 0, 374, 378, "MapB7Exit02", "", False, 9, 2, "Ankor Wat: Map 183 to Map 185 (W)" ],
            581: [580, 0, 0,   0,   0, "MapB9Exit01", "", False, 9, 2, "Ankor Wat: Map 185 to Map 183 (W)" ],
            582: [583, 0, 0, 378, 375, "MapB9Exit02", "", False, 9, 2, "Ankor Wat: Map 185 to Map 183 (E)" ],
            583: [582, 0, 0,   0,   0, "MapB7Exit03", "", False, 9, 2, "Ankor Wat: Map 183 to Map 185 (E)" ],
            584: [585, 0, 0, 375, 379, "MapB7Exit05", "", False, 9, 2, "Ankor Wat: Map 183 to Map 186" ],
            585: [584, 0, 0,   0,   0, "MapBAExit01", "", False, 9, 2, "Ankor Wat: Map 186 to Map 183" ],
            586: [587, 0, 0, 379, 381, "MapBAExit02", "", False, 9, 2, "Ankor Wat: Map 186 to Map 187 (W)" ],
            587: [586, 0, 0,   0,   0, "MapBBExit01", "", False, 9, 2, "Ankor Wat: Map 187 to Map 186 (W)" ],
            588: [589, 0, 0, 381, 380, "MapBBExit02", "", False, 9, 2, "Ankor Wat: Map 187 to Map 186 (E)" ],
            589: [588, 0, 0,   0,   0, "MapBAExit03", "", False, 9, 2, "Ankor Wat: Map 186 to Map 187 (E)" ],
            590: [591, 0, 0, 381, 384, "MapBBExit03", "", False, 9, 2, "Ankor Wat: Map 187 to Map 188" ],
            591: [590, 0, 0,   0,   0, "MapBCExit01", "", False, 9, 2, "Ankor Wat: Map 188 to Map 187" ],
            592: [593, 0, 0, 385, 386, "MapBCExit06", "", False, 9, 2, "Ankor Wat: Map 188 to Map 189" ],
            593: [592, 0, 0,   0,   0, "MapBDExit01", "", False, 9, 2, "Ankor Wat: Map 189 to Map 188" ],
            594: [595, 0, 0, 387, 389, "MapBDExit03", "", False, 9, 2, "Ankor Wat: Map 189 to Map 190 (E)" ],
            595: [594, 0, 0,   0,   0, "MapBEExit02", "", False, 9, 2, "Ankor Wat: Map 190 to Map 189 (E)" ],
            596: [597, 0, 0, 388, 390, "MapBDExit02", "", False, 9, 2, "Ankor Wat: Map 189 to Map 190 (W)" ],
            597: [596, 0, 0,   0,   0, "MapBEExit01", "", False, 9, 2, "Ankor Wat: Map 190 to Map 189 (W)" ],
            598: [599, 0, 0, 390, 391, "MapBEExit04", "", False, 9, 2, "Ankor Wat: Map 190 to Map 191" ],
            599: [598, 0, 0,   0,   0, "MapBFExit01", "", False, 9, 2, "Ankor Wat: Map 191 to Map 190" ],
            600: [  0, 0, 0, 366, 368, "MapB3Exit02", "", False, 9, 2, "Ankor Wat: Map 179 to Map 180 (drop)" ],
            601: [  0, 0, 0, 384, 381, "MapBCExit02", "", False, 9, 2, "Ankor Wat: Map 188 to Map 187 NW-L (drop)" ],
            602: [  0, 0, 0, 384, 381, "MapBCExit03", "", False, 9, 2, "Ankor Wat: Map 188 to Map 187 NW-R (drop)" ],
            603: [  0, 0, 0, 384, 383, "MapBCExit04", "", False, 9, 2, "Ankor Wat: Map 188 to Map 187 NE (drop)" ],
            604: [  0, 0, 0, 385, 382, "MapBCExit05", "", False, 9, 2, "Ankor Wat: Map 188 to Map 187 SW (drop)" ],
            605: [  0, 0, 0, 389, 388, "MapBEExit03", "", False, 9, 2, "Ankor Wat: Map 190 to Map 189 (drop)" ],
            
            # Dao
            612: [613, 0, 0, 400, 401, "MapC3Exit01", "", False, 0, 1, "Dao: NW House (in)" ],
            613: [612, 0, 0,   0,   0, "MapC4Exit01", "", False, 0, 1, "Dao: NW House (out)" ],
            614: [615, 0, 0, 400, 402, "MapC3Exit02", "", False, 0, 1, "Dao: Neil's House (in)" ],
            615: [614, 0, 0,   0,   0, "MapC8Exit01", "", False, 0, 1, "Dao: Neil's House (out)" ],
            616: [617, 0, 0, 400, 403, "MapC3Exit03", "", False, 0, 1, "Dao: Snake Game House (in)" ],
            617: [616, 0, 0,   0,   0, "MapC6Exit01", "", False, 0, 1, "Dao: Snake Game House (out)" ],
            618: [619, 0, 0, 400, 404, "MapC3Exit04", "", False, 0, 1, "Dao: SW House (in)" ],
            619: [618, 0, 0,   0,   0, "MapC7Exit01", "", False, 0, 1, "Dao: SW House (out)" ],
            620: [621, 0, 0, 400, 405, "MapC3Exit05", "", False, 0, 1, "Dao: S House (in)" ],
            621: [620, 0, 0,   0,   0, "MapC5Exit01", "", False, 0, 1, "Dao: S House (out)" ],
            622: [623, 0, 0, 400, 406, "MapC3Exit06", "", False, 0, 1, "Dao: SE House (in)" ],
            623: [622, 0, 0,   0,   0, "MapC9Exit01", "", False, 0, 1, "Dao: SE House (out)" ],
            
            # Pyramid
            634: [635, 0, 0, 411, 415, "",            "", False, 10, 0, "Pyramid: Map 204 to Map 205" ], # Hieroglyph room, ALWAYS LINKED (1a33e)
            635: [634, 0, 0,   0,   0, "",            "", False, 10, 0, "Pyramid: Map 205 to Map 204" ], # Hieroglyph room, ALWAYS LINKED (1a394)
            636: [637, 0, 0, 413, 416, "MapCCExit02", "", False, 10, 2, "Pyramid: Map 204 to Map 206" ],  # Room 1
            637: [636, 0, 0,   0,   0, "MapCEExit01", "", False, 10, 2, "Pyramid: Map 206 to Map 204" ],
            638: [639, 0, 0, 417, 418, "MapCEExit02", "", False, 10, 2, "Pyramid: Map 206 to Map 207" ],
            639: [638, 0, 0,   0,   0, "MapCFExit01", "", False, 10, 2, "Pyramid: Map 207 to Map 206" ],
            640: [641, 0, 0, 419, 442, "MapCFExit02", "", False, 10, 2, "Pyramid: Map 207 to Map 218" ],
            641: [640, 0, 0,   0,   0, "MapDAExit01", "", False, 10, 2, "Pyramid: Map 218 to Map 207" ],
            642: [643, 0, 0, 413, 420, "MapCCExit03", "", False, 10, 2, "Pyramid: Map 204 to Map 208" ],  # Room 2
            643: [642, 0, 0,   0,   0, "MapD0Exit01", "", False, 10, 2, "Pyramid: Map 208 to Map 204" ],
            644: [645, 0, 0, 421, 422, "MapD0Exit02", "", False, 10, 2, "Pyramid: Map 208 to Map 209" ],
            645: [644, 0, 0,   0,   0, "MapD1Exit01", "", False, 10, 2, "Pyramid: Map 209 to Map 208" ],
            646: [647, 0, 0, 423, 443, "MapD1Exit02", "", False, 10, 2, "Pyramid: Map 209 to Map 218" ],
            647: [646, 0, 0,   0,   0, "MapDAExit02", "", False, 10, 2, "Pyramid: Map 218 to Map 209" ],
            648: [649, 0, 0, 413, 431, "MapCCExit04", "", False, 10, 2, "Pyramid: Map 204 to Map 214" ],  # Room 3
            649: [648, 0, 0,   0,   0, "MapD6Exit01", "", False, 10, 2, "Pyramid: Map 214 to Map 204" ],
            650: [651, 0, 0, 434, 435, "MapD6Exit02", "", False, 10, 2, "Pyramid: Map 214 to Map 215" ],
            651: [650, 0, 0,   0,   0, "MapD7Exit01", "", False, 10, 2, "Pyramid: Map 215 to Map 214" ],
            652: [653, 0, 0, 450, 444, "MapD7Exit02", "", False, 10, 2, "Pyramid: Map 215 to Map 218" ],
            653: [652, 0, 0,   0,   0, "MapDAExit05", "", False, 10, 2, "Pyramid: Map 218 to Map 215" ],
            654: [655, 0, 0, 413, 436, "MapCCExit05", "", False, 10, 2, "Pyramid: Map 204 to Map 216" ],  # Room 4
            655: [654, 0, 0,   0,   0, "MapD8Exit01", "", False, 10, 2, "Pyramid: Map 216 to Map 204" ],
            656: [657, 0, 0, 437, 438, "MapD8Exit02", "", False, 10, 2, "Pyramid: Map 216 to Map 217" ],
            657: [656, 0, 0,   0,   0, "MapD9Exit01", "", False, 10, 2, "Pyramid: Map 217 to Map 216" ],
            658: [659, 0, 0, 439, 440, "MapD9Exit02", "", False, 10, 2, "Pyramid: Map 217 to Map 219" ],
            659: [658, 0, 0,   0,   0, "MapDBExit01", "", False, 10, 2, "Pyramid: Map 219 to Map 217" ],
            660: [661, 0, 0, 441, 445, "MapDBExit02", "", False, 10, 2, "Pyramid: Map 219 to Map 218" ],
            661: [660, 0, 0,   0,   0, "MapDAExit06", "", False, 10, 2, "Pyramid: Map 218 to Map 219" ],
            662: [663, 0, 0, 413, 426, "MapCCExit06", "", False, 10, 2, "Pyramid: Map 204 to Map 212" ],  # Room 5
            663: [662, 0, 0,   0,   0, "MapD4Exit01", "", False, 10, 2, "Pyramid: Map 212 to Map 204" ],
            664: [665, 0, 0, 429, 430, "MapD4Exit02", "", False, 10, 2, "Pyramid: Map 212 to Map 213" ],
            665: [664, 0, 0,   0,   0, "MapD5Exit01", "", False, 10, 2, "Pyramid: Map 213 to Map 212" ],
            666: [667, 0, 0, 430, 446, "MapD5Exit02", "", False, 10, 2, "Pyramid: Map 213 to Map 218" ],
            667: [666, 0, 0,   0,   0, "MapDAExit04", "", False, 10, 2, "Pyramid: Map 218 to Map 213" ],
            668: [669, 0, 0, 413, 424, "MapCCExit07", "", False, 10, 2, "Pyramid: Map 204 to Map 210" ],  # Room 6
            669: [668, 0, 0,   0,   0, "MapD2Exit01", "", False, 10, 2, "Pyramid: Map 210 to Map 204" ],
            670: [671, 0, 0, 424, 425, "MapD2Exit02", "", False, 10, 2, "Pyramid: Map 210 to Map 211" ],
            671: [670, 0, 0,   0,   0, "MapD3Exit01", "", False, 10, 2, "Pyramid: Map 211 to Map 210" ],
            672: [673, 0, 0, 425, 447, "MapD3Exit02", "", False, 10, 2, "Pyramid: Map 211 to Map 218" ],
            673: [672, 0, 0,   0,   0, "MapDAExit03", "", False, 10, 2, "Pyramid: Map 218 to Map 211" ],
            
            # Babel
            682: [683, 0, 0, 460, 461, "MapDEExit01", "", False, 11, 0, "Babel: Map 222 to Map 223" ],
            683: [682, 0, 0,   0,   0, "MapDFExit01", "", False, 11, 0, "Babel: Map 223 to Map 222" ],
            684: [685, 0, 0, 462, 463, "MapDFExit02", "", False, 11, 0, "Babel: Map 223 to Map 224" ],
            685: [684, 0, 0,   0,   0, "MapE0Exit01", "", False, 11, 0, "Babel: Map 224 to Map 223" ],
            686: [687, 0, 0, 463, 474, "",            "", False, 11, 0, "Babel: Map 224 to Map 242" ],  # Castoth, ALWAYS LINKED (1a81e)
            687: [686, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 242 to Map 224" ],  # Castoth, ALWAYS LINKED (a9af9)
            688: [689, 0, 0, 463, 475, "",            "", False, 11, 0, "Babel: Map 224 to Map 243" ],  # Viper, ALWAYS LINKED (1a82a)
            689: [688, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 243 to Map 224" ],  # Viper, ALWAYS LINKED (ad165)
            690: [691, 0, 0, 463, 465, "MapE0Exit02", "", False, 11, 0, "Babel: Map 224 to Map 225 (bottom)" ],
            691: [690, 0, 0,   0,   0, "MapE1Exit01", "", False, 11, 0, "Babel: Map 225 to Map 224 (bottom)" ],
            692: [693, 0, 0, 466, 464, "MapE1Exit02", "", False, 11, 0, "Babel: Map 225 to Map 224 (top)" ],
            693: [692, 0, 0,   0,   0, "MapE0Exit03", "", False, 11, 0, "Babel: Map 224 to Map 225 (top)" ],
            694: [695, 0, 0, 464, 476, "",            "", False, 11, 0, "Babel: Map 224 to Map 244" ],  # Vampires, ALWAYS LINKED (1a836)
            695: [694, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 244 to Map 224" ],  # Vampires, ALWAYS LINKED (af1ed)
            696: [697, 0, 0, 464, 477, "",            "", False, 11, 0, "Babel: Map 224 to Map 245" ],  # Sand Fanger, ALWAYS LINKED (1a842)
            697: [696, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 245 to Map 224" ],  # Sand Fanger, ALWAYS LINKED (b8130)
            698: [699, 0, 0, 464, 469, "MapE0Exit04", "", False, 11, 0, "Babel: Map 224 to Map 226" ],
            699: [698, 0, 0,   0,   0, "MapE2Exit01", "", False, 11, 0, "Babel: Map 226 to Map 224" ],
            #700: [701, 0, 0, 470, 471, "",           "", False, 11, 0, "Babel: Map 226 to Map 227" ],  #DUPLICATE W/BOSS EXITS
            #701: [700, 0, 0,   0,   0, "",           "", False, 11, 0, "Babel: Map 227 to Map 226" ],
            702: [703, 0, 0, 471, 478, "",            "", False, 11, 0, "Babel: Map 227 to Map 246" ],  # Mummy Queen -- EVERYTHING HERE DOWN ALWAYS LINKED
            703: [702, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 246 to Map 227" ],
            704: [705, 0, 0, 471, 467, "",            "", False, 11, 0, "Babel: Map 227 to Map 225 (bottom)" ],
            705: [704, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 225 to Map 227 (bottom)" ],
            706: [707, 0, 0, 468, 472, "",            "", False, 11, 0, "Babel: Map 225 to Map 227 (top)" ],
            707: [706, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 227 to Map 225 (top)" ],
            708: [709, 0, 0, 472, 473, "",            "", False, 11, 0, "Babel: Map 227 to Map 222" ],
            709: [708, 0, 0,   0,   0, "",            "", False, 11, 0, "Babel: Map 222 to Map 227" ],
            
            # Jeweler's Mansion
            720: [721, 0, 0,   8, 480, "MapMansionEntranceString", "", False, 12, 1, "Mansion entrance" ],
            721: [720, 0, 0, 480, 400, "MapMansionExitString",     "", False, 12, 1, "Mansion exit" ]
        }
        
        # Logic requirements for exits to be traversable.
        # During initialization, new nodes are created and entries are added to self.logic as needed.
        # If IsCoupled, the logic will be applied to the coupled exit too.
        # Format: { ID: [0: ExitId,
        #                1: [[item1, qty1],[item2,qty2],...],
        #                2: Direction (0 = to exit from node, 1 = from exit to node, 2 = both),
        #                3: IsCoupled
        #               ] }
        self.exit_logic = {
            1:  [ 62,  [[701, 1]], 0, False ],   # Edward's first worm door
            2:  [ 64,  [[702, 1]], 0, False ],   # Edward's second worm door
            3:  [ 68,  [[703, 1]], 0, False ],   # Edward's bat door
            4:  [ 70,  [[501, 1]], 0, False ],   # Edward's Lilly door
            5:  [ 90,  [[608, 1]], 0, False ],   # Itory cave wall
            6:  [ 152, [[8, 1]], 0, False ],     # Inca Golden Tile
            7:  [ 126, [[524, 1]], 2, False ],   # Inca Diamond Block
            8:  [ 234, [[608, 1]], 0, False ],   # Mine tunnel wall
            9:  [ 224, [[15, 1]], 0, False ],    # Mine elevator
            10: [ 246, [[11, 1], [12, 1]], 0, False ],   # Mine end
            11: [ 310, [[16, 1]], 0, True ],     # Sea Palace door
            12: [ 354, [[511, 1]], 2, False ],    # Mu-NW door (Hope Room)
            13: [ 362, [[512, 1]], 2, True ],    # Mu-NW/W exit (Bot)
            14: [ 356, [[62, 1]], 0, True ],     # Mu-NW/W Slider hole
            15: [ 360, [[512, 1]], 2, True ],    # Mu-NE/E exit 1 (Bot)
            16: [ 340, [[511, 1]], 2, True ],    # Mu-NE/E exit 2 (Mid)
            17: [ 358, [[512, 1]], 2, True ],    # Mu-E/W exit 1 (Bot)
            18: [ 342, [[511, 1]], 2, True ],    # Mu-E/W exit 2 (Mid)
            19: [ 352, [[511, 1]], 2, True ],    # Mu-W/SW exit 1 (Mid)
            20: [ 364, [[512, 1]], 2, True ],    # Mu-W/SW exit 2 (Bot)
            21: [ 346, [[511, 1]], 2, True ],    # Mu-W/SW exit 3 (Mid)
            22: [ 348, [[511, 1]], 2, True ],    # Mu-SW/SE exit 1 (Mid)
            23: [ 366, [[512, 1]], 2, True ],    # Mu-SW/SE exit 2 (Bot)
            24: [ 350, [[511, 1]], 2, True ],    # Mu-SW/SE exit 3 (Mid)
            25: [ 368, [[512, 1]], 2, False ],   # Mu-SE exit door (Bot)
            26: [ 408, [[62, 1]], 0, True ],     # Angl chest slider
            27: [ 414, [[62, 1]], 0, True ],     # Angl Ishtar slider
            28: [ 591, [[28, 1]], 2, False],     # Wat bright room N
            29: [ 591, [[601, 1]], 2, False],    # Wat bright room N
            30: [ 592, [[28, 1]], 2, False],     # Wat bright room S
            31: [ 592, [[601, 1]], 2, False]    # Wat bright room S
        }
        
        
