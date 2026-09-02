import sys
sys.path.append("current")
from dimensional_quantity_engine import DimensionalQuantityEngine

res1 = DimensionalQuantityEngine.compare_typed_quantities("10m", 10.0, "kg")
print(res1)
assert res1["is_match"] == False

res2 = DimensionalQuantityEngine.compare_typed_quantities("10 million", 10.0, "m")
print(res2)

