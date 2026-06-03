# Pipeline Docker Practice

This folder is a small learning project for running a Python data pipeline
inside Docker.

The goal is not only to make the code run. The goal is to understand what each
Dockerfile line is doing, why it exists, and how Docker turns your local files
into a runnable image.

## The Big Picture

Normally, you can run the pipeline directly on your computer:

```bash
python pipeline.py 10
```

That works only if your computer already has:

- the right Python version
- the right Python packages
- access to the project files
- a working environment where `pandas` and `pyarrow` are installed

Docker lets you package those requirements into an image.

An image is like a saved recipe/result for an environment. A container is a
running copy of that image.

In this project:

```text
Dockerfile -> docker build -> Docker image -> docker run -> Container
```

Your Dockerfile teaches Docker how to build an image that can run:

```bash
uv run python pipeline.py 2
```

inside the container.

## Files in This Folder

```text
pipeline/
  Dockerfile       Instructions for building the Docker image
  pipeline.py      Main script that creates a DataFrame and writes Parquet
  pyproject.toml   Project metadata and dependency list
  uv.lock          Exact locked dependency versions
  .python-version  Python version requested by the project
  main.py          Starter script created by the Python project template
```

Generated files such as `output_day_10.parquet` are ignored by Git because the
repo's `.gitignore` includes:

```text
*.parquet
```

That is useful because output data files are usually generated artifacts, not
source code.

## What `pipeline.py` Does

`pipeline.py` accepts one command-line argument: the day number.

Example:

```bash
python pipeline.py 10
```

The script does this:

1. Imports `sys` so it can read command-line arguments.
2. Imports `pandas` so it can create a DataFrame.
3. Prints `sys.argv` so you can see what arguments Python received.
4. Creates a small DataFrame.
5. Reads the first argument as the day number.
6. Writes the DataFrame to a Parquet file.

This line reads the day argument:

```python
day = int(sys.argv[1])
```

If you run:

```bash
python pipeline.py 10
```

then Python sees:

```python
sys.argv == ["pipeline.py", "10"]
```

So:

```python
sys.argv[0] == "pipeline.py"
sys.argv[1] == "10"
```

That is why the script uses `sys.argv[1]`.

For day `10`, the script writes:

```text
output_day_10.parquet
```

For day `2`, it writes:

```text
output_day_2.parquet
```

## Dockerfile

Current Dockerfile:

```dockerfile
# Start with slim Python 3.13 image
FROM python:3.13.10-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Copy application code
COPY pipeline.py pipeline.py

# Set entry point
ENTRYPOINT ["uv", "run", "python", "pipeline.py"]
```

## Dockerfile Line by Line

### `FROM python:3.13.10-slim`

Every Dockerfile starts from a base image.

This line means:

```text
Start with an existing image that already has Python 3.13.10 installed.
```

Why use it:

- You do not need to install Python yourself.
- Docker starts from a known Python environment.
- The `slim` version is smaller than the full Python image.

Why not start from nothing:

You could start from a very minimal Linux image, but then you would need to
install Python and system tools yourself. For learning and for many Python apps,
the official Python image is simpler.

### `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/`

This copies the `uv` executable from the official `uv` Docker image into your
image.

Broken down:

```text
COPY                 copy a file into this image
--from=...           copy from another Docker image, not from your laptop
/uv                  source file inside the uv image
/bin/                destination folder inside your image
```

In plain English:

```text
Take the /uv program from the uv image and put it in /bin/ in my image.
```

Why use it:

- Your image needs the `uv` command.
- Later, the Dockerfile runs `uv sync --locked`.
- The final container runs `uv run python pipeline.py`.

Without this line, Docker would reach:

```dockerfile
RUN uv sync --locked
```

and fail because `uv` would not exist inside the image.

This is called a multi-stage-style copy because you copy something from another
image. You are not using the whole `uv` image as your final image. You are only
borrowing the `uv` binary from it.

### `WORKDIR /app`

This sets the working directory inside the image.

It is similar to running:

```bash
cd /app
```

inside the container.

Why use it:

- It gives your project a clean home inside the container.
- Later `COPY` commands copy files into `/app`.
- Later commands run from `/app`.

After this line:

```dockerfile
COPY pipeline.py pipeline.py
```

means:

```text
copy local pipeline.py to /app/pipeline.py
```

Without `WORKDIR`, Docker would use its default location, which can make file
paths less clear.

### `ENV PATH="/app/.venv/bin:$PATH"`

This sets an environment variable inside the image.

`PATH` tells Linux where to look when you type a command.

For example, when you run:

```bash
python
```

Linux searches through folders listed in `PATH`.

This line puts the virtual environment first:

```text
/app/.venv/bin
```

The `:$PATH` part keeps the old PATH after it.

Why use it:

- `uv sync --locked` creates a virtual environment at `/app/.venv`.
- Commands inside that environment live in `/app/.venv/bin`.
- Putting `/app/.venv/bin` first means the container prefers the project's
  Python environment.

In plain English:

```text
Use this project's virtual environment before using the system Python tools.
```

Without `:$PATH`, you would replace the old PATH completely, which could hide
normal system commands. That is why this line adds to PATH instead of replacing
it.

### `COPY "pyproject.toml" "uv.lock" ".python-version" ./`

This copies dependency-related files into the image.

The files are:

```text
pyproject.toml   says what the project depends on
uv.lock          records exact package versions
.python-version  records the Python version used by the project
```

The destination is:

```text
./
```

Because `WORKDIR /app` was already set, `./` means:

