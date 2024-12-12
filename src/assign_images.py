from os import getenv
from pathlib import Path
import sys
from typing import Annotated

import geopandas as gpd
from loguru import logger as log
from pandas import Series
from requests.exceptions import HTTPError
from tenacity import RetryError
from tqdm import tqdm
from typer import Argument, Option, Typer

from src.images.image_source import ImageSourceSelector
from src.images.local_images import LocalImages
from src.images.mapillary import Mapillary

app = Typer()


@app.command()
def main(
    points_file: Annotated[
        Path,
        Argument(help="Path to input points file"),
    ],
    image_source: Annotated[
        ImageSourceSelector, Argument(help="Where to get images from")
    ],
    images_path: Annotated[
        Path,
        Argument(help="Where the images should be located"),
    ],
    output_file: Annotated[
        Path,
        Argument(
            help="File to write output data to (can specify any GDAL-supported format)."
        ),
    ],
    max_distance: Annotated[
        float,
        Option(help="Maximum distance between point and image location, in meters"),
    ] = 10,
    verbose: Annotated[bool, Option(help="Sets log level to DEBUG")] = False,
) -> Path:
    """
    Assigns Images to Points
    Args:
        points_file: Path to input points file
            File format should be readable by geopandas.read_file
        image_source: Where to get images from
        images_path: Where the images should be located
        output_file: file to save GeoPackage output to (provide full path)
        max_distance: Maximum distance between point and image location, in meters
            Can also be interpreted as "radius" of image bounding box
        verbose: Sets log level to DEBUG

    Returns: The Path of the output GPKG file
    """

    log.remove()
    if verbose:
        log.add(sys.stdout, level="DEBUG")
    else:
        log.add(sys.stdout, level="INFO")

    if image_source == ImageSourceSelector.local:
        source = LocalImages(images_path, max_distance)
    elif image_source == ImageSourceSelector.mapillary:
        source = Mapillary(getenv("MAPILLARY_CLIENT_TOKEN"), images_path, max_distance)
    else:
        raise ValueError(f"Unknown Image Source: {image_source}")

    gdf = gpd.read_file(points_file)
    gdf["image_id"] = Series()
    gdf["image_lat"] = Series()
    gdf["image_lon"] = Series()
    gdf["residual"] = Series()
    gdf["image_path"] = Series()
    gdf["error"] = Series()

    for i, point in tqdm(
        gdf.iterrows(),
        total=len(gdf.index),
        desc="Assigning Images to Points",
        unit="points",
    ):
        latitude = point["geometry"].y
        longitude = point["geometry"].x

        try:
            results = source.get_image_from_coordinates(latitude, longitude)
            gdf.at[i, "image_lat"] = results["image_lat"]
            gdf.at[i, "image_lon"] = results["image_lon"]
            gdf.at[i, "residual"] = results["residual"]
            gdf.at[i, "image_id"] = results["image_id"]
            gdf.at[i, "image_path"] = str(results["image_path"])
            gdf.at[i, "error"] = results["error"]
        except HTTPError or RetryError as e:
            log.error(e)
            gdf.at[i, "error"] = e.__class__.__name__

    log.info(gdf.head())
    log.info(
        "Are There Duplicates? {}",
        gdf[gdf["image_id"] is not None and gdf["image_id"].notna()]["image_id"]
        .duplicated()
        .any(),
    )

    output_file = output_file.resolve()
    gdf.to_file(output_file, driver="GPKG")
    log.success("Saved Points and Images to {}", output_file)

    return output_file


if __name__ == "__main__":
    app()
