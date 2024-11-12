# Database Quick Query

- [Database Quick Query](#database-quick-query)
  - [Environment Variables](#environment-variables)
  - [Initialization](#initialization)
  - [Connection Configuration](#connection-configuration)
    - [Parameter Stores](#parameter-stores)
  - [Encrypting Configs](#encrypting-configs)
    - [Creating Private and Public Keys](#creating-private-and-public-keys)
    - [Encrypting The Configuration File](#encrypting-the-configuration-file)
  - [Connectors](#connectors)
    - [Caching](#caching)
    - [Getting Basic Table Metadata](#getting-basic-table-metadata)
    - [Running Queries from a File](#running-queries-from-a-file)
      - [Extracting queries and connections from a file](#extracting-queries-and-connections-from-a-file)
        - [Basic Connection No Cache](#basic-connection-no-cache)
        - [Connection With Cache](#connection-with-cache)
        - [Connection With Cache and Date Lower Bound](#connection-with-cache-and-date-lower-bound)
    - [Parsing Files](#parsing-files)
    - [Jinja Templates](#jinja-templates)
  - [Common Table Expressions](#common-table-expressions)
    - [Rollback](#rollback)
  - [Databricks Development](#databricks-development)
  - [CLI Tools](#cli-tools)
    - [dbqq-clean-connections](#dbqq-clean-connections)
    - [dbqq-run-sql](#dbqq-run-sql)

A wrapper over various database connector libraries for quickly performing
queries for analysis. The package leverages [polars](https://www.pola.rs/) and
[connectorx](https://github.com/sfu-db/connector-x) for their speed when handling Big data.

## Environment Variables

Example environment variable setup

```powershell
# path to private key
$env:DBQQ_PRIVATE_KEY = ".\private_key.pem" or ".\private_key.der" or "none"
# path to connections, supports encrypted or flat yaml files
$env:DBQQ_CONNECTORS = ".\connections.dbqq" or ".\connections.yaml"
# if we have aws parameter store configuration
$env:DBQQ_SSM_NAME= "name of parameter"
```

## Initialization

Connections are loaded dynamically, and are initially blank within the
connection files

```python
# dbqq/connectors/databricks.py etc.

#! begin inject regex

#! end inject regex
```

To initialize connections, simply install the package and run the command

```powershell
dbqq-initialize-connectors
```

As an example, after importing the package the configured connections should now
be visible within the connection files. The following will be the result of an
initialization given the configs in the `Connection Configuration` section.

```python
# dbqq/connectors/databricks.py

#! begin inject regex

class preprod(_general_connector):
    source: str = 'preprod'

class prod(_general_connector):
    source: str = 'prod'

class test(_general_connector):
    source: str = 'test'

class dev(_general_connector):
    source: str = 'dev'

#! end inject regex
```

## Connection Configuration

To configure login details for various databases fill out the following required
details into a `.yaml` (optionally now encrypt the file and delete the yaml)
and set the environment variable `DBQQ_PRIVATE_KEY` to the location of the file.

```yaml
databricks:
  dev:
    access_token: "*******"
    http_path: "*******"
    server_hostname: "*******"
  test:
    access_token: "*******"
    http_path: "*******"
    server_hostname: "*******"
  preprod:
    access_token: "*******"
    http_path: "*******"
    server_hostname: "*******"
  prod:
    access_token: "*******"
    http_path: "*******"
    server_hostname: "*******"
mssql:
  conn1:
    authentication_type: "*******"
    database: "*******"
    driver: "*******"
    hostname: "*******"
    password: "*******"
    port: "*******"
    username: "*******"
  conn2:
    trusted_connection: true
    server: "*****"
    driver: "{*****}"
  conn3:
    trusted_connection: true
    server: "*****"
    driver: "{*****}"
    database: "*****"
oracle:
  conn1:
    authentication_type: "*******"
    connection_type: "*******"
    database: "*******"
    hostname: "*******"
    password: "*******"
    port: "*******"
    role: "*******"
    username: "*******"
  conn2:
    authentication_type: "*******"
    connection_type: "*******"
    database: "*******"
    hostname: "*******"
    password: "*******"
    port: "*******"
    role: "*******"
    username: "*******"
redshift:
  conn1:
    database: "*******"
    hostname: "*******"
    password: "*******"
    port: "*******"
    username: "*******"
  conn2:
    database: "*******"
    hostname: "*******"
    password: "*******"
    port: "*******"
    username: "*******"
```

### Parameter Stores

Parameters can be extracted from the AWS Parameter Store, which overrides local
configs. To retrieve the parameters, set the `name` and the `region`. By default,
the region is set to `ap-southeast-2``.

```powershell
$env:DBQQ_SSM_NAME="name"
$env:DBQQ_SSM_REGION="region"
```

## Encrypting Configs

It is probably not the best idea to store passwords as a flat file on your local
computer. We have added the ability to encrypt configuration files via the
`dbqq-encrypt-yaml.exe`.

### Creating Private and Public Keys

Before we can encrypt our configuration file we need to create both private and
public keys. For our example let's say we have a working directory
with the following configuration file

```powershell
C:\devops> ls

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----                                            config.yaml

```

create a folder called keys

```powershell
C:\devops> mkdir keys
```

we can use the `dbqq-write-keys.exe` method to generate the private and public
keys

```powershell
C:\devops> dbqq-write-keys -l './keys' -k 1024 # supports der or pem call -h for help
C:\devops> ls keys
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----                                            private_key.der
-a----                                            public_key.der
```

### Encrypting The Configuration File

Apply `dbqq-encrypt-yaml` on the config file with the generated private key

```powershell

C:\devops> dbqq-encrypt-yaml 'config.yaml' './keys/private_key.der'
C:\devops> ls keys
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----                                            config.dbqq

```

Finally secure the private key

## Connectors

The connectors module reads from the configuration files, categorizing the
details into (currently) either an `oracle`, `mssql`, `databricks`, `redshift` connection.

Given our example configuration file we can create an `oracle` to db `conn1` by
calling:

```python
import polars as pl
from dbqq import connectors

connection = connectors.oracle.db1()

```

to run a query simply call the connection

```python
df: pl.LazyFrame = connection("select * from some.table")
```

connection calls always return a polars
[LazyFrame](https://pola-rs.github.io/polars/py-polars/html/reference/lazyframe/index.html).
This is because LazyFrames allow for whole-query optimisation in addition to
parallelism, making them the preferred (and highest-performance) mode of
operation for polars.

Run `collect` to work with a DataFrame or `fetch` to partially collect

```python
df: pl.Dataframe = df.collect()
```

### Caching

During the analysis, we may want to cache queries for iteration. This can be
performed simply by calling the cache method:

```python
connection.cache()("select * from schema.table")
```

the data will be saved as a `.parquet` file with a corresponding `.yaml` file.
The cached files will be stored in the `.temp` folder with a unique identifier
unless specified.

To set the location and name of the cached files

```python
connection.cache(directory="./cache_directory",name="name")(
    "select * from schema.table")
```

Finally, we might want to save a new cache every day while clearing out old
files. This can be done using the `date_lower_bound` keyword argument. Files
before this date will be deleted for **all** cached queries.

```python
from datetime import datetime, timedelta

connection.cache(
    date_lower_bound = datetime.now() - timedelta(days=1)
)("select * from schema.table")
```

### Getting Basic Table Metadata

To get information about the columns before running the query run the
`describe_columns` method on the table using the required connection.

```python
connection.describe("table_name")
```

To get the schema of the table call the `schema` attribute on the LazyFrame

```python
df: pl.LazyFrame = connection("select * from some.table")
df.schema
```

### Running Queries from a File

To run a query directly from a file

```python
connection.from_file("path to file", *args, **kwargs)
```

where `*args`, `**kwargs` are the arguments for a regular `__call__`.

#### Extracting queries and connections from a file

We can include metadata to an sql file and call the `connectors.from_file`
method to extract both a the connection and query. There are 3 ways we can
include metadata.

##### Basic Connection No Cache

To create a simple connection we can add the following configuration string
to the sql file.

```sql
--! name/connector.{type}.{db}
select * from some.table
```

Replace {} with connection information i.e. databricks.prod.

The configuration string will be removed from the query.

```python
connection, query = connectors.from_file(filepath)
df = connection(query)

```

##### Connection With Cache

To create a connection with a path to a cache file add a string to the
configuration specifying the path to the cache folder. The `name` provided will
be used as the name of the cache i.e. `name.parquet`. If `name`=`_` then a
unique identifier will be used as the name for the cache.

```sql
--! name/"./temp"/connector.{type}.{db}
select * from some.table
```

##### Connection With Cache and Date Lower Bound

To add a date lower bound add a command which can be evaluated by python. Note, datetim and timedelta
are imported during the eval process.

```sql
--! name/"./temp"/datetime.now()-timedelta(days=7)/connector.{type}.{db}
select * from some.table
```

### Parsing Files

We might simply want to parse the files i.e. for automating tasks.

```python
from dbqq import utils

data = utils.parse_file("<path to file>")
```

data for parsed sql can be found in connectors.data.parsed.sql

### Jinja Templates

We can parse jinja templates, let's say we have a template called `test_query.sql.j2`

```jinja
select
{% for item in  columns %}
{% if loop.last %}
    {{ item }}
{% else %}
    {{ item }},
{% endif %}
{% endfor %}
from
  some.table
```

We can create a `RenderedTemplateLoader` from it using the following

```python
import dbqq.connectors as dbc

conn = dbc.<source>.<conn>()

rendered_template_loader = conn.render_template(
    "test_query.sql.j2",
    columns=[
      "col1",
      "col2",
      "col3",
      "col4"
    ],
)

# will return a object that shows the renderedquery

"""
select
  col1,
  col2,
  col3,
  col4
from
  some.table
"""

table = rendered_template_loader.execute()

```

## Common Table Expressions

We can construct a common table expression with the following method

```python
from dbqq import utils
from triple_quote_clean import TripleQuoteCleaner

tqc = TripleQuoteCleaner(skip_top_lines=1)

cte = utils.CommonTableExpression()

cte.add_query(
    "query_1",
    """--sql
        select *
        from table_1
    """ >> tqc
)

cte.add_query(
    "query_2",
    """--sql
        select
            *
        from
            table_2 t2
        inner join table_1 t1
            on t1.col1 = t2.col2

    """ >> tqc
)

print(cte("select * from table_2"))
```

output

```sql
with
query_1 as (
    select *
    from table_1
)
,
query_2 as (
    select
        *
    from
        table_2 t2
    inner join table_1 t1
        on t1.col1 = t2.col2
)
select * from table_2
```

### Rollback

When in a jupyter notebook we can rollback queries during the development process

```python
cte.rollback_one() # or rollback(version_no)
cte.add_query(
    query_name,
    query
)
```

this allows us to modify the cte on the fly

## Databricks Development

sometimes we may want to develop databricks queries locally, and use spark when
in databricks.

```python
connection = dbqq.connectors.databricks.prod()
...
```

when in databricks the connection will be automatically converted into a

```python
dbqq.connectors.databricks.Cluster
```

object, which now will use the spark context to run queries.

## CLI Tools

### dbqq-clean-connections

Clean up all the connections, useful for a fresh start

```powershell
usage: dbqq-clean-connections.exe [-h]

Clean up all connection information

optional arguments:
  -h, --help  show this help message and exit
```

### dbqq-run-sql

run the sql with the provided configurations

```powershell
usage: dbqq-run-sql.exe [-h] [-n ROWS] [-i {0,1}] file

Run a query directly from an file

positional arguments:
  file                  *.sql file to be run

optional arguments:
  -h, --help            show this help message and exit
  -n ROWS, --rows ROWS  the total number of rows to show number, specify 'all' to show all
  -i {0,1}, --show_index {0,1}
                        show the index
```

Combine [parquet to csv](https://github.com/Chr1sC0de/ParquetToCSV) to view/convert the output
