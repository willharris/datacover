#!/usr/bin/env python3
import argparse
import html
import re

from collections import defaultdict
from lxml import html as xmlhtml

import demjson
import requests

from unidecode import unidecode


def _get_data(name, url, datafile):
    try:
        with open(datafile, "rb") as infile:
            data = infile.read().decode("utf8")
        print(f"{name} data loaded from file '{datafile}'")
    except:
        data = requests.get(url).text
        with open(datafile, "wb") as outfile:
            outfile.write(data.encode("utf8"))
        print(f"{name} data loaded from url '{url}' and written to file '{datafile}'")
    
    return data


def do_qynamic(coverage):
    name = "Qynamic"
    url = "https://www.qynamic.com/zones/"
    datafile = "data_qynamic" 

    data = _get_data(name, url, datafile)

    regions = re.search(r"var regions = (\[.+?\]);", data).group(1)
    regions = demjson.decode(regions)

    for region in regions:
        name = unidecode(html.unescape(region["value"]))
        try:
            code = re.search(r"(..)\.png", region["flag"]).group(1)
        except:
            code = None
        key = code or name
        if "Global+" in region["data"]:
            coverage[key]["list"].append("Qynamic Global+")
        elif "Global" in region["data"]:
            coverage[key]["list"].append("Qynamic Global")

        if not coverage[key]["name"]:
            coverage[key]["name"] = name


def do_mtx(coverage):
    name = "MTX"
    url = "https://www.mtxc.eu/en/coverage.html"
    datafile = "data_mtx"

    data = _get_data(name, url, datafile)
    tree = xmlhtml.fromstring(data)

    # regions = list(map(lambda x: x.strip(), tree.xpath("//ul[@class='country_list']/li/a/text()[normalize-space() != '']")))
    regions = []
    for node in tree.xpath("//ul[@class='country_list']/li/a"):
        name = unidecode(html.unescape(' '.join(map(lambda x: x.strip(), node.xpath("text()[normalize-space() != '']")))))
        code = node.attrib["id"].lower() or name
        regions.append((code, name))

    for code, name in regions:
        if name[-1] == "*":
            coverage[code]["list"].append("MTX*")
            if not coverage[code]["name"]:
                coverage[code]["name"] = name[:-1]
        else:
            coverage[code]["list"].append("MTX")
            if not coverage[code]["name"]:
                coverage[code]["name"] = name


def write_output(coverage, all_countries):
    outfile = "coverage.csv"

    with open(outfile, "wb") as output:
        for code, data in sorted(coverage.items(), key=lambda kv: kv[1]["name"]):
            if data["list"] or all_countries:
                optstr = ','.join(map(lambda x: f'"{x}"', data["list"]))
                output.write(f"\"{data['name']}\",{optstr}\n".encode("iso-8859-1", "replace"))

    print(f"Wrote coverage data to '{outfile}")


def main(all_countries):
    coverage = defaultdict(lambda: {'name': '', 'list': []})

    do_qynamic(coverage)
    do_mtx(coverage)
    write_output(coverage, all_countries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a CSV showing data roaming coverage.")
    parser.add_argument("-a", "--all", action="store_true",
                        help="show all listed countries, even if no coverage is reported")
    args = parser.parse_args()

    main(args.all)
