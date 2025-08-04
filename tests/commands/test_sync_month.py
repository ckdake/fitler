import pytest
from fitler.commands.sync_month import generate_correlation_key


@pytest.mark.parametrize(
    "timestamp1,distance1,timestamp2,distance2",
    [
        (1746504000, 30.55, 1746570520, 30.546996425),
        (1748491200, 15.0, 1748559503, 15.00241904),
        (1748559503, 14.99832225, 1748559503, 15.00241904),
        (1743546548, 15.551244, 1743480000, 15.55),
        (1720411200, 2.5, 1720475888, 2.5043798)
    ],
)
def test_generate_correlation_key(timestamp1, distance1, timestamp2, distance2):
    assert generate_correlation_key(timestamp1, distance1) == generate_correlation_key(
        timestamp2, distance2
    )
