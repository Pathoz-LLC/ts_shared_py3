"""
client/app api for the behavioral recording feature:

List level:
    getTopLevel()
    getChildrenOf(categoryName)
    searchByKeyword()
future..?
    findRelatedQuestions()

Behavior level:
    incrementUsageCount()
    recordAnEvent()
    shareEvent()
"""
from __future__ import annotations
from typing import Callable, Tuple, Dict, Any, List
import random
import yaml
import json  # dumps( {} ) turns dict into string

# from pathlib import Path
# import inspect
from dataclasses import dataclass
from marshmallow.fields import Number
import logging
from importlib.resources import files, as_file
import importlib.resources as ilr


#
from ...constants import (
    APP_IMPACT_WEIGHT_MAX,
    IMPACT_WEIGHT_DECIMALS,
    FEELING_CD_PREFIX,
)

from ts_shared_py3.api_data_classes.behavior import FullBehaviorListMsg, NodeListMsg
from ...utils.singleton import Singleton
from .beh_constants import (
    SHOWALL_CAT_LABEL,
    SHOWALL_CODE_PREFIX,
    FEELING_ONLY_CODE_POS,
    FEELING_ONLY_CODE_NEG,
)

# usage:
# from common.config.behavior.load_yaml import BehaviorSourceSingleton

# normalize both Behaviors & Categories into BehaviorCatNode before sending to the client


def forRowInYaml(fileName: str, funcToRun: Callable) -> list[BehCatNode]:
    """process yaml file using passed function"""
    yamlRows = []

    # inspFile = inspect.getfile(inspect.currentframe())

    # pHome = Path.home()
    # p = Path(__file__).with_name(fileName)
    # pa: Path = Path(__file__).absolute()
    # res: Path = Path().resolve()
    # cwd: Path = Path().cwd()
    # logging.warn("forRowInYaml")
    # # logging.warn("file: {0}".format(__file__))
    # logging.warn("pHome: {0}".format(pHome.as_posix()))
    # logging.warn("pPosx: {0}".format(p.as_posix()))
    # # logging.warn("absolute: {0}".format(pa.as_posix()))
    # logging.warn("res: {0}".format(res.as_posix()))
    # logging.warn("cwd: {0}".format(cwd.as_posix()))
    # f = importlib.resources.read_text(__package__, fileName)
    # with p.open("r") as f:
    # with open(os.path.join(sys.path[0], fileName), "r") as f:
    #
    # path = ilr.Resource()
    # trav: ilr.Traversable = ilr.files(__package__)
    # f = trav.open(fileName, mode="r")

    source: ilr.Traversable = files(__package__).joinpath(fileName)  # PosixPath
    f = source.open(mode="r")
    # with open(source) as f:
    try:
        yamlRows = yaml.load(f, Loader=yaml.FullLoader)
        # yamlRows = fileAsDict.get('questions')
    except yaml.YAMLError as exc:
        print(exc)
        raise

    # print('yamlRows:')
    # print(yamlRows)
    results = []
    for rec in yamlRows:
        results.append(funcToRun(rec))
    return results


