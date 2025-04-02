{
  description = "nix-darwin system flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:LnL7/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
    nix-homebrew.url = "github:zhaofengli-wip/nix-homebrew";

    # Optional: Declarative tap management
    # homebrew-core = {
    #   url = "github:homebrew/homebrew-core";
    #   flake = false;
    # };
    # homebrew-cask = {
    #   url = "github:homebrew/homebrew-cask";
    #   flake = false;
    # };
    # homebrew-bundle = {
    #   url = "github:homebrew/homebrew-bundle";
    #   flake = false;
    # };
  };

  outputs = inputs@{ self, nix-darwin, nixpkgs, nix-homebrew }:
  let
    configuration = { pkgs, ... }: {


      nixpkgs.config.allowUnfree = true;

      # List packages installed in system profile. To search by name, run:
      # $ nix-env -qaP | grep wget
      environment.systemPackages =
        [ 
          ## Brew
          # pkgs.jadx
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
          pkgs.eza
          pkgs.imagemagick
          pkgs.neovim
          pkgs.silver-searcher
          pkgs.ffmpeg

          ## Brew Cask
          pkgs.keycastr
          # pkgs.mongodb-compass # Compass doesn't exist for aarch64-darwin

          ## Store
          # pkgs.bitwarden-desktop # Bitwarden doesn't exist for aarch64-darwin
          # pkgs.todoist-electron # Todoist doesn't exist for aarch64-darwin
          pkgs.telegram-desktop
          pkgs.slack
          pkgs.xcodes

          ## Launchpad
          pkgs.raycast
          pkgs.android-file-transfer
          # pkgs.docker_26
          pkgs.obsidian
          # pkgs.zoom-us # Not playing well with permissions, using self installed zoom
          pkgs.jetbrains.webstorm
          pkgs.mos
          # pkgs.code-cursor # Code Cursor doesn't exist for aarch64-darwin


          ## Don't need right now
          #pkgs.zsh
          #pkgs.circleci
          #pkgs.tig

          ## New packages
          pkgs.fabric-ai
          pkgs.wezterm
          pkgs.aerospace
          pkgs.skhd
          pkgs.google-cloud-sdk
          pkgs.gtypist
          pkgs.atuin
          # pkgs.ghostty # ghostty is marked as broken for darwin
          pkgs.syncthing
          # pkgs.kanata # Kanata is marked as broken for darwin
          pkgs.uv
          pkgs.awscli2

          (pkgs.callPackage ./phantomjs.nix {})

          pkgs.fswatch
          pkgs.unison

        ];

            homebrew = {
                enable = true;

                brews = [
                  # "mas"
                  "kanata" # Kanata is marked as broken in nix packages
                ];
                casks = [
                  "notunes"
                  "ghostty" # ghostty is marked as broken in nix packages
                  # "docker" # Docker is annoying apple security
                ];
                
                # taps = [ 
                # ];
                # masApps = {  };
                
                onActivation.autoUpdate = true;
                onActivation.upgrade = true;

                
              };

      # fonts.packages = [
      #   (pkgs.nerdfonts.override { fonts = [ "JetBrainsMono" ]; })
      # ];

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
      # system = "aarch64-darwin";
      modules = [
        configuration 
        nix-homebrew.darwinModules.nix-homebrew
        {
            nix-homebrew = {
                enable = true;

                # Apple Silicon Only
                enableRosetta = true;

                # # Optional: Declarative tap management
                # taps = {
                #   "homebrew/homebrew-core" = homebrew-core;
                #   "homebrew/homebrew-cask" = homebrew-cask;
                #   "homebrew/homebrew-bundle" = homebrew-bundle;
                # };

                # User owning the homebrew prefix
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
