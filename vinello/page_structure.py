from typing import List, NamedTuple, Optional, Text


VinelloPage = NamedTuple('WinePage', [
    ('wine_name', Text),
    ('description', Text),
    ('verification', Text),
    ('type', Text),
    ('country', Text),
    ('region', int),
    ('acidity', float),
    ('sugar', float),
    ('sweetness', Text),
    ('sub_region', Text),
    ('perfect_for', Text),
    ('ageing', Text),
    ('vintage', int),
    ('soil', Text),
    ('aromas', Text),
    ('texture', Text),
    ('food_pairing', Text),
    ('alcohol', Text),
    ('allergens', Text),
    ('colour', Text),
    ('variety', Text),
    ('harvest', Text),
    ('maturation_duration', int),
    ('style', Text)
])