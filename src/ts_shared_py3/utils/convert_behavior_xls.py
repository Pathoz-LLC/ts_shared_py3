import os
import sys

# irritating that common.behavior.constants won't import without adding paths
PROJ_ROOT = "/Users/dgaedcke/dev/TouchstoneMicroservices"
sys.path.insert(0, PROJ_ROOT)
sys.path.insert(0, PROJ_ROOT + "/lib")


import yaml
from ts_shared_py3.config.behavior.beh_constants import (
    FEELING_ONLY_CODE_POS,
    FEELING_ONLY_CODE_NEG,
)


SOURCE_DATA_PATH = "/Users/dgaedcke/Downloads/yaml/"
DEBUG_MODE = True  # True  # False


# Dimensions replaced with impact weight
# in the behavior file;  this class NIU
# class Dimensions(object):
#     """ a static class to hold customization options for each
#         input file type
#     """
#     outFileName = 'behavior_map.yaml'
#     headerCount = 1
#     items = []
#
#     @classmethod
#     def loopFunc(cls, reader, debugMode):
#         cls.items = []   # init class var
#         print('Assuming {0} headers in {1}!'.format(cls.headerCount, cls.outFileName))
#         for i in range(0, cls.headerCount):
#             next(reader)  # skip headers
#
#         fourRows = []
#         for rowNum, line in enumerate(reader):
#             if debugMode:
#                 print( "Line #{0} in {1}".format(rowNum, cls.__name__) )
#             fourRows.append(line)
#             if len(fourRows) == 4:
#                 cls.makeYamlDict(fourRows)
#                 fourRows = []
#         return cls.items
#
#     @classmethod
#     def makeYamlDict( cls, fl):
#         item = {
#             'code': fl[0][0].strip(),
#             'respMin': int(fl[0][2]),
#             'respMax': int(fl[0][3]),
#             'commMin': int(fl[1][2]),
#             'commMax': int(fl[1][3]),
#             'trusMin': int(fl[2][2]),
#             'trusMax': int(fl[2][3]),
#             'lifeMin': int(fl[3][2]),
#             'lifeMax': int(fl[3][3]),
#             'frequencyNudge': 0.5  #float(fl[0][11])
#         }
#         cls.items.append(item)


class Behavior(object):
    """a static class to hold customization options for each
    input file type
    """

    outFileName = "behaviors.yaml"
    headerCount = 1
    items = []

    @classmethod
    def loopFunc(cls, reader, debugMode):
        cls.items = []  # init class var
        print("Assuming {0} headers in {1}!".format(cls.headerCount, cls.outFileName))
        for i in range(0, cls.headerCount):
            next(reader)  # skip headers

        for rowNum, line in enumerate(reader):
            if debugMode:
                print("Line #{0} in {1}".format(rowNum, cls.__name__))
            if line[0] != "":
                cls.makeYamlDict(line)
        return cls.items

    @classmethod
    def makeYamlDict(cls, ln):

        keywordsNoCommas = ln[4].replace(",", " ")
        keywords = [cleanKeyword(x) for x in keywordsNoCommas.split(" ") if len(x) > 2]
        keywords = list(set(keywords))
        sort = resolveIntWithDefault(ln[7], 18)
        # convert impact INT from 1-10 to 0-1 (float) and then
        # add 0.5 to make the effective range be 0.5<-->1.5
        # so behaviors with impact of 5 (mid-range) become 1 and
        # do not affect the math
        normalizedImpactWeight = int(ln[2])

        code = ln[0].strip()
        parentCode = ln[6].strip()
        if code in [FEELING_ONLY_CODE_POS, FEELING_ONLY_CODE_NEG]:
            parentCode = code

        text = convertToAscii(ln[1])
        item = {
            "code": code,
            "text": text,
            "impact": normalizedImpactWeight,
            "oppositeCode": ln[3],  # pierce added code of sibling here
            "sort": sort,
            "positive": bool(ln[5] == "1"),
            "parentCode": parentCode,
            "altCategories": [],  # altCategories,
            "keywords": keywords,
        }
        assert len(ln[6]) > 0, "every behavior must have a mainCategory"
        cls.items.append(item)


def cleanKeyword(x):
    return convertToAscii(x.strip())


def _defaultFeelingEntries():
    # category section
    posFeel = {
        "parentCode": "root",
        "code": FEELING_ONLY_CODE_POS,
        "text": "Positive Feeling",
        "positive": True,
        "sort": 0,
        "searchable": True,
        "keywords": "",
        "childrenSearchable": 0,
    }
    negFeel = {
        "parentCode": "root",
        "code": FEELING_ONLY_CODE_NEG,
        "text": "Negative Feeling",
        "positive": False,
        "sort": 0,
        "searchable": True,
        "keywords": "",
        "childrenSearchable": 0,
    }
    return [posFeel, negFeel]


