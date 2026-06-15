from __future__ import annotations



from typing import TYPE_CHECKING, Optional



from src.core.contest.contest_result import ContestResult

from src.core.contestant.models import Contestant

from src.core.tournament.match_outcome import HeadToHeadPoints

from src.core.tournament.ranking import (

    describe_two_way_result,

    head_to_head_points,

    single_first_place,

)

from src.core.tournament.result_reader import TournamentResultReader



if TYPE_CHECKING:

    from src.core.contest.contest import Contest





class FootballTournamentResultReader(TournamentResultReader):

    def read_head_to_head(

        self, contest: Contest, result: ContestResult

    ) -> Optional[HeadToHeadPoints]:

        sides = contest.contestants

        if len(sides) != 2:

            return None



        side_a, side_b = sides[0], sides[1]

        ranking = result.ranking()

        if not ranking:

            return None



        points_a, points_b = head_to_head_points(side_a, side_b, ranking)

        return HeadToHeadPoints(side_a, side_b, points_a, points_b)



    def read_knockout_winner(

        self, contest: Contest, result: ContestResult

    ) -> Optional[Contestant]:

        return single_first_place(result.ranking())



    def describe_result(self, contest: Contest, result: ContestResult) -> str:

        return describe_two_way_result(result.ranking())


