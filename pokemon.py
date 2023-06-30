import requests
import json
import sys
import pandas

#pokeapi url
url = "https://pokeapi.co/api/v2/"


#gets the number of pokemon currently listed on the api. This includes variant forms as well 
# ?limit raises the query limit. default = 20
def getMonCount():
    return json.loads(requests.get(url+"pokemon").text)["count"]

#does a request for all the info for the poke with the requested id
def getMon(pokemon_id):
    return requests.get(url+"pokemon/"+str(pokemon_id)).text

def getMonSpecies(pokemon_id):
    return requests.get(url+"pokemon-species/"+str(pokemon_id)).text

#using the pokemon id, get requested json for each pokemon
def getJson(json_str, info):
    return json.loads(json_str)[info]

#A dictionary keyed by pokemon id for the pokemon information.
pokemon_dictionary = {}

#A dict for each pokemon species
poke_species_dict = {}

#get a composite list of information for a specific pokemon
def getMonInfo(pokemon_id, pokemon_json_dict, pokemon_species_dict, info_list):
    for info in info_list:
            ##if (info == "capture_rate" or "gender_rate" or "egg_groups"):
            pokemon_dictionary[pokemon_id][info] = loadMonInfo(pokemon_json_dict,pokemon_species_dict, info)


#queries every existing pokemon for selected information. Asks whether to export to csv (Excel format)
#forms were recently moved to 10001 from the end of the list so once the end of the list is reached, find how many remaining forms there are and then continue there
def getInfoInEachMon(info_list, lower_bound, upper_bound):
    form_search = False
    recalc = 0
    for pokemon_id in range(lower_bound, upper_bound):
        #A cool little progress counter!
        sys.stdout.write(f"\rGetting Mon and Form Info! %i/{upper_bound}" % pokemon_id)
        sys.stdout.flush()

        pokemon_dictionary[pokemon_id] = {}
        pokemon_json_dict = getMon(pokemon_id)
        if(form_search):
            pokemon_id = recalc + pokemon_id
            pokemon_json_dict = getMon(pokemon_id)
            pokemon_species_dict = getMonSpecies(pokemon_id)
            pokemon_id = pokemon_id - recalc
            getMonInfo(pokemon_id, pokemon_json_dict, pokemon_species_dict, info_list)
            

        elif(pokemon_json_dict == "Not Found"):
            print(" Starting Pokemon Forms")
            form_search = True
            recalc = 10001-(pokemon_id)
            pokemon_id = recalc + pokemon_id
            pokemon_json_dict = getMon(pokemon_id)
            pokemon_id = pokemon_id - recalc
            getMonInfo(pokemon_id, pokemon_json_dict, pokemon_species_dict, info_list)

        else:
            pokemon_species_dict = getMonSpecies(pokemon_id)
            getMonInfo(pokemon_id, pokemon_json_dict, pokemon_species_dict, info_list)
        




#loads the pokemons info from the json file
def loadMonInfo(pokemon_json_dict, pokemon_species_dict, info):
    if(info == "capture_rate" or info == "gender_rate" or info == "egg_groups"):
        if(pokemon_species_dict == "Not Found"): 
            return "X"
        species_info = getJson(pokemon_species_dict, info)
        if(info == "egg_groups"):  
            return getPokeEggInfo(species_info)

        return species_info
        
    mon_info = getJson(pokemon_json_dict, info)
    match(info):
        case "types":
            return getPokeTypeInfo(mon_info)
        case "stats":
            return getPokeStatInfo(mon_info)
        case "abilities":
            return getPokeAbilitiesInfo(mon_info)
        case "moves":
            return
        case "height" | "weight":
            mon_info = str(mon_info/10)
            if (info == "height"):
                mon_info = mon_info + "m"
            else:
                mon_info = mon_info + "kg"
            return mon_info
        case _:
            return mon_info


#gets information for all pokemon stats
def getPokeStatInfo(stats_dict):
    formatted_stats = {}
    for stat in stats_dict:
        stat_name = stat["stat"]["name"]
        base_stat = stat["base_stat"]
        formatted_stats[stat_name] = base_stat
    return formatted_stats

#gets information for all pokemon abilities
def getPokeAbilitiesInfo(abilities_dict):
    ability_list = []
    for ability in abilities_dict:
        ability_name = ability["ability"]["name"]
        ability_list.append(ability_name)
    return ability_list

#gets information for all pokemon stats
def getPokeTypeInfo(type_dict):
    formatted_types = []
    for type in type_dict:
        type_name = type["type"]["name"]
        formatted_types.append(type_name)
    return formatted_types

def getPokeEggInfo(egg_dict):
    formatted_egg_group = []
    for egg_group in egg_dict:
        group_name = egg_group["name"]
        formatted_egg_group.append(group_name)
    return formatted_egg_group



#the pokemon information being requested
desired_info = ["name","types","abilities","stats","height","weight", "capture_rate", "gender_rate","egg_groups"]

print("getting information for each pokemon! This will take a while depending on your internet speed.")
getInfoInEachMon(desired_info, 1, getMonCount())

print("Doing some database management! Halfway there!")
pokemon_df = pandas.DataFrame.from_dict(pokemon_dictionary).transpose()
#Takes all the data and modifies it so the lists and dict values take multiple columns. The lists will have a repeating name
#And dict will have a column name for each key
def dataFrameReassembler(df):
    new_frame = pandas.DataFrame()
    for data_cat in df:

        #Gets a list from each data point
        data_list = pokemon_df[str(data_cat)].to_list()

        #get the number of rows that the list will produce
        row_number = len(data_list)
        
        if (type(data_list[0]) == dict):
            split_frame =  pandas.DataFrame(data_list)

        elif(type(data_list[0]) == list):
            split_frame =  pandas.DataFrame(data_list)
            columns_no = len(data_list[0])
            for i in data_list:
                if(len(i) > columns_no):
                    columns_no = len(i)
            split_frame =  pandas.DataFrame(data_list,columns= [str(data_cat)] * (columns_no))
        else:
            split_frame =  pandas.DataFrame(data_list, columns= [str(data_cat)])

        new_frame = pandas.concat([new_frame, split_frame], axis= 1)
    return new_frame


pokemon_df = dataFrameReassembler(pokemon_df)
print("creating csv (Excel) file! Homestretch")
pokemon_df.to_csv("pokemon.csv")

