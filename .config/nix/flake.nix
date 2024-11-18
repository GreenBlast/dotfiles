{
  description = "nix-darwin system flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:LnL7/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
    nix-homebrew.url = "github:zhaofengli-wip/nix-homebrew";
  };

  outputs = inputs@{ self, nix-darwin, nixpkgs, nix-homebrew}:
  let
    configuration = { pkgs, config, ... }: {

      config.allowUnfree = true;

      # List packages installed in system profile. To search by name, run:
      # $ nix-env -qaP | grep wget
      environment.systemPackages =
        [ 
          ## Brew
          pkgs.jadx
          pkgs.lazygit
          pkgs.pandoc
          pkgs.mongosh
          pkgs.yt-dlp
          pkgs.sshpass
          pkgs.htop
          pkgs.zoxide
          pkgs.duf
          pkgs.ncdu
          pkgs.dust
          pkgs.exa
          pkgs.imagemagick
          pkgs.neovim
          pkgs.silver-searcher
          pkgs.ffmpeg

          ## Brew Cask
          pkgs.keycastr
          pkgs.mongodb-compass

          ## Store
          pkgs.bitwarden-desktop
          pkgs.todoist-electron
          pkgs.telegram-desktop
          pkgs.slack
          pkgs.xcodes

          ## Launchpad
          pkgs.raycast
          pkgs.android-file-transfer
          pkgs.docker_26
          pkgs.obsidian
          pkgs.zoom-us
          pkgs.jetbrains.webstorm
          pkgs.mos
          pkgs.code-cursor


          ## Don't need right now
          #pkgs.zsh
          #pkgs.circleci
          #pkgs.tig
        ];

      fonts.packages = [
        (pkgs.nerdfonts.override { fonts = [ "JetBrainsMono" ]; })
      ];

      # Necessary for using flakes on this system.
      nix.settings.experimental-features = "nix-command flakes";

      # Enable alternative shell support in nix-darwin.
      # programs.fish.enable = true;

      # Set Git commit hash for darwin-version.
      system.configurationRevision = self.rev or self.dirtyRev or null;

      # Used for backwards compatibility, please read the changelog before changing.
      # $ darwin-rebuild changelog
      system.stateVersion = 5;

      # The platform the configuration will be used on.
      nixpkgs.hostPlatform = "aarch64-darwin";
    };
  in
  {
    # Build darwin flake using:
    # $ darwin-rebuild build --flake .#simple
    darwinConfigurations."mac" = nix-darwin.lib.darwinSystem {
      modules = [
        configuration 
        nix-homebrew.darwinModules.nix-hombrew
        {
            nix-hombrew = {
                enable = true;
                casks = [
                  "notunes"
                ];
                # Apple Silicon Only
                enableRosetta = true;
                # User owning the hombrew prefix
                user = "user";
                
                # Handle the fact that brew is already installed
                autoMigrate = true;
              };
          }
      ];
    };

    # Expose the package set, including overlays, for convenience.
    darwinPackages = self.darwinConfigurations."mac".pkgs;
  };
}
