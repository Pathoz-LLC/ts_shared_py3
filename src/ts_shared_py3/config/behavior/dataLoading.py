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
import random
import json  # dumps( {} ) turns dict into string
import logging
from pathlib import Path

#
from ...utils.singleton import Singleton
from ...utils.data_gen import forRowInYaml
from ...utils.stop_words import removeStopWords

# from api_data_classes.behavior import FullBehaviorListMsg, BehOrCatMsg, NodeListMsg
# from . import constants     # local 4 this module only

from .beh_constants import (
    SHOWALL_CAT_LABEL,
    SHOWALL_CODE_PREFIX,
    FEELING_ONLY_CODE_POS,
    FEELING_ONLY_CODE_NEG,
)
from ...constants import (
    APP_IMPACT_WEIGHT_MAX,
    IMPACT_WEIGHT_DECIMALS,
    FEELING_CD_PREFIX,
)

# usage:
# from common.behavior.dataLoading import BehaviorSourceSingleton

# normalize both Behaviors & Categories into BehaviorCatNode before sending to the client
# BehaviorCatNode = namedtuple('BehaviorCatNode', ['code', 'text', 'sort', 'keywords', 'positive', 'childrenSearchable', 'isCategory', 'parentCode'])


class BehCatNode(object):
    @staticmethod
    def yamlToBcn(isCategory, row):
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

    def inheritParentVals(self, masterDict):
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
    def isFeelingReport(self):
        return self.code.startswith(FEELING_CD_PREFIX)

    @property
    def iconName(self):
        # only applies to category entries
        if not self.isCategory:
            return ""
        return "bc_" + self.code.replace("Neg", "Pos")  # .replace("Pos","")

    @property
    def categoryName(self):
        # NIU & not tested
        return BehaviorSourceSingleton().catNameFromCode(self.topCategoryCode)

    def __str__(self):
        return "Bcn:{0}  parent:{1}   impact:{2}".format(
            self.code, self.parentCode, self.impact
        )

    @staticmethod
    def validateInt(val):
        return int(val)

    @property
    def asDict(self):
        return dict(
            code=self.code,
            parentCode=self.parentCode,
            text=self.text,
            catCode=self.topCategoryCode,
            pos=self.positive,
            parentDescription=self.parentDescription,
            impact=self.impact,
        )

    def _toMsg(self):
        # convert rec to a client msg
        from common.messages.behavior import BehOrCatMsg

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
    def make(isCategory, code, text, parentCode, isPositive, oppositeCode):
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


def finalKeywordsList(behKeywordsLst, catKeywordsLst, theText):
    # all keywords come in as string of words; return a list
    # print("behKeywordsLst:", type(behKeywordsLst))
    # print("catKeywordsLst:", type(catKeywordsLst))
    # print("theText:", type(theText))

    textWordsList = theText.lower().split(" ")
    bkl = behKeywordsLst.lower().split(",")  # [w.lower() for w in behKeywordsLst]
    ckl = catKeywordsLst.lower().split(",")  # [w.lower() for w in catKeywordsLst]
    dedupSet = set(bkl + ckl + textWordsList)  # remove dups
    return removeStopWords(list(dedupSet))  # list in/out


def inheritCategoryDescripToBehKeywords(behaviorsDict, categoriesDict):
    """combine keywords, dedup, lowercase & remove punctuation from search words"""
    # print("categoriesDict:")
    # print(categoriesDict)

    for _cd, beh in behaviorsDict.items():
        theSubCat = categoriesDict.get(beh.parentCode)
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
        keywords = "*" + "*".join(keywordList)
        # keywords.translate(None, string.punctuation)
        keywords = keywords.replace("**", "*")
        beh.keywords = keywords.lower()
        # print("KWs for {0} are: {1}".format(beh.code, beh.keywords))


def makePerRowFunc(isCategory, categoryDict):
    # lineNumLst = [1]
    def makeNewRow(rec):
        # rec comes in as a yaml object (basically a dict)
        categoryDict[rec.get("code")] = BehCatNode.yamlToBcn(isCategory, rec)

    return makeNewRow


def sortTupleList(tupList):
    if len(tupList) < 1:
        return []
    # print('tupList = {0}'.format(tupList))
    return [t[0] for t in sorted(tupList, key=lambda tup: tup[1])]


def getCategoryListSorted(catDict, filterFunc):
    tupList = [(cd, cat.sort) for cd, cat in catDict.items() if filterFunc(cat)]
    # print('tupList had {0} entries'.format(len(tupList)))

    # return sorted list of top-level catCode strings
    return sortTupleList(tupList)


