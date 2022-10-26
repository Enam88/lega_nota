#Domain Availability
from domainavailability import *
import pandas as pd
def domain_name_checker(query):
    
    client = Client('at_kvQSqHPLS7IgXJQiRdDA0o1ePSNBv')

    raw_result_ch = client.raw_data(
    f'{query}' + '.ch',
    mode=Client.DNS_AND_WHOIS_MODE,
    credits_type=Client.WHOIS_CREDITS,
    output_format=Client.XML_FORMAT)

    #time.sleep(1)

    raw_result_swiss = client.raw_data(
    f'{query}' + '.swiss',
    mode=Client.DNS_AND_WHOIS_MODE,
    credits_type=Client.WHOIS_CREDITS,
    output_format=Client.XML_FORMAT)

    df_ch = pd.read_xml(raw_result_ch)
    df_swiss = pd.read_xml(raw_result_swiss)

    frames = [df_ch, df_swiss]
    df_domain = pd.concat(frames, ignore_index=True)

    for i in df_domain['domainAvailability']:
        if i == "AVAILABLE":
            df_domain['domainAvailability'].replace(i, 'Disponible', inplace=True)
        else:
            df_domain['domainAvailability'].replace(i, 'Pas Disponible', inplace=True)
            
    return df_domain
        
        

