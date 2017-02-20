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
curl -fLo /home/$USER/.local/bin/yadm https://github.com/TheLocehiliosan/yadm/raw/master/yadm || exit 1
chmod a+x /home/$USER/.local/bin/yadm || exit 1

}

echo ""

echo "Cloning"

yadm clone git@github.com:GreenBlast/dotfiles.git
