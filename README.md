# street-view-green-view

## Project description

### Goal

We want to automate mapping of urban vegetation from street level imagery (SLI) to create an informative layer for exploring which areas of a city might be at greater risk during future heat waves and for engaging people in discussions about green and nature-based solutions for climate adaptation. 

The collection and analysis of SLI can be used as part of a citizen science workflow. We hypothesize that a participatory approach to assessing issues like extreme heat hazards from climate change can empower communities by: giving them a greater understanding of the hazards facing their community, building their confidence in designing effective actions to reduce the impacts of those hazards, and strengthening connections between community members.

### Project inspiration

This project was inspired by the [Treepedia project](https://github.com/mittrees/Treepedia_Public) from [MIT Senseable City Lab](https://senseable.mit.edu/). Treepedia aimed to raise a proactive awareness of urban vegetation improvement, using computer vision techniques applied to Google Street View images. Treepedia measured and mapped the amount of vegetation cover along a city's streets by computing the Green View Index (GVI) on Google Street View (GSV) panoramas. Their method considered the obstruction of tree canopies and classified the images accordingly.

We plan to either collect imagery ourselves and use it in a local-only workflow, or we can leverage the crowd-sourced, openly licensed imagery uploaded to [Mapillary](https://www.mapillary.com/). This will give us greater control over the recency of the images and the geographic coverage of the images, and it may lower costs. 

### Why street level imagery (SLI)?

Satellite imagery is a well-known source of data, but launching a satellite is a costly endeavor and there are limits to what we can interpret from it. SLI provides an accessible way to gather images from a different perspective with exciting implications for humanitarians. 
- Effective hardware for SLI is no longer limited to vehicle-top rigs costing tens of thousands of dollars like those used by Google for their Street View service. There are a variety of options for high quality digital action cameras at a reasonable price that are durable, rugged, can capture at a frequent interval, and can automatically tag images with GPS coordinates. 
- There are more powerful computing resources, better data storage and transfer options, and innovations in algorithms and machine learning tools are making it easier and more accessible to quickly collect data, process large amounts of data, and automate extraction of insights. 
- There is a growing ecosystem of open tools and open data for SLI that organizations can use, build on, and contribute to.

### Contributing

This project is a collaboration with [Civic Tech DC](https://civictechdc.org/).

If you are interested in joining the project, please check out [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Usage

### 0. Setup

> [!NOTE]
> This project has a `Makefile` with some convenience commands that came be invoked like `make <command name>`, e.g.. `make requirements`. You can either use them or do things yourself manually.

1. Create a Python virtual environment.
     - You can use the shortcut command `make create_environment`.
     - The log will tell you how to activate the environment. Do so with: `source .venv/bin/activate`
2. Install the project and its requirements.
    ```bash
    pip install -e .
    ```
    - You can use the shortcut command `make requirements` to do the same thing.
3. Put your raw OpenStreetMaps road vector data in `data/raw`.
    - Your raw data should be geospatial vector features of type `LineString`. The features must include standard OpenStreetMap keys `osm_id` and `highway`.
    - For example, download [`Three_Rivers_Michigan_USA_line.zip`](https://drive.google.com/file/d/1fpI4I5KP2WyVD5PeytW_hoXZswOt0dwA/view?usp=drive_link) to `data/raw/Three_Rivers_Michigan_USA_line.zip`. Note that this Google Drive link is only accessible to approved project members.
4. Make a copy of the `.env.example` file, removing the `.example` from the end of the filename.
    - To download images from [Mapillary](https://www.mapillary.com/) you will need to create a (free) account and replace `MY_MAPILLARY_CLIENT_TOKEN` in the `.env` file with your own token. See the "Setting up API access and obtaining a client token" section on this [Mapillary help page](https://help.mapillary.com/hc/en-us/articles/360010234680-Accessing-imagery-and-data-through-the-Mapillary-API). You only need to enable READ access scope on your token.

### 1. Sample points from roads data

The first step is to sample points along the roads in your provided data. You can use the [`create_points.py`](./src/create_points.py) script to sample these points and write them out to a new file. This script filters out certain types of highways, and then samples points along each remaining road. By default, the sampling distance is 20 meters.

#### Example

For example, if you're using the `Three_Rivers_Michigan_USA_line.zip` data mentioned in the "Setup" section above:

```bash
python -m src.create_points data/raw/Three_Rivers_Michigan_USA_line.zip data/interim/Three_Rivers_Michigan_USA_points.gpkg
```

This will write out a zipped shapefile containing the sampled points to `data/interim/Three_Rivers_Michigan_USA_points.gpkg`. The input and output formats can be any vector-based spatial data format [supported by geopandas](https://geopandas.org/en/stable/docs/user_guide/io.html), such as shapefiles, GeoJSON, and GeoPackage. The output format is automatically inferred from the file extension.

#### Advanced usage

For additional documentation on how to use `create_points.py`, you can run:

```bash
python -m src.create_points --help
```

Both the input files and output files support any file formats that geopandas supports, so long as it can correctly infer the format from the file extension. See the [geopandas documentation](https://geopandas.org/en/stable/docs/user_guide/io.html) for more details.

### 2. Match an image to each point

We want a 360 image for each of the sampled points. There is more than option for the imagery source, but you have to choose one option. You cannot use multiple sources (at least at this time). You can use the [`assign_images.py`](./src/assign_images.py) script to find the closest image to each point and generate a new file with the data included. The output will have `_images` appended to the filename.

#### Example

For example, if you're continuing from the example in previous steps and already generated a `Three_Rivers_Michigan_USA_points.gpkg` file:

```bash
python -m src.download_images data/interim/Three_Rivers_Michigan_USA_points.gpkg MAPILLARY data/raw/images/Three_Rivers_Michigan_USA/
```

### 3. Assign a Green View score to each image/feature

Now that we have a point feature for each image, we want to analyze each image 
and assign a score to the relevant point feature. We can use the 
[`score_images.py`]('./src/score_images.py') script for this. We have two 
methods implemented. 

With the `PIXELS` option, we can calculate a Green View Index (GVI) score.
For more information on how GVI is calculated, see Li et al. (2015), 
[_Who lives in greener neighborhoods?_](https://doi.org/10.1016/j.ufug.2015.07.006), 
Urban Forestry & Urban Greening 14, pp.751--759.

With the `SEGMENTATION` option, we can also use a pre-trained machine learning 
model to label the parts of each image then store the percentage labelled 
vegetation.

#### Example

This example follows from the files and directories created in previous steps and 
saves an output to a new file. 

```bash
python -m src.score_images data/interim/Three_Rivers_Michigan_USA_points_images.gpkg SEGMENTATION data/processed/Three_Rivers_segmentation_score.gpkg
```



## Project Organization

    ├── LICENSE
    ├── Makefile                       <- Makefile with commands like `make data` or `make train`
    ├── README.md                      <- The top-level README for developers using this project.
    ├── data
    │   ├── interim                    <- Intermediate data that has been transformed.
    │   ├── processed                  <- The final, canonical data sets for modeling.
    │   └── raw                        <- The original, immutable data dump.
    │
    ├── notebooks                      <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                                  the creator's initials, and a short `-` delimited description, e.g.
    │                                  `1.0-jqp-initial-data-exploration`.
    │
    ├── pyproject.toml                 <- Single source of truth for dependencies, build system, etc
    └── src                            <- Source code for use in this project.
        └── __init__.py                <- Makes src a Python module
        └── create_points.py           <- Creates a list of points along the roads of an area
        └── download_images.py         <- Downloads images from the list of points
        └── assign_gvi_to_points.py    <- Calculates a Green View Index (GVI) from the images

--------

<p><small>Project structure based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