class BehaviorSourceSingleton(object):
    """
    takes raw Category & Behavior data from yaml files
        and generates a JSON file to be sent to app-clients via rest or rpc

        this object has 3 properties:
            masterDict   dict( key=code, value=BehCatNode)
            topLevelCategoryCodes  list(string)
            graph   dict as tree of codes
    """

    __metaclass__ = Singleton

    @staticmethod
    def loadAll(projRoot=""):
        #
        # categoriesDict = dict()
        # # forRowInYaml returns a list which we can ignore here
        # forRowInYaml(projRoot + 'common/behavior/category.yaml', makePerRowFunc(Category, categoriesDict))
        # behaviorsDict = dict()  # behavior
        # forRowInYaml(projRoot + 'common/behavior/behaviors.yaml', makePerRowFunc(BehaviorRowYaml, behaviorsDict))
        return BehaviorSourceSingleton(projRoot)

    def __init__(self, projRoot=""):
        """initialize the full object graph & also create master dict by code

        masterDict = {code: BehaviorCatNode}
        graph should be a list (not dict because we need order) of tuples like:
            graph = [ (anyCode_1, [childListCode1, childListCode2] ), ]

        NOTE: hidden behaviors may be a problem for showing parent category on Behavior stats
        """
        categoriesDict = dict()
        file_path = Path(__file__).with_name("category.yaml")
        # forRowInYaml returns a list which we can ignore here
        forRowInYaml(
            file_path,  # projRoot + config/behavior/
            makePerRowFunc(True, categoriesDict),
        )
        behaviorsDict = dict()  # behavior
        file_path = Path(__file__).with_name("behaviors.yaml")
        forRowInYaml(
            file_path,  # projRoot +
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

    def getBehAsDict(self, code):
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

    def catAndSubForCode(self, code):
        # use beh code to determine cat & subCat codes
        bcn = self.masterDict.get(code, None)
        if bcn is not None:
            return (bcn.topCategoryCode, bcn.parentCode)
        else:
            return "cat", "subCat"

    def allBehaviorCodes(self, pos):
        """all pos or neg behCodes
        skip categories
        pass None to get both +-
        """
        codes = []
        for beh in self.masterDict.itervalues():
            if beh.isCategory:
                continue  # skip cat & subcat recs
            if pos is None or beh.positive == pos:
                codes.append(beh.code)
        return codes

    def buildSortedGraph(self, categoriesDict):
        # every behavior or subCat has a parent
        # we need a sorted list of every parent's child  codes
        # tempGraphDict first contains tuples & then converted to strings after sorting
        tempGraphDict = dict()
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
            behCodeOnlyList = self.removeDupChildCodesThenSort(lstOfCodeSortTup)
            # NOTE:  not updating tempGraphDict
            graph.append((catCode, behCodeOnlyList))

        return graph

    def removeDupChildCodesThenSort(self, lstOfCodeSortTup):
        newList = []
        seenList = []
        for tup in lstOfCodeSortTup:
            if tup[0] not in seenList:
                newList.append(tup)
                seenList.append(tup[0])

        return map(lambda x: x[0], sorted(newList, key=lambda x: x[1]))

    def appendShowAllCategories(self):
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

    # def appendFeelingOnlyCodes(self):
    #     """
    #     add the pos/neg feeling only codes
    #     when user does not select a behavior
    #
    #     Returns: none
    #     """
    #
    #     # make(isCategory, code, text, parentCode, isPositive, oppositeCode)
    #     feelBehPos = BehCatNode.make(False, FEELING_ONLY_CODE_POS, 'General Positive Feeling', 'hiddenPos', True,
    #                                  FEELING_ONLY_CODE_NEG)
    #     feelBehPos.sort = 100
    #     feelBehPos.childrenSearchable = False
    #     feelBehPos.topCategoryCode = 'hiddenPos'
    #     feelBehPos.parentDescription = 'General Positive Feeling'
    #
    #     feelBehNeg = BehCatNode.make(False, FEELING_ONLY_CODE_NEG, 'General Negative Feeling', 'hiddenNeg', False,
    #                                  FEELING_ONLY_CODE_POS)
    #     feelBehNeg.sort = 100
    #     feelBehNeg.childrenSearchable = False
    #     feelBehNeg.topCategoryCode = 'hiddenNeg'
    #     feelBehNeg.parentDescription = 'General Negative Feeling'
    #
    #     self.masterDict[FEELING_ONLY_CODE_POS] = feelBehPos
    #     self.masterDict[FEELING_ONLY_CODE_NEG] = feelBehNeg
    #     # added 12/16/17 so feelings show up in beh history wrapper
    #     # fixed in history_wrapper instead; below not needed

    def bcnFromCode(self, code):
        return self.masterDict.get(code)

    def catNameFromCode(self, code):
        catBcn = self.masterDict.get(code)
        if catBcn is not None:
            return catBcn.text
        return "_notFnd_{0}".format(code)

    @property
    def countsByCategory(self):
        if self._countsByCategory is None:
            self._countsByCategory = self._makeCategoryCountDict()
        return self._countsByCategory

    def _makeCategoryCountDict(self):
        d = dict()
        for bcn in self.masterDict.itervalues():
            if bcn.isCategory or bcn.positive:
                continue  # only count negative questions
            cnt = d.setdefault(bcn.topCategoryCode, 0)
            d[bcn.topCategoryCode] = cnt + 1
        return d

    @property
    def behaviorListMsg(self):
        if self._behaviorListMsg is None:
            self._behaviorListMsg = self._toMsg()
        return self._behaviorListMsg

    def _toMsg(self):
        # remember to remove feelings from list
        from common.messages.behavior import FullBehaviorListMsg, NodeListMsg

        mastLst = [
            b._toMsg()
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

    def findTopCategory(self, behaviorCode, isPositive):
        # set topCategoryCode on each behavior when it is stored
        bcn = self.masterDict.get(behaviorCode)
        if bcn:
            return bcn.topCategoryCode
        else:
            return "hiddenPos" if isPositive else "hiddenNeg"

    # to support the Score calcs below:
    def isPositiveByCode(self, code):
        bcn = self.masterDict.get(code)
        if bcn == None:
            logging.error("behavior code {0} not found in master dict".format(code))
            return False
        return bcn.positive

    def countByFeeling(self, personBehavior, countPositive=True, feelingsOnly=False):
        # return counts by pos/neg & whether behavior is attached or generic feeling

        filteredBehaviors = personBehavior.entries
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

    def categoryCodesWithNames(self, neg=True):
        # return sorted list of tuples (catCode, catText) (Negative cats only)
        if neg and self._negCatCodesWithNames is None:
            self._negCatCodesWithNames = self._buildCatCodeAndNameList(False)
        elif not neg and self._posCatCodesWithNames is None:
            self._posCatCodesWithNames = self._buildCatCodeAndNameList(True)
        return self._negCatCodesWithNames if neg else self._posCatCodesWithNames

    def getXBehaviorsForCatAfter(self, count, categoryCode, startingAfter):
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
    def _indexPastLastEntry(bcnLst, startingAfter):
        # find the bcn rec in list & return idx 1 past there
        idx = 0
        for i, b in enumerate(bcnLst):
            if b.code == startingAfter:
                idx = i + 1
                break
        return idx

    def _buildBehListByCat(self, categoryCode):
        # return sorted list of behavior recs
        # unify into one sorted list
        behaveList = [
            rec
            for rec in self.masterDict.itervalues()
            if rec.topCategoryCode == categoryCode and not rec.isCategory
        ]
        # behaveList = sorted(behaveList, key = lambda r: r.sort)
        return sorted(behaveList, key=lambda r: r.sort)

    def _buildCatCodeAndNameList(self, pos=False):
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

    def getRandomBcns(self, count, pos=False):
        # Type: int, bool -> [BehCatNode]
        lstBcn = []
        consumedPositions = set()  # confirms all beh recs are unique
        allBehCodes = [
            cd
            for cd, v in self.masterDict.iteritems()
            if not v.isCategory and v.positive == pos
        ]
        for i in range(count):
            bcn, selectedIdx = self._getRandBcnRec(allBehCodes, consumedPositions)
            consumedPositions.add(selectedIdx)
            lstBcn.append(bcn)
        return lstBcn

    def _getRandBcnRec(self, allBehCodes, excludedIdxs):
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
    def default(self, obj):
        if isinstance(obj, BehCatNode):
            return obj.toDict()
        return json.JSONEncoder.default(self, obj)


if __name__ == "__main__":

    masterObj = BehaviorSourceSingleton.loadAll(
        "/Users/dgaedcke/dev/TouchstoneMicroservices/"
    )

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
