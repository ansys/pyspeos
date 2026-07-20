# Contribute

Overall guidance on contributing to a PyAnsys library appears in the
[Contributing] topic in the *PyAnsys developer's guide*. Ensure that you
are thoroughly familiar with this guide before attempting to contribute to
PySpeos.

[Contributing]: https://dev.docs.pyansys.com/how-to/contributing.html

<!-- Begin content specific to your library here. -->
The following contribution information is specific to PySpeos.


## Running tests locally

PySpeos core tests require an active Speos RPC server. In this repository,
`tests/local_config.json` is configured to use Docker by default:

- container name: `speos-rpc`
- port: `50098`
- asset mount path inside the container: `/app/assets`

To match the current CI setup, start the Docker image before running the test suite:

```bash
docker login ghcr.io/ansys
docker run --detach --name speos-rpc \
  -p 127.0.0.1:50098:50098 \
  -e SPEOS_LOG_LEVEL=2 \
  -e ANSYSLMD_LICENSE_FILE=$LICENSE_SERVER \
  -v "$(pwd)/tests/assets:/app/assets" \
  --entrypoint /app/SpeosRPC_Server.x \
  ghcr.io/ansys/speos-rpc:dev \
  --transport_insecure --host 0.0.0.0
```

The `docker login` step requires credentials that can pull `ghcr.io/ansys/speos-rpc`.
Use the same GHCR access process documented in `README.rst` before starting the container.

Then install the test dependencies and run pytest:

```bash
python -m pip install -e . --group tests
pytest -xs
```

When you are done, stop and remove the container:

```bash
docker kill speos-rpc
docker rm speos-rpc
```