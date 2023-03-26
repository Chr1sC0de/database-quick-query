# Database Quick Query

- [Database Quick Query](#database-quick-query)
  - [Basic Configuration](#basic-configuration)
  - [Encrypting the Configuration File](#encrypting-the-configuration-file)
    - [Creating public and private keys](#creating-public-and-private-keys)
    - [Encrypting the config file](#encrypting-the-config-file)
    - [Setting the Environment Variables for Encrypted Files](#setting-the-environment-variables-for-encrypted-files)
  - [Connectors](#connectors)
    - [Caching](#caching)
    - [Describing Columns](#describing-columns)
    - [Running Queries from an SQL File](#running-queries-from-an-sql-file)
    - [Parsing Files](#parsing-files)
  - [Common Table Expressions](#common-table-expressions)
    - [Rollback](#rollback)
  - [Databricks](#databricks)

A wrapper over various database connector libraries for quickly performing
queries for analysis

## Basic Configuration

To configure login details for various databases fill out the following required
details into a `.yaml` file

```yaml
oracle:
    db1:
        username: '*******'
        password: '*******'
        hostname: '*******'
        port    : '*******'
        database: '*******'
.
.
.

databricks:
    db1:
      access_token   : '******'
      server_hostname: '*******'
      http_path      : '*******'

.
.
.

mssql:
    db1:
        username: '*******'
        password: '*******'
        hostname: '*******'
        port    : '*******'
        database: '*******'

.
.
.
```

set the environment variable `DBQQ_CONNECTORS` to the path of the configuration

## Encrypting the Configuration File

It might not be the best practice to store and distribute the data as a
raw yaml file. We can encrypt the data for added security.

### Creating public and private keys

To encrypt the data first create `public` and `private` keys using the
`dbqq-write-keys` method, find help bellow

```powershell
>> dbqq-write-keys.exe --help

usage: dbqq-write-keys.exe [-h] [--key_length KEY_LENGTH] [--location LOCATION] [--pb_key_name PB_KEY_NAME] [--pr_key_name PR_KEY_NAME] [--format {PEM,DER}] [--poolsize POOLSIZE]

optional arguments:
  -h, --help            show this help message and exit
  --key_length KEY_LENGTH, -k KEY_LENGTH
                        the length of th key
  --location LOCATION, -l LOCATION
                        the location to save the keys
  --pb_key_name PB_KEY_NAME, -pbn PB_KEY_NAME
                        the saved public key name
  --pr_key_name PR_KEY_NAME, -prn PR_KEY_NAME
                        the saved private key name
  --format {PEM,DER}, -f {PEM,DER}
                        The format the output the keys use PEM for human readable DER for purely binary format
  --poolsize POOLSIZE, -ps POOLSIZE
                        number of cores to use
```

An example can be found bellow

```powershell
>> dbqq-write-keys -k 1024 -l {} -pbn {} -f PEM
```

### Encrypting the config file

After creating the variables we can now encrypt the yaml file. To encrypt the
yaml file we can use `dbqq-encrypt-yaml`

```powershell
>> dbqq-encrypt-yaml.exe --help
usage: dbqq-encrypt-yaml.exe [-h] [--encrypted_file ENCRYPTED_FILE] file public_key

positional arguments:
  file
  public_key            location of the public key

optional arguments:
  -h, --help            show this help message and exit
  --encrypted_file ENCRYPTED_FILE, -ef ENCRYPTED_FILE
                        location to save encrypted file, if none save within current folder
```

the file must be saved with the extension `dbqq`

### Setting the Environment Variables for Encrypted Files

When the files are encrypted we need to set the `DBQQ_PRIVATE_KEY`
variable in conjunction with the `DBQQ_CONNECTORS` variable

## Connectors

The connectors module reads from the configuration files, categorizing the
details into (currently) either:

- oracle
- mssql
- databricks

for example, creating a connector for oracle using the details from `db1`

```python
from dbqq import connectors

connection = connectors.oracle.db1()

```

to run a query simply call the connection, remember to close the connection
after use


```python
polars_df = connection("select * from schema.table")
connection.close()
```

### Caching

During analysis we may want to cache queries for iteration. This can be
performed simply by calling the cache method

```python
connection.cache()("select * from schema.table")
```

the data will be saved as a metadata `.yaml` file with a corresponding
`.parquet` file. Identifier will be generated uniquely unless specified.

To set the location and name of the cached files

```python
connection.cache(directory="./cache_directory",name="name")(
    "select * from schema.table")
```

We might also want to save a new cache every day while clearing out old
files.

```python
from datetime import datetime, timedelta

connection.cache(
    date_lower_bound = datetime.now() - timedelta(days=1)
)("select * from schema.table")
```

### Describing Columns

To get information about the columns a `describe_columns` method has been
implemented.

```python
connection.describe("table_name")
```

### Running Queries from an SQL File

To run a query directly from a file

```python
connection.from_file("path to file", *args, **kwargs)
```

where `*args`, `**kwargs` are the arguments for a regular `__call__`.

### Parsing Files

For ease of use we may want to include the connector info and name of the query
in a file, i.e. for automating tasks.

```sql
--! <NAME>/connectors.oracle.<CONNECTION>
select * from some_table
```

```python
from dbqq import utils

name, query, connection = utils.parse_file("<path to file>")
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

## Databricks

when running on databricks a Cluster object is returned

```python
connection = dbqq.connectors.databricks.location() # when in databricks a cluster object is returned
if utils.in_databricks(): # write a function which checks if you are in databricks
    connection.sql = spark
...
```