@dataclass
class BehCatNode(object):

    code: str
    parentCode: str
    text: str
    keywords: str
    sort: int
    positive: bool
    childrenSearchable: bool
    isCategory: bool
    impact: float
    aliases: str
    altCategories: str
    oppositeCode: str

    def __init__(self: BehCatNode) -> None:
        pass

    @staticmethod
    def yamlToBcn(isCategory: bool, row: Dict[str, Any]) -> BehCatNode:
        """BIG WARNING HERE
            our YAML files deliver Bool true or false

        row == yamlDict
        isCategory == Bool
        set common fields first
        data cleanup funcs
        """

        validateInt = BehCatNode.validateInt

        bcn = BehCatNode()
        # print(row.get('code'))
        bcn.code = row.get("code")
        # parentCode is name for (parent, mainCategory)
        bcn.parentCode = row.get("parentCode", "")
        text = row.get("text")
        # if isinstance(text, unicode):
        #     text = text.encode("utf8")
        # print("unicode", text, bcn.code)
        assert text, "behavior %s is missing text" % (bcn.code)

        bcn.text = text  # BehCatNode.normalizeText( text )
        # keywords can come from yaml as EITHER list or empty string
        kw = row.get("keywords", "")
        bcn.keywords = kw
        bcn.sort = validateInt(row.get("sort", 10))
        bcn.positive = row.get("positive", False)  # == "true"
        bcn.childrenSearchable = validateInt(row.get("childrenSearchable", 0))
        bcn.isCategory = isCategory  # 1 if isCategory else 0    # client wants string

        # these are mid-range INT impact vals on scale of 1 to 8
        # range is 9 to leave room for user-slider position making things better/worse
        impactOn1To9Scale = row.get("impact", 1)
        impactOn1To9Scale *= 1 if bcn.positive else -1
        bcn.impact = round(
            float(impactOn1To9Scale) / float(APP_IMPACT_WEIGHT_MAX),
            IMPACT_WEIGHT_DECIMALS,
        )
        # if bcn.code == 'conversationDeepPos':
        #     print('conversationDeepPos %s:%s' % (bcn.impact, impactOn1To9Scale) )
        # print(bcn.code, bcn.text)
        assert bcn.code, "every BCN MUST have a unique code (%s)" % (bcn.code)
        bcn.topCategoryCode = ""  # will be set later after master dict is build
        bcn.parentDescription = ""  # will be set later after master dict is built

        # Note: JSON converter (toDict()) requires all objs to have same fields
        if isCategory:
            bcn.childrenSearchable = False

            aliasStr = row.get("aliases", "")
            if aliasStr and aliasStr != "" and len(aliasStr) > 4:
                bcn.aliases = aliasStr.split(",")
            else:
                bcn.aliases = []
            bcn.altCategories = ""
            bcn.oppositeCode = ""
        else:  # a behavior
            bcn.childrenSearchable = False
            bcn.altCategories = row.get("altCategories", [])
            bcn.oppositeCode = row.get("oppositeCode")
            bcn.aliases = []

            assert bcn.parentCode, "every Behavior MUST have a parentCode: {0}".format(
                bcn.parentCode
            )
            assert bcn.oppositeCode, "every Behavior MUST have an oppositeCode code"

        if isinstance(bcn.keywords, list):
            if len(bcn.keywords) > 0:
                # delimit all words & phrases with comma to keep separate
                bcn.keywords = ",".join(bcn.keywords)
            else:
                bcn.keywords = ""
        # keywords must be string when we exit this function
        return bcn

    def inheritParentVals(self: BehCatNode, masterDict: Dict[str, Any]):
        # only call this for leaf nodes (non categories)
        dirParentAkaSubcat = masterDict.get(self.parentCode)
        if dirParentAkaSubcat is None:
            if self.parentCode.startswith("hidden"):
                self.topCategoryCode = self.parentCode
                self.parentDescription = self.parentCode
                return
            # print(self.parentCode)
            assert False, "no subcat exists for {0}".format(self.parentCode)
        topCat = masterDict.get(dirParentAkaSubcat.parentCode)
        if topCat is None:
            print(
                "err: subCat could not find it's parentCat using:"
                + dirParentAkaSubcat.parentCode
            )
            return
        # update recs
        dirParentAkaSubcat.topCategoryCode = topCat.code
        dirParentAkaSubcat.parentDescription = topCat.text
        self.topCategoryCode = topCat.code
        self.parentDescription = dirParentAkaSubcat.text

        # recursive walk up does not look right??
        # parentCatRec = categoriesDict.get(self.parentCode)
        # if parentCatRec:  # found subcat, now find its parent (ie root) category
        #     parentCatRec.inheritParentVals(categoriesDict)

    @property
    def isFeelingReport(self: BehCatNode) -> bool:
        return self.code.startswith(FEELING_CD_PREFIX)

    @property
    def iconName(self: BehCatNode) -> str:
        # only applies to category entries
        if not self.isCategory:
            return ""
        return "bc_" + self.code.replace("Neg", "Pos")  # .replace("Pos","")

    @property
    def categoryName(self: BehCatNode) -> str:
        # NIU & not tested
        return BehaviorSourceSingleton().catNameFromCode(self.topCategoryCode)

    def __str__(self: BehCatNode) -> str:
        return "Bcn:{0}  parent:{1}   impact:{2}".format(
            self.code, self.parentCode, self.impact
        )

    @staticmethod
    def validateInt(val: Number) -> int:
        return int(val)

    @property
    def asDict(self: BehCatNode) -> Dict[str, Any]:
        return dict(
            code=self.code,
            parentCode=self.parentCode,
            text=self.text,
            catCode=self.topCategoryCode,
            pos=self.positive,
            parentDescription=self.parentDescription,
            impact=self.impact,
        )

    def toMsg(self):
        # convert rec to a client msg
        from ...api_data_classes.behavior import BehOrCatMsg

        return BehOrCatMsg(
            code=self.code,
            parentCode=self.parentCode,
            catCode=self.topCategoryCode,
            oppositeCode=self.oppositeCode,
            text=self.text,
            catDescription=self.parentDescription,
            isCategory=self.isCategory,
            isPositive=self.positive,
            sort=self.sort,
            keywords=self.keywords,
        )

    # def toDict(self):
    #     # do NOT change this:  client expects these in exact order
    #     return [self.code, self.text, self.sort, self.keywords, self.positive, self.childrenSearchable, self.isCategory, self.parentCode, self.oppositeCode, self.parentDescription]

    @staticmethod
    def make(
        isCategory: bool,
        code: str,
        text: str,
        parentCode: str,
        isPositive: bool,
        oppositeCode: str,
    ) -> BehCatNode:
        """FYI
        our YAML files deliver Bool lc true or false
        """
        bcn = BehCatNode()
        bcn.isCategory = isCategory  # 1 if isCategory else 0
        bcn.code = code
        bcn.parentCode = parentCode
        bcn.oppositeCode = oppositeCode
        bcn.text = text
        bcn.impact = float(0)  # float(1.0)/float(9.0)
        bcn.positive = isPositive  # 1 if isPositive else 0
        bcn.sort = 100
        bcn.keywords = ""
        bcn.childrenSearchable = 0
        bcn.topCategoryCode = "hiddenPos" if isPositive else "hiddenNeg"
        bcn.parentDescription = (
            "Feelings"  # category name for the feeling only behaviors
        )
        return bcn


