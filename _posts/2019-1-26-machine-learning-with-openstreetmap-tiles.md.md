---
layout: post
title: Machine Learning with OpenStreetMap tiles
---

![Estimating population using openstreetmap tiles]({{ site.baseurl }}/images/estimating_population_from_openstreetmap_tiles.png)

[OpenStreetMap](https://www.openstreetmap.org/) is an amazing data source.  The collective effort of 1000s of volunteers has created a rich set of information that covers almost every location on the planet.

There are a large number of problems where this information could be helpful:
- city planning, characterising the features of a neighborhood
- identifying suitable locations for marketing campaigns
- researching land usage, public transit infrastructure
- identifying accident hotspots

However for each specific problem domain, there is a significant amount of work to be done to decide which map features will be informative for the task at hand.  One then needs to write code to extract those features from the OpenStreetMap database.  A simple alternative to this manual feature engineering approach could be to use convolutional networks on the rendered map tiles.

### How could convolutional networks be used?

If there is enough information in the map tiles, a convolutional network may be able to learn which of the map tiles features are predictive for the specific problem domain.  The designers of the OpenStreetMap have done a great job of making sure the map rendering exposes as much information as the visual system can work with, and convolutional networks have proven very capable of mimicking the performance of the visual system.  If there is information in the spatial distibution of the features, then there is a chance a convolutional network can make use of that information, something that would be hard to do with a manual feature engineering approach.

### Testing the hypothesis

To test whether convolutional networks can learn useful features from map tiles, I've chosen simple test problem:  **Estimate the population for a given map tile**.  The USA census provides data on population numbers at the census tract level, and we can **use the populations of the tracts to approximate the populations of map tiles**.

The steps involved:
1. Download population data at the census tract level from the [Census Bureau](https://www.census.gov/geo/reference/centersofpop.html).
2. For a given zoom level, identify the OpenStreetMap tiles which intersect with 1 or more census tracts.
3. Download the tiles from a local instance of [OpenMapTiles](https://openmaptiles.org/).
4. Sum the population of the tracts inside each tile, and add the fractional populations for tracts the intersect with the tile

[map of intersecting tracts]

This gives us:
- **Input X**: an RGB bitmap representation of the OSM tile
- **Target Y**: the estimated population of the tile

For this experiment I generated a dataset for California tiles and tracts, but the same process can be done for every US state.  By using a simplified Densenet architecture, and minimising the mean-squared error on the log scale, the network achieves the following cross-validation performance after a few epochs.

![Convolutional network predicting population of OpenStreetMap tiles outperforms baseline mean estimator]({{ site.baseurl }}/images/conv_net_performance.png)

This equates to a mean-absolute error of 0.51 on the log-scale for each tile.  So the prediction tends to be of the right order of magnitude, but off by a factor of 3X (we haven't done our best to optimize performance, so this isn't a bad start).

## Summary:

- In the example of estimating population there is enough information in openstreetmap tiles to significantly outperform a naive estimator of population.
- For problems with a strong enough signal, OpenStreetMap tiles can be used as a data source without the need for manual feature engineering

Credits:
- Many thanks to all the volunteers behind [OpenStreetMap](https://www.openstreetmap.org/)
- The US government which makes the census data freely available
- [OpenMapTiles](https://openmaptiles.org/) for providing a map rendering service for research purposes
