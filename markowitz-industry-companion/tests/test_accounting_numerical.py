"""Engineered floating-point controls, entirely invented; no market evidence."""
from datetime import date
import math

import pytest

from industry_companion.audit import expected_sessions
from industry_companion.synthetic_accounting import (
    AccountingError, CalendarGrid, EQUAL, drift_weights, make_instruction,
    required_decisions, simulate,
)


@pytest.mark.parametrize('weights', [EQUAL,(.31,.17,.11,.10,.08,.07,.06,.04,.03,.03)])
@pytest.mark.parametrize('common_return', [-.1,.1,.123456789])
def test_exact_common_returns_do_not_manufacture_any_weight_trade(weights,common_return):
    drifted,gross,adjustment=drift_weights(weights,(common_return,)*10)
    assert drifted==weights
    assert gross==1+common_return and adjustment==0
    assert math.fsum(abs(a-b) for a,b in zip(drifted,weights))==0


def test_unrepresentable_fee_aggregate_has_a_typed_failure():
    calendar=CalendarGrid(expected_sessions(),date(2016,1,1),date(2024,12,31),
                          provenance='Pinned local XNYS dates; invented extreme accounting fixture')
    dates=tuple(d for d in calendar.sessions if date(2021,1,4)<=d<=date(2023,12,29))
    illustrative=(.35,)+(.65/9,)*9
    instructions=tuple(make_instruction(calendar,d0,weights=illustrative if i%2==0 else EQUAL)
                       for i,d0 in enumerate(required_decisions(calendar,dates)))
    # Recapitalize via invented common returns after each 20% close fee. All
    # individual states remain finite; cumulative fees exceed binary64 capacity.
    effective_dates={instruction.d2 for instruction in instructions}
    rows=tuple(((1e308 if i==0 else .25 if d in effective_dates else 0.),)*10
               for i,d in enumerate(dates))
    ledger=simulate(calendar=calendar,dates=dates,returns=rows,instructions=instructions,
                    cost_rate=.4,evidence_kind='invented_synthetic_fixture')
    assert all(math.isfinite(d.wealth) and d.wealth>0 and math.isfinite(d.rebalance_fee) for d in ledger.days)
    with pytest.raises(AccountingError,match='NONFINITE_AGGREGATE_METRIC'):
        ledger.summary()
