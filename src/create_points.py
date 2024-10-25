"""Rewrite of createPoints.py from the mittrees/Treepedia_Public project.
See: https://github.com/mittrees/Treepedia_Public/blob/master/Treepedia/createPoints.py
"""

from pathlib import Path
from typing import List

try:
    from typing import Annotated
except ImportError:
    # For Python <3.9
    from typing_extensions import Annotated

import geopandas as gpd
from loguru import logger
import numpy as np
import shapely
import typer
from typer_config import use_toml_config
from typer_config.callbacks import argument_list_callback

DEFAULT_MINI_DIST = 20.0  # meters
DEFAULT_HIGHWAY_VALUES_TO_KEEP = [
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
]

app = typer.Typer()


def filter_by_highway_type(
    gdf: gpd.GeoDataFrame, highway_types: List[str] = DEFAULT_HIGHWAY_VALUES_TO_KEEP
):
    """Returns a copy of a GeoDataFrame of OpenStreetMap road features filtered by
    highway type.

    Args:
        gdf (geopandas.GeoDataFrame): OpenStreetMap features.
        highway_types (List[str]): List of OSM highway types to keep. Features whose
            'highway' value does not match the provided list will be filtered out.

    Returns:
        geopandas.GeoDataFrame: Copy of input GeoDataFrame of features filtered by
            highway type.
    """
    if "highway" not in gdf.columns:
        raise ValueError(
            "'highway' column not found in input GeoDataFrame. "
            "Input data must be of OpenStreetMap roads."
        )
    out_gdf = gdf[gdf["highway"].isin(highway_types)].copy()
    return out_gdf


def interpolate_along_line(
    line: shapely.LineString, mini_dist: float
) -> shapely.MultiPoint:
    """Given a LineString, returns a MultiPoint feature with interpolated points with
    distaince `mini_dist` between each point, excluding the endpoint.

    Args:
        line (shapely.LineString): input line
        mini_dist (float): distance in meters between interpolated points

    Returns:
        shapely.MultiPoint: new MultiPoint feature containing interpolated points
    """
    new_coords = [
        line.interpolate(dist)
        for dist in np.linspace(
            0.0, line.length, num=int(line.length / mini_dist), endpoint=False
        )
    ]
    return shapely.MultiPoint(new_coords)


def create_points(gdf: gpd.GeoDataFrame, mini_dist: float = DEFAULT_MINI_DIST):
    """Given a GeoDataFrame of OpenStreetMap data with LineString features, returns an
    exploded GeodataFrame of Point features interpolated along the lines with distance
    `mini_dist` in meters.

    Args:
        gdf (geopandas.GeoDataFrame): input GeoDataFrame of LineString features
        mini_dist (float): distance in meters between interpolated points

    Returns:
        geopandas.GeoDataFrame: new linestrings with interpolated points
    """
    if (gdf.geometry.isna()).any():
        raise ValueError(
            "Input GeoDataFrame contains null geometries. "
            "Rerun with --drop-null to exclude these features."
        )
    if (gdf.geom_type == "MultiLineString").any():
        gdf = gdf.explode()
    if not (gdf.geom_type == "LineString").all():
        raise ValueError("Input GeoDataFrame must contain only LineString features.")
    # Drop metadata other than 'osm_id'
    gdf = gdf[["osm_id", "highway", "geometry"]]
    # EPSG:3857 is pseudo WGS84 with unit in meters
    gdf = gdf.to_crs("EPSG:3857")
    # Interpolate along lines and explode
    gdf["geometry"] = gdf["geometry"].apply(interpolate_along_line, args=(mini_dist,))
    gdf = gdf.explode(ignore_index=True, index_parts=False)
    # Convert output to WGS84
    gdf.to_crs("EPSG:4326", inplace=True)
    return gdf


@app.command()
@use_toml_config(section=["create_points"])
def main(
    in_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to input OpenStreetMap roads data file. Must be a geospatial "
                "vector format readable by geopandas."
            )
        ),
    ],
    out_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to write interpolated points data. The file extension should "
                "correspond to a geospatial vector format writable by geopandas."
            )
        ),
    ],
    mini_dist: Annotated[
        float, typer.Option(help="Distance in meters between interpolated points.")
    ] = DEFAULT_MINI_DIST,
    drop_null: Annotated[
        bool,
        typer.Option(
            "--drop-null",
            help="Set whether features with null geometries should be removed",
        ),
    ] = False,
    highway_types: Annotated[
        List[str],
        typer.Option(
            "--highway-type",
            help="Set which OSM highway types to keep from input features.",
            callback=argument_list_callback,
        ),
    ] = DEFAULT_HIGHWAY_VALUES_TO_KEEP,
):
    """Create a dataset of interpolated points along OpenStreetMap roads."""
    logger.debug("mini_dist: {}", mini_dist)
    logger.debug("drop_null: {}", drop_null)
    logger.debug("highway_types: {}", highway_types)

    logger.info("Loading road features from: {}", in_file)

    gdf = gpd.read_file(in_file)
    gdf = filter_by_highway_type(gdf, highway_types=highway_types)
    if drop_null:
        gdf = gdf[~gdf.geometry.isna()]
    else:
        pass
    gdf = create_points(gdf, mini_dist=mini_dist)
    gdf.to_file(out_file)
    logger.success("Interpolated points written to: {}", out_file)


if __name__ == "__main__":
    app()
