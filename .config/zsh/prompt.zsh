# Setting to show timestamp at prompt
SPACESHIP_TIME_SHOW=true

# Timestamp format
SPACESHIP_TIME_FORMAT="[%D{%T}]"

# Setting suffix for time
SPACESHIP_TIME_SUFFIX=' '

# Setting user prefix
SPACESHIP_USER_PREFIX=''

# Setting user suffix
SPACESHIP_USER_SUFFIX=''

# Setting user color
SPACESHIP_USER_COLOR='blue'

# Setting host prefix
SPACESHIP_HOST_PREFIX="%{$FG[247]%}@%f"

# Setting host prefix
SPACESHIP_HOST_SUFFIX="%{$FG[226]%}:%f"

# Directory prefix
SPACESHIP_DIR_PREFIX=''

# Set no newline in spaceship prompt
export SPACESHIP_PROMPT_ADD_NEWLINE=false

# Command line is one line
export SPACESHIP_PROMPT_SEPARATE_LINE=false

# Don't truncate dirpath
export SPACESHIP_DIR_TRUNC=0

# Disable git prefix
export SPACESHIP_GIT_PREFIX=''

# Setting different user and host function (Always shown)
# USER
# If user is root, then paint it in red. Otherwise, just print in yellow.
spaceship_user() {
  [[ $SPACESHIP_USER_SHOW == false ]] && return

    local user_color

    if [[ $USER == 'root' ]]; then
      user_color=$SPACESHIP_USER_COLOR_ROOT
    else
      user_color="$SPACESHIP_USER_COLOR"
    fi

    _prompt_section \
      "$user_color" \
      "$SPACESHIP_USER_PREFIX" \
      '%n' \
      "$SPACESHIP_USER_SUFFIX"
}

# HOST
# If there is an ssh connections, current machine name.
spaceship_host() {
  [[ $SPACESHIP_HOST_SHOW == false ]] && return

  _prompt_section \
    "$SPACESHIP_HOST_COLOR" \
    "$SPACESHIP_HOST_PREFIX" \
    '%m' \
    "$SPACESHIP_HOST_SUFFIX"
}

# BACKGROUND JOBS
SPACESHIP_BACKGROUND_JOBS_SHOW="${SPACESHIP_BACKGROUND_JOBS_SHOW:-true}"
SPACESHIP_BACKGROUND_JOBS_SYMBOL="${SPACESHIP_BACKGROUND_JOBS_SYMBOL:-⚙}"
export SPACESHIP_BACKGROUND_JOBS_SYMBOL="%{$FG[208]%}✱%f"

# Are there background jobs running?
spaceship_background_jobs_status() {
  [[ $SPACESHIP_BACKGROUND_JOBS_SHOW == false ]] && return

  [[ $(jobs -l | wc -l) -gt 0 ]] && echo -n "${SPACESHIP_BACKGROUND_JOBS_SYMBOL} "
}


# Setting right prompt to git
RPROMPT='$(spaceship_git)'

# Setting order of prompt objects, excluding git
SPACESHIP_PROMPT_ORDER=(
    time
    user
    host
    dir
    hg
    node
    ruby
    xcode
    swift
    golang
    php
    rust
    julia
    docker
    venv
    pyenv
    line_sep
    vi_mode
    background_jobs_status
    char
)

# Set prompt symbol
export SPACESHIP_PROMPT_SYMBOL='➔>'

ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=248'