def finalKeywordsList(
    behKeywordsLst: list[str], catKeywordsLst: list[str], theText: str
) -> list[str]:
    # all keywords come in as string of words; return a list
    # print("behKeywordsLst:", type(behKeywordsLst))
    # print("catKeywordsLst:", type(catKeywordsLst))
    # print("theText:", type(theText))

    textWordsList = theText.lower().split(" ")
    bkl = behKeywordsLst.lower().split(",")  # [w.lower() for w in behKeywordsLst]
    ckl = catKeywordsLst.lower().split(",")  # [w.lower() for w in catKeywordsLst]
    dedupSet = set(bkl + ckl + textWordsList)  # remove dups
    # return removeStopWords(list(dedupSet))  # list in/out
    return list(dedupSet)


def inheritCategoryDescripToBehKeywords(
    behaviorsDict: Dict[str, Any], categoriesDict: Dict[str, Any]
) -> None:
    """combine keywords, dedup, lowercase & remove punctuation from search words"""
    # print("categoriesDict:")
    # print(categoriesDict)

    for _cd, beh in behaviorsDict.items():
        theSubCat: str = categoriesDict.get(beh.parentCode)
        if theSubCat:
            keywordList = finalKeywordsList(beh.keywords, theSubCat.keywords, beh.text)

            rootCat = categoriesDict.get(theSubCat.parentCode)
            if rootCat:  # add category name to keywords
                keywordList.append(rootCat.text.lower())

        elif beh.parentCode.startswith("hidden"):
            keywordList = finalKeywordsList(beh.keywords, "", beh.text)
        else:
            assert (
                theSubCat
            ), 'behavior {0} contains parentCode "{1}" but no such category exists in cat-list'.format(
                beh.code, beh.parentCode
            )

        # convert list back to string delimited by * for discrete search
        keywords: str = "*" + "*".join(keywordList)
        # keywords.translate(None, string.punctuation)
        keywords = keywords.replace("**", "*")
        beh.keywords = keywords.lower()
        # print("KWs for {0} are: {1}".format(beh.code, beh.keywords))


