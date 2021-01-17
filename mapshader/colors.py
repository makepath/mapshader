from datashader.colors import Elevation
from datashader.colors import inferno
from datashader.colors import viridis
from datashader.colors import Greys9
from datashader.colors import Hot
from datashader.colors import Set1
from datashader.colors import Set2
from datashader.colors import Set3
from datashader.colors import Sets1to3
from datashader.colors import hex_to_rgb

import bokeh.palettes as bokeh_colors

colors = {
    'race': dict((('w', 'aqua'),
                  ('b', 'lime'),
                  ('a', 'red'),
                  ('h', 'fuchsia'),
                  ('o', 'yellow'))),
    'inferno': inferno,
    'viridis': viridis,
    'elevation': Elevation,
    'greys9': Greys9,
    'hot': Hot,
    'set1': Set1,
    'set2': Set2,
    'set3': Set3,
    'sets1to3': Sets1to3,
    'hotspots': list(reversed(['#d53e4f', '#fc8d59',
                               '#fee08b', '#ffffbf', "#e6f598",
                               '#99d594', '#3288bd']))
}

for color_group_name, hex_by_number in bokeh_colors.all_palettes.items():
    for n, hex_list in hex_by_number.items():
        colors[color_group_name + str(n)] = [hex_to_rgb(hex_color) for hex_color in hex_list]
