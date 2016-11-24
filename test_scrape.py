from scrape import *
import pytest

def test_num():
    nums = get_nums() 
    assert type(nums) == list
    assert len(nums) != 0

def test_dow():
    dows = get_dows()
    assert type(dows) == list
    assert len(dows) != 0
    assert len(dows) < 10

def test_stops():
    stops = get_stops()
    assert type(stops) == list
    assert len(stops) != 0
    


