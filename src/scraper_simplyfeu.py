#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from tqdm import tqdm
import pandas as pd
import numpy as np
import argparse
import time
import json
import os
  
def click(browser, button_selector):
    time.sleep(1)
    browser.find_element_by_css_selector(button_selector).click()

def fill_input(browser, input_selector, value):
    
    time.sleep(1)
    entry = browser.find_element_by_css_selector(input_selector)
    entry.clear()
    entry.send_keys(value)
    
def try_click(browser, button_selector):
    try:
        time.sleep(1)
        browser.find_element_by_css_selector(button_selector).click()
        return False
    except:
        return True

def print_infos(begin, code_postal, volume_p, prix_1p, prix_2p):
    print("code postal: " + code_postal)
    print("prix d'une palette: " + prix_1p)
    print("prix de 2 palettes: " + prix_2p)
    print("poids en kg d'une palette: " + volume_p)
    end = time.time()
    print("temps: " + str(end - begin) + " secondes\n")

def error(browser, code_postal, debug, begin):
    url = "https://www.simplyfeu.com/shop/product/granules-de-bois-pellet-dinplus-enplus-174"
    browser.get(url)
    if debug:
        print("Code postal " + code_postal + " non trouve")
        nan = str(np.nan)
        print_infos(begin, code_postal, nan, nan, nan)
        
    return np.nan, np.nan, np.nan
    
def get_infos(browser, code_postal, debug):
    
    if debug:
        begin = time.time()
        
    url = browser.current_url + "?target=StoreLocator"
    browser.get(url)
    time.sleep(1)
    
    #Choose postal code
    fill_input(browser, "div#divInputZipOverlay input", code_postal)
    click(browser, "div#divCheckZipCountryStoreLoc")
    
    #Test if the postal code exists
    message = browser.find_element_by_css_selector("div#divErreur").text
    if message == "Le code postal n'existe pas":
        return error(browser, code_postal, debug, begin)
    
    while try_click(browser, "button.bselect-caret"):
        time.sleep(1)
        
    fill_input(browser, "input.bselect-search-input", code_postal[:2])
    
    message = browser.find_element_by_css_selector("div.bselect-message").text
    if message == "No options available.":
        return error(browser, code_postal, debug, begin)
        
        
    #Validate postal code
    time.sleep(1)
    click(browser, "div.col-xs-12.col-sm-push-8.col-sm-4 button")

    #Add one pallet
    while try_click(browser, 'a.mb8.input-group-addon.float_left.js_add_cart_json[alt="Plus"]'):
        time.sleep(1)
        
    #Get prix_1p
    price_sel = "span.oe_currency_value"
    prix_1p = browser.find_elements_by_css_selector(price_sel)[2].text.replace(',', '.')
         
    #Get prix_2p
    total_sel = "span#sf_total_price"
    time.sleep(1)
    prix_2p = browser.find_element_by_css_selector(total_sel).text.replace(',', '.')
     
    #Get volume_p
    try:
        volume_sel = "tbody tr:nth-child(15) td:nth-child(5)"
        volume_p = browser.find_element_by_css_selector(volume_sel).text.replace(',', '.')
    except:
        volume_sel = "tbody tr:nth-child(14) td:nth-child(2)"
        text = browser.find_element_by_css_selector(volume_sel).text
        volume_p = ""
        for char in text:
            if char.isdigit():
                volume_p += char
            else:
                break
    
    if debug:
        print_infos(begin, code_postal, volume_p, prix_1p, prix_2p)        
    
    return prix_1p, prix_2p, volume_p
    
def scraper_simplyfeu(codes_postaux, debug, progress_bar):
    
    #Open the browser
    browser =  webdriver.Firefox()
    
    #Connect to the url
    url = "https://www.simplyfeu.com/shop/product/granules-de-bois-pellet-dinplus-enplus-174"
    browser.get(url)
    
    lst = list()
    
    #Use a progression bar
    if progress_bar:
        for code_postal in tqdm(codes_postaux["codes_postaux"].tolist(), desc = "codes postaux"):
            lst.append(get_infos(browser, code_postal[:3] + "00", debug))
    else:
        for code_postal in codes_postaux["codes_postaux"].tolist():
            lst.append(get_infos(browser, code_postal[:3] + "00", debug))

    browser.quit()
    
    #Extract values from the list
    prix_1p = [element[0] for element in lst]
    prix_2p = [element[1] for element in lst]
    volume_p = [element[2] for element in lst]

    return prix_1p, prix_2p, volume_p

def main():
    
    #Save begining time to compute execution time
    begin = time.time()
    
    #Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="chemin du fichier contenant les codes postaux", type=str, required = True)
    parser.add_argument("-o", "--output", help="chemin du fichier de sortie", type=str, nargs='?', default='.')
    parser.add_argument("-f", "--format", help="format de sortie", type=str, nargs='*', choices = ['csv', 'json'], default = ['csv'])
    parser.add_argument("-d", "--debug", help="active le mode debug", action='store_true')
    parser.add_argument("-b", "--progress_bar", help="active la bar de progression", action='store_true')
    args = parser.parse_args()
    
    #Check input
    if not os.path.isfile(args.input):
        print("erreur: l'input spécifié n'est pas un fichier\n")
        parser.print_help()
        return
    
    #Check output
    if not os.path.isdir(args.output):
        print("erreur: l'output spécifié n'est pas un chemin valide\n")
        parser.print_help()
        return

    #Get postal codes        
    codes_postaux = pd.read_csv(args.input, index_col = False, header = None, names = ["codes_postaux"], converters = {"codes_postaux" : str})
        
    prix_1p, prix_2p, volume_p = scraper_simplyfeu(codes_postaux, args.debug, args.progress_bar)
    
    #Create a csv file
    if 'csv' in args.format:
        df = pd.DataFrame({"code_postal" : codes_postaux["codes_postaux"].tolist(), "volume_p" : volume_p, "prix_1p" : prix_1p, "prix_2p" : prix_2p})
        df["volume_p"] = df["volume_p"].apply(float)
        df["prix_1p"] = df["prix_1p"].apply(float)
        df["prix_2p"] = df["prix_2p"].apply(float)
        df.to_csv(os.path.join(args.output, "scraping_simplyfeu.csv"), index = False, encoding="utf-8", decimal='.')
        print("scraping_simplyfeu.csv a ete cree dans " + args.output)
        
    #Create a json file   
    if 'json' in args.format:
        jsn = [{"code_postal" : code_postal, "volume_p" : vol_p, "prix_1p" : prx_1p, "prix_2p" : prx_2p} for code_postal, vol_p, prx_1p, prx_2p in zip(codes_postaux["codes_postaux"].tolist(), volume_p, prix_1p, prix_2p)]
        with open(os.path.join(args.output, 'scraping_simplyfeu.json'), 'w', encoding = "utf-8") as outfile:
            json.dump(str(jsn), outfile)
        print("scraping_simplyfeu.json a ete cree dans " + args.output)
    
    #Print execution time
    if args.debug:
        end = time.time()
        print("Temps d'execution: " + str(end - begin) + " secondes")

if __name__ == '__main__':
    main()
