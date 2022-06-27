import fnmatch
import os
import re


def _find_files(base_directory, pattern):
    for root, _, files in os.walk(base_directory):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                filename = os.path.join(root, file)
                yield filename


def _vrt_to_source_dicts(vrt_file, overview_levels):
    source_dicts = []  # To return

    name = os.path.splitext(os.path.basename(vrt_file))[0]
    sanitised_name = name.replace(" ", "-")

    source_dict = dict(
        name=name,
        text=name,
        description=name,
        key=sanitised_name,
        filepath=vrt_file,
        geometry_type="raster",
        cmap=["white", "red"],
        band="band_data",
        service_types=["tile"],
    )

    transforms = []

    # Check for existence of overviews, regardless of whether they are
    # requested or not.
    overview_directory = os.path.join(os.path.split(vrt_file)[0], "overviews")
    if os.path.isdir(overview_directory):
        pattern = re.compile(r"(\d+)_" + source_dict["band"] + ".tif")
        for file in os.listdir(overview_directory):
            m = pattern.match(file)
            if m:
                if overview_levels is None:
                    overview_levels = []
                overview_levels.append(int(m.group(1)))

    if overview_levels:
        overview_levels = sorted(list(set(overview_levels)))
        levels = {level: 256*(2**level) for level in overview_levels}
        transform = dict(
            name="build_raster_overviews",
            args=dict(levels=levels),
        )
        transforms.append(transform)

    if transforms:
        source_dict["transforms"] = transforms

    source_dicts.append(source_dict)

    return source_dicts


def directory_to_config(directory, overview_levels=None):
    # Scan directory for possible map sources.
    print("directory_to_config", directory)

    if not os.path.isdir(directory):
        raise RuntimeError(f"Not a directory: '{directory}'")

    source_dicts = []
    for filename in _find_files(directory, "*.vrt"):
        source_dicts += _vrt_to_source_dicts(filename, overview_levels)

    return source_dicts
