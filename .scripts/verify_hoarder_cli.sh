#!/bin/bash
# NOTE: this file is *sourced* into an interactive shell (see pat/pav/apat in
# ~/.config/zsh/aliases.zsh). Never use `exit` here -- it would kill the shell
# (and close the tmux pane). Always `return` and let callers propagate.

# Cache lives under ~/.config (not /tmp): macOS purges /tmp every few days, which
# turned a once-per-reboot unlock prompt into a once-every-few-days one.
TEMP_DIR="${HOME}/.config/hoarder-cli"
HOARDER_KEY_FILE="${TEMP_DIR}/hoarder_key"
HOARDER_ADDRESS_FILE="${TEMP_DIR}/hoarder_address"

function get_bw_session() {
    if [ -n "${BW_SESSION}" ]; then
        return 0
    fi

    # `bw unlock` only works when logged in but locked. If the CLI has been
    # logged out entirely (tokens cleared, e.g. after a Vaultwarden restart)
    # it fails with "You are not logged in." -- say so plainly instead of
    # letting the caller guess.
    # NB: not named `status` -- that is a read-only builtin variable in zsh,
    # and this file is sourced into zsh.
    local bw_state
    bw_state=$(bw status 2>/dev/null)
    case "${bw_state}" in
        *'"status":"unauthenticated"'*)
            echo "Bitwarden CLI is logged out. Run:  bw login" >&2
            return 1
            ;;
    esac

    local session
    # Assign separately from `export`: `export VAR=$(cmd)` reports the status
    # of `export`, not of the command substitution.
    session=$(bw unlock --raw)
    if [ $? -ne 0 ] || [ -z "${session}" ]; then
        echo "Failed to unlock Bitwarden" >&2
        return 1
    fi

    export BW_SESSION="${session}"
}

function _hoarder_make_temp_dir() {
    mkdir -p "${TEMP_DIR}" || return 1
    chmod 700 "${TEMP_DIR}" || return 1
}

# _hoarder_fetch_secret <bitwarden item name> <destination file>
function _hoarder_fetch_secret() {
    local item="$1"
    local dest="$2"
    local value

    _hoarder_make_temp_dir || return 1
    get_bw_session || return 1

    # Fetch into a variable first, so a failed lookup can't leave an empty
    # file behind that later looks like a valid cached secret.
    value=$(bw get password "${item}")
    if [ $? -ne 0 ] || [ -z "${value}" ]; then
        echo "Failed to get '${item}' from Bitwarden" >&2
        return 1
    fi

    printf '%s\n' "${value}" > "${dest}" || return 1
    chmod 600 "${dest}" || return 1
}

function create_hoarder_key_file() {
    _hoarder_fetch_secret "hoarder api cli key" "${HOARDER_KEY_FILE}"
}

function create_hoarder_address_file() {
    _hoarder_fetch_secret "hoarder api cli address" "${HOARDER_ADDRESS_FILE}"
}

# _hoarder_read_file <file> -- echoes contents, fails if missing or empty
function _hoarder_read_file() {
    local file="$1"
    local value

    value=$(cat "${file}" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "${value}" ]; then
        echo "Failed to read ${file}" >&2
        # Drop the unusable cache so the next run re-fetches from Bitwarden.
        rm -f "${file}"
        return 1
    fi

    printf '%s' "${value}"
}

function verify_hoarder_cli_key_and_address() {
    # Already set for this shell -- nothing to do.
    if [ -n "${HOARDER_KEY}" ] && [ -n "${HOARDER_ADDRESS}" ]; then
        return 0
    fi

    if [ ! -s "${HOARDER_KEY_FILE}" ]; then
        echo "Hoarder key file does not exist"
        create_hoarder_key_file || return 1
    fi

    if [ ! -s "${HOARDER_ADDRESS_FILE}" ]; then
        echo "Hoarder address file does not exist"
        create_hoarder_address_file || return 1
    fi

    HOARDER_KEY=$(_hoarder_read_file "${HOARDER_KEY_FILE}") || return 1
    HOARDER_ADDRESS=$(_hoarder_read_file "${HOARDER_ADDRESS_FILE}") || return 1
}

# ---------------------------------------------------------------------------
# Preferred path: a credential broker that holds the API key on our behalf.
#
# The broker validates a per-machine token, then REPLACES the Authorization
# header with the real API key -- so this machine never holds that key and needs
# no Bitwarden unlock. Because the header is replaced, we can hand the broker
# token straight to the CLI as its --api-key.
#
# This file is in a PUBLIC dotfiles repo, so the broker's address and token are
# NOT defined here -- both come from ~/.zshenv, which is deliberately untracked.
# With either unset we simply fall through to the Bitwarden path below.
# ---------------------------------------------------------------------------
function _hoarder_broker_ok() {
    [ -n "${AGENT_BROKER_TOKEN}" ] || return 1
    [ -n "${HOARDER_BROKER_ADDR}" ] || return 1

    local code
    code=$(curl -s -o /dev/null -m 3 -w '%{http_code}' \
        -H "Authorization: Bearer ${AGENT_BROKER_TOKEN}" \
        "${HOARDER_BROKER_ADDR}/api/trpc" 2>/dev/null)

    # 000/empty = dockerhost unreachable (off the tailnet, host down, sealed).
    # 401/403   = broker up but refusing us -- fall back rather than fail hard.
    case "${code}" in
        ''|000|401|403) return 1 ;;
        *) return 0 ;;
    esac
}

# Sets HOARDER_KEY + HOARDER_ADDRESS from the broker, falling back to the
# Bitwarden-backed cache. This is what pat/pav/apat call.
function hoarder_cli_creds() {
    if [ -n "${HOARDER_KEY}" ] && [ -n "${HOARDER_ADDRESS}" ]; then
        return 0
    fi

    if _hoarder_broker_ok; then
        HOARDER_KEY="${AGENT_BROKER_TOKEN}"
        HOARDER_ADDRESS="${HOARDER_BROKER_ADDR}"
        return 0
    fi

    echo "hoarder-proxy broker unavailable; falling back to Bitwarden" >&2
    verify_hoarder_cli_key_and_address
}
