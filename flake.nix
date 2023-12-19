{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/nixos-23.11";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };
  outputs = { nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        inherit system;
      };
    in rec {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          python3
          python311Packages.google
          python311Packages.google-api-core
          python311Packages.google-api-python-client
          python311Packages.google-auth
          python311Packages.google-auth-httplib2
          python311Packages.google-auth-oauthlib
          python311Packages.googleapis-common-protos
          python311Packages.slack-sdk
          python311Packages.luhn
        ];
      };
    }
  );
}