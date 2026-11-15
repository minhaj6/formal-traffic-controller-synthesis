#!/bin/sh
# Download one hour of high-resolution controller events for UDOT signal 7185
# (17 Oct 2017, 17:00-18:00) from the ATSPM repository's unit-test data and
# convert it to CSV: timestamp,code,param  (Indiana enumerations).
set -eu
commit=cfc01e88e513190403f8c9dce479257cf8d1577a
url=https://raw.githubusercontent.com/udotdevelopment/ATSPM/$commit/MOE.CommonTests/XMLDataFiles
cd "$(dirname "$0")"
curl -fsSL "$url/EventLogFiles/7185_10_17_2017.xml" | python3 -c '
import sys, xml.etree.ElementTree as ET
rows = sorted((e.findtext("timestamp"), int(e.findtext("EventCode")), int(e.findtext("EventParam")))
              for e in ET.parse(sys.stdin).getroot())
print("timestamp,code,param")
for row in rows:
    print(*row, sep=",")
' > events.csv
curl -fsSL "$url/Approaches/approachesfor7185.xml" -o approaches.xml
