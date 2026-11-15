"""Date-only pinned calendar tests; no historical market observations."""
from datetime import date

import pytest

from industry_companion.audit import expected_sessions
from industry_companion.synthetic_accounting import (
    AccountingError, CalendarGrid, EQUAL, has_minimum_samples,
    make_instruction, required_decisions, simulate, training_window,
)


@pytest.fixture(scope='module')
def calendar():
    return CalendarGrid(expected_sessions(),date(2016,1,1),date(2024,12,31),
                        provenance='Pinned exchange-calendars 4.11.1 XNYS, dates only')


def test_month_end_and_lag_use_xnys_not_weekdays(calendar):
    # Memorial Day is not an XNYS session. No price/return data involved.
    target=make_instruction(calendar,date(2021,5,28),weights=EQUAL)
    assert target.d1==date(2021,6,1) and target.d2==date(2021,6,2)
    assert date(2018,12,5) not in calendar.sessions
    with pytest.raises(AccountingError):make_instruction(calendar,date(2021,5,31),weights=EQUAL)


def test_missing_duplicate_nonmonotone_or_weekend_panel_dates_fail(calendar):
    for dates in [(date(2021,1,5),date(2021,1,7)),
                  (date(2021,1,5),date(2021,1,5)),
                  (date(2021,1,6),date(2021,1,5)),(date(2021,1,9),)]:
        with pytest.raises(AccountingError):required_decisions(calendar,dates)


def test_partial_observed_month_is_not_inferred_month_end(calendar):
    with pytest.raises(AccountingError):make_instruction(calendar,date(2021,1,28),weights=EQUAL)
    dates=(date(2021,1,26),date(2021,1,27),date(2021,1,28))
    assert required_decisions(calendar,dates)==()
    # A calendar whose coverage ends before January finishes cannot certify d0.
    partial=CalendarGrid(tuple(d for d in calendar.sessions if date(2021,1,1)<=d<=date(2021,1,29)),
                         date(2021,1,1),date(2021,1,29),provenance='Explicit partial date-only fixture')
    with pytest.raises(AccountingError):make_instruction(partial,date(2021,1,29),weights=EQUAL)


def test_first_2021_and_final_2024_boundaries(calendar):
    first=(date(2021,1,4),date(2021,1,5))
    assert required_decisions(calendar,first)==(date(2020,12,31),)
    final=make_instruction(calendar,date(2024,12,31),weights=EQUAL)
    assert final.d1 is final.d2 is None
    dates=(date(2024,12,30),date(2024,12,31))
    result=simulate(calendar=calendar,dates=dates,returns=((0.,)*10,)*2,
                    instructions=(final,),evidence_kind='invented_synthetic_fixture')
    assert result.summary()['total_rebalance_q']==0
    assert len(result.skipped_instructions)==1


def test_sixty_complete_calendar_months_and_advancing_window(calendar):
    first=training_window(calendar,calendar.sessions,date(2020,12,31))
    assert first.window_start==date(2016,1,1) and first.window_end==date(2020,12,31)
    assert first.dates[0]==date(2016,1,4) and first.dates[-1]==date(2020,12,31)
    assert first.sufficient and len(first.dates)!=60*21
    next_window=training_window(calendar,calendar.sessions,date(2021,1,29))
    assert next_window.window_start==date(2016,2,1)
    assert next_window.dates[-1]==date(2021,1,29)
    leap=training_window(calendar,calendar.sessions,date(2024,2,29))
    assert leap.window_start==date(2019,3,1)
    assert all(leap.window_start<=d<=leap.window_end for d in leap.dates)


def test_history_insufficiency_is_distinct_from_missing_internal_session(calendar):
    window=training_window(calendar,calendar.sessions,date(2019,12,31))
    assert not window.sufficient and window.reason=='INSUFFICIENT_HISTORY'
    available=tuple(d for d in calendar.sessions if d>=date(2017,1,1))
    assert training_window(calendar,available,date(2020,12,31)).reason=='INSUFFICIENT_HISTORY'
    broken=tuple(d for d in calendar.sessions if d!=date(2018,6,1))
    with pytest.raises(AccountingError):training_window(calendar,broken,date(2020,12,31))
    assert has_minimum_samples(999) is False and has_minimum_samples(1000) is True
    for invalid in (-1,True,1000.0):
        with pytest.raises(AccountingError):has_minimum_samples(invalid)


def test_insufficient_history_reason_can_feed_a_flagged_target(calendar):
    window=training_window(calendar,calendar.sessions,date(2019,12,31))
    instruction=make_instruction(calendar,date(2019,12,31),weights=None,failure_reason=window.reason)
    result=simulate(calendar=calendar,dates=(date(2020,1,2),date(2020,1,3)),
                    returns=((0.,)*10,)*2,instructions=(instruction,),
                    evidence_kind='invented_synthetic_fixture',cost_rate=0.)
    assert result.days[0].used_fallback and result.days[0].failure_reason=='INSUFFICIENT_HISTORY'
    assert result.summary()['fallback_count']==1


def test_scope_rejection_precedes_any_return_access(calendar):
    class Poison:
        def __len__(self):raise AssertionError('Return values must not be touched')
        def __iter__(self):raise AssertionError('Return values must not be touched')
    with pytest.raises(AccountingError):
        simulate(calendar=calendar,dates=(date(2025,1,2),),returns=Poison(),
                 instructions=(),evidence_kind='invented_synthetic_fixture')


def test_calendar_requires_explicit_scope_identity_and_provenance(calendar):
    for changes in [dict(name='WEEKDAYS'),dict(provenance=''),dict(coverage_end=date(2025,1,1)),
                    dict(sessions=(date(2021,1,9),)),dict(sessions=tuple(reversed(calendar.sessions)))]:
        args=dict(sessions=calendar.sessions,coverage_start=calendar.coverage_start,
                  coverage_end=calendar.coverage_end,provenance=calendar.provenance)
        args.update(changes)
        with pytest.raises(AccountingError):CalendarGrid(**args)