```text
/app
```

So this line copies the files into:

```text
/app/pyproject.toml
/app/uv.lock
/app/.python-version
```

Why copy these before `pipeline.py`:

Docker builds images in layers. If a layer does not change, Docker can reuse it
from cache.

Dependencies usually change less often than application code. So this order is
intentional:

```dockerfile
COPY "pyproject.toml" "uv.lock" ".python-version" ./
RUN uv sync --locked
COPY pipeline.py pipeline.py
```

If you edit only `pipeline.py`, Docker can often reuse the dependency install
layer instead of reinstalling all packages.

That makes rebuilds faster.

### `RUN uv sync --locked`

`RUN` means:

```text
Run this command while building the image.
```

`uv sync` means:

```text
Create/sync the project environment based on pyproject.toml and uv.lock.
```

`--locked` means:

```text
Use the existing uv.lock exactly. Do not update it.
```

Why use it:

- It installs project dependencies like `pandas` and `pyarrow`.
- It uses the exact versions from `uv.lock`.
- It makes builds more reproducible.

This is the `uv` version of installing dependencies.

A simpler Dockerfile might use:

```dockerfile
RUN pip install pandas pyarrow
```

That works, but it is less reproducible because package versions can change over
time.

With:

```dockerfile
RUN uv sync --locked
```

the image uses the versions recorded in `uv.lock`.

### `COPY pipeline.py pipeline.py`

This copies your application code into the image.

Because `WORKDIR /app` is active, this means:

```text
copy local pipeline.py to /app/pipeline.py
```

Why this comes after dependency installation:

- `pipeline.py` may change often.
- Dependencies change less often.
- Keeping this line after `RUN uv sync --locked` helps Docker cache dependency
  installation.

If you copied all project files before installing dependencies, then every code
change could force Docker to reinstall packages.

### `ENTRYPOINT ["uv", "run", "python", "pipeline.py"]`

`ENTRYPOINT` tells Docker what command to run when the container starts.

This line means:

```bash
uv run python pipeline.py
```

The square bracket syntax is called exec form.

Each item is one part of the command:

```text
["uv", "run", "python", "pipeline.py"]
  |     |      |          |
  |     |      |          script name
  |     |      Python command
  |     uv subcommand
  command to start
```

Why use `uv run`:

- It runs the command inside the project environment.
- It makes sure the installed packages from the `uv` environment are available.

Why use exec form:

- Docker receives the command as a clear list of arguments.
- There is no extra shell parsing.
- Extra arguments from `docker run` are appended cleanly.

When you run:

```bash
docker run -it test:pandas 2
```

Docker combines the entrypoint with `2`:

```bash
uv run python pipeline.py 2
```

Then Python sees:

```python
sys.argv == ["pipeline.py", "2"]
```

That is why this works:

```python
day = int(sys.argv[1])
```

Without an `ENTRYPOINT`, Docker would treat the final `2` as the command to
run:

```bash
docker run -it test:pandas 2
```

Docker would try to execute a program literally named `2`, causing:

```text
exec: "2": executable file not found in $PATH
```

The entrypoint fixes that by telling Docker:

```text
The command is uv run python pipeline.py.
Anything after the image name is an argument to that command.
```

## Build the Image

Run this command from the `pipeline` folder:

```bash
docker build -t test:pandas .
```

Breakdown:

```text
docker build        build a Docker image
-t test:pandas      name the image test with tag pandas
.                   use the current folder as the build context
```

The build context is the set of local files Docker is allowed to copy into the
image. Because the command ends with `.`, Docker uses the current folder.

That matters because the Dockerfile has lines like:

```dockerfile
COPY pipeline.py pipeline.py
COPY "pyproject.toml" "uv.lock" ".python-version" ./
```

Docker can only copy those files if they are inside the build context.

## Run the Pipeline in Docker

After building the image, run:

```bash
docker run -it test:pandas 2
```

Breakdown:

```text
docker run      start a container from an image
-it             interactive terminal flags
test:pandas     image name and tag
2               argument passed to pipeline.py
```

Because of the entrypoint, this becomes:

```bash
uv run python pipeline.py 2
```

If you want Docker to automatically remove the stopped container afterward, use:

```bash
docker run --rm -it test:pandas 2
```

`--rm` is useful for short one-off jobs because it avoids leaving stopped
containers behind.

## Useful Docker Commands

Build the image:

```bash
docker build -t test:pandas .
```

List local images:

```bash
docker images
```

Run the pipeline for day `2`:

```bash
docker run -it test:pandas 2
```

Run the pipeline for day `10`:

```bash
docker run -it test:pandas 10
```

Run and remove the stopped container afterward:

```bash
docker run --rm -it test:pandas 2
```

General pattern:

```bash
docker build -t IMAGE_NAME:TAG .
docker run -it IMAGE_NAME:TAG ARGUMENT
```

For this project:

```text
IMAGE_NAME = test
TAG = pandas
ARGUMENT = the day number, such as 2 or 10
```

## Important Learning Points

- `FROM` chooses the starting environment.
- `COPY --from=...` can copy files from another Docker image.
- `WORKDIR` controls where later commands run.
- `ENV PATH=...` changes which commands are found first.
- `COPY` brings your project files into the image.
- `RUN` executes commands at image build time.
- `ENTRYPOINT` chooses the command that runs at container start time.
- Arguments after the image name in `docker run` are passed to the entrypoint.
- `uv.lock` makes dependency installation more reproducible.
- Copying dependency files before app code helps Docker cache package installs.
