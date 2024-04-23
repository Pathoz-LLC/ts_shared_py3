from __future__ import annotations
from datetime import datetime, timedelta
import google.cloud.ndb as ndb


class DeltaSince:
    def __init__(self, dt: datetime, userDelta: float, communityDelta: float):
        self.dt = dt
        self.user_delta = userDelta
        self.community_delta = communityDelta


class RescoreEntry(ndb.Model):
    score_dttm = ndb.DateTimeProperty(indexed=False)
    user_score = ndb.FloatProperty(indexed=False)
    community_score = ndb.FloatProperty(indexed=False)


class ScoreHistory(ndb.Model):
    """tracks score history for a given prospect"""

    # userID = ndb.StringProperty(default=0, indexed=False)
    # prospectID = ndb.IntegerProperty(indexed=False, default=False)
    recent_scores = ndb.LocalStructuredProperty(
        RescoreEntry,
        repeated=True,
    )

    @property
    def user_score(self) -> float:
        return self.recent_scores[-1].user_score if self.recent_scores else 0.5

    @property
    def community_score(self) -> float:
        return self.recent_scores[-1].community_score if self.recent_scores else 0.5

    def _append_and_truncate(self, rescore_entry: RescoreEntry):
        self.recent_scores.append(rescore_entry)
        if len(self.recent_scores) > 20:
            self.recent_scores = self.recent_scores[-20:]

    @staticmethod
    def _get_or_create(
        userID: str,
        prospectID: int,
    ) -> ScoreHistory:
        #
        sh_key = ndb.Key(__class__.__name__, userID, "Person", prospectID)
        score_history: ScoreHistory = sh_key.get()
        if score_history is None:
            score_history = ScoreHistory(key=sh_key, recent_scores=[])
            # score_history.key = sh_key
            # score_history.recent_scores = []
            # score_history.userID = userID
            # score_history.prospectID = prospectID
        return score_history

    @staticmethod
    def update_score(
        userID: str, prospectID: int, userScore: float, communityScore: float
    ) -> None:
        #
        score_history = ScoreHistory._get_or_create(userID, prospectID)
        #
        rescore_entry = RescoreEntry()
        rescore_entry.score_dttm = datetime.now()
        rescore_entry.user_score = userScore
        rescore_entry.community_score = communityScore
        #
        score_history._append_and_truncate(rescore_entry)
        score_history.put()

    @staticmethod
    def get_score_change_since(
        userID: str, prospectID: int, past_dttm: datetime = None
    ) -> DeltaSince:
        # default to 60 days ago
        score_history = ScoreHistory._get_or_create(userID, prospectID)
        return score_history.get_score_deltas(past_dttm)

    def get_score_deltas(self, past_dttm: datetime = None) -> DeltaSince:
        # default to 60 days ago
        if past_dttm is None:
            today = datetime.now()
            past_dttm = today - timedelta(days=60)

        # prior_scores_count: list[int] = len(self.recent_scores)
        # if prior_scores_count < 2:
        #     return DeltaSince(past_dttm, 0, 0)

        recent_scores = [rs for rs in self.recent_scores if rs.score_dttm > past_dttm]
        if len(recent_scores) < 2:
            return DeltaSince(past_dttm, 0, 0)

        deflt_score = 0.5
        old_user_score = recent_scores[0].user_score if recent_scores else deflt_score
        new_user_score = recent_scores[-1].user_score if recent_scores else deflt_score
        old_community_score = (
            recent_scores[0].community_score if recent_scores else deflt_score
        )
        new_community_score = (
            recent_scores[-1].community_score if recent_scores else deflt_score
        )
        user_delta = new_user_score - old_user_score
        community_delta = new_community_score - old_community_score
        return DeltaSince(past_dttm, user_delta, community_delta)


# rescore_entry = 55
# lst_scores = []
# lst_scores.append(rescore_entry)
# if len(lst_scores) > 20:
#     lst_scores = lst_scores[-20:]
