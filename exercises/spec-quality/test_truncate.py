# `test_truncate.py` - Tests for the `truncate` function specified in
# [my\_truncate.py](my_truncate.py)
# ===================================================================
#
# This uses the pytest framework.
#
# Imports
# -------
#
# ### Local imports
from my_truncate import truncate

# Code
# ----
#
# Show how tests work. <fragment id="cc-Utv4vgn1Kk"></fragment>
def test_1():
    assert truncate("one") == "one"
