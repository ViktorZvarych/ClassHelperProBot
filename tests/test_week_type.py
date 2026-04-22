import pytest
from datetime import date
from services.schedule import get_week_type

def test_week_type():
    assert get_week_type(date(2025,1,13), date(2025,1,13), 'numerator') == 'numerator'
    assert get_week_type(date(2025,1,20), date(2025,1,13), 'numerator') == 'denominator'