# Mnemosyne memory for Hermes

Mnemosyne implements Hermes' memory provider interface as a plugin. It is not
a network service, so this setup adds no Compose service or exposed port. It
uses Hermes' existing persistent `/opt/data` mount for the wrapper and database.

## Install

The script uses the Python interpreter in the official Hermes container and
installs the last audited stable pair: `mnemosyne-memory[embeddings]==3.15.1`
and `mnemosyne-hermes==0.7.1`. It stores the wrapper environment in
`/opt/data/venvs/mnemosyne`, enables the plugin, selects it as the memory
provider, and checks the reported provider status. A Hermes Python minor-version
change stops the script so the persistent environment is reviewed before it is
replaced.

To apply the setup manually to the existing service:

```sh
ssh <vps> 'docker exec -i hermes-agent sh -s' < scripts/install_mnemosyne.sh
```

The Hostinger deployment workflow runs this script after a reviewed image
update. It does not read or alter Hostinger's environment-variable values.

## Persistent data and backup

Mnemosyne's main SQLite database is
`/opt/data/mnemosyne/data/mnemosyne.db`. Keep the existing `/opt/data` Docker
volume mounted when updating Hermes; do not add a nested mount until the live
Compose file and volume layout have been inventoried.

The production workflow takes an SQLite online backup of only `mnemosyne.db`
before each update and sends it to the Restic repository on Google Drive.
Restic encrypts the snapshot on the runner before upload. The first setup may
skip the backup only if that database has not been created yet and the operator
selects the one-time bootstrap checkbox. Every later missing-database or backup
failure stops deployment. The workflow does not restore automatically; test
restores separately and review the provider's memory status after a recovery.

## Upstream references

- [Mnemosyne Hermes integration guide](https://github.com/mnemosyne-oss/mnemosyne/blob/main/docs/hermes-integration.md)
- [Hermes Docker setup](https://hermes-agent.nousresearch.com/docs/user-guide/docker)