def makePerRowFunc(isCategory: bool, categoryDict: Dict[str, Any]) -> Callable:
    # lineNumLst = [1]
    def makeNewRow(rec: Dict[str, Any]):
        # rec comes in as a yaml object (basically a dict)
        categoryDict[rec.get("code")] = BehCatNode.yamlToBcn(isCategory, rec)

    return makeNewRow


def sortTupleList(tupList: list[Tuple[str, int]]) -> list[str]:
    if len(tupList) < 1:
        return []
    # print('tupList = {0}'.format(tupList))
    return [t[0] for t in sorted(tupList, key=lambda tup: tup[1])]


def getCategoryListSorted(
    catDict: Dict[str, BehCatNode], filterFunc: Callable
) -> list[str]:
    tupList: list[Tuple[str, int]] = [
        (cd, cat.sort) for cd, cat in catDict.items() if filterFunc(cat)
    ]
    # print('tupList had {0} entries'.format(len(tupList)))

    # return sorted list of top-level catCode strings
    return sortTupleList(tupList)


class BehaviorSourceSingleton(metaclass=Singleton):
    """
    takes raw Category & Behavior data from yaml files
        and generates a JSON file to be sent to app-clients via rest or rpc

        this object has 3 properties:
            masterDict   dict( key=code, value=BehCatNode)
            topLevelCategoryCodes  list(string)
            graph   dict as tree of codes
    """

    @staticmethod
    def loadAll(projRoot: str = "") -> BehaviorSourceSingleton:
        #
        # categoriesDict = dict()
        # # forRowInYaml returns a list which we can ignore here
        # forRowInYaml(projRoot + 'common/behavior/category.yaml', makePerRowFunc(Category, categoriesDict))
        # behaviorsDict = dict()  # behavior
        # forRowInYaml(projRoot + 'common/behavior/behaviors.yaml', makePerRowFunc(BehaviorRowYaml, behaviorsDict))
        return BehaviorSourceSingleton(projRoot)

    def __init__(
        self: BehaviorSourceSingleton,
        niuPath: str = "",
    ):
        """initialize the full object graph & also create master dict by code

        masterDict = {code: BehaviorCatNode}
        graph should be a list (not dict because we need order) of tuples like:
            graph = [ (anyCode_1, [childListCode1, childListCode2] ), ]

        NOTE: hidden behaviors may be a problem for showing parent category on Behavior stats
        """
        if self.init_completed:
            return

        categoriesDict: dict[str, BehCatNode] = dict()

        # import os

        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # print(dir_path)

        # forRowInYaml returns a list which we can ignore here
        forRowInYaml(
            "category.yaml",
            makePerRowFunc(True, categoriesDict),
        )
        behaviorsDict: dict[str, BehCatNode] = dict()  # behavior
        forRowInYaml(
            "behaviors.yaml",
            makePerRowFunc(False, behaviorsDict),
        )

        # walk thru every behavior in behaviorsDict
        # update the beh.keywords as a unique, lowercase string of search words
        inheritCategoryDescripToBehKeywords(behaviorsDict, categoriesDict)

        self.masterDict = categoriesDict
        self.masterDict.update(behaviorsDict)

        # figure out the root of hierarchy
        self.topLevelCategoryCodes = getCategoryListSorted(
            categoriesDict, lambda cat: cat.parentCode in ("", "root")
        )
        assert (
            len(self.topLevelCategoryCodes) > 3
        ), "top level categories missing (%s found)" % (len(self.topLevelCategoryCodes))

        self.graph = self.buildSortedGraph(categoriesDict)
        # NOTE:  Show all and Feelings are not getting augmentation from buildSortedGraph
        self.appendShowAllCategories()

        # feelingOnlyCodes are now in YAML .. no need to add them here
        # self.appendFeelingOnlyCodes()
        print(
            "master:{0}  beh:{1}  graph(cats/subcats):{2}".format(
                len(self.masterDict), len(behaviorsDict), len(self.graph)
            )
        )

        # values to build & cache when requested
        self._behaviorListMsg = None  # full list
        self._orderedBehByCat = None  # dict of question under top level category
        self._negCatCodesWithNames = None  # list of tuples (catCode, catName)
        self._posCatCodesWithNames = None
        self._countsByCategory = None  # of beh/questions per category

    def getBehAsDict(self: BehaviorSourceSingleton, code: str) -> Dict[str, Any]:
        """return a dict to describe behavior atts
        for community news meta
        """
        bcn = self.masterDict.get(code, None)
        if bcn is not None:
            bcnAsDict = bcn.asDict
            catRec = self.masterDict.get(bcn.topCategoryCode, None)
            if catRec is not None:
                bcnAsDict["catName"] = catRec.text
            else:
                bcnAsDict["catName"] = "Cat??"

            return bcnAsDict
        else:
            return dict()

    def catAndSubForCode(self: BehaviorSourceSingleton, code: str) -> tuple[str, str]:
        # use beh code to determine cat & subCat codes
        bcn = self.masterDict.get(code, None)
        if bcn is not None:
            return (bcn.topCategoryCode, bcn.parentCode)
        else:
            return "cat", "subCat"

    def allBehaviorCodes(self: BehaviorSourceSingleton, pos: bool) -> list[str]:
        """all pos or neg behCodes
        skip categories
        pass None to get both +-
        """
        codes = []
        for beh in self.masterDict.values():
            if beh.isCategory:
                continue  # skip cat & subcat recs
            if pos is None or beh.positive == pos:
                codes.append(beh.code)
        return codes

    def buildSortedGraph(
        self: BehaviorSourceSingleton, categoriesDict: dict[str, BehCatNode]
    ) -> list[Tuple[str, list[str]]]:
        # every behavior or subCat has a parent
        # we need a sorted list of every parent's child  codes
        # tempGraphDict first contains tuples & then converted to strings after sorting
        tempGraphDict = dict()
        beh: BehCatNode = ""
        for cd, beh in self.masterDict.items():
            # only need to process subCats & behaviors (parentCode filters out topLevelCats)
            if beh.parentCode not in ("", "root"):
                tempGraphDict.setdefault(beh.parentCode, []).append((cd, beh.sort))

                if (
                    not beh.isCategory
                ):  # skip subcats; DO NOT REMOVE THIS  (see "OR" above)
                    # copy super-parent code & descrip to the behavior
                    beh.inheritParentVals(self.masterDict)

                # # also make sure same behavior added to alt-categories
                # # 190104 -> we eliminated altCategories
                # for cat in beh.altCategories:
                #     # sort #s typically skip 5 digits
                #     # there are never more than 16 items in a subcat list
                #     # 5 x 16 = 80
                #     # add 80 so alt-cats always sort at bottom of list in relative order
                #     tempGraphDict.setdefault(cat, []).append((cd, beh.sort + 80))

        # tempGraphDict.keys() contains every category pointed at by a Behavior or subcat
        # if we subtract the TOTAL (bigger) list of category keys, we should get EMPTY set
        # some behaviors are hidden (only found by searching) & have no parent
        # allowed to have 1 (hidden) as a left over category code
        leftoverKeys = set(tempGraphDict.keys()) - set(categoriesDict.keys())
        if len(leftoverKeys) > 1:
            print("Warn:  left over category codes: {}".format(leftoverKeys))

        # now sort all sublists & build final graph
        # graph is a list of tuples where t.0 == catOrSubCatCode & t.1 == [behCodes]
        graph = []
        for catCode, lstOfCodeSortTup in tempGraphDict.items():
            behCodeOnlyList: list[str] = self.removeDupChildCodesThenSort(
                lstOfCodeSortTup
            )
            # NOTE:  not updating tempGraphDict
            graph.append((catCode, behCodeOnlyList))

        return graph

    def removeDupChildCodesThenSort(
        self: BehaviorSourceSingleton, lstOfCodeSortTup: List[str]
    ) -> list[str]:
        newList: list[Tuple[str, int]] = []
        seenList: list[str] = []
        for tup in lstOfCodeSortTup:
            if tup[0] not in seenList:
                newList.append(tup)
                seenList.append(tup[0])

        return map(lambda x: x[0], sorted(newList, key=lambda x: x[1]))

    def appendShowAllCategories(self: BehaviorSourceSingleton) -> None:
        """
        puts showAll (children searchable) on both the pos & neg top level categories
        Returns: none
        """
        posCode = SHOWALL_CODE_PREFIX + "Pos"
        negCode = SHOWALL_CODE_PREFIX + "Neg"

        self.topLevelCategoryCodes.insert(0, posCode)  # at top of category list
        self.topLevelCategoryCodes.insert(0, negCode)

        # find all pos & neg behaviors
        posChildren = [
            cd for cd, v in self.masterDict.items() if v.positive and not v.isCategory
        ]
        negChildren = [
            cd
            for cd, v in self.masterDict.items()
            if not v.positive and not v.isCategory
        ]

        self.graph.append((posCode, posChildren))
        self.graph.append((negCode, negChildren))

        showAllPositiveCat = BehCatNode.make(
            True, posCode, SHOWALL_CAT_LABEL + " Positive", "", True, negCode
        )
        showAllPositiveCat.childrenSearchable = True

        showAllNegativeCat = BehCatNode.make(
            True, negCode, SHOWALL_CAT_LABEL + " Negative", "", False, posCode
        )
        showAllNegativeCat.childrenSearchable = True

        self.masterDict[posCode] = showAllPositiveCat
        self.masterDict[negCode] = showAllNegativeCat

    def bcnFromCode(self: BehaviorSourceSingleton, code: str) -> BehCatNode:
        return self.masterDict.get(code)

    def catNameFromCode(self: BehaviorSourceSingleton, code: str) -> str:
        catBcn = self.masterDict.get(code)
        if catBcn is not None:
            return catBcn.text
        return "_notFnd_{0}".format(code)

    @property
    def countsByCategory(self: BehaviorSourceSingleton) -> Dict[str, int]:
        if self._countsByCategory is None:
            self._countsByCategory = self._makeCategoryCountDict()
        return self._countsByCategory

    def _makeCategoryCountDict(self: BehaviorSourceSingleton) -> Dict[str, int]:
        d: Dict[str, int] = dict()
        for bcn in self.masterDict.values():
            if bcn.isCategory or bcn.positive:
                continue  # only count negative questions
            cnt = d.setdefault(bcn.topCategoryCode, 0)
            d[bcn.topCategoryCode] = cnt + 1
        return d

    @property
    def behaviorListMsg(self: BehaviorSourceSingleton) -> FullBehaviorListMsg:
        # serves all
        if self._behaviorListMsg is None:
            self._behaviorListMsg = self._toMsg()
        return self._behaviorListMsg

    def _toMsg(self) -> FullBehaviorListMsg:
        # remember to remove feelings from list
        # from common.messages.behavior import FullBehaviorListMsg, NodeListMsg
        # raise Exception

        mastLst = [
            b.toMsg()
            for b in self.masterDict.values()
            if not b.code.startswith("feelingReport")
        ]
        nodeList = [NodeListMsg(code=tup[0], children=tup[1]) for tup in self.graph]
        fbl = FullBehaviorListMsg(
            topCategoryCodes=self.topLevelCategoryCodes,
            graph=nodeList,
            masterList=mastLst,
        )
        return fbl

    def findTopCategory(
        self: BehaviorSourceSingleton, behaviorCode: str, isPositive: bool
    ) -> str:
        # set topCategoryCode on each behavior when it is stored
        bcn = self.masterDict.get(behaviorCode)
        if bcn:
            return bcn.topCategoryCode
        else:
            return "hiddenPos" if isPositive else "hiddenNeg"

    # to support the Score calcs below:
    def isPositiveByCode(self: BehaviorSourceSingleton, code: str) -> bool:
        bcn = self.masterDict.get(code)
        if bcn == None:
            logging.error("behavior code {0} not found in master dict".format(code))
            return False
        return bcn.positive

    def countByFeeling(
        self: BehaviorSourceSingleton,
        personBehavior: "PersonBehavior",  # PersonBehavior causes circular import
        countPositive: bool = True,
        feelingsOnly: bool = False,
    ) -> int:
        # return counts by pos/neg & whether behavior is attached or generic feeling

        filteredBehaviors = personBehavior.entryList
        if feelingsOnly:
            # we can match on exact code without calling isPositiveByCode()
            code = FEELING_ONLY_CODE_POS if countPositive else FEELING_ONLY_CODE_NEG
            filteredBehaviors = [b for b in filteredBehaviors if b.behaviorCode == code]
            return len(filteredBehaviors)

        # exclude feeling only reports by both of those codes
        # check remainder for pos/neg
        tot = sum(
            1
            if b.behaviorCode not in (FEELING_ONLY_CODE_POS, FEELING_ONLY_CODE_NEG)
            and self.isPositiveByCode(b.behaviorCode) == countPositive
            else 0
            for b in filteredBehaviors
        )
        return tot

    def categoryCodesWithNames(self: BehaviorSourceSingleton, neg: bool = True):
        # return sorted list of tuples (catCode, catText) (Negative cats only)
        if neg and self._negCatCodesWithNames is None:
            self._negCatCodesWithNames = self._buildCatCodeAndNameList(False)
        elif not neg and self._posCatCodesWithNames is None:
            self._posCatCodesWithNames = self._buildCatCodeAndNameList(True)
        return self._negCatCodesWithNames if neg else self._posCatCodesWithNames

    def getXBehaviorsForCatAfter(
        self: BehaviorSourceSingleton,
        count: int,
        categoryCode: str,
        startingAfter: str = "",
    ) -> list[BehCatNode]:
        """
        count = int (how many bcn to return
        categoryCode = string
        startingAfer = string (bcn.code of last user answer)
        return {count} behaviors under category in order
        """
        if count < 1:
            return []

        if self._orderedBehByCat is None:
            self._orderedBehByCat = dict()

        bcnLst = self._orderedBehByCat.setdefault(categoryCode, [])
        if len(bcnLst) < 1:
            bcnLst = self._buildBehListByCat(categoryCode)
            self._orderedBehByCat[categoryCode] = bcnLst
            if len(bcnLst) < 1:
                print("serious error")
                return []

        idxAfterStarting = BehaviorSourceSingleton._indexPastLastEntry(
            bcnLst, startingAfter
        )
        if startingAfter == "_testMode" and idxAfterStarting + count > len(bcnLst) - 1:
            # in test mode, we need a predictable # of recs back
            idxAfterStarting = len(bcnLst) - (count + 1)
        return bcnLst[idxAfterStarting : idxAfterStarting + count]

    @staticmethod
    def _indexPastLastEntry(bcnLst: list[BehCatNode], startingAfter: str) -> int:
        # find the bcn rec in list & return idx 1 past there
        idx = 0
        for i, b in enumerate(bcnLst):
            if b.code == startingAfter:
                idx = i + 1
                break
        return idx

    def _buildBehListByCat(
        self: BehaviorSourceSingleton, categoryCode: str
    ) -> list[BehCatNode]:
        # return sorted list of behavior recs
        # unify into one sorted list
        behaveList = [
            rec
            for rec in self.masterDict.values()
            if rec.topCategoryCode == categoryCode and not rec.isCategory
        ]
        # behaveList = sorted(behaveList, key = lambda r: r.sort)
        return sorted(behaveList, key=lambda r: r.sort)

    def _buildCatCodeAndNameList(
        self: BehaviorSourceSingleton, pos: bool = False
    ) -> list[Tuple[str, str, str, bool]]:
        # master list of tuples containing top level category (code, name, icon, pos)
        # using specified sort order
        md = self.masterDict
        lstTups = []
        for cd in self.topLevelCategoryCodes:
            rec = md.get(cd)
            if (
                rec is not None
                and rec.positive == pos
                and not rec.code.startswith(SHOWALL_CODE_PREFIX)
            ):
                lstTups.append((cd, rec.text.upper(), rec.iconName, rec.positive))

        # sortFunc = lambda cd: md.get(cd).sort
        # return sorted(lstTups, key=sortFunc)
        return lstTups  # should already be sorted

    def getRandomBcns(
        self: BehaviorSourceSingleton, count: int, pos: bool = False
    ) -> list[BehCatNode]:
        # Type: int, bool -> [BehCatNode]
        lstBcn = []
        consumedPositions = set()  # confirms all beh recs are unique
        allBehCodes = [
            cd
            for cd, v in self.masterDict.items()
            if not v.isCategory and v.positive == pos
        ]
        for i in range(count):
            bcn, selectedIdx = self._getRandBcnRec(allBehCodes, consumedPositions)
            consumedPositions.add(selectedIdx)
            lstBcn.append(bcn)
        return lstBcn

    def _getRandBcnRec(
        self: BehaviorSourceSingleton, allBehCodes: list[str], excludedIdxs: list[int]
    ) -> Tuple[BehCatNode, int]:
        # assert False, "length of Graph: {0}".format(len(self.graph))
        rowIdx = random.randint(0, len(allBehCodes) - 1)
        bcnCode = allBehCodes[rowIdx]
        bcn = self.masterDict.get(bcnCode)
        while rowIdx in excludedIdxs or bcn is None:
            # next lines are dups from above
            rowIdx = random.randint(0, len(allBehCodes) - 1)
            bcnCode = allBehCodes[rowIdx]
            bcn = self.masterDict.get(bcnCode)
        return bcn, rowIdx


class BcnEncoder(json.JSONEncoder):
    #
    def default(self: BcnEncoder, obj) -> dict[str, Any]:
        if isinstance(obj, BehCatNode):
            return obj.toDict()
        return json.JSONEncoder.default(self, obj)


if __name__ == "__main__":
    from os import path, getcwd

    cwd = path.abspath(getcwd())
    masterObj = BehaviorSourceSingleton.loadAll(cwd)

    # print masterObj.__dict__
    # print '\n\n\n'
    # print masterObj.toJson()

    masterDict = masterObj.masterDict
    graph = masterObj.graph

    # badBreath = masterDict["breathBad"]
    # print(badBreath.altCategories)
    # # print(len(graph))
    #
    # idx = -1
    # for i, t in enumerate(graph):
    #     # print t[0]
    #     if t[0] == "compatAppearanceNeg":
    #         idx = i
    #
    # print( graph[idx])
