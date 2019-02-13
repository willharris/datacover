#!/usr/bin/env python3
import re

from collections import defaultdict
from lxml import html

import demjson
import requests


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
        if "Global+" in region["data"]:
            coverage[region["value"]].append("Qynamic Global+")
        elif "Global" in region["data"]:
            coverage[region["value"]].append("Qynamic Global")
        else:
            coverage[region["value"]]


def do_mtx(coverage):
    name = "MTX"
    url = "https://www.mtxc.eu/en/coverage.html"
    datafile = "data_mtx"

    data = _get_data(name, url, datafile)
    tree = html.fromstring(data)

    # regions = list(map(lambda x: x.strip(), tree.xpath("//ul[@class='country_list']/li/a/text()[normalize-space() != '']")))
    regions = []
    for node in tree.xpath("//ul[@class='country_list']/li/a"):
        regions.append(' '.join(map(lambda x: x.strip(), node.xpath("text()[normalize-space() != '']"))))

    for region in regions:
        if region[-1] == "*":
            coverage[region[:-1]].append("MTX*")
        else:
            coverage[region].append("MTX")


def write_output(coverage):
    outfile = "coverage.csv"

    with open(outfile, "wb") as output:
        for region, opts in sorted(coverage.items()):
            optstr = ','.join(map(lambda x: f'"{x}"', opts))
            output.write(f"\"{region}\",{optstr}\n".encode("iso-8859-1"))

    print(f"Wrote coverage data to '{outfile}")


def main():
    coverage = defaultdict(lambda: [])

    do_qynamic(coverage)
    do_mtx(coverage)
    write_output(coverage)

if __name__ == "__main__":
    main()
