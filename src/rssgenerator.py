#!/usr/bin/env python
#encoding:UTF-8
"""
    print node.toxml()
"""
import datetime
import PyRSS2Gen

rss = PyRSS2Gen.RSS2(
    title = "Explora",
    link = "http://www.hrt.hr/index.php?id=439&tx_ttnews[tt_news]=61157&tx_ttnews[backPid]=438&cHash=a5054a7c72",
    description = u"Radio Pula - Explora"
                  u"Kontakt emisija u kojoj se \"bez dlake na jeziku\" analiziraju povijesne zagonetke, neobjašnjeni fenomeni, trendovi razvoja znanosti i tehnologije, sve u kontekstu razvoja ljudskog društva. ",

    lastBuildDate = datetime.datetime.now(),

    items = [
       PyRSS2Gen.RSSItem(
         title = "EXPLORA 21.09.",
         link = "http://rnz.hrt.hr/view_file.php?dat_id=42291",
         description = "Dalke Scientific today announced PyRSS2Gen-0.0, "
                       "a library for generating RSS feeds for Python.  ",
         guid = PyRSS2Gen.Guid("http://rnz.hrt.hr/view_file.php?dat_id=42291"),
         pubDate = datetime.datetime.strptime("21.09.2010","%d.%m.%Y")),
    ])

rss.write_xml(open("explora.xml", "w"))
