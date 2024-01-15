<!--
Copyright (C) 2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
-->

# UCS@school User Management

## Documentation

To run the liveserver for developing the documentation run the following command in the repository's root:

```shell
docker run -ti --rm -v "$PWD:/project" -w /project -u $UID --network=host --pull always \
docker-registry.knut.univention.de/sphinx:latest \
make -C docs/user-management-manual/ livehtml
```
