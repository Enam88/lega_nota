import pandas as pd
from suds.client import Client
import pdfkit
from IPython.core.display import HTML
import re
from abydos.phonetic import FONEM, Phonet, Dolby, Phonem, PHONIC
import time
from abydos.distance import sim
import json
import requests
from pandas import json_normalize
import unicodedata
import phonetics
import xml.etree.ElementTree as et 



#remove accents function
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


#to do match queries without vowels
#vowels = r'[AEIOUÀÄÈÉÊÖÜ]'
def anti_vowel(s):
    """Remove vowels from string."""
    vowels = r'[AEIOUÀÄÈÉÊÖÜ]'
    result = re.sub(vowels, '', s, flags=re.IGNORECASE)
    return result


#string rotation
def vowel_rotate(string):
    """rotate vowels in query only if vowels exist"""
    results = []

    sub_function = lambda x: 'eiouaEIOUA'['aeiouAEIOU'.find(x.group(0))]

    for x in range(5):
        string = re.sub('(?i)[aeiou]', sub_function, string)
        results.append(string)
    return ",".join(results)

#
# query = input("Quelle marque souhaitez-vous chercher ? ")

def wsdl_connect(query):
    pe_fr = FONEM()
    pe_de = Phonet()
    db = Dolby()
    pe_gm = Phonem()
    pe_ph = PHONIC()
    url = 'https://www.swissreg.ch/services11/SwissregWebService?wsdl'
    client = Client(url, username='legalmarque', password='dvMXQsUzcIXEZMdAD6Ls')
    Ip_Right = client.service.searchIpRight("CH-TM", 'tmText' '=' f'{vowel_rotate(query)}{query} {anti_vowel(query)} {db.encode_alpha(query)} {pe_gm.encode(query)} {pe_fr.encode(query)} ')
    #use query result as input to generate both trademark & bname xml
    response = client.service.getIpRightXML("CH-TM", Ip_Right)

    return response


    
  

##Marque Visuelle
def retrieve_marque_visuelle(transac):
    """"""

    basappn = transac.find("basappn").text
    basregn = transac.find("basregn").text if transac.find("basregn") is not None else None
    marpicn = transac.find("marpicn").text
    

    
    # Classes
    gsgr = transac.find("gsgr")
    intreggs = gsgr.findall("intregg")

    classes = []

    for intregg in intreggs:
        
        nicclai = intregg.find("nicclai").text
        
        classes.append(int(nicclai))

    

    regadrs = transac.findall("regadr")
    
    # TODO check format of mandataire/titulaire
    titulaire_name = None
    titulaire_addrl = None
    titulaire_plainco = None
    titulaire_nat = None

    
    
    # Addresses
    for regadr in regadrs:
        
        addrrole = regadr.find("addrrole").text
        nameadd = regadr.find("nameadd")
        
        namel = nameadd.find("namel").text if nameadd.find("namel") is not None else None
        addrl = nameadd.find("addrl").text if nameadd.find("addrl") is not None else None
        
        plainco = nameadd.find("plainco").text
        nat = nameadd.find("nat").text
        
        # 1: titulaire
        if int(addrrole) == 1:
            titulaire_name = namel
            titulaire_addrl = addrl
            titulaire_plainco = plainco
            titulaire_nat = nat
        
        
        
    # TODO verify what oppositiongr and oppositionstate mean
    oppositiongr = transac.find("oppositiongr")
    oppositionstate = oppositiongr.find("oppositionstate")


    row = [basappn,basregn,marpicn,
           classes, 
           titulaire_name,
           titulaire_addrl,
           titulaire_plainco,
           titulaire_nat]
    
    return row

#Parse visuelle xml
def parse_xml_visuelle(response, encoding="utf-8"):
    
    rows = []
    
    # Parse file
    xtree = et.parse(response)
    xroot = xtree.getroot()

    for node in xroot:
        if node.tag == 'transac':
            for transac in node:
                if transac.tag == 'marinfo':
                    # Marques verbales
                    marpicn = transac.find("marpicn")
                    if marpicn is not None:
                        row = retrieve_marque_visuelle(transac)
                        rows.append(row)
    return rows


#Visual Data Cleaning and Preparation

#Merge, Rename and drop unused Columns
#display trademark logo in dataframe and convert to html
def to_img_tag(path):
    return '<img src="'+ path + '" width="80"  >'

def clean_marque_visuelle(xml_file_path):
    with open(xml_file_path, 'r') as xml_file:
        rows = parse_xml_visuelle(xml_file)
    tables = []
    tables.extend(rows)
    columns = ['basappn','basregn','marpicn', 
           'classes', 
           'titulaire_name',
           'titulaire_addrl',
           'titulaire_plainco',
           'titulaire_nat']
    
    df_visuelle = pd.DataFrame(tables, columns=columns)
    df_visuelle['titulaire'] = df_visuelle.titulaire_name.fillna('') + ' ' + df_visuelle.titulaire_addrl.fillna('') + ' ' + df_visuelle.titulaire_plainco.fillna('') + ' ' + df_visuelle.titulaire_nat.fillna('')
    df_visuelle.drop(['titulaire_name', 'titulaire_addrl', 'titulaire_plainco',
       'titulaire_nat'], axis=1, inplace=True)
    #old,new
    df_visuelle.rename(columns = {'classes':'Classes de Nice', 'basappn':'No de la demande', 'basregn':'No de la marque','basannd':'Depot', 'marpicn':'Logo' }, inplace = True)
    df_visuelle['titulaire'] = df_visuelle['titulaire'].apply(lambda x: remove_accents(x)).str.replace(r'\n', '', regex=True)
    df_visuelle['Classes de Nice'] = df_visuelle['Classes de Nice'].apply(lambda x: ','.join(map(str, x)))

    return df_visuelle



