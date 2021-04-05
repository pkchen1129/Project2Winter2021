#################################
##### Name: Po-Kang Chen
##### Uniqname: pkchen
#################################

from bs4 import BeautifulSoup
import requests
import json
import os.path
import secrets # file that contains your API key


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, name, category, address, zipcode, phone):
        self.category = category or ""
        self.name = name or ""
        self.address = address or ""
        self.zipcode = zipcode or ""
        self.phone = phone or ""
    def info(self):
        s = self.name + ' (' + self.category + '): ' + self.address + ' ' + self.zipcode
        return s

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    dict = {}
    # Check if file exists
    if os.path.isfile('./cache/state_list.html'):
        print ("Using cache")
    else:
        print ("Fetching")
        # Requires and download html from website
        r = requests.get("https://www.nps.gov", allow_redirects=True)
        open('./cache/state_list.html', 'wb').write(r.content)
    
    # Open the html file and create soup
    f = open("./cache/state_list.html")
    html_text = f.read()
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Using Find and place items in dictionary
    all_state_list = soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    state_list = all_state_list.find_all('li')
    for item in state_list:
        key = item.find('a').contents[0].lower()
        val = item.find('a', href=True)['href']
        dict[key] = "https://www.nps.gov" + val
    return dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''

    site_html = "./cache/site_" + site_url[20:24] + ".html"
    if os.path.isfile(site_html):
            print ("Using cache")
    else:
        print ("Fetching")
        # Requires and download html from website
        r = requests.get(site_url, allow_redirects=True)
        open(site_html, 'wb').write(r.content)
    
    # Open the html file and create soup
    f = open(site_html)
    html_text = f.read()
    soup = BeautifulSoup(html_text, 'html.parser')
    name = soup.find(class_="Hero-titleContainer clearfix").find('a').text
    try:
        category = soup.find(class_="Hero-designation").text.strip()
    except:
        category = "no Category"
    
    try:
        phone = soup.find(class_="tel").text.strip()
    except:
        phone = "no phone"
    
    try:
        address = soup.find(class_="adr").find(itemprop="addressLocality").text + ', ' + soup.find(class_="adr").find(itemprop="addressRegion").text.strip()
    except:
        address = "no address"
    
    try:
        zipcode = soup.find(class_="adr").find(itemprop="postalCode").text.strip()
    except:
        zipcode = "no zipcode"
    
    # Construct instance
    # name, category, address, zipcode, phone
    instance = NationalSite(name, category, address, zipcode, phone)
    # print(instance.info())

    return instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    site_list = []
    site_html_state = "./cache/state_" + state_url[26:28] + ".html"
    if os.path.isfile(site_html_state):
            print ("Using cache")
    else:
        print ("Fetching")
        # Requires and download html from website
        r = requests.get(state_url, allow_redirects=True)
        open(site_html_state, 'wb').write(r.content)
        
    # Open the html file and create soup
    f = open(site_html_state)
    html_text = f.read()
    soup = BeautifulSoup(html_text, 'html.parser')
    park_list = soup.find(id ='list_parks')
    for item in park_list:
        if (item.find('h2') == -1):
            continue
        site_code = item.find('h3').find('a', href=True)['href']
        site_url = "https://www.nps.gov" + site_code + "index.htm"
        site_list.append(get_site_instance(site_url))
    return site_list
    


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    key = secrets.API_KEY
    origin = site_object.zipcode
    radius = 10
    maxMatches = 10
    ambiguities = "ignore"
    outFormat = "json"

    # https://www.mapquestapi.com/search/v2/radius?origin=Denver,+CO&radius=0.15&maxMatches=3&ambiguities=ignore&hostedData=mqap.ntpois|group_sic_code=?|581208&outFormat=json&key=KEY
    # http://www.mapquestapi.com/search/v2/radius?key=KEY&maxMatches=4&origin=39.750307,-104.999472

    # https://www.mapquestapi.com/search/v2/radius?

    url = "http://www.mapquestapi.com/search/v2/radius?origin=" + str(origin) + "&radius=" + str(radius) + "&maxMatches=" + str(maxMatches) + "&ambiguities=" + str(ambiguities) + "&outFormat=" + str(outFormat) + "&key=" + str(key)
    file_name = "./cache/" + str(origin) + ".json"
    
    
    try:
        cache_file = open(file_name, 'r')
        cache_contents = cache_file.read()
        Results_Dictionary = json.loads(cache_contents)
        print("Using Cache")
        cache_file.close()
    except:
        print("Fetching")
        response = requests.get(url)
        Results_Dictionary = json.loads(response.text)
        dumped_json_cache = json.dumps(Results_Dictionary,sort_keys=True, indent=4)
        fw = open(file_name,"w")
        fw.write(dumped_json_cache)
        fw.close() 
    dict = Results_Dictionary
    return dict
if __name__ == "__main__":

    while True:
        # print List of national sites
        state_name = input("Enter a state name (e.g. Michigan, michigan) or \"exit\": ")
        dict = build_state_url_dict() 
        if state_name == "exit":
            exit()
        try:
            state_url = dict[state_name.lower()]
        except:
            print("[Error] Enter proper state name")
            continue
        site_list = []
        site_list = get_sites_for_state(state_url)
        print("-------------------------------------")
        print("List of national sites in ",state_name)
        print("-------------------------------------")
        for i in range(len(site_list)):
            s = site_list[i].info()
            print_str = "[" + str(i+1) + "] " + s
            print(print_str)
        
        # print list of nearby place
        while True:
            number = input("Choose the number for detail search or \"exit\" or \"back\": ")
            if number == "exit":
                exit()
            elif number == "back":
                break
            elif number.isdigit() and int(number) < len(site_list) and int(number) > 0:
                number = int(number)
                instance = site_list[number-1]
                Result_dict = get_nearby_places(instance)
                # Print Result_dict
                print("------------------------------")
                print("Places near",instance.name)
                print("------------------------------")
                for item in Result_dict["searchResults"]:
                    name = item["fields"]["name"] or "no name"
                    category = item["fields"]["group_sic_code_name"] or "no category"
                    address = item["fields"]["address"] or "no address"
                    city = item["fields"]["city"] or "no city"
                    print_str = "- " + name + " (" + category + "): " + address + ", " + city
                    print(print_str)
            else: 
                print("[Error] Invalid input")
                continue
        
        continue