class Categories(object):
    """parent,text,code,pos,order,keywords"""

    outFileName = "category.yaml"
    headerCount = 1
    # add feelings loopFunc as hidden invisible categories
    items = []

    @classmethod
    def loopFunc(cls, reader, debugMode):
        cls.items = _defaultFeelingEntries()  # init class var
        print("Assuming {0} headers in {1}!".format(cls.headerCount, cls.outFileName))
        for i in range(0, cls.headerCount):
            next(reader)  # skip headers

        for rowNum, line in enumerate(reader):
            if debugMode:
                print("Line #{0} in {1}".format(rowNum, cls.__name__))
            cls.makeYamlDict(line)
        return cls.items

    @classmethod
    def makeYamlDict(cls, ln):
        """ """
        text = convertToAscii(ln[2])
        parent = ln[0].strip()
        if len(ln) > 6:  # 6 == col 7
            keywords = ln[6].split()
        else:
            keywords = []

        sort = resolveIntWithDefault(ln[4], 15)
        searchable = resolveIntWithDefault(ln[5], 0)

        item = {
            "parentCode": parent if parent != "root" else "",
            "code": ln[1].strip(),
            "text": text,
            "positive": bool(ln[3] == "1"),
            "sort": sort,
            "searchable": searchable,
            "keywords": keywords if len(keywords) > 0 else "",
            "childrenSearchable": 0
            # , 'aliases': ''
        }
        cls.items.append(item)


def resolveIntWithDefault(val, deflt=0):
    if len(val) > 0:
        return int(val)
    else:
        return deflt


def convertToAscii(s):
    """added 11/22/17 by dg to handle pierce quotes & apostrophies"""
    return s.replace("\u2018", "'").replace("\u2019", "`")


class CsvToYaml(object):
    """master class to parse CSV & generate YAML"""

    def __init__(self, inFile, logicClass, copyPath):
        self.inFileName = inFile
        self.outFileName = logicClass.outFileName
        self.logicClass = logicClass
        self.items = []
        self.copyPath = copyPath
        # generated at runtime:
        # self.in
        # self.out

    def run(self):
        self.openFiles()
        self.readData()
        self.writeData()
        self.closeFiles()
        # try:
        #     self.openFiles()
        #     self.readData()
        #     self.writeData()
        # except IOError as err:
        #     print("IOError")
        #     print(err)
        # except ValueError as err:
        #     print("ValueError")
        #     print(err)
        # finally:
        #     self.closeFiles()

    def openFiles(self):
        # create file handles
        self.inFh = open(SOURCE_DATA_PATH + self.inFileName, "r")
        self.reader = unicodecsv.reader(self.inFh, encoding="utf-8", delimiter=",")
        # self.reader = csv.reader(self.inFh)
        self.outFh = open(self.copyPath + self.outFileName, "w")
        # try:
        #     self.inFh = open(TOP_PATH + self.inFileName, "r")
        #     self.outFh = open(TOP_PATH + self.outFileName, "w")
        # except IOError:
        #     print("file could not be open/created")
        #     raise IOError

    def readData(self):
        self.items = self.logicClass.loopFunc(self.reader, DEBUG_MODE)

    def writeData(self):
        self.outFh.write(
            yaml.safe_dump(self.items, default_flow_style=False, encoding="utf-8")
        )

    def closeFiles(self):
        self.inFh.close()
        self.outFh.close()


def instantiateSingletonAsTest():
    from common.behavior.dataLoading import BehaviorSourceSingleton

    masterObj = BehaviorSourceSingleton.loadAll()

    if DEBUG_MODE:
        masterDict = masterObj.masterDict
        # graph = masterObj.graph
        for key, behCatNode in masterDict.iteritems():
            head = "Category: " if behCatNode.isCategory else "BehText: "
            print(head + behCatNode.text)


# invocations to build the yaml files below
# location to copy files
projectPath = PROJ_ROOT + "/common/behavior/"

# dimensions = CsvToYaml('dimensions.csv', Dimensions, projectPath)
# dimensions.run()

behaviors = CsvToYaml("behaviors.csv", Behavior, projectPath)
behaviors.run()

categories = CsvToYaml("categories.csv", Categories, projectPath)
categories.run()

os.chdir(PROJ_ROOT)
# test to make certain all data lines up
# BehaviorSourceSingleton.loadAll() will throw errors if data misaligned
instantiateSingletonAsTest()
