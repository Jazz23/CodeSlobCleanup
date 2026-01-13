from hypothesis import given
import hypothesis.strategies as st

def reverse(s):
    return s[::-1]

@given(st.text())
def test_reverse_roundtrip(s):
    assert reverse(reverse(s)) == s

@given(st.text())
def test_reverse_length(s):
    assert len(reverse(s)) == len(s)
