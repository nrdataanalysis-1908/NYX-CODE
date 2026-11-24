# NYX Scientific Use Cases

This document records representative use cases that may guide future NYX Data and NYX Science APIs. The programs below are conceptual proposals unless explicitly marked executable in the repository README.

## 1. Commercial analysis

Example: [01_sales_analysis.nyx](../examples/01_sales_analysis.nyx)

The intended workflow consolidates commercial indicators by region:

- load a CSV dataset;
- validate positive transaction values;
- select region and value columns;
- group records by region;
- calculate revenue, average ticket, and transaction count.

## 2. Sensor analysis

Example: [02_sensor_analysis.nyx](../examples/02_sensor_analysis.nyx)

The intended workflow evaluates sensor readings and summarizes data quality:

- exclude missing measurements;
- retain records marked as valid;
- group measurements by sensor;
- calculate sample count, mean, standard deviation, minimum, and maximum.

## 3. Scientific experiment analysis

Example: [03_scientific_experiment.nyx](../examples/03_scientific_experiment.nyx)

The intended workflow compares experimental groups using descriptive statistics:

- retain observations with non-null responses;
- apply quality criteria;
- group observations by experimental group;
- calculate sample size, mean response, median response, and dispersion.

## 4. Common tabular API

The three use cases converge on a possible minimal tabular domain:

1. read_csv(path): load a table and infer or validate its schema.
2. filter(expression): select rows using a Boolean expression.
3. select(columns...): project columns.
4. group_by(keys...): define grouping keys.
5. aggregate(named_expressions...): calculate aggregations.
6. show(): inspect a result in the local environment.

This API is a design proposal. It is not available in the current alpha runtime.

## 5. Open semantic decisions

The following decisions require formal specification before implementation:

- whether data is a declaration modifier or a type;
- whether composition uses method chaining, a pipeline operator, or both;
- how column names are resolved inside expressions;
- how null values are represented and propagated through aggregations;
- the return type of each transformation;
- whether evaluation is eager, lazy, or hybrid;
- how missing columns and incompatible types are diagnosed;
- how deterministic group ordering and numerical reproducibility are guaranteed.

## 6. Acceptance criteria for the first tabular API

The first tabular API should execute all three use cases with verifiable results, include positive and negative tests, and document missing-value, type, grouping, and aggregation rules. Until then, these examples remain conceptual syntax proposals.
