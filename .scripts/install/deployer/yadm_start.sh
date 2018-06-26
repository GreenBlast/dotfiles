#/bin/sh

# Check git command
type git || {
    echo "No git, Attempting to install git"
    apt-get install -q -y git

    type git || {
        echo "Git install failed, exiting"
        exit 1
    }
}
echo ""


# Check yadm command

type yadm || {
echo 'Attempting to download yadm'
mkdir -p $HOME/.local/bin/
curl -fLo $HOME/.local/bin/yadm https://github.com/TheLocehiliosan/yadm/raw/master/yadm || exit 1
chmod a+x $HOME/.local/bin/yadm || exit 1

}

echo ""

echo "Cloning"

$HOME/.local/bin/yadm clone --bootstrap https://github.com/GreenBlast/dotfiles.git
