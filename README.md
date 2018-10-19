# scraper_simplyfeu
A python script scraper

This scraper collects the price of one pallet, two pallets and the volume in kg for one pallet depending on the postal code

The script seeks this article:
https://www.simplyfeu.com/shop/product/granules-de-bois-pellet-dinplus-enplus-174

Parameters are:

-i, --input:		    path to the file containing postal codes

-o, --output:		    path to the result

-f, --format:		    format for the result. json, csv (csv by default)

-d, --debug:		    print the informations collected and the execution time for each step

-b, --progress_bar:	add a progress bar
