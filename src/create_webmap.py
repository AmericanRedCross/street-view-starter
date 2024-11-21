import os
from pathlib import Path

from dotenv import load_dotenv
import geopandas as gpd
from jinja2 import Environment, FileSystemLoader
import matplotlib
import numpy as np
from shapely.geometry import box
import typer

try:
    from typing import Annotated
except ImportError:
    # for Python 3.9
    from typing_extensions import Annotated


app = typer.Typer()


def h3_to_webmap():
    return


@app.command()
def main(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to file containing h3 polygons."),
    ],
    filename: Annotated[
        str, typer.Argument(help="(Optional) Path to file for HTML output.")
    ] = "./data/processed/gvi_webmap.html",
    zoom_level: Annotated[
        int,
        typer.Argument(
            help="""(Optional) Starting zoom level for webmap. 
			Takes integer between 0 (small scale) and 20 (large scale).
			"""
        ),
    ] = 12,
):
    gdf = gpd.read_file(input_file)
    # if crs is not 4326, convert to 4326
    if gdf.crs == "EPSG:4326":
        pass
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # Round GVI score to make map labels more readable
    gdf["gvi_score"] = round(gdf["gvi_score"], 2)

    # get central coordinates of all features
    centre = (
        str(gdf.dissolve().centroid.x.values[0])
        + ", "
        + str(gdf.to_crs("4326").dissolve().centroid.y.values[0])
    )
    centre_str = "[" + centre + "]"

    # Calculate datasdet bounds (with a buffer of 0.5 degrees) to limit webmap bounds
    gdf_bounds = gdf.total_bounds
    bbox = box(*gdf_bounds).buffer(0.25, cap_style="square", join_style="mitre")
    bounds = bbox.bounds
    bounds_str = (
        "["
        + str(bounds[0])
        + ","
        + str(bounds[1])
        + "], ["
        + str(bounds[2])
        + ","
        + str(bounds[3])
        + "]"
    )

    # Load API key for map tiles from environment variable
    load_dotenv()

    if "MAPTILER_API_KEY" in os.environ:
        maptiler_api_key = os.getenv("MAPTILER_API_KEY")
    else:
        maptiler_api_key = "None"

    if maptiler_api_key in ["MY_MAPTILER_API_KEY", ""]:
        maptiler_api_key = "None"

    # Lookup the colourmap values for each GVI score
    cmap = matplotlib.colormaps["Greens"]
    gdf["gvi_norm"] = (gdf.gvi_score - np.min(gdf.gvi_score)) / (
        np.max(gdf.gvi_score) - np.min(gdf.gvi_score)
    )
    gdf["html_color"] = gdf["gvi_norm"].apply(
        lambda x: matplotlib.colors.rgb2hex(cmap(x))
    )

    # Generate divs for legend
    # Pick 4 evenly-spaced values from the gvi scores to use in the legend
    legend_gvi = list(
        np.arange(
            gdf.gvi_score.min(),
            gdf.gvi_score.max(),
            (gdf.gvi_score.max() - gdf.gvi_score.min()) / 4,
            dtype=float,
        )
    )

    # Generate labels by looking up what the GVI score would be for those values
    legend_label_1 = round(
        np.linspace(gdf.gvi_score.min(), gdf.gvi_score.max(), 100)[0], 1
    )
    legend_label_2 = round(
        np.linspace(gdf.gvi_score.min(), gdf.gvi_score.max(), 100)[33], 1
    )
    legend_label_3 = round(
        np.linspace(gdf.gvi_score.min(), gdf.gvi_score.max(), 100)[66], 1
    )
    legend_label_4 = round(
        np.linspace(gdf.gvi_score.min(), gdf.gvi_score.max(), 100)[99], 1
    )

    # Normalise the label values to lookup against the colourmap
    legend_gvi_norm = (legend_gvi - np.min(legend_gvi)) / (
        np.max(legend_gvi) - np.min(legend_gvi)
    )

    # Generate the html colour code from the normalised values
    legend_colours = []
    for i in legend_gvi_norm:
        legend_colours.append(matplotlib.colors.rgb2hex(cmap(i)))
    # Assign patch colours to use in HTML template
    legend_patch_1, legend_patch_2, legend_patch_3, legend_patch_4 = legend_colours

    # Load the MapLibre HMTL template
    environment = Environment(loader=FileSystemLoader("src/templates"))
    template = environment.get_template("maplibre_template.html")

    # Generate the HTML file from the template, filling dynamic values
    with open(filename, mode="w", encoding="utf-8") as message:
        message.write(
            template.render(
                title="GVI score hex map",
                geojson=gdf.to_json(),
                centre_coords=centre_str,
                zoom=zoom_level,
                bounds=bounds_str,
                maptiler_api_key=maptiler_api_key,
                legend_label_1=legend_label_1,
                legend_label_2=legend_label_2,
                legend_label_3=legend_label_3,
                legend_label_4=legend_label_4,
                legend_patch_1=legend_patch_1,
                legend_patch_2=legend_patch_2,
                legend_patch_3=legend_patch_3,
                legend_patch_4=legend_patch_4,
            )
        )


if __name__ == "__main__":
    app()
