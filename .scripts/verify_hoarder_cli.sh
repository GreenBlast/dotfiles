#!/bin/bash


TEMP_DIR="/tmp/hoarder_cli_config"
HOARDER_KEY_FILE="${TEMP_DIR}/hoarder_key"
HOARDER_ADDRESS_FILE="${TEMP_DIR}/hoarder_address"

function get_bw_session() {
    if [ -z "${BW_SESSION}" ]; then
        export BW_SESSION=$(bw unlock --raw)
        if [ $? -ne 0 ]; then
            echo "Failed to unlock Bitwarden"
            exit 1
        fi
    fi
}

function set_hoarder_key_from_file() {
    HOARDER_KEY=$(cat "${HOARDER_KEY_FILE}")
    if [ $? -ne 0 ]; then
        echo "Failed to read Hoarder key from file"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
    echo "Hoarder key set from file"
}

function set_hoarder_address_from_file() {
    HOARDER_ADDRESS=$(cat "${HOARDER_ADDRESS_FILE}")
    if [ $? -ne 0 ]; then
        echo "Failed to read Hoarder address from file"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
    echo "Hoarder address set from file"
}


function create_hoarder_key_file() {
    # Create secure temporary directory and file if they don't exist
    mkdir -p "${TEMP_DIR}"
    chmod 700 "${TEMP_DIR}"
    chown "$(whoami)" "${TEMP_DIR}"
    
    get_bw_session
    
    bw get password "hoarder api cli key" > "${HOARDER_KEY_FILE}"
    if [ $? -ne 0 ]; then
        echo "Failed to get Hoarder API key"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
    chmod 600 "${HOARDER_KEY_FILE}"
}

function create_hoarder_address_file() {
    # Create secure temporary directory and file if they don't exist
    mkdir -p "${TEMP_DIR}"
    chmod 700 "${TEMP_DIR}"
    chown "$(whoami)" "${TEMP_DIR}"
    
    get_bw_session
    
    bw get password "hoarder api cli address" > "${HOARDER_ADDRESS_FILE}"
    if [ $? -ne 0 ]; then
        echo "Failed to get Hoarder API address"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
    chmod 600 "${HOARDER_ADDRESS_FILE}"
}

function verify_hoarder_cli_key_and_address() {
    # Check if hoarder key is already set
    if [ ! -z "${HOARDER_KEY}" ] && [ ! -z "${HOARDER_ADDRESS}" ]; then
        return 0
    fi
    
    # Check if hoarder key file exists
    if [ ! -f "${HOARDER_KEY_FILE}" ]; then
        echo "Hoarder key file does not exist"
        create_hoarder_key_file
    fi
    

    if [ ! -f "${HOARDER_ADDRESS_FILE}" ]; then
        echo "Hoarder address file does not exist"
        create_hoarder_address_file
    fi


    # Create new hoarder key file and set key
    set_hoarder_key_from_file
    set_hoarder_address_from_file
}
