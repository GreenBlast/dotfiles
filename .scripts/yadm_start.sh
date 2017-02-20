#/bin/sh

# Check git command
type git || {
  echo 'Please install git or update your path to include the git executable!'
  exit 1
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

$HOME/.local/bin/yadm clone https://github.com/GreenBlast/dotfiles.git
