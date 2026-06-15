{
  description = "OCRBridge monorepo";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";
    nix-darwin.url = "github:nix-darwin/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, nix-darwin, ... }:
    flake-utils.lib.eachSystem (import ./nix/systems.nix)
      (system:
        let
          pkgs = import nixpkgs { inherit system; };
          isLinux = pkgs.stdenv.hostPlatform.isLinux;
          isDarwin = pkgs.stdenv.hostPlatform.isDarwin;
          pythonEnvs = import ./nix/python-envs.nix {
            inherit pkgs;
            inherit (pkgs) lib;
            inherit (inputs) pyproject-nix uv2nix pyproject-build-systems;
          };
        in
        {
          packages = pythonEnvs.packages // {
            default = pythonEnvs.packages.ocr-service-lite;
          };

          apps = {
            default = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-lite; };
            ocr-service-lite = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-lite; };
            ocr-service-full = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-full; };
          } // pkgs.lib.optionalAttrs isDarwin {
            ocr-service-macos = flake-utils.lib.mkApp { drv = pythonEnvs.packages.ocr-service-macos; };
          };

          devShells.default = pkgs.mkShell {
            packages = [ pkgs.nixpkgs-fmt ];
          };

          checks = pkgs.lib.optionalAttrs isLinux
            {
              nixos-module-eval = import ./nix/tests/nixos-module-eval.nix {
                inherit nixpkgs self system;
              };
            } // pkgs.lib.optionalAttrs isDarwin {
            darwin-module-eval = import ./nix/tests/darwin-module-eval.nix {
              inherit nix-darwin nixpkgs self system;
            };
          };
        }) // {
      nixosModules.ocr-service = import ./nix/modules/nixos/ocr-service.nix;
      darwinModules.ocr-service = import ./nix/modules/darwin/ocr-service.nix;
    };
}