#Marque Verbal
def retrieve_marque_verbal(transac):
    """"""

    basappn = transac.find("basappn").text
    basregn = transac.find("basregn").text if transac.find("basregn") is not None else None
    markve = transac.find("markve").text
    

    
    # Classes
    gsgr = transac.find("gsgr")
    intreggs = gsgr.findall("intregg")

    classes = []

    for intregg in intreggs:
        
        nicclai = intregg.find("nicclai").text
        
        classes.append(int(nicclai))

    

    regadrs = transac.findall("regadr")
    
    # TODO check format of mandataire/titulaire
    titulaire_name = None
    titulaire_addrl = None
    titulaire_plainco = None
    titulaire_nat = None

    
    
    # Addresses
    for regadr in regadrs:
        
        addrrole = regadr.find("addrrole").text
        nameadd = regadr.find("nameadd")
        
        namel = nameadd.find("namel").text if nameadd.find("namel") is not None else None
        addrl = nameadd.find("addrl").text if nameadd.find("addrl") is not None else None
        
        plainco = nameadd.find("plainco").text
        nat = nameadd.find("nat").text
        
        # 1: titulaire
        if int(addrrole) == 1:
            titulaire_name = namel
            titulaire_addrl = addrl
            titulaire_plainco = plainco
            titulaire_nat = nat
        
        
        
    # TODO verify what oppositiongr and oppositionstate mean
    oppositiongr = transac.find("oppositiongr")
    oppositionstate = oppositiongr.find("oppositionstate")


    row = [basappn,basregn,markve,
           classes, 
           titulaire_name,
           titulaire_addrl,
           titulaire_plainco,
           titulaire_nat]
    
    return row


#Parse xml Verbal
def parse_xml_verbal(xml_file):
    
    rows = []
    
    # Parse file
    xtree = et.parse(xml_file)
    xroot = xtree.getroot()

    for node in xroot:
        if node.tag == 'transac':
            for transac in node:
                if transac.tag == 'marinfo':
                    # Marques verbales
                    markve = transac.find("markve")
                    if markve is not None:
                        row = retrieve_marque_verbal(transac)
                        rows.append(row)
    return rows

#Clean Marque Verbal
def clean_marque_verbal(xml_file_path):
    with open(xml_file_path, 'r') as xml_file:
        rows = parse_xml_verbal(xml_file)
    tables = []
    tables.extend(rows)
    columns = ['basappn','basregn','markve', 
           'classes', 
           'titulaire_name',
           'titulaire_addrl',
           'titulaire_plainco',
           'titulaire_nat']
    
    df = pd.DataFrame(tables, columns=columns)
    df['titulaire'] = df.titulaire_name.fillna('') + ' ' + df.titulaire_addrl.fillna('') + ' ' + df.titulaire_plainco.fillna('') + ' ' + df.titulaire_nat.fillna('')
    df.drop(['titulaire_name', 'titulaire_addrl', 'titulaire_plainco',
       'titulaire_nat'], axis=1, inplace=True)
    #old,new
    df.rename(columns = {'classes':'Classes de Nice', 'basappn':'No de la demande', 'basregn':'No de la marque','basannd':'Depot', 'markve':'marque' }, inplace = True)
    df['titulaire'] = df['titulaire'].apply(lambda x: remove_accents(x)).str.replace(r'\n', '', regex=True)
    df['Classes de Nice'] = df['Classes de Nice'].apply(lambda x: ','.join(map(str, x)))

    return df




#Marque_Commerce
#function to search for company name and return dataframe


def commmerce_name_search(query):

    username = "bs@legalmarque.com"
    password = "YbxnQ2rt"
    url = 'https://www.zefix.admin.ch/ZefixPublicREST/api/v1/company/search'


    #String Formatting
    post_json = (

    "{"  #first curly bracket
    "\"activeOnly\": true,"  #--> key, value begins and ends with \" except for bool
     f"\"name\": \"{query}\""
     "}" #last curly bracket
     
     )
    #convert formatted string to json
    payload = json.loads(post_json)

    #define headers
    headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
    }

    #post request using above params
    response = requests.post(url, 
                         headers=headers,
                         auth=(username, password), 
                         json=payload)
    
    if response.status_code == 200:
        commerce_search = response.json()
        df_commerce = json_normalize(commerce_search)

        #drop unwanted columns
        df_commerce.drop(['ehraid','chid', 'legalSeatId',
       'registryOfCommerceId', 'status', 'sogcDate', 'deletionDate',
       'legalForm.id', 'legalForm.uid', 'legalForm.name.de',
       'legalForm.name.fr', 'legalForm.name.it', 'legalForm.name.en',
       'legalForm.shortName.de',
       'legalForm.shortName.it', 'legalForm.shortName.en'], axis=1, inplace=True)
        
        #rename cols with new names
        df_commerce[['Marque', 'IDE', 'Siege', 'Forme']] = df_commerce[['name', 'uid','legalSeat','legalForm.shortName.fr']]

        #drop old names
        df_commerce.drop(["name", "uid", "legalSeat", "legalForm.shortName.fr"], axis=1, inplace=True)
        
        df_commerce['Siege'] = df_commerce['Siege'].apply(lambda x: remove_accents(x))
        df_commerce['Marque'] = df_commerce['Marque'].apply(lambda x: remove_accents(x))
        df_commerce['Forme'] = df_commerce['Forme'].apply(lambda x: remove_accents(x))

        return df_commerce



        
        

