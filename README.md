# target-squarespace

`target-squarespace` is a Singer target for Squarespace.

Build with the [Meltano Target SDK](https://sdk.meltano.com).

## Installation

- [ ] `Developer TODO:` Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

```bash
pipx install target-squarespace
```

## Configuration

Two authentication methods are supported: **API Key** and **OAuth 2.0**. Use OAuth when you have a registered Squarespace API application; otherwise use an API key.

| Name | Required | Description | Example |
|------|----------|-------------|---------|
| `api_key` | Yes (API key auth) | Squarespace API key used to authenticate requests via Bearer token. Not required when using OAuth. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `client_id` | Yes (OAuth) | OAuth application client ID. When present, OAuth auth is used instead of API key. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `client_secret` | Yes (OAuth) | OAuth application client secret. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `refresh_token` | Yes (OAuth) | OAuth refresh token. Used to obtain a new access token automatically. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `access_token` | No (OAuth) | Current OAuth access token. Written back to the config file after each refresh. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### Example config — API key

```json
{
  "api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

### Example config — OAuth

```json
{
  "client_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

> **API key:** Generate one from your Squarespace account under **Settings → Advanced → API Keys**. Ensure the key has the Commerce (Orders) permission scope.
>
> **OAuth:** Register an application in the [Squarespace Developer Platform](https://developers.squarespace.com/). The target uses the refresh token grant to keep the access token up-to-date automatically, writing the new tokens back to the config file after each refresh.

## Usage

You can easily run `target-squarespace` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-squarespace --version
target-squarespace --help
# Test using the "Carbon Intensity" sample:
tap-carbon-intensity | target-squarespace --config /path/to/target-squarespace-config.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `target_squarespace/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `target-squarespace` CLI interface directly using `poetry run`:

```bash
poetry run target-squarespace --help
```

### Testing with [Meltano](https://meltano.com/)

_**Note:** This target will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd target-squarespace
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke target-squarespace --version
# OR run a test `elt` pipeline with the Carbon Intensity sample tap:
meltano elt tap-carbon-intensity target-squarespace
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the Meltano SDK to
develop your own Singer taps and targets.
